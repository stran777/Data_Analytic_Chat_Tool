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
    - Query Cosmos DB for financial data using Hierarchical Partition Keys
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
        cosmos_query = state.get("cosmos_query", "")
        query_parameters = state.get("query_parameters", [])
        
        self.logger.info("Retrieving relevant data")
        
        retrieved_data = {
            "financial_data": [],
            "metadata": {}
        }
        
        try:
            # Query financial data from Cosmos DB using dynamically generated query
            if cosmos_query:
                financial_data = await self._execute_cosmos_query(
                    cosmos_query,
                    query_parameters
                )
                retrieved_data["financial_data"] = financial_data
                self.logger.info(f"Retrieved {len(financial_data)} financial records")
            else:
                self.logger.warning("No Cosmos DB query generated, skipping data retrieval")
            
            # Add metadata about retrieval
            retrieved_data["metadata"] = {
                "financial_records_count": len(retrieved_data["financial_data"]),
                "query_executed": bool(cosmos_query),
                "query": cosmos_query
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving data: {e}", exc_info=True)
            retrieved_data["error"] = str(e)
            retrieved_data["metadata"]["error"] = str(e)
        
        state["retrieved_data"] = retrieved_data
        return state
    
    async def _execute_cosmos_query(
        self,
        query: str,
        parameters: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cosmos DB NoSQL query.
        
        Args:
            query: The Cosmos DB NoSQL query string
            parameters: Query parameters
            
        Returns:
            List of query results
        """
        try:
            # Check if gold container is initialized
            if not self.cosmos_service.gold_container:
                self.logger.warning("Gold container not configured, returning empty results")
                return []
            
            self.logger.info(f"Executing Cosmos DB query:")
            self.logger.info(f"  Query: {query}")
            if parameters:
                self.logger.info(f"  Parameters: {parameters}")
            
            # Execute query using cosmos service
            results = await self.cosmos_service.query_gold_data(
                query=query,
                parameters=parameters
            )
            
            self.logger.info(f"Query executed successfully: {len(results)} items returned")
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing Cosmos DB query: {e}")
            # Log diagnostic information for troubleshooting
            self.logger.error(f"  Failed query: {query}")
            if parameters:
                self.logger.error(f"  Parameters: {parameters}")
            return []