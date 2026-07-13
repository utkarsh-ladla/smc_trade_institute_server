import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("DATABASE_URL not set in .env")
        return

    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Adding columns to resources table...")
        await conn.execute("""
            ALTER TABLE resources ADD COLUMN IF NOT EXISTS pages INT DEFAULT 0;
            ALTER TABLE resources ADD COLUMN IF NOT EXISTS rating FLOAT DEFAULT 0.0;
            ALTER TABLE resources ADD COLUMN IF NOT EXISTS downloads INT DEFAULT 0;
            ALTER TABLE resources ADD COLUMN IF NOT EXISTS topics JSONB DEFAULT '[]'::jsonb;
        """)
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
