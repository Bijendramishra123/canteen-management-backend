# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

# Database
users_db = [
    {"id": "1", "name": "Admin User", "email": "admin@example.com", "role": "admin", "hashed_password": pwd_context.hash("admin123")},
    {"id": "2", "name": "Test User", "email": "test@example.com", "role": "user", "hashed_password": pwd_context.hash("test123")},
    {"id": "3", "name": "Bijendra Mishra", "email": "bijendramishra2002@gmail.com", "role": "user", "hashed_password": pwd_context.hash("bijendra123")}
]

foods_db = [
    {"id": 1, "name": "Fried Rice", "price": 249, "category": "main", "description": "Delicious fried rice with vegetables", "image": "/fried-rice.jpeg", "availability": True},
    {"id": 2, "name": "Paneer Butter Masala", "price": 299, "category": "main", "description": "Creamy paneer curry", "image": "/paneer-butter-masala.jpeg", "availability": True},
    {"id": 3, "name": "Coca Cola", "price": 49, "category": "beverages", "description": "Chilled soft drink", "image": "/coca-cola.jpeg", "availability": True},
    {"id": 4, "name": "Cheeseburger", "price": 179, "category": "main", "description": "Juicy cheeseburger", "image": "/cheeseburger.jpeg", "availability": True},
    {"id": 5, "name": "Pizza Slice", "price": 199, "category": "main", "description": "Cheesy pizza slice", "image": "/pizza-slice.jpeg", "availability": True},
    {"id": 6, "name": "Food Platter", "price": 399, "category": "main", "description": "Complete meal platter", "image": "/food-platter.jpeg", "availability": True},
    {"id": 7, "name": "Aloo Paratha", "price": 89, "category": "main", "description": "Stuffed potato paratha", "image": "/aloo-paratha.jpeg", "availability": True},
    {"id": 8, "name": "Sprite", "price": 49, "category": "beverages", "description": "Refreshing drink", "image": "/sprite-logo.jpeg", "availability": True},
]

orders_db = []
next_food_id = 9
next_order_id = 1

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/api/auth/register")
async def register(user: UserCreate):
    for existing_user in users_db:
        if existing_user["email"].lower() == user.email.lower():
            raise HTTPException(status_code=400, detail="Email already exists")
    new_id = str(len(users_db) + 1)
    new_user = {"id": new_id, "name": user.name, "email": user.email.lower(), "role": "user", "hashed_password": pwd_context.hash(user.password)}
    users_db.append(new_user)
    access_token = create_access_token(data={"sub": user.email.lower()})
    return {"message": "Registration successful", "access_token": access_token, "token_type": "bearer", "user": {"id": new_user["id"], "name": new_user["name"], "email": new_user["email"], "role": new_user["role"]}}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    db_user = None
    for u in users_db:
        if u["email"].lower() == user.email.lower():
            db_user = u
            break
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    if not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid password")
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"message": "Login successful", "access_token": access_token, "token_type": "bearer", "user": {"id": db_user["id"], "name": db_user["name"], "email": db_user["email"], "role": db_user["role"]}}

@app.get("/api/foods")
async def get_foods(search: Optional[str] = Query(None, description="Search by food name")):
    if search:
        filtered_foods = [food for food in foods_db if search.lower() in food["name"].lower()]
        return filtered_foods
    return foods_db

@app.post("/api/foods")
async def create_food(food: FoodCreate):
    global next_food_id
    new_food = {"id": next_food_id, "name": food.name, "price": food.price, "category": food.category, "description": food.description or "", "image": food.image or "", "availability": food.availability}
    foods_db.append(new_food)
    next_food_id += 1
    return new_food

@app.patch("/api/foods/{food_id}/availability")
async def toggle_availability(food_id: int, update: FoodUpdate):
    for food in foods_db:
        if food["id"] == food_id:
            food["availability"] = update.availability
            return {"message": f"Availability updated to {update.availability}", "food": food}
    raise HTTPException(status_code=404, detail="Food not found")

@app.delete("/api/foods/{food_id}")
async def delete_food(food_id: int):
    global foods_db
    foods_db = [f for f in foods_db if f["id"] != food_id]
    return {"message": "Food deleted successfully"}

@app.post("/api/orders")
async def create_order(order: OrderCreate):
    global next_order_id
    new_order = {
        "id": next_order_id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "customer_email": order.customer_email,
        "items": [item.dict() for item in order.items],
        "total_amount": order.total_amount,
        "tip_amount": order.tip_amount,
        "number_of_people": order.number_of_people,
        "special_instructions": order.special_instructions,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    orders_db.append(new_order)
    next_order_id += 1
    return new_order

@app.get("/api/orders")
async def get_orders():
    return orders_db

@app.patch("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, status_update: StatusUpdate):
    for order in orders_db:
        if order["id"] == order_id:
            order["status"] = status_update.status
            return {"message": "Status updated", "order": order}
    raise HTTPException(status_code=404, detail="Order not found")

@app.get("/")
def root():
    return {"message": "Canteen Backend Running"}
