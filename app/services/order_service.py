from app.config.db import orders_collection
from datetime import datetime

def place_order(order):
    order_data = order.dict()
    
    order_data["status"] = "Preparing"
    order_data["created_at"] = datetime.utcnow()
    
    result = orders_collection.insert_one(order_data)
    
    return {
        "message": "Order placed successfully",
        "order_id": str(result.inserted_id)
    }


def get_all_orders():
    orders = []
    
    for order in orders_collection.find():
        order["_id"] = str(order["_id"])
        orders.append(order)
    
    return orders


def update_order_status(order_id, status):
    from bson import ObjectId
    
    orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": status}}
    )
    
    return {"message": "Order status updated"}