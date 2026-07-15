import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def create_orders_table():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            razorpay_order_id VARCHAR(255) UNIQUE NOT NULL,
            razorpay_payment_id VARCHAR(255),
            razorpay_signature VARCHAR(255),
            amount INT NOT NULL,
            currency VARCHAR(10) DEFAULT 'INR',
            status VARCHAR(50) DEFAULT 'created',
            receipt VARCHAR(255),
            course_id UUID,
            user_email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("orders table created successfully")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(create_orders_table())
