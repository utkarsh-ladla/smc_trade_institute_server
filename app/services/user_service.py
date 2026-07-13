from uuid import UUID
from typing import List, Optional
import asyncpg
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserInDB

class UserService:
    def __init__(self, connection: asyncpg.Connection):
        self.repo = UserRepository(connection)
        
    async def get_user(self, user_id: UUID) -> Optional[UserInDB]:
        return await self.repo.get_by_id(user_id)
        
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        return await self.repo.get_all(skip, limit)

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        return await self.repo.get_by_email(email)

    async def create_user(self, user_data: dict) -> UserInDB:
        return await self.repo.create(user_data)

    async def change_password(self, user_id: UUID, new_hashed_password: str) -> bool:
        return await self.repo.update_password(user_id, new_hashed_password)
