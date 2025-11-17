"""
Analytics API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from src.services import get_cosmos_service, get_rag_service
from src.utils import get_logger

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = get_logger(__name__)


class QueryRequest(BaseModel):
    """Request model for analytics queries."""
    query: str
    user_id: str
    filters: Optional[dict] = None


@router.post("/query", status_code=status.HTTP_200_OK)
async def execute_query(request: QueryRequest):
    """
    Execute an analytics query against financial data.
    
    Args:
        request: Query request with SQL/natural language query
        
    Returns:
        Query results
    """
    try:
        cosmos_service = get_cosmos_service()
        
        logger.info(f"Executing analytics query for user: {request.user_id}")
        
        # Execute query
        results = await cosmos_service.query_gold_data(
            request.query,
            filters=request.filters
        )
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while executing the query: {str(e)}"
        )


@router.get("/search", status_code=status.HTTP_200_OK)
async def semantic_search(
    query: str = Query(..., description="Search query"),
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(5, description="Number of results to return")
):
    """
    Perform semantic search over financial documents.
    
    Args:
        query: Search query
        user_id: User ID for logging
        limit: Number of results to return
        
    Returns:
        Search results with relevance scores
    """
    try:
        rag_service = get_rag_service()
        
        logger.info(f"Performing semantic search for user: {user_id}")
        
        # Perform similarity search
        results = rag_service.similarity_search(query, k=limit)
        
        # Format results
        formatted_results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": getattr(doc, "score", None)
            }
            for doc in results
        ]
        
        return {
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Error performing semantic search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while performing the search: {str(e)}"
        )


@router.get("/insights/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_insights(user_id: str, days: int = 30):
    """
    Get analytics insights for a user.
    
    Args:
        user_id: User ID
        days: Number of days to analyze
        
    Returns:
        User insights and statistics
    """
    try:
        cosmos_service = get_cosmos_service()
        
        logger.info(f"Generating insights for user: {user_id}")
        
        # Get user conversations
        conversations = await cosmos_service.list_conversations(
            user_id=user_id,
            limit=100,
            status="active"
        )
        
        # Calculate insights
        total_conversations = len(conversations)
        total_messages = sum(len(conv.messages) for conv in conversations)
        avg_messages_per_conv = total_messages / total_conversations if total_conversations > 0 else 0
        
        # Get most common query types (simplified)
        query_types = []
        for conv in conversations:
            for msg in conv.messages:
                if msg.role.value == "user" and msg.metadata:
                    query_type = msg.metadata.get("query_type")
                    if query_type:
                        query_types.append(query_type)
        
        from collections import Counter
        common_query_types = Counter(query_types).most_common(5)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_messages_per_conversation": round(avg_messages_per_conv, 2),
            "common_query_types": [
                {"type": qt, "count": count}
                for qt, count in common_query_types
            ],
            "recent_conversations": [
                {
                    "id": conv.id,
                    "message_count": len(conv.messages),
                    "updated_at": conv.updated_at
                }
                for conv in conversations[:5]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating insights"
        )


@router.post("/documents/index", status_code=status.HTTP_201_CREATED)
async def index_documents(
    documents: list[dict],
    user_id: str
):
    """
    Index documents for semantic search.
    
    Args:
        documents: List of documents to index
        user_id: User ID for logging
        
    Returns:
        Success message
    """
    try:
        rag_service = get_rag_service()
        
        logger.info(f"Indexing {len(documents)} documents for user: {user_id}")
        
        # Format documents
        from langchain_core.documents import Document
        
        docs = [
            Document(
                page_content=doc.get("content", ""),
                metadata=doc.get("metadata", {})
            )
            for doc in documents
        ]
        
        # Add to vector store
        rag_service.add_documents(docs)
        
        return {
            "message": f"Successfully indexed {len(docs)} documents",
            "count": len(docs)
        }
        
    except Exception as e:
        logger.error(f"Error indexing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while indexing documents: {str(e)}"
        )
