from tests.conftest import PLATFORM_EMAIL, PLATFORM_PASSWORD, auth_header, register


def test_register_login_me_and_refresh_rotation(client):
    created = register(client, "owner@example.com", "Acme")
    assert created["user"]["email"] == "owner@example.com"
    assert created["organizations"][0]["role"] == "organization_admin"
    assert created["organizations"][0]["name"] == "Acme"

    me = client.get("/api/v1/auth/me", headers=auth_header(created["access_token"]))
    assert me.status_code == 200
    assert me.json()["user"]["full_name"] == "Test User"

    renamed = client.patch(
        "/api/v1/auth/me",
        headers=auth_header(created["access_token"]),
        json={"full_name": "Acme Owner"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["full_name"] == "Acme Owner"

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": created["refresh_token"]})
    assert refreshed.status_code == 200
    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": created["refresh_token"]})
    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "UNAUTHORIZED"

    login = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "Password123"})
    assert login.status_code == 200
    body = login.json()

    changed = client.post(
        "/api/v1/auth/change-password",
        headers=auth_header(body["access_token"]),
        json={"current_password": "Password123", "new_password": "NewPassword123"},
    )
    assert changed.status_code == 204
    old_login = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "Password123"})
    assert old_login.status_code == 401
    new_login = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "NewPassword123"})
    assert new_login.status_code == 200
    revoked = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    assert revoked.status_code == 401

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": new_login.json()["refresh_token"]})
    assert logout.status_code == 204
    after_logout = client.post("/api/v1/auth/refresh", json={"refresh_token": new_login.json()["refresh_token"]})
    assert after_logout.status_code == 401


def test_duplicate_register_and_password_rules(client):
    register(client, "owner@example.com", "Acme")
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "Password123",
            "full_name": "Other",
            "organization_name": "Other Co",
        },
    )
    assert duplicate.status_code == 409

    weak = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "password",
            "full_name": "Weak",
            "organization_name": "Weak Co",
        },
    )
    assert weak.status_code == 400
    short = client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@example.com",
            "password": "a1",
            "full_name": "Short",
            "organization_name": "Short Co",
        },
    )
    assert short.status_code == 422


def test_protected_route_requires_bearer_token(client):
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 401


def test_platform_admin_bootstrap_login(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": PLATFORM_EMAIL, "password": PLATFORM_PASSWORD},
    )
    assert response.status_code == 200
    assert response.json()["user"]["is_platform_admin"] is True
