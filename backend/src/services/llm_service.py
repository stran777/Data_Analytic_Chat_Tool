"""
LLM service for managing language model interactions.
Supports multiple providers: OpenAI, Azure OpenAI, Google Gemini, Anthropic Claude.
"""
from typing import Any, Dict, List, Literal, Optional

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from src.utils import LoggerMixin, settings


class LLMService(LoggerMixin):
    """Service for managing LLM interactions across different providers."""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM service.
        
        Args:
            provider: LLM provider to use (openai, azure-openai, google, anthropic)
        """
        self.provider = provider or settings.default_llm_provider
        self._model = None
    
    def _get_model(self) -> Any:
        """Get the appropriate LLM model based on provider."""
        if self._model is not None:
            return self._model
        
        if self.provider == "openai":
            self._model = ChatOpenAI(
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens,
                api_key=settings.openai_api_key,
            )
        elif self.provider == "azure-openai":
            self._model = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                azure_deployment=settings.azure_openai_deployment_name,
                api_version=settings.azure_openai_api_version,
                api_key=settings.azure_openai_api_key,
                temperature=settings.azure_openai_temperature,
                max_tokens=settings.azure_openai_max_tokens,
            )
        elif self.provider == "google":
            self._model = ChatGoogleGenerativeAI(
                model=settings.google_model,
                google_api_key=settings.google_api_key,
            )
        elif self.provider == "anthropic":
            self._model = ChatAnthropic(
                model=settings.anthropic_model,
                anthropic_api_key=settings.anthropic_api_key,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        self.logger.info(f"Initialized {self.provider} LLM model")
        return self._model
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to prepend
            **kwargs: Additional arguments to pass to the model
            
        Returns:
            Generated response text
        """
        try:
            model = self._get_model()
            
            # Convert messages to LangChain format
            lc_messages: List[BaseMessage] = []
            
            if system_prompt:
                lc_messages.append(SystemMessage(content=system_prompt))
            
            for msg in messages:
                if msg["role"] == "user":
                    lc_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    lc_messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    lc_messages.append(SystemMessage(content=msg["content"]))
            
            # Generate response
            response = await model.agenerate([lc_messages], **kwargs)
            response_text = response.generations[0][0].text
            
            self.logger.info(f"Generated response using {self.provider}")
            return response_text
            
        except Exception as e:
            self.logger.error(f"Failed to generate response: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # This would use a separate embedding model
        # For now, placeholder implementation
        raise NotImplementedError("Embeddings generation not yet implemented")


# Global service instance
_llm_service: Optional[LLMService] = None


def get_llm_service(provider: Optional[str] = None) -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None or (provider and provider != _llm_service.provider):
        _llm_service = LLMService(provider=provider)
    return _llm_service
