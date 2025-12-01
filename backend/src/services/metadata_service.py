"""
Metadata Service - Manages database schema metadata for query understanding.

This service provides schema information to LLM agents for understanding
user queries and generating appropriate Cosmos DB NoSQL queries without
requiring vector embeddings.
"""
from typing import Any, Dict, List, Optional

from src.utils import LoggerMixin


class MetadataService(LoggerMixin):
    """
    Service for managing database schema metadata.
    
    This enables metadata-driven query understanding by providing:
    - Field names and descriptions
    - Data types and valid value ranges
    - Sample data and business context
    - Query patterns and examples
    """
    
    def __init__(self):
        """Initialize metadata service."""
        super().__init__()
        self.schemas = self._load_schemas()
        self.logger.info("Metadata service initialized")
    
    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Load database schemas and metadata.
        
        In production, this could load from:
        - Configuration files (JSON/YAML)
        - Database metadata tables
        - External schema registry
        
        Returns:
            Dictionary of container schemas
        """
        return {
            "gold": {
                "description": "Financial transaction data with settlement information",
                "partition_key": {
                    "type": "hierarchical",
                    "fields": ["pkType", "pkFilter"],
                    "description": "Hierarchical partition key for efficient querying"
                },
                "fields": {
                    "id": {
                        "type": "string",
                        "description": "Unique transaction identifier",
                        "required": True,
                        "example": "txn_2025_08_001"
                    },
                    "pkType": {
                        "type": "string",
                        "description": "Partition key type indicating data category or table. For example, 'repay:settlement' for settlement data or 'merchant:information' for merchant demographic details.",
                        "required": True,
                        "valid_values": [
                            "repay:settlement",
                            "merchant:information",
                        ],
                        "example": "repay:settlement"
                    },
                    "pkFilter": {
                        "type": "string",
                        "description": "Partition key filter - typically date in YYYYMMDD format. This represents the date of data ingestion.",
                        "required": True,
                        "format": "YYYYMMDD",
                        "example": "20250824",
                        "note": "Used for time-based partitioning"
                    },
                    "transactionDate": {
                        "type": "integer",
                        "description": "Date when transaction occurred - typically in YYYYMMDD format",
                        "format": "YYYYMMDD",
                        "example": "20250824"
                    },
                    "transactionTime": {
                        "type": "string",
                        "description": "Time when transaction occurred - typically in HH:MM:SS format",
                        "format": "HH:MM:SS",
                        "example": "14:30:00"
                    },
                    "transactionAmount": {
                        "type": "Money",
                        "description": "Transaction amount in USD",
                        "range": {"min": 0, "max": 1000000},
                        "example": 1250.50
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code",
                        "valid_values": ["USD", "EUR", "GBP", "JPY"],
                        "example": "USD"
                    },
                    "status": {
                        "type": "string",
                        "description": "Merchant enrollment status",
                        "valid_values": ["OPEN", "CLOSED", "REOPENED", "DELETED"],
                        "example": "OPEN"
                    },
                    "mid": {
                        "type": "string",
                        "description": "Merchant identifier or number",
                        "valid_values": ["123456789", "987654321"],
                        "example": "498430293025"
                    },
                    "mid": {
                        "type": "string",
                        "description": "Merchant name or DBA name",
                        "valid_values": ["JOHNSON-STRICKLAND", "STRICKLAND, MILLER AND HOFFMAN"],
                        "example": "STRICKLAND, MILLER AND HOFFMAN"
                    },
                    "customerId": {
                        "type": "string",
                        "description": "Customer identifier",
                        "example": "CUST_12345"
                    },
                    "paymentMethod": {
                        "type": "string",
                        "description": "Payment method used",
                        "valid_values": ["credit_card", "debit_card", "bank_transfer", "digital_wallet"],
                        "example": "credit_card"
                    },
                    "category": {
                        "type": "string",
                        "description": "Transaction category or type",
                        "valid_values": ["retail", "subscription", "invoice", "refund"],
                        "example": "retail"
                    },
                    "volume": {
                        "type": "integer",
                        "description": "Transaction volume or quantity",
                        "range": {"min": 1, "max": 10000},
                        "example": 5
                    }
                },
                "query_examples": [
                    {
                        "description": "Get total merchants in the database",
                        "query": ["SELECT c.pkType,COUNT(1) as total FROM c WHERE c.pkType = 'merchant:information' GROUP BY c.pkType",
                                  "select VALUE count(1) from c where c.pkType = 'merchant:information'"]
                    },
                    {
                        "description": "Find a merchant for a specific merchant id or number",
                        "query": "SELECT * FROM c WHERE c.pkType = 'merchant:information' AND c.mid = '498430293025'"
                    },
                    {
                        "description": "Find a merchant for a specific merchant name",
                        "query": "SELECT * FROM c WHERE c.pkType = 'merchant:information' AND c.merchantName like '%STRICK%'"
                    },
                    {
                        "description": "Get all settlements for a specific date",
                        "query": "SELECT * FROM c WHERE c.pkType = 'repay:settlement' AND c.transactionDate = '20250824'"
                    },
                    {
                        "description": "Get total transaction amount by status",
                        "query": "SELECT c.status, SUM(c.transactionAmount) as total FROM c WHERE c.pkType = 'repay:settlement' GROUP BY c.status"
                    },
                    {
                        "description": "Count transactions by payment method",
                        "query": "SELECT c.paymentMethod, COUNT(1) as count FROM c WHERE c.pkType = 'repay:settlement' GROUP BY c.paymentMethod"
                    },
                    {
                        "description": "Get high-value transactions over 1000",
                        "query": "SELECT * FROM c WHERE c.pkType = 'repay:settlement' AND c.transactionAmount > 1000 ORDER BY c.transactionAmount DESC"
                    }
                ],
                "business_context": {
                    "common_queries": [
                        "Search merchant information",
                        "Daily transaction volumes",
                        "Transaction amounts by status",
                        "Payment method distribution",
                        "High-value transactions",
                        "Failed transaction analysis"
                    ],
                    "time_periods": {
                        "note": "pkFilter uses YYYYMMDD format",
                        "examples": {
                            "today": "Use current date in YYYYMMDD",
                            "August 2025": "20250801 to 20250831",
                            "Aug 24, 2025": "20250824"
                        }
                    }
                }
            }
        }
    
    def get_container_schema(self, container_name: str) -> Optional[Dict[str, Any]]:
        """
        Get schema for a specific container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Schema dictionary or None if not found
        """
        return self.schemas.get(container_name)
    
    def get_schema_context(self, container_name: str) -> str:
        """
        Get formatted schema context for LLM prompt.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Formatted schema description for LLM context
        """
        schema = self.get_container_schema(container_name)
        if not schema:
            return f"No schema found for container: {container_name}"
        
        context_parts = []
        
        # Container description
        context_parts.append(f"## Container: {container_name}")
        context_parts.append(f"Description: {schema.get('description', 'N/A')}\n")
        
        # Partition key information
        pk_info = schema.get('partition_key', {})
        if pk_info:
            context_parts.append("### Partition Key (Important for Query Performance):")
            context_parts.append(f"- Type: {pk_info.get('type', 'N/A')}")
            context_parts.append(f"- Fields: {', '.join(pk_info.get('fields', []))}")
            context_parts.append(f"- Description: {pk_info.get('description', 'N/A')}\n")
        
        # Field definitions
        context_parts.append("### Available Fields:")
        fields = schema.get('fields', {})
        for field_name, field_info in fields.items():
            field_desc = [f"\n**{field_name}**"]
            field_desc.append(f"  - Type: {field_info.get('type', 'unknown')}")
            field_desc.append(f"  - Description: {field_info.get('description', 'N/A')}")
            
            if 'valid_values' in field_info:
                field_desc.append(f"  - Valid values: {', '.join(map(str, field_info['valid_values']))}")
            
            if 'format' in field_info:
                field_desc.append(f"  - Format: {field_info['format']}")
            
            if 'range' in field_info:
                range_info = field_info['range']
                field_desc.append(f"  - Range: {range_info.get('min', 'N/A')} to {range_info.get('max', 'N/A')}")
            
            if 'example' in field_info:
                field_desc.append(f"  - Example: {field_info['example']}")
            
            if 'note' in field_info:
                field_desc.append(f"  - Note: {field_info['note']}")
            
            context_parts.append('\n'.join(field_desc))
        
        # Query examples
        examples = schema.get('query_examples', [])
        if examples:
            context_parts.append("\n### Query Examples:")
            for i, example in enumerate(examples, 1):
                context_parts.append(f"\n{i}. {example.get('description', 'Example query')}")
                context_parts.append(f"   ```sql\n   {example.get('query', 'N/A')}\n   ```")
        
        # Business context
        biz_context = schema.get('business_context', {})
        if biz_context:
            context_parts.append("\n### Business Context:")
            
            common_queries = biz_context.get('common_queries', [])
            if common_queries:
                context_parts.append("\nCommon query types:")
                for query in common_queries:
                    context_parts.append(f"  - {query}")
            
            time_periods = biz_context.get('time_periods', {})
            if time_periods:
                context_parts.append(f"\nTime Period Handling:")
                if 'note' in time_periods:
                    context_parts.append(f"  Note: {time_periods['note']}")
                if 'examples' in time_periods:
                    context_parts.append("  Examples:")
                    for period, format_info in time_periods['examples'].items():
                        context_parts.append(f"    - {period}: {format_info}")
        
        return '\n'.join(context_parts)
    
    def get_all_containers(self) -> List[str]:
        """
        Get list of all available containers.
        
        Returns:
            List of container names
        """
        return list(self.schemas.keys())


# Global service instance
_metadata_service: Optional[MetadataService] = None


def get_metadata_service() -> MetadataService:
    """Get or create metadata service instance."""
    global _metadata_service
    if _metadata_service is None:
        _metadata_service = MetadataService()
    return _metadata_service
