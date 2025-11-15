"""
User API endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from src.models import User, UserCreate, UserPreferences
from src.services import get_cosmos_service
from src.utils import get_logger

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)


class UpdateUserPreferencesRequest(BaseModel):
    """Request model for updating user preferences."""
    default_llm_provider: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    response_format: str | None = None
    show_sources: bool | None = None


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """
    Create a new user.
    
    Args:
        user_data: User creation data
        
    Returns:
        Created user
    """
    try:
        cosmos_service = get_cosmos_service()
        
        # Check if user already exists
        existing_user = await cosmos_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Create user
        user = User(
            email=user_data.email,
            name=user_data.name,
            department=user_data.department,
            preferences=user_data.preferences or UserPreferences()
        )
        
        created_user = await cosmos_service.create_user(user)
        
        logger.info(f"Created new user: {created_user.id}")
        
        return {
            "id": created_user.id,
            "email": created_user.email,
            "name": created_user.name,
            "department": created_user.department,
            "role": created_user.role,
            "preferences": created_user.preferences.model_dump(),
            "created_at": created_user.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(user_id: str):
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        User data
    """
    try:
        cosmos_service = get_cosmos_service()
        
        user = await cosmos_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "department": user.department,
            "role": user.role,
            "preferences": user.preferences.model_dump(),
            "created_at": user.created_at,
            "last_active": user.last_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the user"
        )


@router.patch("/{user_id}/preferences", status_code=status.HTTP_200_OK)
async def update_user_preferences(
    user_id: str,
    preferences: UpdateUserPreferencesRequest
):
    """
    Update user preferences.
    
    Args:
        user_id: User ID
        preferences: Updated preferences
        
    Returns:
        Updated user data
    """
    try:
        cosmos_service = get_cosmos_service()
        
        user = await cosmos_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update preferences
        if preferences.default_llm_provider is not None:
            user.preferences.default_llm_provider = preferences.default_llm_provider
        if preferences.temperature is not None:
            user.preferences.temperature = preferences.temperature
        if preferences.max_tokens is not None:
            user.preferences.max_tokens = preferences.max_tokens
        if preferences.response_format is not None:
            user.preferences.response_format = preferences.response_format
        if preferences.show_sources is not None:
            user.preferences.show_sources = preferences.show_sources
        
        # Update user
        updated_user = await cosmos_service.update_user(user)
        
        logger.info(f"Updated preferences for user: {user_id}")
        
        return {
            "id": updated_user.id,
            "preferences": updated_user.preferences.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating user preferences"
        )


@router.post("/{user_id}/login", status_code=status.HTTP_200_OK)
async def record_login(user_id: str):
    """
    Record user login.
    
    Args:
        user_id: User ID
        
    Returns:
        Success message
    """
    try:
        cosmos_service = get_cosmos_service()
        
        user = await cosmos_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update last active time
        from datetime import datetime
        user.last_active = datetime.utcnow()
        await cosmos_service.update_user(user)
        
        logger.info(f"Recorded login for user: {user_id}")
        
        return {"message": "Login recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while recording login"
        )
