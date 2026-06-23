# -*- coding: utf-8 -*-
"""
Canteen Management System Backend API
FastAPI + MongoDB with OpenAPI/Specmatic Contract Testing Support

This API serves as the backend for a canteen management system with:
- User authentication (register/login with JWT)
- Food item management (CRUD operations)
- Order management (create, view, update status)
- Full OpenAPI specification with examples
- Contract testing ready with Specmatic

Author: Canteen Management Team
Version: 2.0.0
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
import os
import uvicorn

# ============================================================================
# Application Configuration
# ============================================================================

app = FastAPI(
    title="Canteen Management System API",
    description="""
    A comprehensive REST API for managing canteen operations including:
    
    * **User Management**: Registration and authentication with JWT tokens
    * **Food Management**: Create, read, update, and delete food items
    * **Order Management**: Place orders, view order history, update status
    * **Availability Control**: Toggle food item availability
    
    This API is designed with contract-first principles and is fully compatible
    with Specmatic for contract testing.
    """,
    version="2.0.0",
    contact={
        "name": "Canteen Management Team",
        "email": "support@canteen.com",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User registration and login operations"
        },
        {
            "name": "Food Items",
            "description": "CRUD operations for managing food items"
        },
        {
            "name": "Orders",
            "description": "Order placement and management"
        },
        {
            "name": "Health",
            "description": "Health check endpoints"
        }
    ]
)

# CORS middleware - Keep existing frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "https://canteen-management-frontend.vercel.app",
        "https://canteen-management-frontend-eight.vercel.app",
        "*"  # Allow all for testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["canteenDB"]
users_collection = db["users"]
foods_collection = db["foods"]
orders_collection = db["orders"]

print(f"✅ Connected to MongoDB at {MONGO_URI}")

# ============================================================================
# Helper Functions - Response Conversion (Fixes Specmatic Issues)
# ============================================================================

def convert_mongo_document(doc: dict, exclude_fields: List[str] = None) -> dict:
    """
    Convert MongoDB document to API response format.
    
    This function handles:
    1. Removing internal MongoDB fields (_id)
    2. Normalizing data types (e.g., null -> default values)
    3. Ensuring consistent response structure
    
    🔧 Fixes Specmatic Issues:
    - R2003: Unknown Property (_id leakage)
    - R1001: Type Mismatch (null values)
    """
    if not doc:
        return {}
    
    # Create a copy to avoid modifying original
    response = dict(doc)
    
    # 🔧 FIX: Remove MongoDB internal _id field (Solves Specmatic R2003)
    if "_id" in response:
        del response["_id"]
    
    # Remove any additional excluded fields
    if exclude_fields:
        for field in exclude_fields:
            if field in response:
                del response[field]
    
    # 🔧 FIX: Normalize availability - convert None/null to False (Solves Specmatic R1001)
    if "availability" in response:
        if response["availability"] is None:
            response["availability"] = False
        elif isinstance(response["availability"], bool):
            response["availability"] = response["availability"]
        else:
            # Convert any other truthy/falsy values to boolean
            response["availability"] = bool(response["availability"])
    
    return response


def convert_mongo_documents(docs: List[dict], exclude_fields: List[str] = None) -> List[dict]:
    """
    Convert a list of MongoDB documents to API response format.
    """
    return [convert_mongo_document(doc, exclude_fields) for doc in docs]


def get_next_sequence(collection, field: str = "id") -> int:
    """
    Get the next sequential ID for a collection.
    """
    last_doc = collection.find_one(sort=[(field, -1)])
    return (last_doc[field] + 1) if last_doc else 1

# ============================================================================
# Pydantic Models - Request/Response Contracts
# ============================================================================

# --- Authentication Models ---

class UserCreate(BaseModel):
    """User registration request model"""
    name: str = Field(..., description="Full name of the user", example="John Doe")
    email: EmailStr = Field(..., description="Valid email address", example="john@example.com")
    password: str = Field(..., description="Password (minimum 6 characters)", example="securePass123", min_length=6)


class UserLogin(BaseModel):
    """User login request model"""
    email: EmailStr = Field(..., description="Registered email address", example="john@example.com")
    password: str = Field(..., description="Account password", example="securePass123")


class UserResponse(BaseModel):
    """User information response model"""
    id: str = Field(..., description="User ID", example="507f1f77bcf86cd799439011")
    name: str = Field(..., description="Full name", example="John Doe")
    email: str = Field(..., description="Email address", example="john@example.com")
    role: str = Field(..., description="User role", example="user")


class AuthResponse(BaseModel):
    """Authentication response model"""
    message: str = Field(..., description="Success message", example="Login successful")
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type", example="bearer")
    user: UserResponse = Field(..., description="User information")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp")


# --- Food Models ---

class FoodCreate(BaseModel):
    """Food item creation request model"""
    name: str = Field(..., description="Name of the food item", example="Margherita Pizza", min_length=1)
    price: float = Field(..., description="Price of the food item", example=12.99, gt=0)
    category: str = Field(..., description="Food category", example="Pizza", min_length=1)
    image: Optional[str] = Field(None, description="Image URL", example="https://example.com/pizza.jpg")
    description: Optional[str] = Field(None, description="Detailed description", example="Classic pizza with tomato sauce and mozzarella")
    availability: bool = Field(True, description="Whether the item is available for ordering")


class FoodUpdate(BaseModel):
    """Food item update request model"""
    availability: bool = Field(..., description="Update availability status", example=True)


class FoodResponse(BaseModel):
    """Food item response model - Contract for API responses"""
    id: int = Field(..., description="Unique food item ID", example=1)
    name: str = Field(..., description="Name of the food item", example="Margherita Pizza")
    price: float = Field(..., description="Price of the food item", example=12.99)
    category: str = Field(..., description="Food category", example="Pizza")
    image: Optional[str] = Field(None, description="Image URL", example="https://example.com/pizza.jpg")
    description: Optional[str] = Field(None, description="Detailed description", example="Classic pizza with tomato sauce and mozzarella")
    availability: bool = Field(..., description="Whether the item is available for ordering", example=True)

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Margherita Pizza",
                "price": 12.99,
                "category": "Pizza",
                "image": "https://example.com/pizza.jpg",
                "description": "Classic pizza with tomato sauce and mozzarella",
                "availability": True
            }
        }


# --- Order Models ---

class OrderItem(BaseModel):
    """Individual item within an order"""
    food_id: int = Field(..., description="ID of the food item", example=1)
    quantity: int = Field(..., description="Quantity ordered", example=2, gt=0)
    price: float = Field(..., description="Price per unit at time of order", example=12.99)
    name: str = Field(..., description="Name of the food item", example="Margherita Pizza")


class OrderCreate(BaseModel):
    """Order creation request model"""
    items: List[OrderItem] = Field(..., description="List of items in the order", min_items=1)
    total_amount: float = Field(..., description="Total order amount", example=25.98, gt=0)
    customer_name: str = Field(..., description="Customer full name", example="John Doe", min_length=1)
    customer_phone: str = Field(..., description="Customer phone number", example="+1234567890", min_length=1)
    customer_email: str = Field(..., description="Customer email", example="john@example.com")
    special_instructions: Optional[str] = Field(None, description="Special requests or instructions", example="Extra cheese please")
    tip_amount: float = Field(0.0, description="Tip amount", example=5.00, ge=0)
    number_of_people: int = Field(1, description="Number of people served", example=2, ge=1)


class OrderResponse(BaseModel):
    """Order response model - Contract for API responses"""
    id: int = Field(..., description="Unique order ID", example=1)
    items: List[OrderItem] = Field(..., description="Items in the order")
    total_amount: float = Field(..., description="Total order amount", example=25.98)
    customer_name: str = Field(..., description="Customer full name", example="John Doe")
    customer_phone: str = Field(..., description="Customer phone number", example="+1234567890")
    customer_email: str = Field(..., description="Customer email", example="john@example.com")
    special_instructions: Optional[str] = Field(None, description="Special requests", example="Extra cheese please")
    tip_amount: float = Field(..., description="Tip amount", example=5.00)
    number_of_people: int = Field(..., description="Number of people served", example=2)
    status: str = Field(..., description="Order status", example="pending")
    created_at: str = Field(..., description="Order creation timestamp (ISO format)", example="2024-01-15T10:30:00")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "items": [
                    {
                        "food_id": 1,
                        "quantity": 2,
                        "price": 12.99,
                        "name": "Margherita Pizza"
                    }
                ],
                "total_amount": 25.98,
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "customer_email": "john@example.com",
                "special_instructions": "Extra cheese please",
                "tip_amount": 5.00,
                "number_of_people": 2,
                "status": "pending",
                "created_at": "2024-01-15T10:30:00.123456"
            }
        }


class StatusUpdate(BaseModel):
    """Order status update request model"""
    status: str = Field(..., description="New order status", example="confirmed")

# ============================================================================
# Authentication Utilities
# ============================================================================

def create_access_token(data: dict) -> str:
    """
    Create JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ============================================================================
