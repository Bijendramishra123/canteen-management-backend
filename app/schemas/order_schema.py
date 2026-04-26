from pydantic import BaseModel
from typing import List

class OrderItem(BaseModel):
    food_id: str
    name: str
    price: float
    quantity: int

class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    items: List[OrderItem]
    total_amount: float
    order_type: str  # dine-in / takeaway