import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run():
    try:
        db_url = os.getenv("DATABASE_URL")
        print(f"Connecting to database...")
        conn = await asyncpg.connect(db_url)
        
        print("Applying migration to make book_id optional and add package_name column...")
        await conn.execute("ALTER TABLE orders ALTER COLUMN book_id DROP NOT NULL;")
        await conn.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS package_name VARCHAR(255);")
        
        print("Migration successfully applied!")
        await conn.close()
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
