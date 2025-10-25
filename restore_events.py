#!/usr/bin/env python3
"""
Restore Events Script - Restore all 45 events if they get corrupted
"""

import requests
import json
import time
from datetime import datetime

def restore_events():
    """Restore all 45 events from permanent storage"""
    try:
        print("🔄 Restoring events from permanent storage...")
        
        # Read permanent storage
        with open('permanent_events_storage.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
            metadata = data.get('metadata', {})
        
        print(f"📁 Loaded {len(events)} events from permanent storage")
        print(f"📅 Created: {metadata.get('created_at', 'Unknown')}")
        
        # Upload to backend
        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
        upload_data = {'events': events}
        
        print(f"☁️ Restoring {len(events)} events to backend...")
        response = requests.post(backend_url, json=upload_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully restored {result.get('count', len(events))} events")
                
                # Wait for database update
                time.sleep(5)
                
                # Verify restore
                verify_restore()
                return True
            else:
                print(f"❌ Restore failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Restore failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error restoring events: {e}")
        return False

def verify_restore():
    """Verify that events were restored correctly"""
    try:
        print("🔍 Verifying restore...")
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"✅ Verification: Backend now has {len(events)} events")
            
            if len(events) == 45:
                print("🎉 SUCCESS: All 45 events restored successfully!")
            else:
                print(f"⚠️ WARNING: Expected 45 events, but backend has {len(events)}")
            
            return len(events) == 45
        else:
            print(f"❌ Verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying restore: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Event Restore System")
    print("=" * 30)
    
    if restore_events():
        print("\n🎉 Events restored successfully!")
        print("🔄 Refresh your app to see all 45 events!")
    else:
        print("\n❌ Event restore failed")
