from pydantic import BaseModel

class FoodCreate(BaseModel):
    name: str
    price: float
    category: str
    image: str
    availability: bool