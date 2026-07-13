import asyncpg
from app.core.database import db

async def get_db_connection() -> asyncpg.Connection:
    if not db.pool:
        raise Exception("Database pool is not initialized")
    
    async with db.pool.acquire() as connection:
        yield connection
