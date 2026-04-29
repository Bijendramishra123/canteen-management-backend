# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
import os
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://backend:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB Connection - Use environment variable or default to mongodb service name
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
client = MongoClient(MONGO_URI)
db = client["canteenDB"]
users_collection = db["users"]
foods_collection = db["foods"]
orders_collection = db["orders"]

print(f"Connected to MongoDB at: {MONGO_URI}")

# Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class FoodCreate(BaseModel):
    name: str
    price: float
    category: str
    image: Optional[str] = None
    description: Optional[str] = None
    availability: Optional[bool] = True

class FoodUpdate(BaseModel):
    availability: bool

class OrderItem(BaseModel):
    food_id: int
    quantity: int
    price: float
    name: str

class OrderCreate(BaseModel):
    items: List[OrderItem]
    total_amount: float
    customer_name: str
    customer_phone: str
    customer_email: str
    special_instructions: Optional[str] = None
    tip_amount: Optional[float] = 0
    number_of_people: Optional[int] = 1

class StatusUpdate(BaseModel):
    status: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ============ AUTH ROUTES ============
@app.post("/api/auth/register")
async def register(user: UserCreate):
    existing_user = users_collection.find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    new_user = {
        "name": user.name,
        "email": user.email.lower(),
        "role": "user",
        "hashed_password": pwd_context.hash(user.password)
    }
    result = users_collection.insert_one(new_user)
    access_token = create_access_token(data={"sub": user.email.lower()})
    return {
        "message": "Registration successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(result.inserted_id),
            "name": user.name,
            "email": user.email,
            "role": "user"
        }
    }

@app.post("/api/auth/login")
async def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email.lower()})
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    if not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid password")
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(db_user["_id"]),
            "name": db_user["name"],
            "email": db_user["email"],
            "role": db_user["role"]
        }
    }

# ============ FOOD ROUTES ============
@app.get("/api/foods")
async def get_foods():
    foods = []
    for food in foods_collection.find():
        food["_id"] = str(food["_id"])
        foods.append(food)
    return foods

@app.post("/api/foods")
async def create_food(food: FoodCreate):
    food_dict = food.dict()
    last_food = foods_collection.find_one(sort=[("id", -1)])
    new_id = (last_food["id"] + 1) if last_food else 1
    food_dict["id"] = new_id
    result = foods_collection.insert_one(food_dict)
    food_dict["_id"] = str(result.inserted_id)
    return food_dict

@app.put("/api/foods/{food_id}")
async def update_food(food_id: int, food: FoodCreate):
    existing = foods_collection.find_one({"id": food_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Food not found")
    
    update_data = {
        "name": food.name,
        "price": food.price,
        "category": food.category,
        "description": food.description,
        "image": food.image,
        "availability": food.availability
    }
    foods_collection.update_one({"id": food_id}, {"$set": update_data})
    updated_food = foods_collection.find_one({"id": food_id})
    updated_food["_id"] = str(updated_food["_id"])
    return updated_food

@app.delete("/api/foods/{food_id}")
async def delete_food(food_id: int):
    result = foods_collection.delete_one({"id": food_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Food not found")
    return {"message": "Food deleted successfully"}

@app.patch("/api/foods/{food_id}/availability")
async def toggle_availability(food_id: int, update: FoodUpdate):
    result = foods_collection.update_one({"id": food_id}, {"$set": {"availability": update.availability}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Food not found")
    return {"message": "Availability updated"}

# ============ ORDER ROUTES ============
@app.post("/api/orders")
async def create_order(order: OrderCreate):
    last_order = orders_collection.find_one(sort=[("id", -1)])
    new_id = (last_order["id"] + 1) if last_order else 1
    order_dict = order.dict()
    order_dict["id"] = new_id
    order_dict["status"] = "pending"
    order_dict["created_at"] = datetime.now().isoformat()
    result = orders_collection.insert_one(order_dict)
    order_dict["_id"] = str(result.inserted_id)
    return order_dict

@app.get("/api/orders")
async def get_orders():
    orders = []
    for order in orders_collection.find():
        order["_id"] = str(order["_id"])
        orders.append(order)
    return orders

@app.patch("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, status_update: StatusUpdate):
    result = orders_collection.update_one({"id": order_id}, {"$set": {"status": status_update.status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Status updated"}

@app.get("/")
def root():
    return {"message": "Canteen Backend Running with MongoDB"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
