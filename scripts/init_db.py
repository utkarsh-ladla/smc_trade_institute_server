import asyncio
import asyncpg
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import get_password_hash

async def init_db():
    print(f"Connecting to {settings.DATABASE_URL}...")
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        print("Creating users table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                full_name VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("Creating categories table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                icon VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        print("Creating authors table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS authors (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                bio TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("Creating books table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                isbn VARCHAR(50),
                price DECIMAL(10, 2),
                author_id INTEGER REFERENCES authors(id) ON DELETE SET NULL,
                category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # For existing dev setups, try to add category_id if it's missing (fails silently if it exists)
        try:
            await conn.execute("ALTER TABLE books ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL")
        except asyncpg.exceptions.DuplicateColumnError:
            pass

        print("Creating reviews table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
                reviewer_name VARCHAR(255) NOT NULL,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                comment TEXT,
                is_approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        print("Creating blog_posts table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blog_posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                slug VARCHAR(255) UNIQUE NOT NULL,
                content TEXT NOT NULL,
                cover_image VARCHAR(500),
                published_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        print("Creating contact_messages table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                subject VARCHAR(255),
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if admin user exists
        admin_email = "admin@example.com"
        admin = await conn.fetchrow("SELECT id FROM users WHERE email = $1", admin_email)
        
        if not admin:
            print("Creating default admin user (admin@example.com / admin)...")
            hashed_pw = get_password_hash("admin")
            await conn.execute("""
                INSERT INTO users (email, hashed_password, is_admin, full_name)
                VALUES ($1, $2, TRUE, 'System Admin')
            """, admin_email, hashed_pw)
        else:
            print("Default admin user already exists.")
            
        print("Database initialization complete.")
        await conn.close()
    except Exception as e:
        print(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
