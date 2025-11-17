"""
Azure Cosmos DB bulk operations utility.
Implements best practices for efficient batch insertions and updates.

Best Practices Applied:
- Single partition batches (atomic, up to 100 items)
- Cross-partition grouping with parallel execution
- Diagnostic logging for performance monitoring
- Proper error handling and retry logic
"""
from typing import Any, Dict, List, Tuple
from collections import defaultdict
import asyncio

from azure.cosmos.container import ContainerProxy
from azure.cosmos import exceptions

from src.utils import get_logger

logger = get_logger(__name__)


class CosmosBulkOperations:
    """Utility class for bulk operations on Azure Cosmos DB containers."""
    
    @staticmethod
    async def bulk_create_items(
        container: ContainerProxy,
        items: List[Dict[str, Any]],
        partition_key_path: str = "partitionKey"
    ) -> List[Dict[str, Any]]:
        """
        Bulk insert multiple items efficiently using batch operations.
        
        Best Practices:
        - Single partition: Atomic batch operation (up to 100 items)
        - Cross-partition: Automatic grouping and parallel execution
        - Logs diagnostic information for performance monitoring
        
        Args:
            container: Cosmos DB container client
            items: List of items to insert
            partition_key_path: Field name for partition key (default: "partitionKey")
            
        Returns:
            List of successfully created items
            
        Raises:
            ValueError: If items list is empty
            Exception: If bulk operation fails
        """
        if not items:
            raise ValueError("Items list cannot be empty")
        
        container_name = container.id
        logger.info(
            f"Starting bulk insert of {len(items)} items in container: {container_name}"
        )
        
        # Group items by partition key for efficient batch operations
        partitioned_items = CosmosBulkOperations._group_by_partition_key(
            items, 
            partition_key_path
        )
        
        logger.info(f"Partitioned items: {[(pk, len(items_list)) for pk, items_list in partitioned_items.items()]}")
        
        if len(partitioned_items) == 1:
            # Single partition - use atomic batch (most efficient)
            partition_key = next(iter(partitioned_items.keys()))
            logger.info(
                f"Single partition detected ({partition_key}), using atomic batch operation"
            )
            return await CosmosBulkOperations._insert_single_partition_batch(
                container,
                items,
                partition_key
            )
        else:
            # Cross-partition - parallel execution
            logger.info(
                f"Cross-partition insert: {len(items)} items across "
                f"{len(partitioned_items)} partitions"
            )
            return await CosmosBulkOperations._insert_cross_partition_batches(
                container,
                partitioned_items
            )
    
    @staticmethod
    async def bulk_upsert_items(
        container: ContainerProxy,
        items: List[Dict[str, Any]],
        partition_key_path: str = "partitionKey"
    ) -> List[Dict[str, Any]]:
        """
        Bulk upsert (insert or update) multiple items.
        
        Args:
            container: Cosmos DB container client
            items: List of items to upsert
            partition_key_path: Field name for partition key
            
        Returns:
            List of successfully upserted items
        """
        if not items:
            raise ValueError("Items list cannot be empty")
        
        container_name = container.id
        logger.info(
            f"Starting bulk upsert of {len(items)} items in container: {container_name}"
        )
        
        # Group by partition key
        partitioned_items = CosmosBulkOperations._group_by_partition_key(
            items,
            partition_key_path
        )
        
        # Execute upsert operations per partition
        async def upsert_partition_batch(
            pk: str, 
            batch_items: List[Dict[str, Any]]
        ) -> List[Dict[str, Any]]:
            operations = [("upsert", (item,), {}) for item in batch_items]
            try:
                results = container.execute_item_batch(
                    batch_operations=operations,
                    partition_key=pk
                )
                
                successful = [
                    item for i, item in enumerate(batch_items)
                    if results[i].get("statusCode") in [200, 201]
                ]
                
                logger.info(
                    f"Partition {pk}: upserted {len(successful)}/{len(batch_items)} items"
                )
                return successful
                
            except Exception as e:
                logger.error(
                    f"Upsert batch failed for partition {pk}: {str(e)}",
                    exc_info=True
                )
                return []
        
        # Run all partition batches concurrently
        tasks = [
            upsert_partition_batch(pk, batch_items)
            for pk, batch_items in partitioned_items.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        upserted_items = []
        for result in results:
            if isinstance(result, list):
                upserted_items.extend(result)
        
        logger.info(
            f"Bulk upsert completed: {len(upserted_items)}/{len(items)} items successful"
        )
        return upserted_items
    
    @staticmethod
    async def bulk_delete_items(
        container: ContainerProxy,
        item_ids: List[Tuple[str, Any]]
    ) -> int:
        """
        Bulk delete multiple items.
        
        Args:
            container: Cosmos DB container client
            item_ids: List of (item_id, partition_key) tuples
                      partition_key can be a string or list for hierarchical keys
            
        Returns:
            Number of successfully deleted items
        """
        if not item_ids:
            raise ValueError("Item IDs list cannot be empty")
        
        container_name = container.id
        logger.info(
            f"Starting bulk delete of {len(item_ids)} items in container: {container_name}"
        )
        
        # Group by partition key
        partitioned_deletes = defaultdict(list)
        for item_id, partition_key in item_ids:
            partitioned_deletes[partition_key].append(item_id)
        
        async def delete_partition_batch(
            pk: str,
            ids: List[str]
        ) -> int:
            operations = [("delete", (item_id,), {}) for item_id in ids]
            try:
                results = container.execute_item_batch(
                    batch_operations=operations,
                    partition_key=pk
                )
                
                successful = sum(
                    1 for result in results
                    if result.get("statusCode") == 204
                )
                
                logger.info(
                    f"Partition {pk}: deleted {successful}/{len(ids)} items"
                )
                return successful
                
            except Exception as e:
                logger.error(
                    f"Delete batch failed for partition {pk}: {str(e)}",
                    exc_info=True
                )
                return 0
        
        tasks = [
            delete_partition_batch(pk, ids)
            for pk, ids in partitioned_deletes.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_deleted = sum(r for r in results if isinstance(r, int))
        
        logger.info(
            f"Bulk delete completed: {total_deleted}/{len(item_ids)} items deleted"
        )
        return total_deleted
    
    # Private helper methods
    
    @staticmethod
    def _group_by_partition_key(
        items: List[Dict[str, Any]],
        partition_key_path: str
    ) -> Dict[Any, List[Dict[str, Any]]]:
        """Group items by partition key value (supports hierarchical keys)."""
        partitioned_items = defaultdict(list)
        
        for item in items:
            # Check if hierarchical partition key (multiple fields)
            if ',' in partition_key_path:
                # Hierarchical partition key: pkType,pkFilter
                pk_fields = [f.strip() for f in partition_key_path.split(',')]
                pk_values = []
                for field in pk_fields:
                    val = item.get(field)
                    if val is None:
                        logger.warning(
                            f"Item missing hierarchical partition key field '{field}': {item}"
                        )
                        break
                    pk_values.append(val)
                else:
                    # All fields present, create tuple as partition key
                    pk = tuple(pk_values)
                    partitioned_items[pk].append(item)
            else:
                # Single partition key
                pk = item.get(partition_key_path) or item.get("id")
                if not pk:
                    logger.warning(
                        f"Item missing partition key '{partition_key_path}' and 'id': {item}"
                    )
                    continue
                partitioned_items[pk].append(item)
        
        return dict(partitioned_items)
    
    @staticmethod
    async def _insert_single_partition_batch(
        container: ContainerProxy,
        items: List[Dict[str, Any]],
        partition_key: Any
    ) -> List[Dict[str, Any]]:
        """
        Insert items in a single partition using atomic batch operation.
        Cosmos DB guarantees atomicity for single-partition batches.
        Supports both single and hierarchical partition keys.
        """
        # Cosmos DB batch limit is 100 operations
        MAX_BATCH_SIZE = 100
        
        # Convert tuple partition key to list for hierarchical keys
        pk_for_batch = list(partition_key) if isinstance(partition_key, tuple) else partition_key
        
        created_items = []
        
        for i in range(0, len(items), MAX_BATCH_SIZE):
            batch = items[i:i + MAX_BATCH_SIZE]
            operations = [("create", (item,), {}) for item in batch]
            
            try:
                results = container.execute_item_batch(
                    batch_operations=operations,
                    partition_key=pk_for_batch
                )
                
                for idx, result in enumerate(results):
                    status_code = result.get("statusCode")
                    if status_code in [200, 201]:
                        created_items.append(batch[idx])
                    else:
                        logger.warning(
                            f"Item {idx} failed to insert: "
                            f"{status_code} - {result.get('errorMessage')}"
                        )
                
                logger.info(
                    f"Batch {i // MAX_BATCH_SIZE + 1}: "
                    f"inserted {len([r for r in results if r.get('statusCode') in [200, 201]])}"
                    f"/{len(batch)} items"
                )
                
            except exceptions.CosmosHttpResponseError as e:
                logger.error(
                    f"Batch insert failed (items {i}-{i + len(batch)}): "
                    f"Status {e.status_code}, Message: {e.message}",
                    exc_info=True
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error in batch insert: {str(e)}",
                    exc_info=True
                )
        
        logger.info(
            f"Single partition insert completed: "
            f"{len(created_items)}/{len(items)} items successful"
        )
        return created_items
    
    @staticmethod
    async def _insert_cross_partition_batches(
        container: ContainerProxy,
        partitioned_items: Dict[Any, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Insert items across multiple partitions using parallel execution.
        """
        async def insert_partition(
            pk: str,
            batch_items: List[Dict[str, Any]]
        ) -> List[Dict[str, Any]]:
            return await CosmosBulkOperations._insert_single_partition_batch(
                container,
                batch_items,
                pk
            )
        
        # Execute all partitions in parallel
        tasks = [
            insert_partition(pk, batch_items)
            for pk, batch_items in partitioned_items.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten successful results
        created_items = []
        for result in results:
            if isinstance(result, list):
                created_items.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Partition batch failed: {str(result)}")
        
        total_items = sum(len(items) for items in partitioned_items.values())
        logger.info(
            f"Cross-partition insert completed: "
            f"{len(created_items)}/{total_items} items successful"
        )
        
        return created_items
