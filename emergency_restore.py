#!/usr/bin/env python3
"""
Emergency Restore - Immediate restore of all 45 events
"""

import requests
import json
import os

def emergency_restore():
    """Emergency restore all events"""
    print("🚨 EMERGENCY RESTORE - Restoring all 45 events immediately...")
    
    # Try all backup files
    backup_files = [
        'bulletproof_events_backup.json',
        'events_emergency_backup.json',
        'events_master_backup.json',
        'events_final_backup.json',
        'permanent_events_storage.json'
    ]
    
    for backup_file in backup_files:
        if os.path.exists(backup_file):
            try:
                print(f"🔄 Trying {backup_file}...")
                
                with open(backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    events = data.get('events', [])
                
                if len(events) == 45:
                    print(f"✅ Found 45 events in {backup_file}")
                    
                    # Upload immediately
                    backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
                    upload_data = {'events': events}
                    
                    response = requests.post(backend_url, json=upload_data, timeout=60)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            print(f"🎉 EMERGENCY RESTORE SUCCESSFUL!")
                            print(f"✅ Restored {len(events)} events from {backup_file}")
                            return True
                        else:
                            print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                    else:
                        print(f"❌ Upload failed with status code: {response.status_code}")
                else:
                    print(f"⚠️ {backup_file} has {len(events)} events (expected 45)")
                    
            except Exception as e:
                print(f"❌ Error with {backup_file}: {e}")
                continue
    
    print("❌ EMERGENCY RESTORE FAILED - No working backup found")
    return False

if __name__ == "__main__":
    emergency_restore()
