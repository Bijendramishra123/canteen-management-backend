from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class BirthdayRequest(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    birth_date: date
    aadhar_number: str
    aadhar_photo_url: str
    digilocker_screenshot_url: str
    status: str = "pending"  # pending, approved, rejected
    request_date: datetime = datetime.now()
    approved_date: Optional[datetime] = None
    rejected_reason: Optional[str] = None
