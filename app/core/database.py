import asyncpg
from app.core.config import settings

class Database:
    pool: asyncpg.Pool = None
    
    async def connect(self):
        print("Connecting to database...")
        self.pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=10
        )
        print("Connected to database.")
        
    async def disconnect(self):
        print("Closing database connection...")
        if self.pool:
            await self.pool.close()
        print("Database connection closed.")
        
db = Database()
