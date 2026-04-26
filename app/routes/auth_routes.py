from fastapi import APIRouter, Depends
from app.schemas.user_schema import UserRegister, UserLogin
from app.services.auth_service import create_user, login_user
from app.utils.dependencies import get_current_user

router = APIRouter()

@router.post("/register")
def register(user: UserRegister):
    return create_user(user)

@router.post("/login")
def login(user: UserLogin):
    return login_user(user)

# 🔥 Protected Route
@router.get("/profile")
def profile(user=Depends(get_current_user)):
    return {
        "message": "Protected route accessed",
        "user": user
    }