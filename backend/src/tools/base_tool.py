"""
Base MCP tool implementation.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

from src.utils import LoggerMixin


class BaseMCPTool(ABC, LoggerMixin):
    """
    Base class for MCP (Model Context Protocol) tools.
    
    MCP tools enable agents to interact with external systems and data sources
    in a standardized way.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize MCP tool.
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        self.logger.info(f"Initialized MCP tool: {name}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get tool schema for LLM function calling.
        
        Returns:
            Tool schema in OpenAI function format
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get parameters schema for the tool.
        
        Returns:
            Parameters schema
        """
        pass
    
    async def __call__(self, **kwargs) -> Dict[str, Any]:
        """Make tool callable."""
        return await self.execute(**kwargs)
