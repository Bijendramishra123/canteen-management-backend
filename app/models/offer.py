from pydantic import BaseModel
from datetime import date
from typing import Optional

class BirthdayOffer(BaseModel):
    user_id: str
    user_email: str
    user_name: str
    birth_date: date
    aadhar_number: str
    aadhar_verified: bool = False
    offer_claimed: bool = False
    claim_date: Optional[date] = None
    discount_applied: float = 0
