# Metadata-Driven Query Understanding Guide

## Overview

This system uses **metadata-driven query understanding** with Azure OpenAI to translate natural language questions into Cosmos DB NoSQL queries **without requiring vector embeddings**.

## Architecture

```
User Query
    ↓
QueryUnderstandingAgent
    ├── Loads schema metadata (fields, types, examples)
    ├── Sends to Azure OpenAI with structured prompt
    └── Receives: Intent + Cosmos DB Query + Parameters
    ↓
DataRetrievalAgent
    ├── Executes generated Cosmos DB query
    └── Returns results
    ↓
ResponseGenerationAgent
    └── Formats results into natural language
```

## Key Components

### 1. MetadataService (`src/services/metadata_service.py`)

**Purpose**: Stores and provides database schema information

**Contains**:
- Field names and descriptions
- Data types and valid value ranges
- Sample data and business context
- Query examples and patterns
- Hierarchical partition key information

**Example metadata structure**:
```python
{
    "gold": {
        "description": "Financial transaction data",
        "partition_key": {
            "type": "hierarchical",
            "fields": ["pkType", "pkFilter"]
        },
        "fields": {
            "pkType": {
                "type": "string",
                "description": "Transaction category",
                "valid_values": ["repay:settlement", "repay:refund"],
                "example": "repay:settlement"
            },
            "pkFilter": {
                "type": "string",
                "description": "Date in YYYYMMDD format",
                "format": "YYYYMMDD",
                "example": "20250824"
            },
            "amount": {
                "type": "number",
                "description": "Transaction amount in USD",
                "range": {"min": 0, "max": 1000000}
            }
            // ... more fields
        }
    }
}
```

### 2. QueryUnderstandingAgent (Updated)

**Changes**:
- ✅ Loads metadata using `MetadataService`
- ✅ Injects schema into Azure OpenAI prompt
- ✅ Requests structured JSON output with:
  - Intent
  - Extracted entities (time periods, metrics, filters)
  - Complete Cosmos DB NoSQL query
  - Query parameters
  - Explanation

**How it works**:
1. User asks: "Show me sales transaction volume in Aug 2025?"
2. Agent loads gold container schema metadata
3. Agent sends to Azure OpenAI with prompt containing:
   - All field definitions
   - Valid values and ranges
   - Query examples
   - Date format requirements (YYYYMMDD)
4. Azure OpenAI returns structured JSON:
```json
{
    "intent": "get_transaction_volume",
    "query_type": "aggregation",
    "entities": {
        "time_period": "August 2025",
        "metrics": ["volume"],
        "pkType": "repay:settlement",
        "pkFilter": "20250801 to 20250831"
    },
    "cosmos_query": "SELECT c.pkFilter as date, COUNT(1) as volume FROM c WHERE c.pkType = @pkType AND c.pkFilter >= @dateStart AND c.pkFilter <= @dateEnd GROUP BY c.pkFilter ORDER BY c.pkFilter",
    "query_parameters": [
        {"name": "@pkType", "value": "repay:settlement"},
        {"name": "@dateStart", "value": "20250801"},
        {"name": "@dateEnd", "value": "20250831"}
    ],
    "reformulated_query": "Get the count of settlement transactions for each day in August 2025",
    "explanation": "This query will return daily transaction volumes for all settlement transactions in August 2025"
}
```

### 3. DataRetrievalAgent (Updated)

**Changes**:
- ✅ Removed hardcoded queries
- ✅ Uses dynamically generated `cosmos_query` from state
- ✅ Uses `query_parameters` from state
- ✅ Executes query via `CosmosDBService.query_gold_data()`

**How it works**:
1. Receives state with `cosmos_query` and `query_parameters`
2. Validates gold container exists
3. Executes query with parameters
4. Returns results to next agent

## Best Practices

### 1. Optimizing Metadata

**DO**:
- ✅ Include clear field descriptions
- ✅ Specify valid value ranges
- ✅ Provide query examples
- ✅ Document partition key strategy
- ✅ Include business context

**DON'T**:
- ❌ Include sensitive data in examples
- ❌ Make descriptions too verbose (increases tokens)
- ❌ Forget to update when schema changes

### 2. Query Generation Guidelines

**Partition Key Optimization**:
```sql
-- GOOD: Targets specific partition
SELECT * FROM c 
WHERE c.pkType = 'repay:settlement' 
AND c.pkFilter = '20250824'

-- BAD: Cross-partition query (expensive)
SELECT * FROM c 
WHERE c.amount > 1000
```

