from fastapi import APIRouter, Depends
from app.schemas.food_schema import FoodCreate
from app.services.food_service import add_food, get_all_foods, update_food, delete_food
from app.utils.dependencies import get_current_user

router = APIRouter()

# 🔥 Add Food (Protected - Admin)
@router.post("/")
def create_food(food: FoodCreate, user=Depends(get_current_user)):
    return add_food(food)

# 🔥 Get All Foods (Public)
@router.get("/")
def fetch_foods():
    return get_all_foods()

# 🔥 Update Food
@router.put("/{food_id}")
def update(food_id: str, food: FoodCreate, user=Depends(get_current_user)):
    return update_food(food_id, food)

# 🔥 Delete Food
@router.delete("/{food_id}")
def delete(food_id: str, user=Depends(get_current_user)):
    return delete_food(food_id)