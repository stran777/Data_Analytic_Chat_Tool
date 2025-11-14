"""
Basic smoke tests for the application.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from src.main import app
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_system_info(client):
    """Test system info endpoint."""
    response = client.get("/health/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data


def test_openapi_docs(client):
    """Test OpenAPI docs are available."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    openapi_spec = response.json()
    assert "openapi" in openapi_spec
    assert "info" in openapi_spec


@pytest.mark.asyncio
async def test_chat_message_validation():
    """Test chat message request validation."""
    from src.api.chat import ChatRequest
    
    # Valid request
    request = ChatRequest(
        message="Test message",
        user_id="user123"
    )
    assert request.message == "Test message"
    assert request.user_id == "user123"
    assert request.conversation_id is None


@pytest.mark.asyncio
async def test_user_creation_validation():
    """Test user creation request validation."""
    from src.models.user import UserCreate
    
    # Valid user
    user = UserCreate(
        email="test@example.com",
        name="Test User",
        department="Finance"
    )
    assert user.email == "test@example.com"
    assert user.name == "Test User"


def test_message_role_enum():
    """Test message role enum."""
    from src.models.message import MessageRole
    
    assert MessageRole.USER.value == "user"
    assert MessageRole.ASSISTANT.value == "assistant"
    assert MessageRole.SYSTEM.value == "system"


def test_configuration_loading():
    """Test configuration can be loaded."""
    from src.utils.config import get_settings
    
    settings = get_settings()
    assert settings.APP_NAME is not None
    assert settings.APP_VERSION is not None
    assert settings.ENVIRONMENT is not None


def test_logger_initialization():
    """Test logger can be initialized."""
    from src.utils.logger import get_logger
    
    logger = get_logger("test")
    assert logger is not None
    logger.info("Test log message")


@pytest.mark.asyncio
async def test_mcp_tools_initialization():
    """Test MCP tools can be initialized."""
    from src.tools import initialize_tools, get_all_tools
    
    tools = initialize_tools()
    assert len(tools) > 0
    
    all_tools = get_all_tools()
    assert "cosmos_db_query" in all_tools
    assert "vector_search" in all_tools
    assert "analytics" in all_tools


def test_agent_orchestrator_creation():
    """Test agent orchestrator can be created."""
    from src.agents import get_orchestrator
    
    orchestrator = get_orchestrator()
    assert orchestrator is not None
    assert hasattr(orchestrator, "process_query")
