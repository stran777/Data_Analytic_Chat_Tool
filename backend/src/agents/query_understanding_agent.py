"""
Query Understanding Agent - Analyzes and interprets user queries.
"""
import json
from typing import Any, Dict, List

from src.agents.base_agent import AgentState, BaseAgent
from src.services import get_llm_service, get_metadata_service


class QueryUnderstandingAgent(BaseAgent):
    """
    Agent responsible for understanding user queries.
    
    Tasks:
    - Extract intent from user query
    - Identify entities and parameters
    - Classify query type (analytical, informational, etc.)
    - Reformulate query for better context
    """
    
    def __init__(self):
        """Initialize Query Understanding Agent."""
        super().__init__("QueryUnderstandingAgent")
        self.llm_service = get_llm_service()
        self.metadata_service = get_metadata_service()
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Analyze and understand the user query using metadata-driven approach.
        
        This method leverages Azure OpenAI structured output with database schema
        metadata to understand user intent and generate appropriate Cosmos DB queries.
        
        Args:
            state: Current agent state containing user_query
            
        Returns:
            Updated state with query analysis and generated Cosmos DB query
        """
        user_query = state.get("user_query", "")
        conversation_history = state.get("conversation_history", [])
        
        self.logger.info(f"Analyzing query: {user_query[:100]}")
        
        # Get schema metadata context
        schema_context = self.metadata_service.get_schema_context("gold")
        
        # Build context from conversation history
        history_context = self._build_history_context(conversation_history)
        
        # Create system prompt with schema information
        system_prompt = f"""You are an expert data analytics assistant that helps users query financial transaction data.

Your task is to analyze user queries and generate appropriate Cosmos DB NoSQL queries.

## Database Schema Information:
{schema_context}

## Query Generation Guidelines:
1. **Partition Key Optimization**: Always use pkType and pkFilter in WHERE clause when possible to minimize RU costs
2. **Date Handling**: Convert natural language dates to YYYYMMDD format for pkFilter
   - "August 2025" or "Aug 2025" → pkFilter values from 20250801 to 20250831
   - "Aug 24 2025" or "August 24, 2025" → pkFilter = '20250824'
   - "today" → current date in YYYYMMDD format
3. **Aggregations**: CRITICAL - For cross-partition aggregate queries, you MUST use VALUE keyword
   - Correct: `SELECT VALUE COUNT(1) FROM c WHERE c.pkType = @pkType`
   - Correct: `SELECT VALUE SUM(c.amount) FROM c WHERE c.pkType = @pkType`
   - Wrong: `SELECT COUNT(1) as total FROM c` (will fail on cross-partition queries)
   - Use VALUE before aggregate functions: COUNT(), SUM(), AVG(), MIN(), MAX()
4. **Group By**: For categorical breakdowns, do NOT use VALUE keyword
   - Correct: `SELECT c.category, COUNT(1) as count FROM c WHERE c.pkType = @pkType GROUP BY c.category`
5. **Filtering**: Apply WHERE conditions based on user criteria
6. **Sorting**: Use ORDER BY for ranking or sorting results

## Response Format:
You must respond with a valid JSON object containing:
{{
    "intent": "The user's intent (e.g., 'get_transaction_volume', 'analyze_amounts', 'compare_metrics')",
    "query_type": "Type of query (e.g., 'aggregation', 'filter', 'summary', 'comparison')",
    "entities": {{
        "time_period": "Extracted time period (e.g., 'August 2025', '2025-08-24')",
        "metrics": ["List of metrics requested (e.g., 'volume', 'amount', 'count')"],
        "filters": {{"field": "value"}},
        "pkType": "The partition key type to use (e.g., 'repay:settlement')",
        "pkFilter": "The partition key filter value in YYYYMMDD format or range"
    }},
    "cosmos_query": "The complete Cosmos DB NoSQL query string",
    "query_parameters": [
        {{"name": "@paramName", "value": "paramValue"}}
    ],
    "reformulated_query": "A clear, standalone version of the user's query",
    "explanation": "Brief explanation of what the query will return"
}}

## Important Notes:
- Always include pkType in the query for partition targeting
- Use parameterized queries (@ parameters) for better performance and security
- For date ranges, you may need to use pkFilter IN (...) or multiple queries
- Focus on the most efficient query possible
"""
        
        # Prepare messages for LLM
        messages = []
        
        if history_context:
            messages.append({
                "role": "system",
                "content": f"## Recent Conversation Context:\n{history_context}\n\nUse this context to understand references in the current query."
            })
        
        messages.append({
            "role": "user",
            "content": f"Analyze this query and generate a Cosmos DB NoSQL query:\n\n{user_query}"
        })
        
        try:
            # Get structured analysis from LLM
            response = await self.llm_service.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.1  # Lower temperature for more consistent structured output
            )
            
            self.logger.info(f"LLM Response: {response[:500]}")
            
            # Parse response
            query_analysis = self._parse_query_analysis(response, user_query)
            
            # Update state with comprehensive analysis
            state["query_analysis"] = query_analysis
            state["reformulated_query"] = query_analysis.get("reformulated_query", user_query)
            state["cosmos_query"] = query_analysis.get("cosmos_query", "")
            state["query_parameters"] = query_analysis.get("query_parameters", [])
            
            self.logger.info(f"Query analysis complete. Intent: {query_analysis.get('intent')}")
            self.logger.info(f"Generated Cosmos DB query: {query_analysis.get('cosmos_query', 'N/A')}")
            
        except Exception as e:
            self.logger.error(f"Error in query understanding: {e}", exc_info=True)
            # Fallback to basic analysis
            state["query_analysis"] = {
                "intent": "general_query",
                "query_type": "informational",
                "entities": {},
                "cosmos_query": "",
                "query_parameters": [],
                "reformulated_query": user_query,
                "error": str(e)
            }
            state["reformulated_query"] = user_query
            state["cosmos_query"] = ""
            state["query_parameters"] = []
        
        return state
    
    def _build_history_context(self, history: List[Dict[str, str]]) -> str:
        """Build context string from conversation history."""
        if not history:
            return ""
        
        recent = history[-3:]  # Last 3 exchanges
        context_parts = []
        
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_parts.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(context_parts)
    
    def _parse_query_analysis(self, response: str, original_query: str) -> Dict[str, Any]:
        """
        Parse LLM response into query analysis dict.
        
        Args:
            response: LLM response containing JSON
            original_query: Original user query for fallback
            
        Returns:
            Parsed query analysis dictionary
        """
        try:
            # Try to extract and parse JSON from response
            import re
            
            # Look for JSON object in the response
            json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                
                # Validate required fields
                if all(key in parsed for key in ['intent', 'query_type', 'entities', 'cosmos_query']):
                    self.logger.info("Successfully parsed structured query analysis")
                    return parsed
                else:
                    self.logger.warning(f"Parsed JSON missing required fields: {list(parsed.keys())}")
            
            # If JSON parsing fails, try to construct from response text
            self.logger.warning("JSON parsing failed, attempting text extraction")
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing response: {e}")
        
        # Fallback: return minimal structure
        return {
            "intent": "analyze_data",
            "query_type": "analytical",
            "entities": {},
            "cosmos_query": "",
            "query_parameters": [],
            "reformulated_query": original_query,
            "raw_analysis": response,
            "parse_error": "Could not extract structured data from LLM response"
        }
