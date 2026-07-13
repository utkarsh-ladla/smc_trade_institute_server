from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
import asyncpg

from app.api.dependencies.db import get_db_connection
from app.api.dependencies.auth import get_current_active_user
from app.schemas.user import User
from app.schemas.courses import CourseInDB, CourseCreate, CourseUpdate
from app.schemas.pagination import PaginatedResponse
from app.repositories.course_repo import CourseRepository

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.get("", response_model=PaginatedResponse[CourseInDB])
async def get_courses(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = CourseRepository(db)
    items, total = await repo.get_all(page=page, limit=limit, search=search)
    pages = (total + limit - 1) // limit
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

@router.post("", response_model=CourseInDB, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: CourseCreate,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = CourseRepository(db)
    created = await repo.create(course.model_dump())
    return created

@router.put("/{id}", response_model=CourseInDB)
async def update_course(
    id: UUID,
    course_update: CourseUpdate,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = CourseRepository(db)
    updated = await repo.update(id, course_update.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Course not found")
    return updated

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    id: UUID,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = CourseRepository(db)
    deleted = await repo.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Course not found")
