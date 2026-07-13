import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("No DATABASE_URL found")
        return

    try:
        conn = await asyncpg.connect(db_url)
        
        # Add new columns if they don't exist
        queries = [
            "ALTER TABLE courses ADD COLUMN IF NOT EXISTS description TEXT;",
            "ALTER TABLE courses ADD COLUMN IF NOT EXISTS duration VARCHAR(100);",
            "ALTER TABLE courses ADD COLUMN IF NOT EXISTS students VARCHAR(100);",
            "ALTER TABLE courses ADD COLUMN IF NOT EXISTS curriculum JSONB DEFAULT '[]'::jsonb;",
            "ALTER TABLE courses ADD COLUMN IF NOT EXISTS features JSONB DEFAULT '[]'::jsonb;"
        ]
        
        for q in queries:
            await conn.execute(q)
            print(f"Executed: {q}")
            
        await conn.close()
        print("Migration complete.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
