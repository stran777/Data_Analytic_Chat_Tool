"""
RAG (Retrieval-Augmented Generation) service for context-aware responses.
"""
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from src.utils import LoggerMixin, settings


class RAGService(LoggerMixin):
    """Service for Retrieval-Augmented Generation."""
    
    def __init__(self):
        """Initialize RAG service with vector store and embeddings."""
        self.embeddings = None
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        if settings.rag_enabled:
            self._initialize()
    
    def _initialize(self) -> None:
        """Initialize vector store and embeddings."""
        try:
            self.logger.info("Initializing RAG service")
            
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            
            # Initialize vector store
            if settings.vector_store_type == "chromadb":
                chroma_client = chromadb.PersistentClient(
                    path=settings.vector_store_path,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
                
                self.vector_store = Chroma(
                    client=chroma_client,
                    collection_name="knowledge_base",
                    embedding_function=self.embeddings,
                )
            else:
                raise ValueError(f"Unsupported vector store: {settings.vector_store_type}")
            
            self.logger.info("RAG service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            texts: List of text documents to add
            metadatas: Optional metadata for each document
            
        Returns:
            List of document IDs
        """
        try:
            # Split documents into chunks
            chunks = []
            chunk_metadatas = []
            
            for i, text in enumerate(texts):
                text_chunks = self.text_splitter.split_text(text)
                chunks.extend(text_chunks)
                
                # Add metadata for each chunk
                base_metadata = metadatas[i] if metadatas else {}
                chunk_metadatas.extend([
                    {**base_metadata, "chunk_index": j}
                    for j in range(len(text_chunks))
                ])
            
            # Add to vector store
            ids = self.vector_store.add_texts(
                texts=chunks,
                metadatas=chunk_metadatas
            )
            
            self.logger.info(f"Added {len(chunks)} chunks to vector store")
            return ids
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of tuples (text, score, metadata)
        """
        try:
            top_k = k or settings.rag_top_k
            
            # Perform similarity search with scores
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter=filter
            )
            
            # Filter by similarity threshold
            filtered_results = [
                (doc.page_content, score, doc.metadata)
                for doc, score in results
                if score >= settings.rag_similarity_threshold
            ]
            
            self.logger.info(
                f"Found {len(filtered_results)} relevant documents for query"
            )
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Failed to perform similarity search: {e}")
            raise
    
    async def get_relevant_context(
        self,
        query: str,
        k: Optional[int] = None,
        max_tokens: int = 2000
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Get relevant context for a query.
        
        Args:
            query: User query
            k: Number of documents to retrieve
            max_tokens: Maximum tokens in context (approximate)
            
        Returns:
            Tuple of (context_string, source_documents)
        """
        try:
            results = await self.similarity_search(query, k=k)
            
            if not results:
                return "", []
            
            # Build context string with token limit
            context_parts = []
            sources = []
            total_chars = 0
            max_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 chars
            
            for text, score, metadata in results:
                if total_chars + len(text) > max_chars:
                    break
                
                context_parts.append(text)
                sources.append({
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "score": float(score),
                    "metadata": metadata
                })
                total_chars += len(text)
            
            context = "\n\n---\n\n".join(context_parts)
            
            self.logger.info(f"Generated context with {len(sources)} sources")
            return context, sources
            
        except Exception as e:
            self.logger.error(f"Failed to get relevant context: {e}")
            raise
    
    async def delete_documents(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Delete documents from vector store.
        
        Args:
            ids: Specific document IDs to delete
            filter: Metadata filter for documents to delete
        """
        try:
            if ids:
                self.vector_store.delete(ids=ids)
                self.logger.info(f"Deleted {len(ids)} documents")
            elif filter:
                # Delete by filter (implementation depends on vector store)
                self.logger.warning("Delete by filter not fully implemented")
            else:
                self.logger.warning("No IDs or filter provided for deletion")
                
        except Exception as e:
            self.logger.error(f"Failed to delete documents: {e}")
            raise


# Global service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
