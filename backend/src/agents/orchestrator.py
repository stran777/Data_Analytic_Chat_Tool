"""
Orchestrator for coordinating multi-agent workflow using LangGraph.
"""
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph

from src.agents.base_agent import AgentState
from src.agents.data_retrieval_agent import DataRetrievalAgent
from src.agents.query_understanding_agent import QueryUnderstandingAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.response_generation_agent import ResponseGenerationAgent
from src.utils import LoggerMixin


class AgentOrchestrator(LoggerMixin):
    """
    Orchestrates the multi-agent workflow using LangGraph.
    
    Workflow:
    1. Query Understanding Agent - Analyzes user query
    2. Data Retrieval Agent - Fetches relevant data
    3. Response Generation Agent - Creates response
    4. Recommendation Agent - Suggests follow-up questions
    """
    
    def __init__(self):
        """Initialize the orchestrator and agents."""
        super().__init__()
        self.logger.info("Initializing Agent Orchestrator")
        
        # Initialize agents
        self.query_understanding_agent = QueryUnderstandingAgent()
        self.data_retrieval_agent = DataRetrievalAgent()
        self.response_generation_agent = ResponseGenerationAgent()
        self.recommendation_agent = RecommendationAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Compiled workflow graph
        """
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("understand_query", self.query_understanding_agent)
        workflow.add_node("retrieve_data", self.data_retrieval_agent)
        workflow.add_node("generate_response", self.response_generation_agent)
        workflow.add_node("generate_recommendations", self.recommendation_agent)
        
        # Define the flow
        workflow.set_entry_point("understand_query")
        workflow.add_edge("understand_query", "retrieve_data")
        workflow.add_edge("retrieve_data", "generate_response")
        workflow.add_edge("generate_response", "generate_recommendations")
        workflow.add_edge("generate_recommendations", END)
        
        # Compile the graph
        compiled_workflow = workflow.compile()
        
        self.logger.info("Workflow graph built successfully")
        return compiled_workflow
    
    async def process_query(
        self,
        user_query: str,
        user_id: str,
        conversation_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the agent workflow.
        
        Args:
            user_query: The user's question
            user_id: User identifier
            conversation_id: Conversation identifier
            conversation_history: Previous messages in conversation
            
        Returns:
            Dict containing response and recommendations
        """
        self.logger.info(f"Processing query for user {user_id}")
        
        # Initialize state
        initial_state: AgentState = {
            "user_query": user_query,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "conversation_history": conversation_history or [],
            "query_analysis": {},
            "retrieved_data": {},
            "response": "",
            "suggestions": [],
        }
        
        try:
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Extract results
            result = {
                "response": final_state.get("response", ""),
                "suggestions": final_state.get("suggestions", []),
                "metadata": {
                    "query_analysis": final_state.get("query_analysis", {}),
                    "response_metadata": final_state.get("response_metadata", {}),
                    "sources": final_state.get("retrieved_data", {}).get("rag_sources", []),
                }
            }
            
            self.logger.info("Query processing completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in workflow execution: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your query. Please try again.",
                "suggestions": [],
                "metadata": {"error": str(e)}
            }


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
