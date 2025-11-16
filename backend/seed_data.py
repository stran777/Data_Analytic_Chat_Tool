"""
CLI script for seeding Cosmos DB with data from CSV or JSON files.

Usage examples:
    # Seed users from CSV
    python seed_data.py --file data/users.csv --container users
    
    # Seed financial data from JSON
    python seed_data.py --file data/financial.json --container financial_data
    
    # Custom partition key field
    python seed_data.py --file data/custom.csv --container users --partition-key user_id
    
    # Auto-generate IDs and partition keys
    python seed_data.py --file data/data.csv --container financial_data --auto-id --auto-partition
    
    # Copy partition key from ID field
    python seed_data.py --file data/users.csv --container users --partition-from id
"""
import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import DataSeeder, configure_logging


async def main():
    """Main entry point for the data seeding script."""
    parser = argparse.ArgumentParser(
        description='Seed Azure Cosmos DB with data from CSV or JSON files'
    )
    
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='Path to CSV or JSON file'
    )
    
    parser.add_argument(
        '--container', '-c',
        required=True,
        choices=['conversations', 'users', 'gold'],
        help='Target container name'
    )
    
    parser.add_argument(
        '--partition-key',
        default='partitionKey',
        help='Name of the partition key field (default: partitionKey)'
    )
    
    parser.add_argument(
        '--id-field',
        default='id',
        help='Name of the ID field (default: id)'
    )
    
    parser.add_argument(
        '--auto-id',
        action='store_true',
        help='Auto-generate IDs if missing'
    )
    
    parser.add_argument(
        '--auto-partition',
        action='store_true',
        help='Auto-generate partition keys if missing'
    )
    
    parser.add_argument(
        '--partition-from',
        help='Copy partition key value from this field (e.g., id, user_id)'
    )
    
    parser.add_argument(
        '--type-mapping',
        help='JSON string mapping field names to types, e.g. \'{"age": "int", "price": "float"}\''
    )
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging()
    
    # Parse type mapping if provided
    type_mapping = None
    if args.type_mapping:
        import json
        type_mapping = json.loads(args.type_mapping)
    
    # Initialize seeder
    seeder = DataSeeder()
    
    try:
        print(f"\n🚀 Starting data seeding...")
        print(f"📁 File: {args.file}")
        print(f"📦 Container: {args.container}")
        print(f"🔑 Partition key field: {args.partition_key}")
        
        result = await seeder.seed_from_file(
            file_path=args.file,
            container_name=args.container,
            partition_key_field=args.partition_key,
            id_field=args.id_field,
            auto_generate_id=args.auto_id,
            auto_generate_partition_key=args.auto_partition,
            partition_key_from_field=args.partition_from,
            type_mapping=type_mapping
        )
        
        print(f"\n✅ Seeding completed!")
        print(f"   Total items: {result['total']}")
        print(f"   Succeeded: {result['success']}")
        print(f"   Failed: {result['failed']}")
        
        if result['errors']:
            print(f"\n⚠️  Errors encountered:")
            for error in result['errors']:
                print(f"   - {error}")
        
        return 0 if result['failed'] == 0 else 1
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
