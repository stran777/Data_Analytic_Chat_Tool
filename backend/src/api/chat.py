"""
Chat API endpoints.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.agents import get_orchestrator
from src.models import Conversation, Message, MessageCreate, MessageResponse, MessageRole
from src.services import get_cosmos_service, get_memory_service
from src.utils import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    conversation_id: Optional[str] = None
    user_id: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: Message
    suggestions: list[str]
    conversation_id: str
    context_used: bool
    sources: list[dict]


@router.post("/message", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Send a message and get AI response.
    
    Args:
        request: Chat request with message and conversation context
        
    Returns:
        Chat response with AI message and suggestions
    """
    try:
        logger.info(f"Received message from user: {request.user_id}")
        
        cosmos_service = get_cosmos_service()
        memory_service = get_memory_service()
        orchestrator = get_orchestrator()
        
        # Get or create conversation
        if request.conversation_id:
            conversation = await cosmos_service.get_conversation(
                request.conversation_id,
                request.user_id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            # Create new conversation
            conversation = Conversation(user_id=request.user_id)
            conversation = await cosmos_service.create_conversation(conversation)
        
        # Create user message
        user_message = Message(
            role=MessageRole.USER,
            content=request.message
        )
        conversation.add_message(user_message)
        
        # Load conversation history into memory
        memory_service.load_conversation_history(conversation)
        
        # Prepare conversation history for orchestrator
        history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation.get_recent_messages(limit=10)
        ]
        
        # Process query through agent orchestrator
        result = await orchestrator.process_query(
            user_query=request.message,
            user_id=request.user_id,
            conversation_id=conversation.id,
            conversation_history=history[:-1]  # Exclude current message
        )
        
        # Create assistant message
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=result["response"],
            metadata=result.get("metadata", {})
        )
        conversation.add_message(assistant_message)
        
        # Update conversation in database
        await cosmos_service.update_conversation(conversation)
        
        # Update memory
        memory_service.add_message_to_memory(conversation.id, assistant_message)
        
        # Build response
        response = ChatResponse(
            message=assistant_message,
            suggestions=result.get("suggestions", []),
            conversation_id=conversation.id,
            context_used=result.get("metadata", {}).get("response_metadata", {}).get("context_used", False),
            sources=result.get("metadata", {}).get("sources", [])
        )
        
        logger.info(f"Successfully processed message for conversation: {conversation.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message"
        )


@router.get("/history/{conversation_id}", status_code=status.HTTP_200_OK)
async def get_conversation_history(
    conversation_id: str,
    user_id: str,
    limit: int = 50
):
    """
    Get conversation history.
    
    Args:
        conversation_id: ID of the conversation
        user_id: User ID for authorization
        limit: Maximum number of messages to return
        
    Returns:
        Conversation history
    """
    try:
        cosmos_service = get_cosmos_service()
        
        conversation = await cosmos_service.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {
            "conversation_id": conversation.id,
            "messages": conversation.get_recent_messages(limit=limit),
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving conversation history"
        )


@router.get("/conversations", status_code=status.HTTP_200_OK)
async def list_user_conversations(user_id: str, limit: int = 20):
    """
    List user's conversations.
    
    Args:
        user_id: User ID
        limit: Maximum number of conversations to return
        
    Returns:
        List of conversations
    """
    try:
        cosmos_service = get_cosmos_service()
        
        conversations = await cosmos_service.list_conversations(
            user_id=user_id,
            limit=limit,
            status="active"
        )
        
        # Format response
        return {
            "conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "message_count": len(conv.messages),
                    "updated_at": conv.updated_at,
                    "last_message": conv.messages[-1] if conv.messages else None
                }
                for conv in conversations
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while listing conversations"
        )


@router.delete("/conversation/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str, user_id: str):
    """
    Delete a conversation.
    
    Args:
        conversation_id: ID of the conversation
        user_id: User ID for authorization
    """
    try:
        cosmos_service = get_cosmos_service()
        memory_service = get_memory_service()
        
        conversation = await cosmos_service.get_conversation(conversation_id, user_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Mark as deleted
        conversation.status = "deleted"
        await cosmos_service.update_conversation(conversation)
        
        # Remove from memory
        memory_service.remove_memory(conversation_id)
        
        logger.info(f"Deleted conversation: {conversation_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the conversation"
        )
