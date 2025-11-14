"""
Memory service for managing conversation context and history.
"""
from typing import Dict, List, Optional

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.models import Conversation, Message, MessageRole
from src.utils import LoggerMixin, settings


class MemoryService(LoggerMixin):
    """Service for managing conversation memory and context."""
    
    def __init__(self):
        """Initialize memory service."""
        self._memories: Dict[str, ChatMessageHistory] = {}
    
    def get_memory(self, conversation_id: str) -> ChatMessageHistory:
        """
        Get or create memory for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            ChatMessageHistory instance
        """
        if conversation_id not in self._memories:
            self._memories[conversation_id] = ChatMessageHistory()
            self.logger.info(f"Created new memory for conversation: {conversation_id}")
        
        return self._memories[conversation_id]
    
    def load_conversation_history(
        self, 
        conversation: Conversation,
        max_messages: Optional[int] = None
    ) -> ChatMessageHistory:
        """
        Load conversation history into memory.
        
        Args:
            conversation: Conversation object with message history
            max_messages: Maximum number of messages to load
            
        Returns:
            ChatMessageHistory with loaded history
        """
        memory = self.get_memory(conversation.id)
        max_msg = max_messages or settings.max_conversation_history
        
        # Get recent messages
        recent_messages = conversation.get_recent_messages(limit=max_msg)
        
        # Clear existing memory
        memory.clear()
        
        # Load messages into memory
        for message in recent_messages:
            if message.role == MessageRole.USER:
                memory.add_user_message(message.content)
            elif message.role == MessageRole.ASSISTANT:
                memory.add_ai_message(message.content)
        
        self.logger.info(
            f"Loaded {len(recent_messages)} messages into memory for conversation: {conversation.id}"
        )
        return memory
    
    def add_message_to_memory(
        self,
        conversation_id: str,
        message: Message
    ) -> None:
        """
        Add a single message to conversation memory.
        
        Args:
            conversation_id: ID of the conversation
            message: Message to add
        """
        memory = self.get_memory(conversation_id)
        
        if message.role == MessageRole.USER:
            memory.add_user_message(message.content)
        elif message.role == MessageRole.ASSISTANT:
            memory.add_ai_message(message.content)
        
        self.logger.debug(f"Added message to memory: {conversation_id}")
    
    def get_conversation_context(
        self,
        conversation_id: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Get conversation context as formatted string.
        
        Args:
            conversation_id: ID of the conversation
            max_tokens: Maximum tokens to include (approximate)
            
        Returns:
            Formatted conversation context
        """
        memory = self.get_memory(conversation_id)
        messages = memory.messages
        
        if not messages:
            return ""
        
        # Build context string
        context_parts = []
        total_chars = 0
        max_chars = (max_tokens or settings.context_window_size) * 4  # Rough estimate
        
        # Add messages in reverse order (most recent first)
        for message in reversed(messages):
            role = "User" if isinstance(message, HumanMessage) else "Assistant"
            msg_text = f"{role}: {message.content}"
            
            if total_chars + len(msg_text) > max_chars:
                break
            
            context_parts.insert(0, msg_text)
            total_chars += len(msg_text)
        
        return "\n\n".join(context_parts)
    
    def clear_memory(self, conversation_id: str) -> None:
        """
        Clear memory for a conversation.
        
        Args:
            conversation_id: ID of the conversation
        """
        if conversation_id in self._memories:
            self._memories[conversation_id].clear()
            self.logger.info(f"Cleared memory for conversation: {conversation_id}")
    
    def remove_memory(self, conversation_id: str) -> None:
        """
        Remove memory for a conversation.
        
        Args:
            conversation_id: ID of the conversation
        """
        if conversation_id in self._memories:
            del self._memories[conversation_id]
            self.logger.info(f"Removed memory for conversation: {conversation_id}")


# Global service instance
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """Get or create memory service instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
