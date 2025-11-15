"""
Response Generation Agent - Generates natural language responses.
"""
from typing import Any, Dict, List

from src.agents.base_agent import AgentState, BaseAgent
from src.services import get_llm_service


class ResponseGenerationAgent(BaseAgent):
    """
    Agent responsible for generating natural language responses.
    
    Tasks:
    - Synthesize information from retrieved data
    - Generate clear, accurate responses
    - Include relevant data points and insights
    - Format response for user consumption
    """
    
    def __init__(self):
        """Initialize Response Generation Agent."""
        super().__init__("ResponseGenerationAgent")
        self.llm_service = get_llm_service()
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Generate response based on retrieved data.
        
        Args:
            state: Current agent state with retrieved_data
            
        Returns:
            Updated state with generated response
        """
        user_query = state.get("user_query", "")
        query_analysis = state.get("query_analysis") or {}
        retrieved_data = state.get("retrieved_data") or {}
        conversation_history = state.get("conversation_history", [])
        
        self.logger.info("Generating response")
        
        try:
            # Build context for response generation
            context = self._build_response_context(retrieved_data)
            
            # Create system prompt for response generation
            system_prompt = """You are an AI assistant for a data analytics platform.

Your role is to:
1. Provide clear, accurate answers based on the available data
2. Cite specific data points when making claims
3. Acknowledge any limitations or missing information
4. Use a professional but friendly tone
5. Structure your response clearly with sections if needed

If the data is insufficient to answer the question, say so clearly and suggest what additional information might be needed.
"""
            
            # Prepare messages
            messages = []
            
            # Add context if available
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Available data and context:\n\n{context}"
                })
            
            # Add conversation history (last 2 exchanges)
            for msg in conversation_history[-4:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            # Add current query
            messages.append({
                "role": "user",
                "content": user_query
            })
            
            # Generate response
            response = await self.llm_service.generate_response(
                messages=messages,
                system_prompt=system_prompt
            )
            
            state["response"] = response
            state["response_metadata"] = {
                "context_used": bool(context),
                "sources_count": len(retrieved_data.get("rag_sources", [])),
                "financial_records_used": len(retrieved_data.get("financial_data", []))
            }
            
            self.logger.info("Response generated successfully")
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            state["response"] = "I apologize, but I encountered an error while generating a response. Please try again."
            state["response_metadata"] = {"error": str(e)}
        
        return state
    
    def _build_response_context(self, retrieved_data: Dict[str, Any]) -> str:
        """
        Build context string for response generation.
        
        Args:
            retrieved_data: Retrieved data from DataRetrievalAgent
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add RAG context
        rag_context = retrieved_data.get("rag_context", "")
        if rag_context:
            context_parts.append(f"## Relevant Context:\n{rag_context}")
        
        # Add financial data summary
        financial_data = retrieved_data.get("financial_data", [])
        if financial_data:
            # Create a summary of financial data
            data_summary = self._summarize_financial_data(financial_data)
            context_parts.append(f"## Financial Data:\n{data_summary}")
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def _summarize_financial_data(self, data: List[Dict[str, Any]]) -> str:
        """
        Create a summary of financial data.
        
        Args:
            data: List of financial data records
            
        Returns:
            Formatted summary string
        """
        if not data:
            return "No financial data available."
        
        summary_parts = [f"Found {len(data)} records:"]
        
        # Show first few records as examples
        for i, record in enumerate(data[:5], 1):
            # Format record (customize based on your schema)
            record_str = ", ".join([f"{k}: {v}" for k, v in list(record.items())[:5]])
            summary_parts.append(f"{i}. {record_str}")
        
        if len(data) > 5:
            summary_parts.append(f"... and {len(data) - 5} more records")
        
        return "\n".join(summary_parts)
