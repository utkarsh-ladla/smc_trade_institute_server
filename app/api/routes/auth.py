from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import asyncpg

from app.api.dependencies.db import get_db_connection
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.schemas.token import Token
from app.schemas.user import UserCreate, User
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
async def login_access_token(
    db: asyncpg.Connection = Depends(get_db_connection),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    service = UserService(db)
    user = await service.get_user_by_email(form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            subject=user["id"], expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=User)
async def register_user(
    user_in: UserCreate,
    db: asyncpg.Connection = Depends(get_db_connection)
):
    service = UserService(db)
    user = await service.get_user_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    hashed_password = get_password_hash(user_in.password)
    user_data = user_in.model_dump()
    user_data["hashed_password"] = hashed_password
    
    # By default, first user shouldn't be admin unless we want to, 
    # but for safety, normal registration is not admin.
    user_data["is_admin"] = False
    
    new_user = await service.create_user(user_data)
    return new_user

@router.post("/register-admin", response_model=User)
async def register_admin(
    user_in: UserCreate,
    db: asyncpg.Connection = Depends(get_db_connection)
):
    service = UserService(db)
    user = await service.get_user_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    hashed_password = get_password_hash(user_in.password)
    user_data = user_in.model_dump()
    user_data["hashed_password"] = hashed_password
    user_data["is_admin"] = True
    
    new_user = await service.create_user(user_data)
    return new_user

from app.schemas.user import ChangePasswordRequest
from app.api.dependencies.auth import get_current_user

@router.put("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db_connection)
):
    service = UserService(db)
    
    # Need to fetch the full user dict to get the hashed_password
    user_dict = await service.get_user_by_email(current_user.email)
    if not user_dict:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 1. Verify current password
    if not verify_password(request.current_password, user_dict["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    # 2. Hash new password and update
    new_hashed_password = get_password_hash(request.new_password)
    success = await service.change_password(current_user.id, new_hashed_password)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
        
    return {"message": "Password updated successfully"}
