from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ContactBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str
    status: Optional[str] = "New"

class ContactCreate(ContactBase):
    pass

class ContactUpdateStatus(BaseModel):
    status: str

class ContactInDB(ContactBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
