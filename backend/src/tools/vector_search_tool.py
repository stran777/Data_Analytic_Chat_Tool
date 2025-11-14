"""
Vector search MCP tool for RAG operations.
"""
from typing import Any, Dict, List

from src.services import get_rag_service
from .base_tool import BaseMCPTool


class VectorSearchTool(BaseMCPTool):
    """
    MCP tool for semantic/vector search operations.
    """
    
    def __init__(self):
        super().__init__(
            name="vector_search",
            description="Perform semantic search over financial documents using vector embeddings"
        )
        self.rag_service = get_rag_service()
    
    async def execute(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.7,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute vector search.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum relevance score (0-1)
            filters: Metadata filters to apply
            
        Returns:
            Search results with relevance scores
        """
        try:
            self.logger.info(f"Executing vector search for query: {query[:50]}...")
            
            # Perform similarity search
            results = self.rag_service.similarity_search(query, k=k)
            
            # Filter by score if available
            filtered_results = []
            for doc in results:
                score = getattr(doc, "score", 1.0)
                if score >= score_threshold:
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": score
                    })
            
            # Apply metadata filters if provided
            if filters:
                filtered_results = [
                    doc for doc in filtered_results
                    if self._matches_filters(doc["metadata"], filters)
                ]
            
            return {
                "success": True,
                "results": filtered_results,
                "count": len(filtered_results)
            }
            
        except Exception as e:
            self.logger.error(f"Error executing vector search: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if metadata matches filters.
        
        Args:
            metadata: Document metadata
            filters: Filters to apply
            
        Returns:
            True if metadata matches all filters
        """
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for semantic search"
                },
                "k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                },
                "score_threshold": {
                    "type": "number",
                    "description": "Minimum relevance score threshold (0-1)",
                    "default": 0.7
                },
                "filters": {
                    "type": "object",
                    "description": "Metadata filters to apply to results"
                }
            },
            "required": ["query"]
        }
