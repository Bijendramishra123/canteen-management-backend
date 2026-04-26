from app.config.db import foods_collection
from bson import ObjectId

def add_food(food):
    food_data = food.dict()
    result = foods_collection.insert_one(food_data)
    
    return {
        "message": "Food added successfully",
        "id": str(result.inserted_id)
    }


def get_all_foods():
    foods = []
    
    for food in foods_collection.find():
        food["_id"] = str(food["_id"])
        foods.append(food)
    
    return foods


def update_food(food_id, food):
    foods_collection.update_one(
        {"_id": ObjectId(food_id)},
        {"$set": food.dict()}
    )
    
    return {"message": "Food updated successfully"}


def delete_food(food_id):
    foods_collection.delete_one({"_id": ObjectId(food_id)})
    
    return {"message": "Food deleted successfully"}