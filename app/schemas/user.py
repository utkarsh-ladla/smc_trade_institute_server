from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class User(UserInDB):
    pass

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
