# Deployment Guide

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Azure Deployment](#azure-deployment)
- [Environment Configuration](#environment-configuration)
- [Production Checklist](#production-checklist)

## Local Development

### Setup
```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run application
python run.py
```

### Development Server
The application will run at http://localhost:8000 with auto-reload enabled in debug mode.

## Docker Deployment

### Build and Run
```bash
# Build image
docker build -t data-analytics-chat-backend .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name chat-backend \
  data-analytics-chat-backend
```

### Using Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables
Create a `.env` file in the same directory as `docker-compose.yml`:
```env
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key
COSMOS_DATABASE_NAME=analytics_chat
OPENAI_API_KEY=sk-...
DEFAULT_LLM_PROVIDER=openai
```

## Azure Deployment

### Option 1: Azure Container Instances (ACI)

```bash
# Login to Azure
az login

# Create resource group
az group create --name rg-analytics-chat --location eastus

# Create container registry
az acr create --resource-group rg-analytics-chat \
  --name acranalyticschat --sku Basic

# Build and push image
az acr build --registry acranalyticschat \
  --image data-analytics-chat:latest .

# Create container instance
az container create \
  --resource-group rg-analytics-chat \
  --name aci-analytics-chat \
  --image acranalyticschat.azurecr.io/data-analytics-chat:latest \
  --cpu 2 --memory 4 \
  --ports 8000 \
  --dns-name-label analytics-chat-api \
  --environment-variables \
    ENVIRONMENT=production \
    COSMOS_ENDPOINT=$COSMOS_ENDPOINT \
  --secure-environment-variables \
    COSMOS_KEY=$COSMOS_KEY \
    OPENAI_API_KEY=$OPENAI_API_KEY
```

### Option 2: Azure App Service

```bash
# Create App Service Plan
az appservice plan create \
  --name asp-analytics-chat \
  --resource-group rg-analytics-chat \
  --is-linux --sku B2

# Create Web App
az webapp create \
  --resource-group rg-analytics-chat \
  --plan asp-analytics-chat \
  --name webapp-analytics-chat \
  --deployment-container-image-name acranalyticschat.azurecr.io/data-analytics-chat:latest

# Configure environment variables
az webapp config appsettings set \
  --resource-group rg-analytics-chat \
  --name webapp-analytics-chat \
  --settings \
    ENVIRONMENT=production \
    COSMOS_ENDPOINT=$COSMOS_ENDPOINT \
    COSMOS_KEY=$COSMOS_KEY \
    OPENAI_API_KEY=$OPENAI_API_KEY \
    DEFAULT_LLM_PROVIDER=openai
```

### Option 3: Azure Container Apps

```bash
# Create Container Apps environment
az containerapp env create \
  --name env-analytics-chat \
  --resource-group rg-analytics-chat \
  --location eastus

# Deploy container app
az containerapp create \
  --name app-analytics-chat \
  --resource-group rg-analytics-chat \
  --environment env-analytics-chat \
  --image acranalyticschat.azurecr.io/data-analytics-chat:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 1.0 --memory 2.0Gi \
  --min-replicas 1 --max-replicas 5 \
  --secrets \
    cosmos-key=$COSMOS_KEY \
    openai-key=$OPENAI_API_KEY \
  --env-vars \
    ENVIRONMENT=production \
    COSMOS_ENDPOINT=$COSMOS_ENDPOINT \
    COSMOS_KEY=secretref:cosmos-key \
    OPENAI_API_KEY=secretref:openai-key
```

## Environment Configuration

### Required Variables
```env
# Application
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Azure Cosmos DB
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-primary-key
COSMOS_DATABASE_NAME=analytics_chat

# LLM Provider (at least one required)
OPENAI_API_KEY=sk-...
# OR
GOOGLE_API_KEY=...
# OR
ANTHROPIC_API_KEY=...

DEFAULT_LLM_PROVIDER=openai
```

### Optional Variables
```env
# CORS
CORS_ORIGINS=https://your-frontend.com,https://app.example.com

# LLM Configuration
DEFAULT_MODEL=gpt-4
TEMPERATURE=0.7
MAX_TOKENS=2000

# Vector Store
VECTOR_STORE_TYPE=chromadb
VECTOR_STORE_PATH=./data/vectorstore
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG Configuration
RAG_TOP_K=5
RAG_SCORE_THRESHOLD=0.7
```

## Production Checklist

### Security
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Use Azure Key Vault for sensitive data
- [ ] Enable authentication/authorization
- [ ] Set up API rate limiting
- [ ] Configure firewall rules for Cosmos DB

### Performance
- [ ] Enable container autoscaling
- [ ] Configure appropriate CPU/memory resources
- [ ] Set up CDN for static assets
- [ ] Enable caching where appropriate
- [ ] Monitor API response times

### Monitoring
- [ ] Set up Azure Application Insights
- [ ] Configure logging to Azure Log Analytics
- [ ] Set up health check endpoints
- [ ] Configure alerts for errors
- [ ] Monitor API usage and costs

### Reliability
- [ ] Set up health checks
- [ ] Configure automatic restarts
- [ ] Enable container health probes
- [ ] Set up backup strategy for data
- [ ] Test disaster recovery procedures

### Compliance
- [ ] Review data retention policies
- [ ] Ensure GDPR compliance
- [ ] Document API security practices
- [ ] Regular security audits
- [ ] Keep dependencies updated

## Scaling Considerations

### Horizontal Scaling
- Use Azure Container Apps with autoscaling
- Configure min/max replicas based on load
- Monitor CPU and memory usage

### Database Scaling
- Use Cosmos DB autoscale throughput
- Partition data appropriately
- Monitor RU consumption

### Caching Strategy
- Implement Redis for session management
- Cache frequently accessed data
- Use CDN for static content

## Monitoring and Logging

### Application Insights Setup
```bash
# Install Application Insights
pip install applicationinsights

# Add to .env
APPINSIGHTS_INSTRUMENTATION_KEY=your-key
```

### Log Analytics
- All logs are structured JSON
- Automatically sent to stdout/stderr
- Ingested by Azure Monitor

### Metrics to Monitor
- Request rate and latency
- Error rate
- LLM API usage and costs
- Cosmos DB RU consumption
- Memory and CPU usage
- Active connections

## Troubleshooting

### Common Issues

**Container won't start:**
- Check environment variables are set
- Verify Cosmos DB connectivity
- Check logs: `docker logs <container-id>`

**High latency:**
- Check Cosmos DB location (use same region)
- Monitor LLM API response times
- Review vector store performance

**Out of memory:**
- Increase container memory limits
- Review vector store size
- Check for memory leaks

### Support Resources
- Azure Documentation: https://docs.microsoft.com/azure
- FastAPI Documentation: https://fastapi.tiangolo.com
- LangChain Documentation: https://python.langchain.com
