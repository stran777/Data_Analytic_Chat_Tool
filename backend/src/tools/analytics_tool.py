"""
Analytics MCP tool for data analysis operations.
"""
from typing import Any, Dict, List
import json

from src.services import get_cosmos_service, get_llm_service
from .base_tool import BaseMCPTool


class AnalyticsTool(BaseMCPTool):
    """
    MCP tool for performing data analytics operations.
    """
    
    def __init__(self):
        super().__init__(
            name="analytics",
            description="Perform data analytics operations like aggregations, calculations, and statistical analysis"
        )
        self.cosmos_service = get_cosmos_service()
        self.llm_service = get_llm_service()
    
    async def execute(
        self,
        operation: str,
        data: List[Dict[str, Any]] = None,
        query: str = None,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute analytics operation.
        
        Args:
            operation: Type of analytics operation (aggregate, calculate, analyze)
            data: Input data for analysis
            query: Query to fetch data if not provided
            parameters: Operation-specific parameters
            
        Returns:
            Analysis results
        """
        try:
            self.logger.info(f"Executing analytics operation: {operation}")
            
            # Fetch data if needed
            if data is None and query:
                data = await self.cosmos_service.query_financial_data(query)
            
            if not data:
                return {
                    "success": False,
                    "error": "No data provided or retrieved"
                }
            
            # Execute operation
            if operation == "aggregate":
                result = self._aggregate(data, parameters or {})
            elif operation == "calculate":
                result = self._calculate(data, parameters or {})
            elif operation == "analyze":
                result = await self._analyze(data, parameters or {})
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }
            
            return {
                "success": True,
                "operation": operation,
                "result": result,
                "data_count": len(data)
            }
            
        except Exception as e:
            self.logger.error(f"Error executing analytics operation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _aggregate(self, data: List[Dict], params: Dict) -> Dict[str, Any]:
        """
        Perform aggregation operations.
        
        Args:
            data: Input data
            params: Aggregation parameters (field, operation)
            
        Returns:
            Aggregation results
        """
        field = params.get("field")
        agg_type = params.get("type", "sum")
        
        if not field:
            return {"error": "Field parameter required for aggregation"}
        
        values = [item.get(field) for item in data if field in item and isinstance(item.get(field), (int, float))]
        
        if not values:
            return {"error": f"No numeric values found for field: {field}"}
        
        result = {}
        if agg_type in ["sum", "all"]:
            result["sum"] = sum(values)
        if agg_type in ["avg", "average", "all"]:
            result["average"] = sum(values) / len(values)
        if agg_type in ["min", "all"]:
            result["min"] = min(values)
        if agg_type in ["max", "all"]:
            result["max"] = max(values)
        if agg_type in ["count", "all"]:
            result["count"] = len(values)
        
        return result
    
    def _calculate(self, data: List[Dict], params: Dict) -> Dict[str, Any]:
        """
        Perform calculations.
        
        Args:
            data: Input data
            params: Calculation parameters
            
        Returns:
            Calculation results
        """
        expression = params.get("expression")
        
        if not expression:
            return {"error": "Expression parameter required for calculation"}
        
        # Simple calculation support
        results = []
        for item in data:
            try:
                # Create safe namespace with item data
                namespace = {k: v for k, v in item.items() if isinstance(v, (int, float))}
                result = eval(expression, {"__builtins__": {}}, namespace)
                results.append(result)
            except Exception as e:
                self.logger.warning(f"Error calculating for item: {e}")
        
        return {
            "expression": expression,
            "results": results,
            "count": len(results)
        }
    
    async def _analyze(self, data: List[Dict], params: Dict) -> Dict[str, Any]:
        """
        Perform AI-powered analysis using LLM.
        
        Args:
            data: Input data
            params: Analysis parameters
            
        Returns:
            Analysis results
        """
        analysis_type = params.get("type", "summary")
        
        # Prepare data summary for LLM
        data_summary = {
            "count": len(data),
            "fields": list(data[0].keys()) if data else [],
            "sample": data[:5]  # First 5 items
        }
        
        prompt = f"""Analyze the following financial data and provide a {analysis_type}:

Data Summary:
- Total Records: {data_summary['count']}
- Fields: {', '.join(data_summary['fields'])}
- Sample Data: {json.dumps(data_summary['sample'], indent=2)}

Please provide insights, patterns, and key findings."""
        
        # Get LLM analysis
        response = await self.llm_service.generate_response([
            {"role": "system", "content": "You are a financial data analyst."},
            {"role": "user", "content": prompt}
        ])
        
        return {
            "analysis_type": analysis_type,
            "insights": response,
            "data_summary": data_summary
        }
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["aggregate", "calculate", "analyze"],
                    "description": "Type of analytics operation to perform"
                },
                "data": {
                    "type": "array",
                    "description": "Input data for analysis (optional if query provided)"
                },
                "query": {
                    "type": "string",
                    "description": "Query to fetch data from database"
                },
                "parameters": {
                    "type": "object",
                    "description": "Operation-specific parameters"
                }
            },
            "required": ["operation"]
        }
