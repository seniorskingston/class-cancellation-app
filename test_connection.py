#!/usr/bin/env python3
"""
Test script to verify backend API connection
"""
import requests
import json

# Test the backend API
BACKEND_URL = "https://class-cancellation-backend.onrender.com"

def test_backend():
    print("🧪 Testing Backend Connection...")
    print(f"Backend URL: {BACKEND_URL}")
    
    try:
        # Test 1: Check if backend is accessible
        print("\n1. Testing backend accessibility...")
        response = requests.get(f"{BACKEND_URL}/docs")
        print(f"   Status: {response.status_code}")
        print(f"   Accessible: {'✅ Yes' if response.status_code == 200 else '❌ No'}")
        
        # Test 2: Test API endpoint
        print("\n2. Testing API endpoint...")
        response = requests.get(f"{BACKEND_URL}/api/cancellations")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Data received: ✅ Yes")
            print(f"   Records count: {len(data.get('data', []))}")
            print(f"   Last loaded: {data.get('last_loaded', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
            
        # Test 3: Test with query parameters
        print("\n3. Testing with query parameters...")
        response = requests.get(f"{BACKEND_URL}/api/cancellations?has_cancellation=true")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Cancellations found: {len(data.get('data', []))}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_backend()
