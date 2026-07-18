from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import razorpay
import os
from typing import Dict, Any, Optional
from uuid import UUID
import asyncpg
import hmac
import hashlib

from app.api.dependencies.db import get_db_connection
from app.repositories.order_repo import OrderRepository

router = APIRouter(prefix="/payment", tags=["Payment"])

# Initialize Razorpay client


class OrderRequest(BaseModel):
    amount: float
    course_id: Optional[UUID] = None
    user_email: Optional[str] = None

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@router.post("/create-order")
async def create_order(
    request: OrderRequest,
    db: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    try:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")
            
        amount_in_paise = int(request.amount * 100)
        receipt_id = "receipt_order_" + os.urandom(4).hex()
        
        data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": receipt_id
        }
        
        from app.core.config import settings
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # 1. Create order with Razorpay
        try:
            from fastapi.concurrency import run_in_threadpool
            print(f"Attempting to create razorpay order with amount {amount_in_paise} paise")
            payment = await run_in_threadpool(razorpay_client.order.create, data=data)
            print(f"Successfully created order: {payment['id']}")
        except Exception as rp_e:
            print(f"Razorpay creation failed: {rp_e}")
            raise rp_e
        
        # 2. Store order in database
        try:
            print("Attempting to store order in database")
            repo = OrderRepository(db)
            await repo.create_order({
            "razorpay_order_id": payment["id"],
            "amount": amount_in_paise,
            "currency": "INR",
            "status": "created",
            "receipt": receipt_id,
            "course_id": request.course_id,
            "user_email": request.user_email
        })
        except Exception as db_e:
            print(f"Database operation failed: {db_e}")
            raise db_e
        
        return payment
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-payment")
async def verify_payment(
    verification: PaymentVerification,
    db: asyncpg.Connection = Depends(get_db_connection)
) -> Dict[str, Any]:
    try:
        repo = OrderRepository(db)
        
        # 1. Check if order exists in DB
        order = await repo.get_order_by_razorpay_id(verification.razorpay_order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # 2. Verify signature
        # Razorpay's utility can be used, or we can manually check HMAC SHA256
        params_dict = {
            'razorpay_order_id': verification.razorpay_order_id,
            'razorpay_payment_id': verification.razorpay_payment_id,
            'razorpay_signature': verification.razorpay_signature
        }
        
        try:
            from app.core.config import settings
            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_client.utility.verify_payment_signature(params_dict)
        except razorpay.errors.SignatureVerificationError:
            await repo.update_payment_status(
                verification.razorpay_order_id,
                verification.razorpay_payment_id,
                verification.razorpay_signature,
                "failed"
            )
            raise HTTPException(status_code=400, detail="Signature verification failed")

        # 3. Signature is valid, update status to paid
        await repo.update_payment_status(
            verification.razorpay_order_id,
            verification.razorpay_payment_id,
            verification.razorpay_signature,
            "paid"
        )
        
        return {"status": "success", "message": "Payment verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: asyncpg.Connection = Depends(get_db_connection)
):
    try:
        from app.core.config import settings
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        
        # If webhook secret is not configured, we might not want to process or we can skip verification (dangerous)
        if not webhook_secret:
            raise HTTPException(status_code=400, detail="Webhook secret not configured")

        signature = request.headers.get("x-razorpay-signature")
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")
            
        body = await request.body()
        payload_str = body.decode('utf-8')
        
        # Verify signature
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            razorpay_client.utility.verify_webhook_signature(payload_str, signature, webhook_secret)
        except razorpay.errors.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Parse payload
        import json
        payload = json.loads(payload_str)
        event = payload.get("event")
        
        repo = OrderRepository(db)
        
        if event == "payment.failed":
            payment_entity = payload["payload"]["payment"]["entity"]
            order_id = payment_entity.get("order_id")
            payment_id = payment_entity.get("id")
            if order_id:
                await repo.update_status(order_id, "failed", payment_id=payment_id)
                
        elif event == "order.paid":
            order_entity = payload["payload"]["order"]["entity"]
            order_id = order_entity.get("id")
            if order_id:
                await repo.update_status(order_id, "paid")
                
        # Other events can be handled here (payment.captured, payment.authorized, etc.)
        
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Webhook processing error: {e}")
        # Return 200 even on processing error so Razorpay doesn't keep retrying unnecessarily, or 500 if we want retries. 
        # Usually best to return 200 and log the error if signature verified.
        return {"status": "error", "detail": str(e)}

