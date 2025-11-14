"""
Recommendation Agent - Suggests next queries based on context.
"""
from typing import Any, Dict, List

from src.agents.base_agent import AgentState, BaseAgent
from src.services import get_llm_service


class RecommendationAgent(BaseAgent):
    """
    Agent responsible for recommending next queries.
    
    Tasks:
    - Analyze current query and response
    - Identify logical follow-up questions
    - Generate 3-5 relevant query suggestions
    - Consider conversation history and context
    """
    
    def __init__(self):
        """Initialize Recommendation Agent."""
        super().__init__("RecommendationAgent")
        self.llm_service = get_llm_service()
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Generate query recommendations.
        
        Args:
            state: Current agent state with query and response
            
        Returns:
            Updated state with recommendations
        """
        user_query = state.get("user_query", "")
        query_analysis = state.get("query_analysis", {})
        response = state.get("response", "")
        conversation_history = state.get("conversation_history", [])
        
        self.logger.info("Generating query recommendations")
        
        try:
            # Create system prompt for recommendations
            system_prompt = """You are a query recommendation assistant for a data analytics platform.

Your task is to suggest 3-5 relevant follow-up questions that users might want to ask based on:
1. The current query and response
2. Common analytical workflows
3. Natural exploration paths in data analysis

Generate diverse suggestions that help users:
- Drill deeper into specifics
- Compare with other dimensions
- Explore trends over time
- Understand related metrics

Respond with ONLY a JSON array of strings, each being a suggested question.
Example: ["What were the sales trends for Q3?", "How does this compare to last year?", "Which products contributed most to growth?"]
"""
            
            # Build context for recommendations
            context_parts = [
                f"Current query: {user_query}",
                f"Query type: {query_analysis.get('query_type', 'general')}",
            ]
            
            if response:
                # Include a summary of the response
                response_summary = response[:500] + "..." if len(response) > 500 else response
                context_parts.append(f"Response summary: {response_summary}")
            
            context = "\n\n".join(context_parts)
            
            # Generate recommendations
            messages = [{
                "role": "user",
                "content": f"Based on this context, suggest 3-5 relevant follow-up questions:\n\n{context}"
            }]
            
            recommendation_response = await self.llm_service.generate_response(
                messages=messages,
                system_prompt=system_prompt
            )
            
            # Parse recommendations
            suggestions = self._parse_recommendations(recommendation_response)
            
            state["suggestions"] = suggestions
            self.logger.info(f"Generated {len(suggestions)} recommendations")
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            state["suggestions"] = self._get_fallback_suggestions(query_analysis)
        
        return state
    
    def _parse_recommendations(self, response: str) -> List[str]:
        """
        Parse LLM response into list of recommendations.
        
        Args:
            response: LLM response
            
        Returns:
            List of recommendation strings
        """
        try:
            import json
            import re
            
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                # Validate and clean
                if isinstance(suggestions, list):
                    return [str(s).strip() for s in suggestions if s][:5]
        except Exception as e:
            self.logger.warning(f"Failed to parse recommendations JSON: {e}")
        
        # Fallback: split by newlines and filter
        lines = response.strip().split('\n')
        suggestions = []
        for line in lines:
            # Remove list markers and quotes
            clean = line.strip().lstrip('*-•123456789.').strip().strip('"\'')
            if clean and len(clean) > 10:  # Reasonable question length
                suggestions.append(clean)
        
        return suggestions[:5]
    
    def _get_fallback_suggestions(self, query_analysis: Dict[str, Any]) -> List[str]:
        """
        Get fallback suggestions when generation fails.
        
        Args:
            query_analysis: Query analysis information
            
        Returns:
            List of generic suggestions
        """
        query_type = query_analysis.get("query_type", "general")
        
        fallback_map = {
            "analytical": [
                "What are the key trends in this data?",
                "Can you break this down by category?",
                "How does this compare to previous periods?",
            ],
            "comparison": [
                "What factors contributed to the differences?",
                "Show me the top performers",
                "What's the trend over time?",
            ],
            "trend_analysis": [
                "What caused these changes?",
                "Project the trend for next quarter",
                "Compare this trend with other metrics",
            ],
            "general": [
                "Show me a summary of recent data",
                "What are the key insights?",
                "How can I explore this further?",
            ]
        }
        
        return fallback_map.get(query_type, fallback_map["general"])
