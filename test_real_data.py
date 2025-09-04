import requests
import json

def test_withdrawal_with_real_data():
    """Test the withdrawal calculation with real API calls"""
    
    print("🧪 Testing Withdrawal with Real Data")
    print("=" * 50)
    
    # Test the API endpoint
    try:
        # Test the test endpoint first
        response = requests.get("http://localhost:8000/api/test")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is running: {data}")
        else:
            print(f"❌ Backend test failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Test getting cancellations to see withdrawal values
    try:
        response = requests.get("http://localhost:8000/api/cancellations")
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Total records: {len(data.get('data', []))}")
            
            # Show first few records with withdrawal values
            for i, record in enumerate(data.get('data', [])[:5]):
                print(f"\n📋 Record {i+1}:")
                print(f"   Date Range: '{record.get('date_range', 'N/A')}'")
                print(f"   Withdrawal: '{record.get('withdrawal', 'N/A')}'")
                print(f"   Program: '{record.get('program', 'N/A')}'")
                print(f"   Sheet: '{record.get('sheet', 'N/A')}'")
        else:
            print(f"❌ Failed to get cancellations: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing cancellations: {e}")

if __name__ == "__main__":
    test_withdrawal_with_real_data()

