import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        await conn.execute("ALTER TABLE admissions ADD COLUMN additional_info JSONB DEFAULT '{}'::jsonb;")
        print("Column added successfully!")
    except Exception as e:
        print("Error:", e)
    finally:
        await conn.close()

asyncio.run(main())
