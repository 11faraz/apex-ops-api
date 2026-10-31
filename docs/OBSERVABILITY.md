# Observability

## Structured logs
Every request writes one JSON line to stdout, so Docker, and later any log tool, can collect it:

```json
{"ts": "2026-10-30T06:01:35+00:00", "level": "INFO", "msg": "request", "request_id": "9f2c1a7b3d10", "method": "GET", "path": "/ready", "status": 200, "duration_ms": 1.4}
```

Errors log the reason, for example `{"level": "ERROR", "msg": "readiness failed", "reason": "unable to open database file"}`.
Each response carries an `X-Request-ID` header so a user report can be matched to a log line. Secrets are never logged.

## Health checks
- `/health` (liveness) and `/ready` (readiness, includes a database query).
- Docker's `HEALTHCHECK` and the Compose healthcheck call these endpoints; `docker compose ps` shows `healthy` or `unhealthy`.

## Metrics
`GET /metrics` exposes request counts by method, route and status, request duration sum and count, uptime, and the running version.

## Alert proposal (Prometheus rules)

```yaml
groups:
  - name: apex-ops-api
    rules:
      - alert: ApiDown
        expr: up{job="apex-ops-api"} == 0
        for: 2m
        labels: {severity: page}
        annotations: {summary: "API is not responding"}
      - alert: HighErrorRate
        expr: sum(rate(apex_http_requests_total{status=~"5.."}[5m])) / sum(rate(apex_http_requests_total[5m])) > 0.05
        for: 5m
        labels: {severity: page}
        annotations: {summary: "More than 5% of requests are failing"}
      - alert: SlowRequests
        expr: rate(apex_http_request_duration_seconds_sum[5m]) / rate(apex_http_request_duration_seconds_count[5m]) > 0.5
        for: 10m
        labels: {severity: ticket}
        annotations: {summary: "Average latency above 500 ms"}
      - alert: NotReady
        expr: sum(rate(apex_http_requests_total{path="/ready",status="503"}[5m])) > 0
        for: 2m
        labels: {severity: page}
        annotations: {summary: "Readiness is failing: check the database"}
```

Thresholds are starting points and should be tuned after a week of real traffic. These rules are a proposal; they are not running in this submission.
