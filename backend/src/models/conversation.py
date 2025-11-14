"""
Conversation model for managing chat sessions.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from src.models.message import Message


class ConversationStatus(str):
    """Conversation status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(BaseModel):
    """Conversation/Session model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    title: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    status: str = ConversationStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Partition key for Cosmos DB
    partition_key: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Auto-generate title from first user message
        if not self.title and message.role.value == "user" and len(self.messages) == 1:
            self.title = message.content[:50] + ("..." if len(message.content) > 50 else "")
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages from the conversation."""
        return self.messages[-limit:] if self.messages else []
    
    def to_cosmos_dict(self) -> Dict[str, Any]:
        """Convert to Cosmos DB compatible dictionary."""
        data = self.model_dump()
        data["id"] = self.id
        data["partitionKey"] = self.user_id  # Use user_id as partition key
        return data


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    user_id: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Response schema for conversations."""
    id: str
    user_id: str
    title: Optional[str]
    message_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    last_message: Optional[Message] = None
