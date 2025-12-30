"""
CLI script for deleting Cosmos DB data by partition key filters.

Usage examples:
    # Delete data from gold container by exact pkType and pkFilter
    python delete_data.py --container gold --pk-type "repay:settlement" --pk-filter "merchant123"
    
    # Delete data with conditional operator (>=, <=, >, <, ==, !=)
    python delete_data.py --container gold --pk-type "repay:settlement" --pk-filter "20251122" --pk-filter-criteria ">="
    python delete_data.py --container gold --pk-type "repay:settlement" --pk-filter "20251120" --pk-filter-criteria "<="
    
    # Delete data without confirmation (use with caution)
    python delete_data.py --container gold --pk-type "repay:settlement" --pk-filter "merchant789" --no-confirm
    
    # Dry run: show what would be deleted without actually deleting
    python delete_data.py --container gold --pk-type "repay:settlement" --pk-filter "20251122" --pk-filter-criteria ">=" --dry-run
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.cosmos_service import CosmosDBService
from src.utils import configure_logging, LoggerMixin


class DataDeleter(LoggerMixin):
    """Utility for deleting items from Cosmos DB based on partition key filters."""
    
    def __init__(self):
        """Initialize the data deleter."""
        self.cosmos_service = CosmosDBService()
    
    async def delete_by_partition_keys(
        self,
        container_name: str,
        pk_type: str,
        pk_filter: str,
        pk_filter_criteria: str = None,
        dry_run: bool = False
    ) -> dict:
        """
        Delete items from Cosmos DB by partition key values.
        
        Args:
            container_name: Name of the target container
            pk_type: Value for pkType partition key
            pk_filter: Value for pkFilter partition key
            pk_filter_criteria: Optional comparison operator for pkFilter (>=, <=, >, <, ==, !=)
            dry_run: If True, only count items without deleting
            
        Returns:
            Dict with summary: {'deleted': int, 'failed': int, 'errors': List[str]}
        """
        container = self.cosmos_service._get_container(container_name)
        
        # Build query based on criteria
        if pk_filter_criteria:
            # Validate operator
            valid_operators = ['>=', '<=', '>', '<', '==', '!=']
            if pk_filter_criteria not in valid_operators:
                raise ValueError(f"Invalid operator: {pk_filter_criteria}. Valid operators: {valid_operators}")
            
            # Use conditional query with cross-partition
            operator = '=' if pk_filter_criteria == '==' else pk_filter_criteria
            query = f"""
                SELECT c.id, c.pkType, c.pkFilter 
                FROM c 
                WHERE c.pkType = @pkType AND c.pkFilter {operator} @pkFilter
            """
            parameters = [
                {"name": "@pkType", "value": pk_type},
                {"name": "@pkFilter", "value": pk_filter}
            ]
            enable_cross_partition = True
        else:
            # Exact match query (single partition)
            query = """
                SELECT c.id, c.pkType, c.pkFilter 
                FROM c 
                WHERE c.pkType = @pkType AND c.pkFilter = @pkFilter
            """
            parameters = [
                {"name": "@pkType", "value": pk_type},
                {"name": "@pkFilter", "value": pk_filter}
            ]
            enable_cross_partition = False
        
        try:
            if pk_filter_criteria:
                self.logger.info(f"Querying items with pkType='{pk_type}' and pkFilter {pk_filter_criteria} '{pk_filter}'")
            else:
                self.logger.info(f"Querying items with pkType='{pk_type}' and pkFilter='{pk_filter}'")
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=enable_cross_partition
            ))
            
            if not items:
                self.logger.info("No items found matching the specified partition keys")
                return {'deleted': 0, 'failed': 0, 'errors': []}
            
            self.logger.info(f"Found {len(items)} items to delete")
            
            if dry_run:
                self.logger.info("DRY RUN: No items will be deleted")
                return {'deleted': 0, 'failed': 0, 'errors': [], 'would_delete': len(items)}
            
            # Delete items
            deleted_count = 0
            failed_count = 0
            errors = []
            
            for item in items:
                try:
                    # Use the actual item's partition key for deletion
                    item_pk_filter = item['pkFilter']
                    container.delete_item(
                        item=item['id'],
                        partition_key=[pk_type, item_pk_filter]
                    )
                    deleted_count += 1
                    self.logger.debug(f"Deleted item: {item['id']}")
                except Exception as e:
                    failed_count += 1
                    error_msg = f"Failed to delete item {item['id']}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            return {
                'deleted': deleted_count,
                'failed': failed_count,
                'errors': errors
            }
            
        except Exception as e:
            error_msg = f"Error querying or deleting items: {str(e)}"
            self.logger.error(error_msg)
            return {'deleted': 0, 'failed': 0, 'errors': [error_msg]}


async def main():
    """Main entry point for the data deletion script."""
    parser = argparse.ArgumentParser(
        description='Delete data from Azure Cosmos DB by partition key filters'
    )
    
    parser.add_argument(
        '--container', '-c',
        required=True,
        choices=['conversations', 'users', 'gold'],
        help='Target container name'
    )
    
    parser.add_argument(
        '--pk-type',
        required=True,
        help='Value for pkType partition key (e.g., "repay:settlement", "cybersource:authorization")'
    )
    
    parser.add_argument(
        '--pk-filter',
        required=True,
        help='Value for pkFilter partition key (e.g., merchant number, date like 20251122)'
    )
    
    parser.add_argument(
        '--pk-filter-criteria',
        choices=['>=', '<=', '>', '<', '==', '!='],
        help='Comparison operator for pkFilter (e.g., >=, <=, >, <, ==, !=). If not specified, exact match is used.'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt (use with caution)'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging()
    
    # Initialize deleter
    deleter = DataDeleter()
    
    try:
        print(f"\n🗑️  Data Deletion Tool")
        print(f"📦 Container: {args.container}")
        print(f"🔑 pkType: {args.pk_type}")
        if args.pk_filter_criteria:
            print(f"🔑 pkFilter {args.pk_filter_criteria} {args.pk_filter}")
        else:
            print(f"🔑 pkFilter: {args.pk_filter}")
        
        if args.dry_run:
            print(f"🔍 DRY RUN MODE - No data will be deleted")
        
        # Confirmation prompt (unless dry-run or no-confirm)
        if not args.dry_run and not args.no_confirm:
            print(f"\n⚠️  WARNING: This will permanently delete all items matching the specified partition keys!")
            confirm = input("Type 'DELETE' to confirm: ")
            if confirm != "DELETE":
                print("❌ Deletion cancelled")
                return 0
        
        print(f"\n🔍 Searching for items to delete...")
        
        result = await deleter.delete_by_partition_keys(
            container_name=args.container,
            pk_type=args.pk_type,
            pk_filter=args.pk_filter,
            pk_filter_criteria=args.pk_filter_criteria,
            dry_run=args.dry_run
        )
        
        if args.dry_run:
            print(f"\n✅ Dry run completed!")
            print(f"   Would delete: {result.get('would_delete', 0)} items")
        else:
            print(f"\n✅ Deletion completed!")
            print(f"   Deleted: {result['deleted']}")
            print(f"   Failed: {result['failed']}")
        
        if result.get('errors'):
            print(f"\n⚠️  Errors encountered:")
            for error in result['errors']:
                print(f"   - {error}")
        
        return 0 if result['failed'] == 0 else 1
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
