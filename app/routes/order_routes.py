from fastapi import APIRouter, Depends
from app.schemas.order_schema import OrderCreate
from app.services.order_service import place_order, get_all_orders, update_order_status
from app.utils.dependencies import get_current_user

router = APIRouter()

# 🔥 Place Order (User)
@router.post("/")
def create_order(order: OrderCreate, user=Depends(get_current_user)):
    return place_order(order)

# 🔥 Get All Orders (Admin)
@router.get("/")
def fetch_orders(user=Depends(get_current_user)):
    return get_all_orders()

# 🔥 Update Status (Admin)
@router.put("/{order_id}")
def update_status(order_id: str, status: str, user=Depends(get_current_user)):
    return update_order_status(order_id, status)