import asyncio
import asyncpg

async def test():
    db = await asyncpg.connect('postgresql://postgres:12345@localhost:5432/smclasses')
    rows = await db.fetch('SELECT id, email, is_active FROM users')
    print([dict(r) for r in rows])
    await db.close()

if __name__ == "__main__":
    asyncio.run(test())