**Date Handling**:
```python
# Azure OpenAI will convert:
"August 2025" → pkFilter >= '20250801' AND pkFilter <= '20250831'
"Aug 24, 2025" → pkFilter = '20250824'
"today" → pkFilter = '20251125' (current date)
```

**Aggregations**:
```sql
-- Count by category
SELECT c.category, COUNT(1) as count 
FROM c 
WHERE c.pkType = 'repay:settlement' 
GROUP BY c.category

-- Sum amounts by status
SELECT c.status, SUM(c.amount) as total 
FROM c 
WHERE c.pkType = 'repay:settlement' 
GROUP BY c.status
```

### 3. Extending Metadata

To add new fields to your schema:

1. Edit `src/services/metadata_service.py`
2. Update the `_load_schemas()` method
3. Add field definition:
```python
"newField": {
    "type": "string",
    "description": "Clear description of what this field represents",
    "valid_values": ["option1", "option2"],  # if applicable
    "example": "example_value"
}
```
4. Restart the server

### 4. Adding Query Examples

Add more query examples to help Azure OpenAI understand patterns:

```python
"query_examples": [
    {
        "description": "Get failed transactions with details",
        "query": "SELECT * FROM c WHERE c.pkType = 'repay:settlement' AND c.status = 'failed'"
    },
    {
        "description": "Calculate average transaction amount by merchant",
        "query": "SELECT c.merchantId, AVG(c.amount) as avg_amount FROM c WHERE c.pkType = 'repay:settlement' GROUP BY c.merchantId"
    }
]
```

## Advantages Over Vector Embeddings

| Feature | Metadata-Driven | Vector Embeddings |
|---------|----------------|-------------------|
| **Setup complexity** | Low - just JSON config | High - need vector store, embeddings |
| **Query accuracy** | High - precise schema info | Medium - similarity-based |
| **Cost** | Low - one LLM call | Higher - embeddings + LLM |
| **Latency** | Fast - direct query gen | Slower - retrieval + generation |
| **Maintenance** | Easy - update JSON | Complex - re-index on changes |
| **Schema awareness** | Perfect - knows all fields | Limited - depends on docs |
| **Works with existing data** | ✅ Yes | ❌ Requires re-indexing |

## Monitoring and Debugging

### Enable Detailed Logging

Check logs for:
```
QueryUnderstandingAgent: Analyzing query: Show me sales...
QueryUnderstandingAgent: Generated Cosmos DB query: SELECT...
DataRetrievalAgent: Executing Cosmos DB query: ...
DataRetrievalAgent: Query executed successfully: 42 items returned
```

### Common Issues

**1. Query returns empty results**
- Check if `pkType` and `pkFilter` values match your data
- Verify date format is YYYYMMDD
- Check logs for actual query executed

**2. LLM doesn't generate query**
- Ensure `RAG_ENABLED=False` in `.env`
- Check Azure OpenAI API key is valid
- Verify `DEFAULT_LLM_PROVIDER=azure` in `.env`

**3. Parse errors**
- LLM might not return valid JSON
- Check `raw_analysis` in logs
- Adjust system prompt temperature (lower = more consistent)

### Testing Queries

Test directly in your code:
```python
from src.services import get_metadata_service

metadata_service = get_metadata_service()
context = metadata_service.get_schema_context("gold")
print(context)
```

## Example User Queries

The system can now handle:

1. **Simple queries**
   - "Show me all transactions from August 24"
   - "Get transaction count"

2. **Aggregations**
   - "What's the total transaction amount in August?"
   - "How many transactions per payment method?"

3. **Filtering**
   - "Show failed transactions"
   - "Get high-value transactions over $1000"

4. **Time-based**
   - "Daily transaction volumes in August 2025"
   - "Compare this week vs last week"

5. **Complex analytics**
   - "Average transaction amount by merchant"
   - "Top 10 customers by transaction volume"

## Next Steps

1. **Customize metadata**: Update `metadata_service.py` with your actual schema
2. **Add more examples**: Include common query patterns
3. **Test with real data**: Run queries against your gold container
4. **Monitor performance**: Track RU consumption and query latency
5. **Iterate on prompts**: Refine system prompt for better query generation

## Future Enhancements

- Add support for multiple containers
- Implement query validation before execution
- Add query result caching
- Support for complex joins (if needed)
- Query optimization suggestions
- Automatic schema discovery from Cosmos DB
