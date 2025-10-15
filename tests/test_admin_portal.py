import pytest


@pytest.mark.story("S-007")
def test_admin_portal_requires_admin(client, django_user_model):
    url = "/admin-portal/"
    response = client.get(url)
    assert response.status_code == 302 and "/accounts/login/" in response.url

    staff_user = django_user_model.objects.create_user(username="staff", password="pw", is_staff=True)
    client.force_login(staff_user)
    response = client.get(url)
    assert response.status_code == 200
    assert "Admin Portal" in response.content.decode()
