import asyncpg
from typing import Dict, Any, Optional
from uuid import UUID

class OrderRepository:
    def __init__(self, db: asyncpg.Connection):
        self.db = db

    async def create_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO orders (
                razorpay_order_id, amount, currency, status, receipt, course_id, user_email
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7
            ) RETURNING *;
        """
        row = await self.db.fetchrow(
            query,
            data["razorpay_order_id"],
            data["amount"],
            data.get("currency", "INR"),
            data.get("status", "created"),
            data.get("receipt"),
            data.get("course_id"),
            data.get("user_email")
        )
        return dict(row) if row else None

    async def update_payment_status(self, razorpay_order_id: str, payment_id: str, signature: str, status: str) -> bool:
        query = """
            UPDATE orders 
            SET razorpay_payment_id = $1, razorpay_signature = $2, status = $3
            WHERE razorpay_order_id = $4
            RETURNING id;
        """
        row = await self.db.fetchrow(query, payment_id, signature, status, razorpay_order_id)
        return bool(row)

    async def update_status(self, razorpay_order_id: str, status: str, payment_id: Optional[str] = None) -> bool:
        if payment_id:
            query = """
                UPDATE orders 
                SET status = $1, razorpay_payment_id = $2
                WHERE razorpay_order_id = $3
                RETURNING id;
            """
            row = await self.db.fetchrow(query, status, payment_id, razorpay_order_id)
        else:
            query = """
                UPDATE orders 
                SET status = $1
                WHERE razorpay_order_id = $2
                RETURNING id;
            """
            row = await self.db.fetchrow(query, status, razorpay_order_id)
        return bool(row)

    async def get_order_by_razorpay_id(self, razorpay_order_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM orders WHERE razorpay_order_id = $1"
        row = await self.db.fetchrow(query, razorpay_order_id)
        return dict(row) if row else None

    async def get_pending_orders(self) -> list[Dict[str, Any]]:
        query = "SELECT * FROM orders WHERE status = 'created'"
        rows = await self.db.fetch(query)
        return [dict(row) for row in rows]
