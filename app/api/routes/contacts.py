from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from uuid import UUID
import asyncpg
import math

from app.api.dependencies.db import get_db_connection
from app.api.dependencies.auth import get_current_active_user
from app.schemas.user import User
from app.schemas.contact import ContactCreate, ContactInDB, ContactUpdateStatus
from app.schemas.pagination import PaginatedResponse
from app.repositories.contact_repo import ContactRepository

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.get("", response_model=PaginatedResponse[ContactInDB])
async def get_contacts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = ContactRepository(db)
    items, total = await repo.get_all(page=page, limit=limit, search=search, status=status_filter)
    
    pages = math.ceil(total / limit)
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

@router.post("", response_model=ContactInDB, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    db: asyncpg.Connection = Depends(get_db_connection)
):
    repo = ContactRepository(db)
    created = await repo.create(contact.model_dump())
    return created

@router.get("/{id}", response_model=ContactInDB)
async def get_contact(
    id: UUID,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = ContactRepository(db)
    contact = await repo.get_by_id(id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.patch("/{id}/status", response_model=ContactInDB)
async def update_contact_status(
    id: UUID,
    status_update: ContactUpdateStatus,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = ContactRepository(db)
    updated = await repo.update_status(id, status_update.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    id: UUID,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = ContactRepository(db)
    deleted = await repo.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
