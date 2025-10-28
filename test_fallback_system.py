#!/usr/bin/env python3
"""
SIMPLE FALLBACK SYSTEM TEST
==========================

This script tests the new simple fallback system to make sure it works correctly.
"""

import requests
import json

def test_fallback_system():
    """Test the fallback system endpoints"""
    base_url = "https://class-cancellation-backend.onrender.com"
    
    print("🧪 TESTING SIMPLE FALLBACK SYSTEM")
    print("=" * 50)
    
    # Test 1: Check current fallback status
    print("\n1️⃣ Testing fallback status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/fallback/status")
        if response.status_code == 200:
            status = response.json()
            print("✅ Fallback status endpoint working")
            print(f"   Events fallback: {'✅' if status['events_fallback']['file_exists'] else '❌'}")
            print(f"   Excel fallback: {'✅' if status['excel_fallback']['file_exists'] else '❌'}")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing status: {e}")
    
    # Test 2: Test events fallback save (if events exist)
    print("\n2️⃣ Testing events fallback save...")
    try:
        response = requests.post(f"{base_url}/api/fallback/save-events")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Events fallback save working: {result['message']}")
            else:
                print(f"⚠️ Events fallback save failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Events fallback save failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing events save: {e}")
    
    # Test 3: Test Excel fallback save
    print("\n3️⃣ Testing Excel fallback save...")
    try:
        response = requests.post(f"{base_url}/api/fallback/save-excel")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Excel fallback save working: {result['message']}")
            else:
                print(f"⚠️ Excel fallback save failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Excel fallback save failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing Excel save: {e}")
    
    # Test 4: Check status again after saves
    print("\n4️⃣ Checking fallback status after saves...")
    try:
        response = requests.get(f"{base_url}/api/fallback/status")
        if response.status_code == 200:
            status = response.json()
            print("✅ Final fallback status:")
            if status['events_fallback']['file_exists']:
                print(f"   📅 Events: {status['events_fallback']['total_events']} events")
                print(f"   🕒 Last updated: {status['events_fallback']['last_updated']}")
            else:
                print("   📅 Events: No fallback data")
                
            if status['excel_fallback']['file_exists']:
                print(f"   📊 Excel: {status['excel_fallback']['total_programs']} programs")
                print(f"   🕒 Last updated: {status['excel_fallback']['last_updated']}")
            else:
                print("   📊 Excel: No fallback data")
        else:
            print(f"❌ Final status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking final status: {e}")
    
    print("\n🎉 FALLBACK SYSTEM TEST COMPLETE!")
    print("\n💡 Next steps:")
    print("   1. Go to Admin Panel in your app")
    print("   2. Upload your Excel file")
    print("   3. Click '💾 Save Excel as Fallback'")
    print("   4. Click '💾 Save Events as Fallback' (if you have events)")
    print("   5. Click '📊 Check Fallback Status' to verify")

if __name__ == "__main__":
    test_fallback_system()