# API Endpoints
# ============================================================================

# --- Health Check ---

@app.get(
    "/",
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running and healthy",
    response_model=dict,
    responses={
        200: {
            "description": "API is running",
            "content": {
                "application/json": {
                    "example": {"message": "Canteen Backend Running with MongoDB", "status": "healthy"}
                }
            }
        }
    }
)
async def root():
    """Health check endpoint to verify API is operational."""
    return {
        "message": "Canteen Backend Running with MongoDB",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# --- Authentication Endpoints ---

@app.post(
    "/api/auth/register",
    tags=["Authentication"],
    summary="Register a new user",
    description="Create a new user account with name, email, and password",
    response_model=AuthResponse,
    responses={
        200: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Registration successful",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "user": {
                            "id": "507f1f77bcf86cd799439011",
                            "name": "John Doe",
                            "email": "john@example.com",
                            "role": "user"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Email already exists",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Email already exists", "status_code": 400, "timestamp": "2024-01-15T10:30:00"}
                }
            }
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def register(user: UserCreate):
    """Register a new user account."""
    # Check if user already exists
    existing_user = users_collection.find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create new user document
    new_user = {
        "name": user.name,
        "email": user.email.lower(),
        "role": "user",
        "hashed_password": pwd_context.hash(user.password)
    }
    result = users_collection.insert_one(new_user)
    
    # Generate access token
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


