import os

from app.main import create_app

KEY = {"X-API-Key": "test-key"}


def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_ready_when_database_works(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ready"


def test_ready_fails_when_database_is_unreachable():
    app = create_app(db_path="/nonexistent-dir/ops.db", api_key="k")
    response = app.test_client().get("/ready")
    assert response.status_code == 503
    assert response.get_json()["status"] == "not_ready"


def test_version_comes_from_configuration(client):
    assert client.get("/version").get_json() == {"version": "9.9.9"}


def test_write_requires_api_key(client):
    response = client.post("/operations", json={"name": "rotate logs"})
    assert response.status_code == 401


def test_create_and_read_operation(client):
    created = client.post("/operations", json={"name": "rotate logs"}, headers=KEY)
    assert created.status_code == 201
    op_id = created.get_json()["id"]
    fetched = client.get(f"/operations/{op_id}")
    assert fetched.status_code == 200
    assert fetched.get_json()["name"] == "rotate logs"
    assert len(client.get("/operations").get_json()) == 1


def test_validation_rejects_bad_input(client):
    assert client.post("/operations", json={}, headers=KEY).status_code == 400
    bad_status = client.post("/operations", json={"name": "x", "status": "nope"}, headers=KEY)
    assert bad_status.status_code == 400


def test_unknown_operation_returns_404(client):
    assert client.get("/operations/999").status_code == 404


def test_metrics_expose_request_counter(client):
    client.get("/health")
    body = client.get("/metrics").get_data(as_text=True)
    assert "apex_http_requests_total" in body
    assert 'apex_app_info{version="9.9.9"} 1' in body


def test_every_response_has_a_request_id(client):
    response = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert response.headers["X-Request-ID"] == "abc123"


def test_intentional_failure_demo():
    """Passes normally. Set DEMO_FAIL=1 (or run the workflow with demo_fail=true) to see
    CI go red and block the build and deploy jobs."""
    if os.getenv("DEMO_FAIL") == "1":
        raise AssertionError("intentional failure: proving that CI blocks a broken release")
