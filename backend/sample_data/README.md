# Data Seeder Utility

This utility allows you to bulk insert data into Azure Cosmos DB from CSV or JSON files.

## Files Created

1. **`src/utils/data_seeder.py`** - Main utility class with methods:
   - `seed_from_file()` - Generic method for any container
   - `seed_users_from_file()` - Convenience method for users
   - `seed_gold_data_from_file()` - Convenience method for gold data (hierarchical partition keys)
   - `seed_financial_data_from_file()` - Legacy method (now uses gold container)

2. **`seed_data.py`** - CLI script for command-line usage

3. **`sample_data/`** - Example data files:
   - `users.csv` / `users.json` - Sample user data
   - `gold_data.csv` / `gold_data.json` - Sample gold container data with hierarchical keys
   - `financial_data.csv` / `financial_data.json` - Legacy financial data samples

## Container Information

### Gold Container (Hierarchical Partition Keys)
The `gold` container uses **hierarchical partition keys** with two levels:
- **pkType** (string) - First level: e.g., "merchant:information", "cybersource:authorization"
- **pkFilter** (integer) - Second level: e.g., 20251030 (date-based filter)

This allows for efficient querying across different data types while maintaining logical partitioning.

## Usage

### Option 1: CLI Script

```powershell
# Seed users from CSV (auto-generate IDs and partition keys from ID)
python seed_data.py --file sample_data/users.csv --container users --auto-id --partition-from id

# Seed users from JSON
python seed_data.py --file sample_data/users.json --container users --auto-id --partition-from id

# Seed gold data from CSV (hierarchical partition keys: pkType, pkFilter)
python seed_data.py --file sample_data/gold_data.csv --container gold --auto-id

# Seed gold data from JSON
python seed_data.py --file sample_data/gold_data.json --container gold --auto-id

# Legacy: Seed financial data (now goes to gold container)
python seed_data.py --file sample_data/financial_data.csv --container gold --auto-id --partition-from symbol

# With type conversion for numeric fields
python seed_data.py --file sample_data/gold_data.csv --container gold --auto-id --type-mapping '{"pkFilter": "int", "averageTransaction": "float", "mid": "int"}'
```

### Option 2: Python Code

```python
from src.utils import DataSeeder

# Initialize seeder
seeder = DataSeeder()

# Generic usage
result = await seeder.seed_from_file(
    file_path='sample_data/users.csv',
    container_name='users',
    auto_generate_id=True,
    partition_key_from_field='id'
)

# Convenience method for users
result = await seeder.seed_users_from_file('sample_data/users.json')

# Convenience method for gold data (hierarchical partition keys)
result = await seeder.seed_gold_data_from_file('sample_data/gold_data.json')

# Legacy: financial data (now uses gold container)
result = await seeder.seed_financial_data_from_file(
    'sample_data/financial_data.csv',
    partition_key_strategy='symbol'
)

print(f"Created {result['success']} items, {result['failed']} failed")
```

### Option 3: Direct Function Call

```python
from src.utils import seed_data_from_file

result = await seed_data_from_file(
    file_path='data/my_data.json',
    container_name='financial_data',
    auto_generate_id=True,
    partition_key_from_field='symbol'
)
```

## Features

✅ **Supports CSV and JSON files**
✅ **Auto-generates IDs** if missing
✅ **Hierarchical partition keys** for gold container (pkType, pkFilter)
✅ **Flexible partition key strategies**:
   - Copy from another field (e.g., `id`, `user_id`, `symbol`)
   - Auto-generate UUIDs
   - Use existing field
   - Hierarchical keys (comma-separated: `pkType,pkFilter`)
✅ **Type conversion** for CSV data (int, float, bool, datetime)
✅ **Bulk operations** using Azure Cosmos DB best practices
✅ **Comprehensive error handling** and logging
✅ **Progress reporting** with success/failure counts

## File Format Examples

### CSV Format (Gold Container with Hierarchical Keys)
```csv
pkType,pkFilter,merchantName,mid,status,averageTransaction
merchant:information,20251030,RANDYS TOWING,460400000000,CLOSED,550
cybersource:authorization,20251111,salequicktest001,,APPROVED,100
```

### JSON Format (Gold Container - Array)
```json
[
  {
    "pkType": "merchant:information",
    "pkFilter": 20251030,
    "merchantName": "RANDYS TOWING AND RECOVERY",
    "mid": 460400000000,
    "status": "CLOSED",
    "averageTransaction": 550
  }
]
```

### CSV Format (Users)
```csv
email,name,preferences
user@example.com,User Name,"{""theme"": ""dark""}"
```

### JSON Format (Object with items key)
```json
{
  "items": [
    {"email": "user@example.com", "name": "User Name"}
  ]
}
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `file_path` | Path to CSV or JSON file | Required |
| `container_name` | Target container | Required |
| `partition_key_field` | Partition key field name | `"partitionKey"` |
| `id_field` | ID field name | `"id"` |
| `auto_generate_id` | Auto-generate IDs if missing | `False` |
| `auto_generate_partition_key` | Auto-generate partition keys | `False` |
| `partition_key_from_field` | Copy partition key from field | `None` |
| `type_mapping` | Dict mapping fields to types | `None` |

## Return Value

All methods return a dictionary with:
```python
{
    'success': 10,      # Number of items created successfully
    'failed': 2,        # Number of items that failed
    'total': 12,        # Total items in file
    'errors': [...]     # List of error messages
}
```
