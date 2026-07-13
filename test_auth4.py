import asyncio
import asyncpg

async def test():
    db = await asyncpg.connect('postgresql://postgres:12345@localhost:5432/smclasses')
    rows = await db.fetch("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE column_name = 'id'")
    print([dict(r) for r in rows])
    await db.close()

if __name__ == "__main__":
    asyncio.run(test())
