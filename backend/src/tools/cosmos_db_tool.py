"""
Cosmos DB MCP tool for querying financial data.
"""
from typing import Any, Dict, List, Optional

from src.services import get_cosmos_service
from .base_tool import BaseMCPTool


class CosmosDBTool(BaseMCPTool):
    """
    MCP tool for querying Azure Cosmos DB financial data.
    """
    
    def __init__(self):
        super().__init__(
            name="cosmos_db_query",
            description="Query financial data from Azure Cosmos DB using SQL queries or filters"
        )
        self.cosmos_service = get_cosmos_service()
    
    async def execute(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        container: str = "financial_data"
    ) -> Dict[str, Any]:
        """
        Execute Cosmos DB query.
        
        Args:
            query: SQL query string or None for filter-based queries
            filters: Dictionary of filters to apply
            container: Container name (default: financial_data)
            
        Returns:
            Query results
        """
        try:
            self.logger.info(f"Executing Cosmos DB query on container: {container}")
            
            if query:
                # Execute SQL query
                results = await self.cosmos_service.query_financial_data(query)
            elif filters:
                # Build query from filters
                query = self._build_query_from_filters(filters)
                results = await self.cosmos_service.query_financial_data(query)
            else:
                return {
                    "success": False,
                    "error": "Either query or filters must be provided"
                }
            
            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
            
        except Exception as e:
            self.logger.error(f"Error executing Cosmos DB query: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_query_from_filters(self, filters: Dict[str, Any]) -> str:
        """
        Build SQL query from filters.
        
        Args:
            filters: Dictionary of field -> value filters
            
        Returns:
            SQL query string
        """
        conditions = []
        
        for field, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"c.{field} = '{value}'")
            elif isinstance(value, (int, float)):
                conditions.append(f"c.{field} = {value}")
            elif isinstance(value, dict):
                # Handle operators like {"$gte": 1000}
                for op, val in value.items():
                    operator = self._get_sql_operator(op)
                    if isinstance(val, str):
                        conditions.append(f"c.{field} {operator} '{val}'")
                    else:
                        conditions.append(f"c.{field} {operator} {val}")
        
        where_clause = " AND ".join(conditions) if conditions else "true"
        return f"SELECT * FROM c WHERE {where_clause}"
    
    def _get_sql_operator(self, mongo_op: str) -> str:
        """Map MongoDB-style operators to SQL."""
        mapping = {
            "$eq": "=",
            "$ne": "!=",
            "$gt": ">",
            "$gte": ">=",
            "$lt": "<",
            "$lte": "<="
        }
        return mapping.get(mongo_op, "=")
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute against Cosmos DB"
                },
                "filters": {
                    "type": "object",
                    "description": "Filters to apply (alternative to query)"
                },
                "container": {
                    "type": "string",
                    "description": "Container name to query",
                    "default": "financial_data"
                }
            }
        }
