# API Usage Guide

## Base URL
```
http://localhost:8000/api
```

## Authentication
Currently, the API uses `user_id` parameter for user identification. In production, implement OAuth2/JWT authentication.

---

## Endpoints

### Health Check

#### GET `/health`
Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "Data Analytics Chat Tool"
}
```

#### GET `/health/ready`
Check if all dependencies are ready.

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "cosmos_db": "healthy",
    "configuration": "healthy"
  }
}
```

#### GET `/health/info`
Get system information.

**Response:**
```json
{
  "app_name": "Data Analytics Chat Tool",
  "version": "1.0.0",
  "environment": "development",
  "llm_providers": {
    "openai": true,
    "google": false,
    "anthropic": false
  },
  "services": {
    "cosmos_db": "analytics_chat",
    "vector_store": "chromadb",
    "rag_enabled": true
  }
}
```

---

### Chat

#### POST `/api/chat/message`
Send a message and get AI response.

**Request:**
```json
{
  "message": "What is the total revenue for Q4 2023?",
  "user_id": "user123",
  "conversation_id": "conv-456"  // Optional, omit to start new conversation
}
```

**Response:**
```json
{
  "message": {
    "role": "assistant",
    "content": "Based on the financial data, the total revenue for Q4 2023 was $5.2 million...",
    "timestamp": "2024-01-15T10:30:00Z",
    "metadata": {
      "query_type": "financial",
      "entities": ["Q4 2023", "revenue"],
      "sources": [...]
    }
  },
  "suggestions": [
    "What was the revenue growth compared to Q3?",
    "Show me the revenue breakdown by product",
    "How does this compare to Q4 2022?"
  ],
  "conversation_id": "conv-456",
  "context_used": true,
  "sources": [
    {
      "type": "database",
      "query": "SELECT SUM(revenue) FROM financial_data WHERE quarter = 'Q4' AND year = 2023"
    }
  ]
}
```

#### GET `/api/chat/history/{conversation_id}`
Get conversation history.

**Parameters:**
- `conversation_id` (path): Conversation ID
- `user_id` (query): User ID
- `limit` (query): Max messages to return (default: 50)

**Response:**
```json
{
  "conversation_id": "conv-456",
  "messages": [
    {
      "role": "user",
      "content": "What is the total revenue?",
      "timestamp": "2024-01-15T10:29:00Z"
    },
    {
      "role": "assistant",
      "content": "The total revenue is...",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "created_at": "2024-01-15T10:29:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### GET `/api/chat/conversations`
List user's conversations.

**Parameters:**
- `user_id` (query): User ID
- `limit` (query): Max conversations to return (default: 20)

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv-456",
      "title": "Q4 Revenue Analysis",
      "message_count": 5,
      "updated_at": "2024-01-15T10:30:00Z",
      "last_message": {
        "role": "assistant",
        "content": "The total revenue is...",
        "timestamp": "2024-01-15T10:30:00Z"
      }
    }
  ]
}
```

#### DELETE `/api/chat/conversation/{conversation_id}`
Delete a conversation.

**Parameters:**
- `conversation_id` (path): Conversation ID
- `user_id` (query): User ID

**Response:** 204 No Content

---

### Users

