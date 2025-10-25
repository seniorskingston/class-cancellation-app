#!/usr/bin/env python3
"""
Auto-Fix Event System - Automatically fixes events if they change
"""

import requests
import json
import time
from datetime import datetime
import os

def check_and_fix_events():
    """Check events and auto-fix if needed"""
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
                print(f"⚠️ ALERT: Events changed from 45 to {event_count}!")
                print("🤖 Auto-fixing...")
                
                # Load correct events from permanent storage
                if os.path.exists('permanent_events_storage.json'):
                    with open('permanent_events_storage.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        correct_events = data.get('events', [])
                else:
                    # Fallback to fixed images file
                    with open('editable_events_fixed_images.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        correct_events = data.get('events', [])
                
                # Upload correct events
                backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
                upload_data = {'events': correct_events}
                
                response = requests.post(backend_url, json=upload_data, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        print(f"✅ Auto-fixed: Restored {len(correct_events)} events")
                        
                        # Wait and verify
                        time.sleep(5)
                        verify_response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
                        if verify_response.status_code == 200:
                            verify_data = verify_response.json()
                            verify_events = verify_data.get('events', [])
                            print(f"✅ Verified: Backend now has {len(verify_events)} events")
                        
                        return True
                
                print("❌ Auto-fix failed")
                return False
            else:
                print("✅ Events are correct (45)")
                return True
        else:
            print(f"❌ Failed to check events: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in auto-fix: {e}")
        return False

if __name__ == "__main__":
    check_and_fix_events()
