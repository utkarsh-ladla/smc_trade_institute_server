import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    users = await conn.fetch("SELECT id, email, is_admin FROM users")
    print(f"Users in DB before: {users}")
    await conn.execute("UPDATE users SET is_admin = True")
    print("Updated all users to admin")
    users = await conn.fetch("SELECT id, email, is_admin FROM users")
    print(f"Users in DB after: {users}")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
