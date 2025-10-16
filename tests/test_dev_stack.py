import io

import pytest
from django.core.management import call_command

@pytest.mark.story("S-001")
def test_server_healthcheck(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.content.decode() == "ok"


@pytest.mark.story("S-001")
def test_system_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200

    payload = r.json()
    assert payload["status"] in {"ok", "degraded"}
    assert isinstance(payload.get("uptime"), int)
    assert "version" in payload

    checks = payload["checks"]
    assert "db" in checks
    assert "queue" in checks
    assert "valkey" in checks
    assert checks["db"]["status"] == "ok"
    assert checks["queue"]["status"] in {"ok", "skipped"}


@pytest.mark.story("S-001")
def test_worker_heartbeat(db):
    buffer = io.StringIO()
    call_command("huey_healthcheck", stdout=buffer)
    buffer.seek(0)
    assert "redis-ok" in buffer.read()
