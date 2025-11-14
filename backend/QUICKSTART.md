# Quick Start Guide

## Prerequisites

- Python 3.11 or higher
- Azure Cosmos DB account
- OpenAI API key (or Google/Anthropic API key)

## Installation

1. **Create virtual environment:**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
notepad .env  # Windows
nano .env     # Linux/Mac
```

Required environment variables:
- `COSMOS_ENDPOINT`: Your Azure Cosmos DB endpoint
- `COSMOS_KEY`: Your Azure Cosmos DB key
- `OPENAI_API_KEY`: Your OpenAI API key (or Google/Anthropic)

## Running the Application

**Start the server:**
```bash
python run.py
```

The API will be available at: http://localhost:8000

**API Documentation:**
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Quick Test

**Health check:**
```bash
curl http://localhost:8000/health
```

**Send a message:**
```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the total revenue for Q4?",
    "user_id": "user123"
  }'
```

## Project Structure

```
backend/
├── src/
│   ├── agents/          # Multi-agent system
│   │   ├── orchestrator.py         # LangGraph workflow
│   │   ├── query_understanding_agent.py
│   │   ├── data_retrieval_agent.py
│   │   ├── response_generation_agent.py
│   │   └── recommendation_agent.py
│   ├── api/             # FastAPI routes
│   │   ├── chat.py      # Chat endpoints
│   │   ├── users.py     # User management
│   │   ├── analytics.py # Analytics endpoints
│   │   └── health.py    # Health checks
│   ├── models/          # Data models
│   │   ├── message.py
│   │   ├── conversation.py
│   │   └── user.py
│   ├── services/        # Business logic
│   │   ├── cosmos_service.py    # Database access
│   │   ├── llm_service.py       # LLM providers
│   │   ├── memory_service.py    # Conversation memory
│   │   └── rag_service.py       # Vector search
│   ├── tools/           # MCP tools
│   │   ├── cosmos_db_tool.py
│   │   ├── vector_search_tool.py
│   │   └── analytics_tool.py
│   ├── utils/           # Utilities
│   │   ├── config.py    # Configuration
│   │   └── logger.py    # Logging
│   └── main.py          # FastAPI app
├── tests/               # Test suite
├── run.py              # Startup script
├── requirements.txt    # Dependencies
└── .env.example        # Environment template
```

## Key Features

### Multi-Agent Architecture
- **Query Understanding Agent**: Analyzes user intent and entities
- **Data Retrieval Agent**: Fetches data from Cosmos DB and vector store
- **Response Generation Agent**: Creates natural language responses
- **Recommendation Agent**: Suggests follow-up queries

### LangGraph Orchestration
Agents are coordinated using LangGraph StateGraph for reliable workflow execution.

### Multi-LLM Support
- OpenAI (GPT-4, GPT-3.5)
- Google (Gemini Pro)
- Anthropic (Claude-3)

### RAG (Retrieval-Augmented Generation)
- Vector search with ChromaDB
- Semantic similarity search
- Context-aware responses

### MCP Tools
- Cosmos DB queries
- Vector search
- Analytics operations

## Development

**Run tests:**
```bash
pytest tests/
```

**Format code:**
```bash
black src/
isort src/
```

**Type checking:**
```bash
mypy src/
```

## Troubleshooting

**Import errors during development:**
All import errors shown by the IDE before installing dependencies are expected. Run `pip install -r requirements.txt` to resolve.

**Cosmos DB connection issues:**
- Verify `COSMOS_ENDPOINT` and `COSMOS_KEY` in `.env`
- Ensure your IP is allowed in Cosmos DB firewall
- Check network connectivity

**LLM errors:**
- Verify API keys are set correctly
- Check rate limits for your provider
- Try switching providers via `DEFAULT_LLM_PROVIDER` setting

## Next Steps

1. **Set up Cosmos DB containers** - The app will auto-create them on startup
2. **Index documents for RAG** - Use `/api/analytics/documents/index` endpoint
3. **Create test users** - Use `/api/users` endpoint
4. **Test chat functionality** - Use `/api/chat/message` endpoint

## Support

For issues or questions, refer to:
- `documentation/design.md` - Architecture details
- API documentation at `/api/docs`
- Logs in console output
