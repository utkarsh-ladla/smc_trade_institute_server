from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies.auth import get_current_active_user
from app.schemas.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current logged in user profile.
    """
    return current_user
