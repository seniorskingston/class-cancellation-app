#!/usr/bin/env python3
"""
Test script for Excel fallback restore functionality
"""

import requests
import json
from datetime import datetime

# Update this to your backend URL
BACKEND_URL = "https://class-cancellation-backend.onrender.com"
# For local testing, use: "http://localhost:8000"

def test_fallback_status():
    """Test the fallback status endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Checking Fallback Status")
    print("="*60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/fallback/status", timeout=30)
        if response.status_code == 200:
            status = response.json()
            print("✅ Status check successful!")
            print(json.dumps(status, indent=2))
            
            # Check if fallback exists
            excel_fallback = status.get("excel_fallback", {})
            if excel_fallback.get("file_exists"):
                print(f"\n✅ Excel fallback file exists")
                print(f"   Programs in fallback: {excel_fallback.get('total_programs', 0)}")
                print(f"   Last updated: {excel_fallback.get('last_updated', 'Unknown')}")
            else:
                print("\n⚠️ Excel fallback file NOT found")
            
            # Check database status
            db_status = status.get("database_status", {})
            print(f"\n📊 Database status:")
            print(f"   Total programs: {db_status.get('total_programs', 0)}")
            print(f"   Is empty: {db_status.get('is_empty', True)}")
            
            return status
        else:
            print(f"❌ Status check failed: HTTP {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None

def test_manual_restore():
    """Test the manual restore endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Manual Restore from Fallback")
    print("="*60)
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/fallback/restore-excel", timeout=60)
        if response.status_code == 200:
            result = response.json()
            print("✅ Restore request successful!")
            print(json.dumps(result, indent=2))
            
            if result.get("success"):
                print(f"\n✅ Successfully restored {result.get('restored_count', 0)} programs")
                print(f"   Fallback had: {result.get('fallback_count', 0)} programs")
            else:
                print(f"\n❌ Restore failed: {result.get('error', 'Unknown error')}")
            
            return result
        else:
            print(f"❌ Restore request failed: HTTP {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error restoring: {e}")
        return None

def test_programs_endpoint():
    """Test that programs endpoint works and triggers auto-restore if needed"""
    print("\n" + "="*60)
    print("TEST 3: Testing Programs Endpoint (Auto-Restore)")
    print("="*60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/programs", timeout=30)
        if response.status_code == 200:
            programs = response.json()
            print(f"✅ Programs endpoint successful!")
            print(f"   Retrieved {len(programs)} programs")
            
            if len(programs) > 0:
                print(f"\n✅ Database has programs")
                print(f"   First program: {programs[0].get('program', 'Unknown')}")
            else:
                print("\n⚠️ No programs found - auto-restore should have triggered")
            
            return programs
        else:
            print(f"❌ Programs endpoint failed: HTTP {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error getting programs: {e}")
        return None

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("EXCEL FALLBACK RESTORE TEST SUITE")
    print("="*60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test time: {datetime.now().isoformat()}")
    
    # Test 1: Check status
    status = test_fallback_status()
    
    # Test 2: Manual restore (if fallback exists)
    if status and status.get("excel_fallback", {}).get("file_exists"):
        restore_result = test_manual_restore()
    else:
        print("\n⚠️ Skipping manual restore test - no fallback file found")
        restore_result = None
    
    # Test 3: Test programs endpoint
    programs = test_programs_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Status check: {'✅ PASSED' if status else '❌ FAILED'}")
    print(f"Manual restore: {'✅ PASSED' if restore_result and restore_result.get('success') else '⚠️ SKIPPED or FAILED'}")
    print(f"Programs endpoint: {'✅ PASSED' if programs is not None else '❌ FAILED'}")
    
    if programs:
        print(f"\n📊 Current database has {len(programs)} programs")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

