from typing import AsyncGenerator
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.database.postgres import (
    UserModel,
    async_session_factory,
    init_db,
)
from backend.main import app
from backend.services.auth_service import hash_password


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    async with async_session_factory() as session:
        admin = UserModel(
            id=uuid4(),
            username=f"test_admin_{uuid4().hex[:6]}",
            hashed_password=hash_password("test123"),
            role="admin",
            full_name="Test Admin",
            active=True,
        )
        session.add(admin)
        await session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": admin.username, "password": "test123"},
    )
    return resp.json()["access_token"]
