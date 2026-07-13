import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import db

async def migrate():
    print("Starting database migration for Languages...")
    await db.connect()
    
    try:
        await db.pool.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Languages table created or already exists.")
        
        try:
            await db.pool.execute("""
                ALTER TABLE books ADD COLUMN IF NOT EXISTS language_id UUID REFERENCES languages(id) ON DELETE SET NULL;
            """)
            print("Added language_id column to books table.")
        except Exception as e:
            print(f"Error adding language_id column (it may already exist): {e}")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        await db.disconnect()
        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
