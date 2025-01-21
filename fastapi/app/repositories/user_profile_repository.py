import asyncpg
from app.models.user_profile import UserProfile, UserProfileCreate
import uuid
from typing import List

class UserProfileRepository:
    def __init__(self, connection):
        self.connection = connection

    async def create(self, user_profile: UserProfileCreate) -> UserProfile:
        user_id = str(uuid.uuid4())
        await self.connection.execute(
            "INSERT INTO user_profiles (id, name, email, is_deleted) VALUES ($1, $2, $3, $4)",
            user_id, user_profile.name, user_profile.email, False
        )
        return UserProfile(id=user_id, name=user_profile.name, email=user_profile.email, is_deleted=False)

    async def get_by_id(self, user_id: str) -> UserProfile:
        row = await self.connection.fetchrow("SELECT * FROM user_profiles WHERE id = $1", user_id)
        if row:
            return UserProfile(**row)
        return None

    async def update(self, user_profile: UserProfile) -> UserProfile:
        await self.connection.execute(
            "UPDATE user_profiles SET name = $1, email = $2 WHERE id = $3",
            user_profile.name, user_profile.email, user_profile.id
        )
        return user_profile

    async def delete(self, user_id: str):
        await self.connection.execute("DELETE FROM user_profiles WHERE id = $1", user_id)

    async def get_all(self) -> List[UserProfile]:
        rows = await self.connection.fetch("SELECT * FROM user_profiles")
        return [UserProfile(**row) for row in rows]

    async def soft_delete(self, user_id: str):
        await self.connection.execute(
            "UPDATE user_profiles SET is_deleted = TRUE WHERE id = $1", user_id
        )

    async def get_all_active(self) -> List[UserProfile]:
        rows = await self.connection.fetch("SELECT * FROM user_profiles WHERE is_deleted = FALSE")
        return [UserProfile(**row) for row in rows]

    async def get_all_inactive(self) -> List[UserProfile]:
        rows = await self.connection.fetch("SELECT * FROM user_profiles")
        return [UserProfile(**row) for row in rows]
