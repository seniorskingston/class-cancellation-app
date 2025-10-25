#!/usr/bin/env python3
"""
Event Consistency Monitor - Run this periodically to ensure events stay at 45
"""

import requests
import json
import time
from datetime import datetime

def monitor_events():
    """Monitor events and fix if they change"""
    try:
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            event_count = len(events)
            
            print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Backend has {event_count} events")
            
            if event_count != 45:
                print(f"⚠️ ALERT: Events changed from 45 to {event_count}!")
                print("🔄 Auto-fixing by uploading correct events...")
                
                # Load the correct events
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
        print(f"❌ Error monitoring events: {e}")
        return False

if __name__ == "__main__":
    monitor_events()
