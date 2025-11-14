"""
MCP tools module.
"""
from .analytics_tool import AnalyticsTool
from .base_tool import BaseMCPTool
from .cosmos_db_tool import CosmosDBTool
from .vector_search_tool import VectorSearchTool

# Tool registry
_tool_registry = {}


def register_tool(tool: BaseMCPTool):
    """Register a tool."""
    _tool_registry[tool.name] = tool


def get_tool(name: str) -> BaseMCPTool:
    """Get a tool by name."""
    return _tool_registry.get(name)


def get_all_tools() -> dict[str, BaseMCPTool]:
    """Get all registered tools."""
    return _tool_registry.copy()


def initialize_tools():
    """Initialize and register all MCP tools."""
    tools = [
        CosmosDBTool(),
        VectorSearchTool(),
        AnalyticsTool()
    ]
    
    for tool in tools:
        register_tool(tool)
    
    return tools


__all__ = [
    "BaseMCPTool",
    "CosmosDBTool",
    "VectorSearchTool",
    "AnalyticsTool",
    "register_tool",
    "get_tool",
    "get_all_tools",
    "initialize_tools"
]
