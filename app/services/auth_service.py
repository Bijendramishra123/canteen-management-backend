from app.config.db import users_collection
from app.utils.hash import hash_password, verify_password
from app.utils.jwt import create_access_token
from bson import ObjectId

def create_user(user):     
    existing_user = users_collection.find_one({"email": user.email})

    if existing_user:      
        return {"error": "User already exists"}       

    hashed_pwd = hash_password(user.password)

    user_data = {
        "name": user.name, 
        "email": user.email,
        "password": hashed_pwd,
        "role": "user"
    }

    result = users_collection.insert_one(user_data)

    return {
        "message": "User registered successfully",
        "user": {
            "id": str(result.inserted_id),
            "name": user.name,
            "email": user.email,
            "role": "user"
        }
    }

def login_user(user):      
    db_user = users_collection.find_one({"email": user.email})

    if not db_user:        
        return {"error": "User not found"}

    if not verify_password(user.password, db_user["password"]):
        return {"error": "Invalid password"}

    token = create_access_token({
        "user_id": str(db_user["_id"]),
        "email": db_user["email"]
    })

    # Get role from database
    user_role = db_user.get("role", "user")

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(db_user["_id"]),
            "name": db_user["name"],
            "email": db_user["email"],
            "role": user_role
        }
    }
