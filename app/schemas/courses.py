from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CourseBase(BaseModel):
    title: str
    category: str
    price: int
    description: Optional[str] = None
    duration: Optional[str] = None
    students: Optional[str] = None
    is_active: bool = True
    curriculum: list[str] = []
    features: list[str] = []

class CourseCreate(CourseBase):
    pass

class CourseUpdate(CourseBase):
    title: Optional[str] = None
    category: Optional[str] = None
    price: Optional[int] = None
    description: Optional[str] = None
    duration: Optional[str] = None
    students: Optional[str] = None
    is_active: Optional[bool] = None
    curriculum: Optional[list[str]] = None
    features: Optional[list[str]] = None

class CourseInDB(CourseBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class Course(CourseInDB):
    pass
