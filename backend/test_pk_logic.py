"""Quick test to verify hierarchical partition key logic."""

# Simulate the _process_item logic
def test_process_hierarchical_pk():
    """Test hierarchical partition key processing."""
    
    # Test item with hierarchical partition keys
    item = {
        "pkType": "merchant:information",
        "pkFilter": 20251030,
        "merchantName": "Test Merchant",
        "mid": 123456
    }
    
    partition_key_field = "pkType,pkFilter"
    
    # Check if hierarchical
    if ',' in partition_key_field:
        pk_fields = [f.strip() for f in partition_key_field.split(',')]
        print(f"✅ Detected hierarchical partition key: {pk_fields}")
        
        # Check if all fields exist
        missing_fields = [f for f in pk_fields if f not in item or item[f] is None]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
        else:
            print(f"✅ All hierarchical partition key fields present:")
            for field in pk_fields:
                print(f"   - {field}: {item[field]}")
    
    print("\n" + "="*50)
    
    # Test with missing field
    item2 = {
        "pkType": "merchant:information",
        "merchantName": "Test Merchant"
    }
    
    print("\nTest with missing pkFilter:")
    if ',' in partition_key_field:
        pk_fields = [f.strip() for f in partition_key_field.split(',')]
        missing_fields = [f for f in pk_fields if f not in item2 or item2[f] is None]
        
        if missing_fields:
            print(f"❌ Missing required hierarchical partition key fields: {missing_fields}")
        else:
            print(f"✅ All fields present")

if __name__ == "__main__":
    test_process_hierarchical_pk()
