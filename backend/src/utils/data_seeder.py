"""
Utility tool for seeding Azure Cosmos DB with data from CSV or JSON files.
"""
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime

from src.utils import LoggerMixin
from src.services.cosmos_service import get_cosmos_service


class DataSeeder(LoggerMixin):
    """Utility for bulk creating items in Cosmos DB from CSV or JSON files."""
    
    def __init__(self):
        """Initialize the data seeder."""
        self.cosmos_service = get_cosmos_service()
    
    async def seed_from_file(
        self,
        file_path: str,
        container_name: str,
        partition_key_field: str = "partitionKey",
        id_field: str = "id",
        auto_generate_id: bool = True,
        auto_generate_partition_key: bool = False,
        partition_key_from_field: Optional[str] = None,
        type_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Seed data from a CSV or JSON file into Cosmos DB.
        
        Args:
            file_path: Path to the CSV or JSON file
            container_name: Name of the target container ('conversations', 'users', 'gold')
            partition_key_field: Name of the partition key field or comma-separated fields for hierarchical keys (default: 'partitionKey')
                                 For gold container with hierarchical keys, use 'pkType,pkFilter'
            id_field: Name of the id field (default: 'id')
            auto_generate_id: Whether to auto-generate IDs if missing (default: True)
            auto_generate_partition_key: Whether to auto-generate partition keys if missing (default: False)
            partition_key_from_field: Copy partition key value from another field (e.g., 'id', 'user_id')
            type_mapping: Optional dict mapping field names to types ('int', 'float', 'bool', 'datetime')
            
        Returns:
            Dict with summary: {'success': int, 'failed': int, 'total': int, 'errors': List[str]}
        """
        # Auto-detect hierarchical partition key for gold container
        if container_name == 'gold' and partition_key_field == 'partitionKey':
            partition_key_field = 'pkType,pkFilter'
            self.logger.info("Gold container detected, using hierarchical partition key: pkType,pkFilter")
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load data based on file type
        if path.suffix.lower() == '.json':
            items = self._load_json(path)
        elif path.suffix.lower() == '.csv':
            items = self._load_csv(path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}. Use .json or .csv")
        
        if not items:
            self.logger.warning(f"No items found in {file_path}")
            return {'success': 0, 'failed': 0, 'total': 0, 'errors': []}
        
        # Process items: add required fields, apply type conversions
        processed_items = []
        errors = []
        
        for idx, item in enumerate(items):
            try:
                processed_item = self._process_item(
                    item=item,
                    partition_key_field=partition_key_field,
                    id_field=id_field,
                    auto_generate_id=auto_generate_id,
                    auto_generate_partition_key=auto_generate_partition_key,
                    partition_key_from_field=partition_key_from_field,
                    type_mapping=type_mapping
                )
                processed_items.append(processed_item)
            except Exception as e:
                error_msg = f"Error processing item {idx}: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        # Bulk create in Cosmos DB
        try:
            self.logger.info(f"Starting bulk insert of {len(processed_items)} items into {container_name}")
            created_items = await self.cosmos_service.bulk_create_items(container_name, processed_items)
            
            result = {
                'success': len(created_items),
                'failed': len(processed_items) - len(created_items) + len(errors),
                'total': len(items),
                'errors': errors
            }
            
            self.logger.info(f"Bulk insert completed: {result['success']} succeeded, {result['failed']} failed")
            return result
            
        except Exception as e:
            self.logger.error(f"Bulk insert failed: {e}")
            raise
    
    def _load_json(self, path: Path) -> List[Dict[str, Any]]:
        """Load data from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Support both array format and object with 'items' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'items' in data:
                return data['items']
            else:
                raise ValueError("JSON must be an array or object with 'items' key")
    
    def _load_csv(self, path: Path) -> List[Dict[str, Any]]:
        """Load data from CSV file."""
        items = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(dict(row))
        return items
    
    def _process_item(
        self,
        item: Dict[str, Any],
        partition_key_field: str,
        id_field: str,
        auto_generate_id: bool,
        auto_generate_partition_key: bool,
        partition_key_from_field: Optional[str],
        type_mapping: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Process a single item: add required fields and apply type conversions."""
        processed = item.copy()
        
        # Handle ID field
        if id_field not in processed or not processed[id_field]:
            if auto_generate_id:
                processed[id_field] = str(uuid.uuid4())
            else:
                raise ValueError(f"Missing required field: {id_field}")
        
        # Handle partition key (single or hierarchical)
        if ',' in partition_key_field:
            # Hierarchical partition key (e.g., "pkType,pkFilter")
            pk_fields = [f.strip() for f in partition_key_field.split(',')]
            
            # Check if all hierarchical partition key fields exist
            missing_fields = [f for f in pk_fields if f not in processed or processed[f] is None]
            
            if missing_fields:
                if partition_key_from_field and partition_key_from_field in processed:
                    # Copy from another field (only works for single partition key)
                    self.logger.warning(
                        f"Cannot copy from single field to hierarchical partition key. "
                        f"Missing fields: {missing_fields}"
                    )
                    raise ValueError(f"Missing required hierarchical partition key fields: {missing_fields}")
                elif auto_generate_partition_key:
                    # Auto-generate missing hierarchical partition key fields
                    for field in missing_fields:
                        processed[field] = str(uuid.uuid4())
                else:
                    raise ValueError(f"Missing required hierarchical partition key fields: {missing_fields}")
        else:
            # Single partition key field
            if partition_key_field not in processed or not processed[partition_key_field]:
                if partition_key_from_field and partition_key_from_field in processed:
                    # Copy from another field
                    processed[partition_key_field] = processed[partition_key_from_field]
                elif auto_generate_partition_key:
                    processed[partition_key_field] = str(uuid.uuid4())
                else:
                    raise ValueError(f"Missing required field: {partition_key_field}")
        
        # Apply type conversions
        if type_mapping:
            for field_name, field_type in type_mapping.items():
                if field_name in processed and processed[field_name] is not None:
                    processed[field_name] = self._convert_type(
                        processed[field_name], 
                        field_type
                    )
        
        return processed
    
    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to target type."""
        if target_type == 'int':
            return int(value)
        elif target_type == 'float':
            return float(value)
        elif target_type == 'bool':
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'y')
            return bool(value)
        elif target_type == 'datetime':
            if isinstance(value, str):
                # Try parsing ISO format
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value
        else:
            return value
    
    async def seed_users_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Convenience method for seeding users.
        
        Expected CSV columns or JSON fields:
        - email (required)
        - name (optional)
        - preferences (optional, JSON string for CSV)
        
        Auto-generates: id, partitionKey (from id), created_at, last_active
        """
        # Load and enrich items
        path = Path(file_path)
        if path.suffix.lower() == '.json':
            items = self._load_json(path)
        else:
            items = self._load_csv(path)
        
        # Enrich with user-specific fields
        for item in items:
            if 'id' not in item or not item['id']:
                item['id'] = str(uuid.uuid4())
            
            item['partitionKey'] = item['id']
            
            if 'created_at' not in item:
                item['created_at'] = datetime.utcnow().isoformat()
            
            if 'last_active' not in item:
                item['last_active'] = datetime.utcnow().isoformat()
            
            # Handle preferences
            if 'preferences' in item and isinstance(item['preferences'], str):
                try:
                    item['preferences'] = json.loads(item['preferences'])
                except json.JSONDecodeError:
                    item['preferences'] = {}
            elif 'preferences' not in item:
                item['preferences'] = {}
        
        # Bulk create
        created_items = await self.cosmos_service.bulk_create_items('users', items)
        
        return {
            'success': len(created_items),
            'failed': len(items) - len(created_items),
            'total': len(items),
            'errors': []
        }
    
    async def seed_financial_data_from_file(
        self, 
        file_path: str,
        partition_key_strategy: str = 'symbol'
    ) -> Dict[str, Any]:
        """
        Convenience method for seeding financial data (legacy, use seed_gold_data_from_file).
        
        Args:
            file_path: Path to CSV or JSON file
            partition_key_strategy: Strategy for partition key ('symbol', 'date', 'uuid')
            
        Expected fields:
        - symbol (required if partition_key_strategy='symbol')
        - date (optional, for time-series data)
        - Various financial metrics
        """
        path = Path(file_path)
        if path.suffix.lower() == '.json':
            items = self._load_json(path)
        else:
            items = self._load_csv(path)
        
        # Enrich with financial data specific fields
        for item in items:
            if 'id' not in item or not item['id']:
                item['id'] = str(uuid.uuid4())
            
            # Set partition key based on strategy
            if partition_key_strategy == 'symbol' and 'symbol' in item:
                item['partitionKey'] = item['symbol']
            elif partition_key_strategy == 'date' and 'date' in item:
                item['partitionKey'] = item['date']
            else:
                item['partitionKey'] = str(uuid.uuid4())
            
            # Convert numeric fields
            numeric_fields = ['price', 'volume', 'market_cap', 'revenue', 'profit', 
                            'open', 'high', 'low', 'close']
            for field in numeric_fields:
                if field in item and item[field]:
                    try:
                        item[field] = float(item[field])
                    except (ValueError, TypeError):
                        pass
        
        # Bulk create
        created_items = await self.cosmos_service.bulk_create_items('gold', items)
        
        return {
            'success': len(created_items),
            'failed': len(items) - len(created_items),
            'total': len(items),
            'errors': []
        }
    
    async def seed_gold_data_from_file(
        self, 
        file_path: str,
        ensure_hierarchical_keys: bool = True
    ) -> Dict[str, Any]:
        """
        Convenience method for seeding gold container data with hierarchical partition keys.
        
        Args:
            file_path: Path to CSV or JSON file
            ensure_hierarchical_keys: Ensure pkType and pkFilter exist (default: True)
            
        Expected fields:
        - pkType (required) - First partition key field
        - pkFilter (required) - Second partition key field
        - id (optional, will be auto-generated if missing)
        - Various data fields specific to the data type
        """
        path = Path(file_path)
        if path.suffix.lower() == '.json':
            items = self._load_json(path)
        else:
            items = self._load_csv(path)
        
        # Enrich with gold data specific fields
        for item in items:
            # Auto-generate ID if missing
            if 'id' not in item or not item['id']:
                item['id'] = str(uuid.uuid4())
            
            # Ensure hierarchical partition keys exist
            if ensure_hierarchical_keys:
                if 'pkType' not in item or not item['pkType']:
                    raise ValueError(f"Item missing required field 'pkType': {item.get('id', 'unknown')}")
                if 'pkFilter' not in item or item['pkFilter'] is None:
                    raise ValueError(f"Item missing required field 'pkFilter': {item.get('id', 'unknown')}")
                
                # Ensure pkFilter is integer if it looks like a date
                if isinstance(item['pkFilter'], str) and item['pkFilter'].isdigit():
                    item['pkFilter'] = int(item['pkFilter'])
            
            # Convert common numeric fields
            numeric_fields = [
                'price', 'volume', 'market_cap', 'revenue', 'profit',
                'open', 'high', 'low', 'close', 'averageTransaction',
                'largestTransaction', 'processingVolume', 'mid',
                'merchantContactPhone', 'taxId', 'last4AccountNumber',
                'authorizationAmount'
            ]
            for field in numeric_fields:
                if field in item and item[field] and item[field] != '':
                    try:
                        item[field] = float(item[field])
                    except (ValueError, TypeError):
                        pass
            
            # Convert integer fields
            int_fields = ['pkFilter', 'recordId']
            for field in int_fields:
                if field in item and item[field] and item[field] != '':
                    try:
                        item[field] = int(item[field])
                    except (ValueError, TypeError):
                        pass
        
        # Bulk create using hierarchical partition key
        created_items = await self.cosmos_service.bulk_create_items('gold', items)
        
        return {
            'success': len(created_items),
            'failed': len(items) - len(created_items),
            'total': len(items),
            'errors': []
        }


async def seed_data_from_file(
    file_path: str,
    container_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for seeding data from a file.
    
    Args:
        file_path: Path to CSV or JSON file
        container_name: Target container name
        **kwargs: Additional arguments passed to DataSeeder.seed_from_file()
    
    Returns:
        Dict with summary of the operation
    """
    seeder = DataSeeder()
    return await seeder.seed_from_file(file_path, container_name, **kwargs)