@app.post(
    "/api/auth/login",
    tags=["Authentication"],
    summary="Login existing user",
    description="Authenticate user with email and password",
    response_model=AuthResponse,
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Login successful",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "user": {
                            "id": "507f1f77bcf86cd799439011",
                            "name": "John Doe",
                            "email": "john@example.com",
                            "role": "user"
                        }
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_found": {
                            "value": {"detail": "User not found", "status_code": 401, "timestamp": "2024-01-15T10:30:00"}
                        },
                        "invalid_password": {
                            "value": {"detail": "Invalid password", "status_code": 401, "timestamp": "2024-01-15T10:30:00"}
                        }
                    }
                }
            }
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def login(user: UserLogin):
    """Authenticate user and return JWT token."""
    db_user = users_collection.find_one({"email": user.email.lower()})
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not pwd_context.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
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

# --- Food Endpoints ---

@app.get(
    "/api/foods",
    response_model=List[FoodResponse],
    tags=["Food Items"],
    summary="Get all food items",
    description="Retrieve a list of all available and unavailable food items",
    responses={
        200: {
            "description": "List of all food items",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Margherita Pizza",
                            "price": 12.99,
                            "category": "Pizza",
                            "image": "https://example.com/pizza.jpg",
                            "description": "Classic pizza with tomato sauce and mozzarella",
                            "availability": True
                        }
                    ]
                }
            }
        }
    }
)
async def get_foods():
    """Get all food items with normalized data."""
    try:
        foods = list(foods_collection.find())
        # ✅ FIX: Return Pydantic models, not dictionaries
        return [FoodResponse(**item) for item in convert_mongo_documents(foods)]
    except Exception as e:
        print(f"Error in get_foods: {e}")
        return []


@app.post(
    "/api/foods",
    response_model=FoodResponse,
    tags=["Food Items"],
    summary="Create a new food item",
    description="Add a new food item to the menu",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Food item created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Margherita Pizza",
                        "price": 12.99,
                        "category": "Pizza",
                        "image": "https://example.com/pizza.jpg",
                        "description": "Classic pizza with tomato sauce and mozzarella",
                        "availability": True
                    }
                }
            }
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def create_food(food: FoodCreate):
    """Create a new food item."""
    food_dict = food.dict()
    
    # Generate sequential ID
    food_dict["id"] = get_next_sequence(foods_collection)
    
    # Insert into database
    result = foods_collection.insert_one(food_dict)
    
    # ✅ FIX: Return Pydantic model, not dictionary
    created_food = convert_mongo_document(food_dict)
    return FoodResponse(**created_food)


