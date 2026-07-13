import asyncio
import asyncpg
import bcrypt

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

async def fix_db():
    db = await asyncpg.connect('postgresql://postgres:12345@localhost:5432/smclasses')
    
    try:
        await db.execute('DROP TABLE IF EXISTS users CASCADE;')
        
        await db.execute('''
            CREATE TABLE users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                full_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        hashed_pw = get_password_hash("admin")
        
        await db.execute('''
            INSERT INTO users (email, hashed_password, is_admin, full_name)
            VALUES ($1, $2, True, 'Admin')
        ''', 'admin@smclasses.com', hashed_pw)

        await db.execute('''
            INSERT INTO users (email, hashed_password, is_admin, full_name)
            VALUES ($1, $2, True, 'Admin User')
        ''', 'admin@gmail.com', hashed_pw)
        
        print("Users table fixed successfully.")
    except Exception as e:
        print("Error:", e)
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(fix_db())
