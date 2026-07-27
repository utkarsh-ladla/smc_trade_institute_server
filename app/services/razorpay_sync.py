import asyncio
import razorpay
from fastapi.concurrency import run_in_threadpool
from app.core.config import settings
from app.core.database import db
from app.repositories.order_repo import OrderRepository

async def sync_razorpay_orders():
    """
    Background task to sync the status of pending Razorpay orders.
    Runs continuously, checking every minute.
    """
    while True:
        try:
            print("Running Razorpay sync check...")
            if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                print("Razorpay keys not configured. Skipping sync.")
                await asyncio.sleep(60)
                continue
                
            if not db.pool:
                print("Database pool not initialized. Waiting...")
                await asyncio.sleep(10)
                continue
                
            async with db.pool.acquire() as conn:
                repo = OrderRepository(conn)
                pending_orders = await repo.get_pending_orders()
                
                if pending_orders:
                    print(f"Found {len(pending_orders)} pending orders to sync.")
                    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    
                    for order in pending_orders:
                        rz_order_id = order.get("razorpay_order_id")
                        if not rz_order_id:
                            continue
                            
                        try:
                            print(f"Fetching details for Razorpay Order ID: {rz_order_id}")
                            # Fetch order details from Razorpay (using threadpool since razorpay client is sync)
                            rz_order = await run_in_threadpool(razorpay_client.order.fetch, rz_order_id)
                            
                            # Print the raw details received from Razorpay
                            print(f"Razorpay details for {rz_order_id}: {rz_order}")
                            
                            status = rz_order.get("status")
                            print(f"Current Razorpay status for {rz_order_id}: '{status}'")
                            
                            # If status is paid, update the database
                            if status == "paid":
                                await repo.update_status(rz_order_id, "paid")
                                print(f"Successfully updated order {rz_order_id} to paid in database.")
                            elif status == "failed":
                                await repo.update_status(rz_order_id, "failed")
                                print(f"Successfully updated order {rz_order_id} to failed in database.")
                            else:
                                print(f"No database update required for order {rz_order_id}. Still pending.")
                                
                        except Exception as inner_e:
                            print(f"Error syncing order {rz_order_id}: {inner_e}")
                else:
                    print("No pending orders to sync.")
                            
        except Exception as e:
            print(f"Error in sync_razorpay_orders task: {e}")
            
        # Wait 1 minute before checking again
        await asyncio.sleep(60)
