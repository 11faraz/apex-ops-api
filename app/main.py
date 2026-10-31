"""Apex Operations API - a small Flask service with health, readiness and metrics.

Everything is configured through environment variables so the same image runs
unchanged on a laptop, in CI and in the cloud.
"""
import hmac
import json
import logging
import os
import sqlite3
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request

VALID_STATUSES = {"open", "in_progress", "done"}


class JsonFormatter(logging.Formatter):
    """One JSON object per line, easy to grep and easy for log tools to parse."""

    def format(self, record):
        entry = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        entry.update(getattr(record, "fields", {}))
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def build_logger():
    logger = logging.getLogger("apex")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    return logger


def create_app(db_path=None, api_key=None, version=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.getenv("DB_PATH", "/data/ops.db")
    app.config["API_KEY"] = api_key if api_key is not None else os.getenv("API_KEY", "")
    app.config["VERSION"] = version or os.getenv("APP_VERSION", "dev")
    app.config["FAULT"] = os.getenv("FAULT_INJECTION", "")  # demo only, off by default
    log = build_logger()
    started = time.time()
    requests_total = defaultdict(int)
    duration = {"sum": 0.0, "count": 0}

    def connect():
        return sqlite3.connect(app.config["DB_PATH"], timeout=2)

    def init_db():
        try:
            with connect() as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS operations ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, "
                    "status TEXT NOT NULL, created_at TEXT NOT NULL)"
                )
            log.info("database ready", extra={"fields": {"db_path": app.config["DB_PATH"]}})
        except sqlite3.Error as exc:
            # Do not crash: /ready will report the problem and the logs explain it.
            log.error("database init failed", extra={"fields": {"error": str(exc)}})

    init_db()

    @app.before_request
    def start_timer():
        g.start = time.perf_counter()
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]

    @app.after_request
    def log_request(response):
        elapsed = time.perf_counter() - g.start
        rule = request.url_rule.rule if request.url_rule else "unmatched"
        requests_total[(request.method, rule, response.status_code)] += 1
        duration["sum"] += elapsed
        duration["count"] += 1
        response.headers["X-Request-ID"] = g.request_id
        log.info(
            "request",
            extra={"fields": {
                "request_id": g.request_id,
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": round(elapsed * 1000, 2),
            }},
        )
        return response

    def require_key():
        configured = app.config["API_KEY"]
        if not configured:
            return jsonify(error="API key is not configured on the server"), 503
        sent = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(sent, configured):
            return jsonify(error="missing or invalid API key"), 401
        return None

    @app.get("/health")
    def health():
        """Liveness: the process is up. It deliberately checks nothing else."""
        return jsonify(status="ok")

    @app.get("/ready")
    def ready():
        """Readiness: the app can do real work, so the database must answer."""
        if app.config["FAULT"] == "not_ready":
            log.error("readiness failed", extra={"fields": {"reason": "fault injection"}})
            return jsonify(status="not_ready", reason="fault injection (demo)"), 503
        try:
            with connect() as conn:
                conn.execute("SELECT 1")
        except sqlite3.Error as exc:
            log.error("readiness failed", extra={"fields": {"reason": str(exc)}})
            return jsonify(status="not_ready", reason="database unavailable"), 503
        return jsonify(status="ready")

    @app.get("/version")
    def version_info():
        return jsonify(version=app.config["VERSION"])

    @app.post("/operations")
    def create_operation():
        denied = require_key()
        if denied:
            return denied
        body = request.get_json(silent=True) or {}
        name = body.get("name")
        status = body.get("status", "open")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
            return jsonify(error="name is required (1-100 characters)"), 400
        if status not in VALID_STATUSES:
            return jsonify(error=f"status must be one of {sorted(VALID_STATUSES)}"), 400
        created = datetime.now(timezone.utc).isoformat()
        try:
            with connect() as conn:
                cur = conn.execute(
                    "INSERT INTO operations (name, status, created_at) VALUES (?, ?, ?)",
                    (name.strip(), status, created),
                )
                new_id = cur.lastrowid
        except sqlite3.Error as exc:
            log.error("insert failed", extra={"fields": {"error": str(exc)}})
            return jsonify(error="database unavailable"), 503
        return jsonify(id=new_id, name=name.strip(), status=status, created_at=created), 201

    @app.get("/operations")
    def list_operations():
        try:
            with connect() as conn:
                rows = conn.execute(
                    "SELECT id, name, status, created_at FROM operations ORDER BY id"
                ).fetchall()
        except sqlite3.Error as exc:
            log.error("query failed", extra={"fields": {"error": str(exc)}})
            return jsonify(error="database unavailable"), 503
        keys = ("id", "name", "status", "created_at")
        return jsonify([dict(zip(keys, row)) for row in rows])

    @app.get("/operations/<int:op_id>")
    def get_operation(op_id):
        try:
            with connect() as conn:
                row = conn.execute(
                    "SELECT id, name, status, created_at FROM operations WHERE id = ?",
                    (op_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            log.error("query failed", extra={"fields": {"error": str(exc)}})
            return jsonify(error="database unavailable"), 503
        if row is None:
            return jsonify(error="operation not found"), 404
        return jsonify(dict(zip(("id", "name", "status", "created_at"), row)))

    @app.get("/metrics")
    def metrics():
        lines = [
            "# HELP apex_http_requests_total Requests handled, by method, route and status.",
            "# TYPE apex_http_requests_total counter",
        ]
        for (method, rule, status), count in sorted(requests_total.items()):
            labels = f'method="{method}",path="{rule}",status="{status}"'
            lines.append(f"apex_http_requests_total{{{labels}}} {count}")
        lines += [
            "# TYPE apex_http_request_duration_seconds summary",
            f"apex_http_request_duration_seconds_sum {duration['sum']:.6f}",
            f"apex_http_request_duration_seconds_count {duration['count']}",
            "# TYPE apex_uptime_seconds gauge",
            f"apex_uptime_seconds {time.time() - started:.0f}",
            "# TYPE apex_app_info gauge",
            f'apex_app_info{{version="{app.config["VERSION"]}"}} 1',
        ]
        return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; version=0.0.4"}

    return app
