import pytest
@pytest.mark.story("S-004")
def test_htmx_header_response(client):
    r = client.get("/partial-example/", HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    assert "HTMX fragment ok" in r.content.decode()
