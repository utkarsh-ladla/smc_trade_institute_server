import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run():
    try:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        
        # Drop all existing tables by dropping and recreating the public schema
        print("Dropping public schema to wipe all integer tables...")
        await conn.execute("DROP SCHEMA public CASCADE;")
        await conn.execute("CREATE SCHEMA public;")
        await conn.execute("GRANT ALL ON SCHEMA public TO postgres;")
        await conn.execute("GRANT ALL ON SCHEMA public TO public;")
        print("Schema recreated.")
        
        with open('database.sql', 'r') as f:
            sql = f.read()
        await conn.execute(sql)
        print("Successfully created all UUID tables from database.sql")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