@app.put(
    "/api/foods/{food_id}",
    response_model=FoodResponse,
    tags=["Food Items"],
    summary="Update a food item",
    description="Update all fields of an existing food item",
    responses={
        200: {
            "description": "Food item updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Updated Pizza",
                        "price": 14.99,
                        "category": "Pizza",
                        "image": "https://example.com/updated-pizza.jpg",
                        "description": "Updated description",
                        "availability": True
                    }
                }
            }
        },
        404: {
            "description": "Food item not found",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Food not found", "status_code": 404, "timestamp": "2024-01-15T10:30:00"}
                }
            }
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def update_food(food_id: int, food: FoodCreate):
    """Update an existing food item."""
    # Check if food exists
    existing = foods_collection.find_one({"id": food_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    
    # Prepare update data
    update_data = {
        "name": food.name,
        "price": food.price,
        "category": food.category,
        "description": food.description,
        "image": food.image,
        "availability": food.availability
    }
    
    # Update in database
    foods_collection.update_one({"id": food_id}, {"$set": update_data})
    
    # Get updated food
    updated_food = foods_collection.find_one({"id": food_id})
    updated_food = convert_mongo_document(updated_food)
    return FoodResponse(**updated_food)


@app.delete(
    "/api/foods/{food_id}",
    tags=["Food Items"],
    summary="Delete a food item",
    description="Remove a food item from the menu",
    responses={
        200: {
            "description": "Food item deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Food deleted successfully", "status_code": 200}
                }
            }
        },
        404: {
            "description": "Food item not found",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Food not found", "status_code": 404, "timestamp": "2024-01-15T10:30:00"}
                }
            }
        }
    }
)
async def delete_food(food_id: int):
    """Delete a food item from the menu."""
    result = foods_collection.delete_one({"id": food_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    
    return {
        "message": "Food deleted successfully",
        "status_code": 200
    }


@app.patch(
    "/api/foods/{food_id}/availability",
    tags=["Food Items"],
    summary="Toggle food availability",
    description="Update the availability status of a food item",
    responses={
        200: {
            "description": "Availability updated successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Availability updated", "status_code": 200}
                }
            }
        },
        404: {
            "description": "Food item not found",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Food not found", "status_code": 404, "timestamp": "2024-01-15T10:30:00"}
                }
            }
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def toggle_availability(food_id: int, update: FoodUpdate):
    """Toggle the availability of a food item."""
    result = foods_collection.update_one(
        {"id": food_id},
        {"$set": {"availability": update.availability}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food not found"
        )
    
    return {
        "message": "Availability updated",
        "status_code": 200
    }

# --- Order Endpoints ---

@app.post(
    "/api/orders",
    response_model=OrderResponse,
    tags=["Orders"],
    summary="Create a new order",
    description="Place a new order with multiple items",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Order created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "items": [
                            {
                                "food_id": 1,
                                "quantity": 2,
                                "price": 12.99,
                                "name": "Margherita Pizza"
                            }
                        ],
                        "total_amount": 25.98,
                        "customer_name": "John Doe",
                        "customer_phone": "+1234567890",
                        "customer_email": "john@example.com",
                        "special_instructions": "Extra cheese please",
                        "tip_amount": 5.00,
                        "number_of_people": 2,
                        "status": "pending",
                        "created_at": "2024-01-15T10:30:00.123456"
                    }
                }
            }
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def create_order(order: OrderCreate):
    """Create a new order."""
    # Generate sequential ID
    order_dict = order.dict()
    order_dict["id"] = get_next_sequence(orders_collection)
    order_dict["status"] = "pending"
    order_dict["created_at"] = datetime.now().isoformat()
    
    # Insert into database
    result = orders_collection.insert_one(order_dict)
    
    # ✅ FIX: Return Pydantic model, not dictionary
    created_order = convert_mongo_document(order_dict)
    return OrderResponse(**created_order)


@app.get(
    "/api/orders",
    response_model=List[OrderResponse],
    tags=["Orders"],
    summary="Get all orders",
    description="Retrieve list of all orders",
    responses={
        200: {
            "description": "List of all orders",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "items": [
                                {
                                    "food_id": 1,
                                    "quantity": 2,
                                    "price": 12.99,
                                    "name": "Margherita Pizza"
                                }
                            ],
                            "total_amount": 25.98,
                            "customer_name": "John Doe",
                            "customer_phone": "+1234567890",
                            "customer_email": "john@example.com",
                            "special_instructions": "Extra cheese please",
                            "tip_amount": 5.00,
                            "number_of_people": 2,
                            "status": "pending",
                            "created_at": "2024-01-15T10:30:00.123456"
                        }
                    ]
                }
            }
        }
    }
)
async def get_orders():
    """Get all orders with normalized data."""
    try:
        orders = list(orders_collection.find())
        # ✅ FIX: Return Pydantic models, not dictionaries
        return [OrderResponse(**item) for item in convert_mongo_documents(orders)]
    except Exception as e:
        print(f"Error in get_orders: {e}")
        return []


@app.patch(
    "/api/orders/{order_id}/status",
    tags=["Orders"],
    summary="Update order status",
    description="Change the status of an existing order",
    responses={
        200: {
            "description": "Order status updated successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Status updated", "status_code": 200}
                }
            }
        },
        404: {
            "description": "Order not found",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Order not found", "status_code": 404, "timestamp": "2024-01-15T10:30:00"}
                }
            }
        },
        422: {
            "description": "Validation error"
        }
    }
)
async def update_order_status(order_id: int, status_update: StatusUpdate):
    """Update the status of an order."""
    result = orders_collection.update_one(
        {"id": order_id},
        {"$set": {"status": status_update.status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return {
        "message": "Status updated",
        "status_code": 200
    }

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )