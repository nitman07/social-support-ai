import asyncio
import uuid

from backend.database.postgres import UserModel, async_session_factory, init_db
from backend.services.auth_service import hash_password


async def main():
    await init_db()
    async with async_session_factory() as session:
        admin = UserModel(
            id=uuid.uuid4(),
            username="admin",
            hashed_password=hash_password("admin123"),
            role="admin",
            full_name="System Administrator",
            active=True,
        )
        session.add(admin)

        reviewer = UserModel(
            id=uuid.uuid4(),
            username="reviewer",
            hashed_password=hash_password("reviewer123"),
            role="reviewer",
            full_name="Senior Reviewer",
            active=True,
        )
        session.add(reviewer)
        await session.commit()
        print("Seeded admin and reviewer users")


if __name__ == "__main__":
    asyncio.run(main())
