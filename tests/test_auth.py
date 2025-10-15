import pytest
from django.contrib.auth.models import User

@pytest.mark.story("S-011")
def test_login_page_renders(client):
    r = client.get("/accounts/login/")
    assert r.status_code == 200

@pytest.mark.story("S-011")
def test_login_flow_success(client, django_user_model):
    u = django_user_model.objects.create_user(username="u1", password="p1")
    r = client.post("/accounts/login/", {"username":"u1","password":"p1"}, follow=True)
    assert r.status_code == 200


@pytest.mark.story("S-011")
def test_login_invalid(client, django_user_model):
    django_user_model.objects.create_user(username="u2", password="p2")
    r = client.post("/accounts/login/", {"username":"u2","password":"wrong"})
    assert r.status_code == 200
    assert "Please enter a correct" in r.content.decode()
