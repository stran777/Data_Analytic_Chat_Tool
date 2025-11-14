"""
Configuration management using Pydantic Settings.
Loads environment variables and provides typed configuration.
"""
from functools import lru_cache
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="DataAnalyticChatTool", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001", alias="CORS_ORIGINS"
    )

    # LLM Configuration
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=2000, alias="OPENAI_MAX_TOKENS")

    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    google_model: str = Field(default="gemini-pro", alias="GOOGLE_MODEL")

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-3-opus-20240229", alias="ANTHROPIC_MODEL"
    )

    default_llm_provider: Literal["openai", "google", "anthropic"] = Field(
        default="openai", alias="DEFAULT_LLM_PROVIDER"
    )

    # Azure Cosmos DB
    cosmos_endpoint: str = Field(default="", alias="COSMOS_ENDPOINT")
    cosmos_key: str = Field(default="", alias="COSMOS_KEY")
    cosmos_database_name: str = Field(
        default="data_analytics_chat", alias="COSMOS_DATABASE_NAME"
    )
    cosmos_container_conversations: str = Field(
        default="conversations", alias="COSMOS_CONTAINER_CONVERSATIONS"
    )
    cosmos_container_users: str = Field(default="users", alias="COSMOS_CONTAINER_USERS")
    cosmos_container_financial_data: str = Field(
        default="financial_data", alias="COSMOS_CONTAINER_FINANCIAL_DATA"
    )

    # Vector Store
    vector_store_type: str = Field(default="chromadb", alias="VECTOR_STORE_TYPE")
    vector_store_path: str = Field(default="./data/vectorstore", alias="VECTOR_STORE_PATH")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )

    # Memory & Context
    max_conversation_history: int = Field(default=10, alias="MAX_CONVERSATION_HISTORY")
    context_window_size: int = Field(default=4000, alias="CONTEXT_WINDOW_SIZE")

    # RAG Configuration
    rag_enabled: bool = Field(default=True, alias="RAG_ENABLED")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")
    rag_similarity_threshold: float = Field(default=0.7, alias="RAG_SIMILARITY_THRESHOLD")

    # MCP Configuration
    mcp_server_host: str = Field(default="localhost", alias="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=5000, alias="MCP_SERVER_PORT")

    # LangSmith
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com", alias="LANGCHAIN_ENDPOINT"
    )
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(
        default="data-analytics-chat", alias="LANGCHAIN_PROJECT"
    )

    # Security
    secret_key: str = Field(default="change_me_in_production", alias="SECRET_KEY")
    session_timeout: int = Field(default=3600, alias="SESSION_TIMEOUT")

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
