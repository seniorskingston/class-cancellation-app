#!/usr/bin/env python3
"""
Fix Events Now - Simple script to immediately fix events if they change
"""

import requests
import json
import os

def fix_events_now():
    """Immediately fix events if they're not 45"""
    try:
        print("🔧 Fixing Events Now...")
        print("=" * 30)
        
        # Check current events
        print("🔍 Checking current events...")
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            current_count = len(events)
            
            print(f"📊 Current events: {current_count}")
            
            if current_count == 45:
                print("✅ Events are already correct (45)")
                return True
            else:
                print(f"⚠️ Events are wrong ({current_count} instead of 45)")
                print("🔄 Fixing now...")
                
                # Load from backup
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
                            with open(backup_file, 'r', encoding='utf-8') as f:
                                backup_data = json.load(f)
                                backup_events = backup_data.get('events', [])
                            
                            if len(backup_events) == 45:
                                print(f"✅ Found 45 events in {backup_file}")
                                
                                # Upload to backend
                                backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
                                upload_data = {'events': backup_events}
                                
                                response = requests.post(backend_url, json=upload_data, timeout=60)
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    if result.get('success'):
                                        print(f"🎉 SUCCESS! Fixed events to 45")
                                        
                                        # Verify
                                        verify_response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
                                        if verify_response.status_code == 200:
                                            verify_data = verify_response.json()
                                            verify_events = verify_data.get('events', [])
                                            print(f"✅ Verified: Backend now has {len(verify_events)} events")
                                        
                                        return True
                                    else:
                                        print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                                else:
                                    print(f"❌ Upload failed with status code: {response.status_code}")
                        except Exception as e:
                            print(f"❌ Error with {backup_file}: {e}")
                            continue
                
                print("❌ Failed to fix events - no working backup found")
                return False
        else:
            print(f"❌ Failed to check events: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing events: {e}")
        return False

if __name__ == "__main__":
    fix_events_now()
