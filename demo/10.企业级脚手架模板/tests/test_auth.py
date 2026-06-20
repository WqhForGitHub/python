"""认证与 RBAC 集成测试。"""
import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_and_me(client):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "Admin123456"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert token

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert me.json()["is_superuser"] is True


@pytest.mark.asyncio
async def test_protected_without_token(client):
    resp = await client.get("/api/v1/users/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_list_users(client):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "Admin123456"},
    )
    token = resp.json()["access_token"]
    resp = await client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_register_and_login(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "Bob123456"},
    )
    assert resp.status_code == 200

    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "bob", "password": "Bob123456"},
    )
    assert resp.status_code == 200
