# Data Analytics Chat Tool - Backend

✅ **COMPLETE** - AI-powered data analytics chat application built with FastAPI, LangChain multi-agent system, and Azure Cosmos DB.

## 🚀 Quick Start

```bash
# 1. Setup environment
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your credentials

# 3. Run
python run.py
```

**Access**: http://localhost:8000/api/docs

## ✨ Features

- ✅ **Multi-Agent System**: LangGraph orchestrated workflow with 4 specialized agents
- ✅ **Multi-LLM Support**: OpenAI (GPT-4), Google (Gemini), Anthropic (Claude)
- ✅ **RAG System**: Vector search with ChromaDB for context-aware responses
- ✅ **Conversation Memory**: LangChain-based context management
- ✅ **Azure Cosmos DB**: Scalable NoSQL database for data persistence
- ✅ **FastAPI**: High-performance async REST API with OpenAPI docs
- ✅ **MCP Tools**: Standardized tools for Cosmos DB, vector search, and analytics
- ✅ **Smart Recommendations**: AI-powered follow-up query suggestions
- ✅ **Type Safety**: Full Pydantic validation throughout
- ✅ **Structured Logging**: JSON logs with context

## 🏗️ Architecture

```
User Query
    ↓
FastAPI Endpoint
    ↓
AgentOrchestrator (LangGraph)
    ↓
┌────────────────────────────────────────┐
│ 1. QueryUnderstandingAgent             │
│    → Intent & Entity Extraction        │
│ 2. DataRetrievalAgent                  │
│    → Cosmos DB + Vector Search         │
│ 3. ResponseGenerationAgent             │
│    → Natural Language Response         │
│ 4. RecommendationAgent                 │
│    → Follow-up Suggestions             │
└────────────────────────────────────────┘
    ↓
Response + Context + Suggestions
```

## 📋 Tech Stack

**Core**: Python 3.11+, FastAPI 0.104.1, Pydantic 2.5.0, Uvicorn  
**AI/ML**: LangChain 0.1.0, LangGraph 0.0.20, OpenAI, Google AI, Anthropic  
**Data**: Azure Cosmos DB 4.5.1, ChromaDB 0.4.18, FAISS  
**Dev**: pytest, black, mypy, flake8

## 📁 Project Structure

```
backend/
├── src/
│   ├── agents/              # Multi-agent system
│   │   ├── orchestrator.py         # LangGraph workflow
│   │   ├── query_understanding_agent.py
│   │   ├── data_retrieval_agent.py
│   │   ├── response_generation_agent.py
│   │   └── recommendation_agent.py
│   ├── api/                 # FastAPI routes
│   │   ├── chat.py         # Chat endpoints
│   │   ├── users.py        # User management
│   │   ├── analytics.py    # Analytics endpoints
│   │   └── health.py       # Health checks
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   │   ├── cosmos_service.py
│   │   ├── llm_service.py
│   │   ├── memory_service.py
│   │   └── rag_service.py
│   ├── tools/               # MCP tools
│   ├── utils/               # Config & logging
│   └── main.py             # FastAPI app
├── tests/                   # Test suite
├── run.py                  # Startup script
├── requirements.txt        # Dependencies
├── .env.example           # Environment template
├── Dockerfile             # Docker build
├── docker-compose.yml     # Docker orchestration
└── README.md              # This file
```

## 🌐 API Endpoints

**Chat**: `POST /api/chat/message`, `GET /api/chat/history/{id}`, `GET /api/chat/conversations`  
**Users**: `POST /api/users`, `GET /api/users/{id}`, `PATCH /api/users/{id}/preferences`  
**Analytics**: `POST /api/analytics/query`, `GET /api/analytics/search`, `POST /api/analytics/documents/index`  
**Health**: `GET /health`, `GET /health/ready`, `GET /health/info`

**Full docs**: http://localhost:8000/api/docs

## 🔧 Configuration

Edit `.env` with required credentials:

```env
# Cosmos DB
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-key

# LLM (at least one)
OPENAI_API_KEY=sk-...
```

See `.env.example` for all 80+ configuration options.

## 🧪 Testing

```bash
pytest tests/              # Run all tests
pytest --cov=src          # With coverage
```

## 🐳 Docker

```bash
docker-compose up -d      # Start services
docker-compose logs -f    # View logs
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Detailed setup guide
- **[API_GUIDE.md](API_GUIDE.md)** - Complete API documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Docker & Azure deployment
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Full implementation details

## 🚢 Deployment

**Docker**: `docker-compose up -d`  
**Azure Container Apps**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## 🛠️ Development

```bash
black src/     # Format
mypy src/      # Type check
flake8 src/    # Lint
```

## 📄 License

[Specify your license]

---

**Status**: ✅ **Backend Complete** - Ready for development, testing, and deployment!
