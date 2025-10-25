#!/usr/bin/env python3
"""
Auto-Restore System - Automatically restores events if they change
"""

import requests
import json
import time
from datetime import datetime
import os

def check_and_restore_events():
    """Check events and restore if needed"""
    try:
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking events...")
        
        # Check current events
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            event_count = len(events)
            
            print(f"📊 Backend has {event_count} events")
            
            if event_count != 45:
                print(f"🚨 ALERT: Events changed from 45 to {event_count}!")
                print("🔄 Auto-restoring from bulletproof backup...")
                
                # Load from bulletproof backup
                backup_files = [
                    'bulletproof_events_backup.json',
                    'events_emergency_backup.json',
                    'events_master_backup.json',
                    'events_final_backup.json',
                    'permanent_events_storage.json'
                ]
                
                restored = False
                for backup_file in backup_files:
                    if os.path.exists(backup_file):
                        try:
                            with open(backup_file, 'r', encoding='utf-8') as f:
                                backup_data = json.load(f)
                                backup_events = backup_data.get('events', [])
                            
                            if len(backup_events) == 45:
                                # Upload backup events
                                backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
                                upload_data = {'events': backup_events}
                                
                                response = requests.post(backend_url, json=upload_data, timeout=60)
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    if result.get('success'):
                                        print(f"✅ Auto-restored from {backup_file}")
                                        restored = True
                                        break
                        except Exception as e:
                            print(f"   ❌ Failed to restore from {backup_file}: {e}")
                            continue
                
                if restored:
                    # Wait and verify
                    time.sleep(5)
                    verify_response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        verify_events = verify_data.get('events', [])
                        print(f"✅ Verified: Backend now has {len(verify_events)} events")
                    return True
                else:
                    print("❌ Auto-restore failed - no working backup found")
                    return False
            else:
                print("✅ Events are correct (45)")
                return True
        else:
            print(f"❌ Failed to check events: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in auto-restore: {e}")
        return False

if __name__ == "__main__":
    check_and_restore_events()
