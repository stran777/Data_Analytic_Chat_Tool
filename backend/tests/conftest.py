"""
Test configuration and fixtures.
"""
import pytest


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    from src.utils.config import Settings
    
    return Settings(
        ENVIRONMENT="test",
        DEBUG=True,
        LOG_LEVEL="DEBUG"
    )


@pytest.fixture
def mock_cosmos_service():
    """Mock Cosmos DB service."""
    from unittest.mock import AsyncMock, MagicMock
    
    service = MagicMock()
    service.get_conversation = AsyncMock(return_value=None)
    service.create_conversation = AsyncMock()
    service.update_conversation = AsyncMock()
    service.list_conversations = AsyncMock(return_value=[])
    service.query_financial_data = AsyncMock(return_value=[])
    
    return service


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    from unittest.mock import AsyncMock, MagicMock
    
    service = MagicMock()
    service.generate_response = AsyncMock(return_value="Test response")
    
    return service


@pytest.fixture
def sample_conversation():
    """Sample conversation for testing."""
    from src.models.conversation import Conversation
    from src.models.message import Message, MessageRole
    
    conv = Conversation(user_id="test_user")
    conv.add_message(Message(role=MessageRole.USER, content="Test message"))
    
    return conv


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    from src.models.user import User
    
    return User(
        email="test@example.com",
        name="Test User",
        department="Finance",
        role="analyst"
    )
