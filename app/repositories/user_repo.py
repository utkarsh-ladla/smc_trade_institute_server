from uuid import UUID
from typing import List, Optional
import asyncpg
from app.schemas.user import UserInDB

class UserRepository:
    def __init__(self, connection: asyncpg.Connection):
        self.connection = connection
        
    async def get_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        query = """
            SELECT id, email, is_active, is_admin, full_name, created_at 
            FROM users 
            WHERE id = $1
        """
        row = await self.connection.fetchrow(query, user_id)
        if row:
            return UserInDB(**dict(row))
        return None
        
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        query = """
            SELECT id, email, is_active, is_admin, full_name, created_at 
            FROM users 
            ORDER BY id
            OFFSET $1 LIMIT $2
        """
        rows = await self.connection.fetch(query, skip, limit)
        return [UserInDB(**dict(row)) for row in rows]

    async def get_by_email(self, email: str) -> Optional[dict]:
        query = """
            SELECT id, email, hashed_password, is_active, is_admin, full_name, created_at 
            FROM users 
            WHERE email = $1
        """
        row = await self.connection.fetchrow(query, email)
        if row:
            return dict(row)
        return None

    async def create(self, user_data: dict) -> UserInDB:
        query = """
            INSERT INTO users (email, hashed_password, is_active, is_admin, full_name)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, email, is_active, is_admin, full_name, created_at
        """
        row = await self.connection.fetchrow(
            query,
            user_data["email"],
            user_data["hashed_password"],
            user_data.get("is_active", True),
            user_data.get("is_admin", False),
            user_data.get("full_name")
        )
        return UserInDB(**dict(row))

    async def update_password(self, user_id: UUID, new_hashed_password: str) -> bool:
        query = """
            UPDATE users
            SET hashed_password = $1
            WHERE id = $2
        """
        result = await self.connection.execute(query, new_hashed_password, user_id)
        return result == "UPDATE 1"
