import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def alter_admissions_table():
    try:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        await conn.execute("ALTER TABLE admissions ADD COLUMN IF NOT EXISTS additional_info TEXT;")
        print("Successfully added additional_info column to admissions table")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(alter_admissions_table())
