import io

import pytest
from django.core.management import call_command

@pytest.mark.story("S-001")
def test_server_healthcheck(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ok") is True


@pytest.mark.story("S-001")
def test_worker_heartbeat(db):
    buffer = io.StringIO()
    call_command("huey_healthcheck", stdout=buffer)
    buffer.seek(0)
    assert "redis-ok" in buffer.read()
