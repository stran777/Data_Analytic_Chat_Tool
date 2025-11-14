# Data Analytics Chat Tool - Backend

AI-Powered Data Analytics Chat Application Backend using LangGraph, LangChain, and Azure Cosmos DB.

## Architecture

This backend implements a multi-agent system using:
- **LangGraph**: For orchestrating multi-agent workflows
- **A2A Protocol**: Agent-to-Agent communication
- **MCP**: Model Context Protocol for tool integration
- **Azure Cosmos DB**: For data storage and retrieval
- **RAG**: Retrieval-Augmented Generation for context-aware responses

## Project Structure

```
backend/
├── src/
│   ├── agents/           # LangGraph agents
│   │   ├── query_understanding_agent.py
│   │   ├── data_retrieval_agent.py
│   │   ├── response_generation_agent.py
│   │   └── recommendation_agent.py
│   ├── tools/            # MCP tools
│   │   ├── cosmos_db_tool.py
│   │   ├── vector_search_tool.py
│   │   └── analytics_tool.py
│   ├── services/         # Business logic
│   │   ├── llm_service.py
│   │   ├── memory_service.py
│   │   ├── rag_service.py
│   │   └── cosmos_service.py
│   ├── models/           # Data models
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── user.py
│   ├── api/              # FastAPI routes
│   │   ├── chat.py
│   │   ├── users.py
│   │   └── analytics.py
│   └── utils/            # Utilities
│       ├── config.py
│       └── logger.py
├── config/               # Configuration files
├── tests/                # Test files
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   copy .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run the Application**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

- `POST /api/v1/chat/message` - Send a message and get response
- `GET /api/v1/chat/history/{session_id}` - Get conversation history
- `POST /api/v1/chat/suggestions` - Get query suggestions
- `GET /api/v1/users/{user_id}` - Get user profile
- `POST /api/v1/analytics/query` - Execute analytics query

## Development

- **Run Tests**: `pytest`
- **Code Formatting**: `black src/`
- **Type Checking**: `mypy src/`
- **Linting**: `flake8 src/`

## Features

- ✅ Natural Language Understanding
- ✅ Multi-Agent Orchestration (LangGraph)
- ✅ Context-Aware Responses
- ✅ Query Recommendations
- ✅ RAG Implementation
- ✅ Conversation Memory
- ✅ Azure Cosmos DB Integration
