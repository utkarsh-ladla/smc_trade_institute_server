import asyncio
import asyncpg
import sys
import os
from dotenv import load_dotenv

load_dotenv()

async def init_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        sys.exit(1)
        
    # Parse DB URL to get parts
    # Format: postgresql://user:pass@host:port/dbname
    try:
        # A simple parsing, assumes no @ or / in password
        prefix, rest = db_url.split("://")
        auth, host_db = rest.split("@")
        user, password = auth.split(":")
        host_port, target_db = host_db.split("/")
        host, port = host_port.split(":")
    except ValueError:
        print("Failed to parse DATABASE_URL")
        sys.exit(1)

    default_dsn = f"postgresql://{user}:{password}@{host}:{port}/postgres"
    target_dsn = db_url

    # 1. Create database
    print(f"Connecting to default database to create '{target_db}'...")
    try:
        conn = await asyncpg.connect(default_dsn)
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", target_db)
        if not exists:
            # Cannot run CREATE DATABASE in a transaction block
            # In asyncpg, you can just execute it if outside a transaction, 
            # but setting isolation level can also work. Actually, asyncpg auto-commits by default.
            try:
                await conn.execute(f"CREATE DATABASE {target_db}")
                print(f"Database '{target_db}' created successfully.")
            except asyncpg.exceptions.ActiveSQLTransactionError:
                pass
        else:
            print(f"Database '{target_db}' already exists.")
        await conn.close()
    except Exception as e:
        print(f"Failed to create database: {e}")
        # sys.exit(1) # We might not be able to connect to 'postgres' DB if user doesn't have access, we can still try creating table

    # 2. Create tables
    print(f"Connecting to '{target_db}' to create tables...")
    try:
        conn = await asyncpg.connect(target_dsn)
        users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            full_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        await conn.execute(users_table_query)
        print("Table 'users' created successfully.")
        await conn.close()
    except Exception as e:
        print(f"Failed to create tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_db())
