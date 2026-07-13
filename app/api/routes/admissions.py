from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
import asyncpg

from app.api.dependencies.db import get_db_connection
from app.api.dependencies.auth import get_current_active_user
from app.schemas.user import User
from app.schemas.admissions import AdmissionInDB, AdmissionUpdateStatus
from app.schemas.pagination import PaginatedResponse
from app.repositories.admission_repo import AdmissionRepository

router = APIRouter(prefix="/admissions", tags=["Admissions"])

@router.get("", response_model=PaginatedResponse[AdmissionInDB])
async def get_admissions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = AdmissionRepository(db)
    items, total = await repo.get_all(page=page, limit=limit, search=search, status=status)
    pages = (total + limit - 1) // limit
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

@router.patch("/{id}/status", response_model=AdmissionInDB)
async def update_admission_status(
    id: UUID,
    status_update: AdmissionUpdateStatus,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = AdmissionRepository(db)
    updated = await repo.update_status(id, status_update.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Admission not found")
    return updated

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admission(
    id: UUID,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = AdmissionRepository(db)
    deleted = await repo.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Admission not found")
