"""
Data Retrieval Agent - Retrieves relevant data from Cosmos DB.
"""
from typing import Any, Dict, List

from src.agents.base_agent import AgentState, BaseAgent
from src.services import get_cosmos_service, get_rag_service


class DataRetrievalAgent(BaseAgent):
    """
    Agent responsible for retrieving relevant data.
    
    Tasks:
    - Query Cosmos DB for financial data
    - Retrieve relevant context from vector store (RAG)
    - Format retrieved data for analysis
    """
    
    def __init__(self):
        """Initialize Data Retrieval Agent."""
        super().__init__("DataRetrievalAgent")
        self.cosmos_service = get_cosmos_service()
        self.rag_service = get_rag_service()
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Retrieve relevant data based on query analysis.
        
        Args:
            state: Current agent state with query_analysis
            
        Returns:
            Updated state with retrieved_data
        """
        query_analysis = state.get("query_analysis", {})
        reformulated_query = state.get("reformulated_query", "")
        
        self.logger.info("Retrieving relevant data")
        
        retrieved_data = {
            "financial_data": [],
            "rag_context": "",
            "rag_sources": [],
            "metadata": {}
        }
        
        try:
            # Retrieve context from RAG if enabled
            if self.rag_service and self.rag_service.vector_store:
                rag_context, rag_sources = await self.rag_service.get_relevant_context(
                    query=reformulated_query,
                    max_tokens=1500
                )
                retrieved_data["rag_context"] = rag_context
                retrieved_data["rag_sources"] = rag_sources
                self.logger.info(f"Retrieved {len(rag_sources)} RAG sources")
            
            # Query financial data from Cosmos DB
            financial_data = await self._query_financial_data(query_analysis)
            retrieved_data["financial_data"] = financial_data
            self.logger.info(f"Retrieved {len(financial_data)} financial records")
            
            # Add metadata about retrieval
            retrieved_data["metadata"] = {
                "rag_enabled": bool(retrieved_data["rag_context"]),
                "financial_records_count": len(financial_data),
                "sources_count": len(retrieved_data["rag_sources"])
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving data: {e}")
            retrieved_data["error"] = str(e)
        
        state["retrieved_data"] = retrieved_data
        return state
    
    async def _query_financial_data(
        self,
        query_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Query financial data from Cosmos DB.
        
        Args:
            query_analysis: Analyzed query information
            
        Returns:
            List of financial data records
        """
        try:
            # Build Cosmos DB query based on analysis
            # This is a simplified example - in production, use proper query builder
            intent = query_analysis.get("intent", "")
            entities = query_analysis.get("entities", [])
            query_type = query_analysis.get("query_type", "")
            
            # Example query - customize based on your schema
            if not self.cosmos_service.financial_data_container:
                self.logger.warning("Cosmos DB not configured, returning empty results")
                return []
            
            # Simple query example
            cosmos_query = "SELECT TOP 100 * FROM c ORDER BY c.timestamp DESC"
            
            # Log the SQL query
            self.logger.info(f"Cosmos DB SQL Query: {cosmos_query}")
            
            # Execute query
            results = await self.cosmos_service.query_financial_data(
                query=cosmos_query
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error querying financial data: {e}")
            return []
