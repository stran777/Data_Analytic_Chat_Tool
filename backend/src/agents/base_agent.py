"""
Base agent class for all agents in the system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langgraph.graph import StateGraph
from langchain_core.messages import BaseMessage

from src.utils import LoggerMixin


class AgentState(Dict[str, Any]):
    """State object passed between agents."""
    pass


class BaseAgent(ABC, LoggerMixin):
    """Base class for all agents."""
    
    def __init__(self, name: str):
        """
        Initialize base agent.
        
        Args:
            name: Name of the agent
        """
        self.name = name
        self.logger.info(f"Initialized agent: {name}")
    
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute the agent's main logic.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        pass
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        Make the agent callable.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        self.logger.info(f"Executing agent: {self.name}")
        return await self.execute(state)
