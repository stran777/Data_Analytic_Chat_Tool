"""
User model for managing user profiles and preferences.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer


class UserPreferences(BaseModel):
    """User preferences for chat interactions."""
    
    preferred_llm: Optional[str] = None
    language: str = "en"
    timezone: str = "UTC"
    enable_suggestions: bool = True
    max_history: int = 10
    theme: str = "light"


class User(BaseModel):
    """User model."""
    
    model_config = ConfigDict()
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    email: EmailStr
    name: str
    department: Optional[str] = None
    role: str = "user"
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_serializer('created_at', 'updated_at', 'last_active')
    def serialize_dt(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None
    
    def to_cosmos_dict(self) -> Dict[str, Any]:
        """Convert to Cosmos DB compatible dictionary."""
        data = self.model_dump()
        data["id"] = self.id
        data["partitionKey"] = self.id  # Use id as partition key
        return data


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    name: str
    department: Optional[str] = None
    preferences: Optional[UserPreferences] = None


class UserResponse(BaseModel):
    """Response schema for user data."""
    
    model_config = ConfigDict()
    
    id: str
    email: EmailStr
    name: str
    department: Optional[str]
    role: str
    created_at: datetime
    last_active: Optional[datetime]
    is_active: bool
    
    @field_serializer('created_at', 'last_active')
    def serialize_dt(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None
