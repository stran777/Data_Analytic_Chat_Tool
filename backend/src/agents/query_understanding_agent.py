"""
Query Understanding Agent - Analyzes and interprets user queries.
"""
from typing import Any, Dict, List

from src.agents.base_agent import AgentState, BaseAgent
from src.services import get_llm_service, get_rag_service


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
        self.rag_service = get_rag_service()
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Analyze and understand the user query.
        
        Args:
            state: Current agent state containing user_query
            
        Returns:
            Updated state with query analysis
        """
        user_query = state.get("user_query", "")
        conversation_history = state.get("conversation_history", [])
        
        self.logger.info(f"Analyzing query: {user_query[:100]}")
        
        # Build context from conversation history
        history_context = self._build_history_context(conversation_history)
        
        # Create system prompt for query understanding
        system_prompt = """You are a query understanding assistant for a data analytics system.
        
Your task is to analyze user queries and extract:
1. Intent: What does the user want to do? (e.g., analyze, compare, summarize, find trends)
2. Entities: Key entities mentioned (e.g., products, time periods, metrics, departments)
3. Query Type: classify as 'analytical', 'informational', 'comparison', 'trend_analysis', etc.
4. Reformulated Query: A clear, standalone version of the query that includes context

Respond in JSON format with these fields.
"""
        
        # Prepare messages for LLM
        messages = []
        
        if history_context:
            messages.append({
                "role": "system",
                "content": f"Recent conversation context:\n{history_context}"
            })
        
        messages.append({
            "role": "user",
            "content": f"Analyze this query: {user_query}"
        })
        
        try:
            # Get query analysis from LLM
            response = await self.llm_service.generate_response(
                messages=messages,
                system_prompt=system_prompt
            )
            
            # Parse response (in production, use structured output)
            query_analysis = self._parse_query_analysis(response, user_query)
            
            # Update state
            state["query_analysis"] = query_analysis
            state["reformulated_query"] = query_analysis.get("reformulated_query", user_query)
            
            self.logger.info(f"Query analysis complete. Intent: {query_analysis.get('intent')}")
            
        except Exception as e:
            self.logger.error(f"Error in query understanding: {e}")
            # Fallback to basic analysis
            state["query_analysis"] = {
                "intent": "general",
                "entities": [],
                "query_type": "informational",
                "reformulated_query": user_query
            }
            state["reformulated_query"] = user_query
        
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
        """Parse LLM response into query analysis dict."""
        # In production, use JSON mode or structured output
        # For now, simple parsing
        try:
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
        
        # Fallback
        return {
            "intent": "analyze",
            "entities": [],
            "query_type": "analytical",
            "reformulated_query": original_query,
            "raw_analysis": response
        }
