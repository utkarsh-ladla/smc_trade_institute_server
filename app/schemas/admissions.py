from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime

class AdmissionBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    course: str
    status: Optional[str] = "Pending"
    additional_info: Optional[Dict[str, Any]] = None

class AdmissionCreate(AdmissionBase):
    pass

class AdmissionUpdateStatus(BaseModel):
    status: str

class AdmissionInDB(AdmissionBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class Admission(AdmissionInDB):
    pass