#### POST `/api/users`
Create a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "department": "Finance",
  "role": "analyst",
  "preferences": {
    "default_llm_provider": "openai",
    "temperature": 0.7,
    "max_tokens": 2000,
    "response_format": "detailed",
    "show_sources": true
  }
}
```

**Response:**
```json
{
  "id": "user-789",
  "email": "user@example.com",
  "name": "John Doe",
  "department": "Finance",
  "role": "analyst",
  "preferences": {...},
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### GET `/api/users/{user_id}`
Get user details.

**Response:**
```json
{
  "id": "user-789",
  "email": "user@example.com",
  "name": "John Doe",
  "department": "Finance",
  "role": "analyst",
  "preferences": {...},
  "created_at": "2024-01-15T10:00:00Z",
  "last_login": "2024-01-15T10:30:00Z"
}
```

#### PATCH `/api/users/{user_id}/preferences`
Update user preferences.

**Request:**
```json
{
  "temperature": 0.8,
  "max_tokens": 3000,
  "show_sources": false
}
```

**Response:**
```json
{
  "id": "user-789",
  "preferences": {
    "default_llm_provider": "openai",
    "temperature": 0.8,
    "max_tokens": 3000,
    "response_format": "detailed",
    "show_sources": false
  }
}
```

#### POST `/api/users/{user_id}/login`
Record user login.

**Response:**
```json
{
  "message": "Login recorded successfully"
}
```

---

### Analytics

#### POST `/api/analytics/query`
Execute analytics query.

**Request:**
```json
{
  "query": "SELECT * FROM c WHERE c.revenue > 1000000",
  "user_id": "user123",
  "filters": {
    "year": 2023,
    "quarter": "Q4"
  }
}
```

**Response:**
```json
{
  "query": "SELECT * FROM c WHERE c.revenue > 1000000",
  "results": [
    {
      "id": "record-1",
      "revenue": 1500000,
      "quarter": "Q4",
      "year": 2023
    }
  ],
  "count": 1
}
```

#### GET `/api/analytics/search`
Perform semantic search.

**Parameters:**
- `query` (query): Search query
- `user_id` (query): User ID
- `limit` (query): Number of results (default: 5)

**Response:**
```json
{
  "query": "revenue trends",
  "results": [
    {
      "content": "Revenue increased by 15% in Q4...",
      "metadata": {
        "source": "financial_report_2023.pdf",
        "page": 5
      },
      "relevance_score": 0.92
    }
  ],
  "count": 1
}
```

#### GET `/api/analytics/insights/{user_id}`
Get user analytics insights.

**Parameters:**
- `user_id` (path): User ID
- `days` (query): Number of days to analyze (default: 30)

**Response:**
```json
{
  "user_id": "user123",
  "period_days": 30,
  "total_conversations": 15,
  "total_messages": 67,
  "average_messages_per_conversation": 4.47,
  "common_query_types": [
    {"type": "financial", "count": 8},
    {"type": "comparison", "count": 4}
  ],
  "recent_conversations": [...]
}
```

#### POST `/api/analytics/documents/index`
Index documents for semantic search.

**Request:**
```json
{
  "documents": [
    {
      "content": "Q4 revenue increased by 15% compared to Q3...",
      "metadata": {
        "source": "report.pdf",
        "page": 1,
        "date": "2023-12-31"
      }
    }
  ],
  "user_id": "user123"
}
```

**Response:**
```json
{
  "message": "Successfully indexed 1 documents",
  "count": 1
}
```

---

## Usage Examples

### Python
```python
import requests

BASE_URL = "http://localhost:8000/api"

# Send a chat message
response = requests.post(
    f"{BASE_URL}/chat/message",
    json={
        "message": "What is the total revenue?",
        "user_id": "user123"
    }
)
data = response.json()
print(f"Response: {data['message']['content']}")
print(f"Suggestions: {data['suggestions']}")

# Get conversation history
response = requests.get(
    f"{BASE_URL}/chat/history/conv-456",
    params={"user_id": "user123"}
)
history = response.json()
```

### JavaScript/TypeScript
```javascript
const BASE_URL = "http://localhost:8000/api";

// Send a chat message
async function sendMessage(message, userId, conversationId = null) {
  const response = await fetch(`${BASE_URL}/chat/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      user_id: userId,
      conversation_id: conversationId
    })
  });
  
  return await response.json();
}

// Usage
const result = await sendMessage(
  "What is the total revenue?",
  "user123"
);
console.log(result.message.content);
console.log(result.suggestions);
```

### cURL
```bash
# Send a message
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the total revenue?",
    "user_id": "user123"
  }'

# Get conversation history
curl "http://localhost:8000/api/chat/history/conv-456?user_id=user123"

# Create user
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "department": "Finance"
  }'
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success with no content
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate user)
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "detail": "Error message description",
  "type": "ErrorType"
}
```

---

## Rate Limiting

Consider implementing rate limiting in production:
- Per user: 100 requests/minute
- Per IP: 1000 requests/hour

---

## Best Practices

1. **Conversation Management**: Always include `conversation_id` for follow-up messages to maintain context

2. **User Preferences**: Set user preferences to customize LLM behavior per user

3. **Error Handling**: Always handle errors gracefully and show user-friendly messages

4. **Semantic Search**: Index relevant documents regularly for better RAG performance

5. **Pagination**: Use `limit` parameters for large result sets

6. **Caching**: Cache frequently accessed data on the client side

7. **Security**: In production, implement proper authentication and use HTTPS
