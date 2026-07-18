import os
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
import asyncpg

from app.api.dependencies.db import get_db_connection
from app.api.dependencies.auth import get_current_active_user
from app.schemas.user import User
from app.schemas.resources import ResourceInDB
from app.schemas.pagination import PaginatedResponse
from app.repositories.resource_repo import ResourceRepository

router = APIRouter(prefix="/resources", tags=["Resources"])

UPLOAD_DIR = "static/uploads/resources"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=PaginatedResponse[ResourceInDB])
async def get_resources(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    type: Optional[str] = None,
    subject: Optional[str] = None,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = ResourceRepository(db)
    items, total = await repo.get_all(page=page, limit=limit, search=search, type=type, subject=subject)
    pages = (total + limit - 1) // limit
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )

import json

@router.post("", response_model=ResourceInDB, status_code=status.HTTP_201_CREATED)
async def create_resource(
    title: str = Form(...),
    type: str = Form(...),
    class_range: str = Form(...),
    subject: str = Form(...),
    description: Optional[str] = Form(None),
    pages: int = Form(0),
    rating: float = Form(0.0),
    downloads: int = Form(0),
    topics: str = Form("[]"),
    file: UploadFile = File(...),
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    # Save file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    file_url = f"/{UPLOAD_DIR}/{file.filename}"
    
    try:
        topics_list = json.loads(topics)
    except:
        topics_list = []

    repo = ResourceRepository(db)
    data = {
        "title": title,
        "description": description,
        "type": type,
        "class_range": class_range,
        "subject": subject,
        "file_url": file_url,
        "pages": pages,
        "rating": rating,
        "downloads": downloads,
        "topics": topics_list
    }
    
    created = await repo.create(data)
    return created

@router.put("/{id}", response_model=ResourceInDB)
async def update_resource(
    id: UUID,
    title: str = Form(...),
    type: str = Form(...),
    class_range: str = Form(...),
    subject: str = Form(...),
    description: Optional[str] = Form(None),
    pages: int = Form(0),
    rating: float = Form(0.0),
    downloads: int = Form(0),
    topics: str = Form("[]"),
    file: Optional[UploadFile] = File(None),
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = ResourceRepository(db)
    existing = await repo.get_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Resource not found")

    try:
        topics_list = json.loads(topics)
    except:
        topics_list = []

    data = {
        "title": title,
        "description": description,
        "type": type,
        "class_range": class_range,
        "subject": subject,
        "pages": pages,
        "rating": rating,
        "downloads": downloads,
        "topics": topics_list
    }

    if file:
        # Save new file locally
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        data["file_url"] = f"/{UPLOAD_DIR}/{file.filename}"
        
        # Optional: delete old file
        try:
            old_file_path = existing.file_url.lstrip("/")
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        except Exception as e:
            print(f"Error deleting old file {existing.file_url}: {e}")

    updated = await repo.update(id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    return updated

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    id: UUID,
    db: asyncpg.Connection = Depends(get_db_connection),
    current_user: User = Depends(get_current_active_user)
):
    repo = ResourceRepository(db)
    # Get resource to delete file
    resource = await repo.get_by_id(id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    # Delete file
    try:
        file_path = resource.file_url.lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file {resource.file_url}: {e}")
        
    deleted = await repo.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resource not found")
