import pytest
from httpx import AsyncClient


class TestHealth:
    async def test_health_endpoint(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "Social Support AI" in data["service"]
        assert data["version"] == "0.1.0"


class TestMetrics:
    async def test_metrics_endpoint(self, client: AsyncClient):
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "request_count" in data
        assert "average_duration_ms" in data


class TestLogin:
    async def test_login_invalid_credentials(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "wrong"},
        )
        assert resp.status_code == 401

    async def test_login_missing_fields(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422


class TestAuthMiddleware:
    async def test_me_without_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_with_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert resp.status_code == 401

    async def test_applications_without_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/applications")
        assert resp.status_code == 401


class TestApplications:
    async def test_list_applications(self, client: AsyncClient, admin_token: str):
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.get("/api/v1/applications", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["page_size"] == 20

    async def test_list_applications_pagination(self, client: AsyncClient, admin_token: str):
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.get(
            "/api/v1/applications?page=1&page_size=5",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 5

    async def test_get_nonexistent_application(self, client: AsyncClient, admin_token: str):
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.get(
            "/api/v1/applications/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_process_nonexistent_application(self, client: AsyncClient, admin_token: str):
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.post(
            "/api/v1/applications/00000000-0000-0000-0000-000000000000/process",
            headers=headers,
        )
        assert resp.status_code == 404


class TestDecisions:
    async def test_flags_for_nonexistent_app(self, client: AsyncClient, admin_token: str):
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.get(
            "/api/v1/applications/00000000-0000-0000-0000-000000000000/flags",
            headers=headers,
        )
        assert resp.status_code in (200, 404)

    async def test_signoff_nonexistent_app(self, client: AsyncClient, admin_token: str):
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.post(
            "/api/v1/applications/00000000-0000-0000-0000-000000000000/signoff",
            headers=headers,
            json={"decision": "approved"},
        )
        assert resp.status_code == 404
