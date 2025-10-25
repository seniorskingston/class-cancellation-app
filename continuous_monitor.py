#!/usr/bin/env python3
"""
Continuous Event Monitor - Runs continuously to monitor events
"""

import requests
import json
import time
from datetime import datetime
import os

def continuous_monitor():
    """Run continuous monitoring"""
    print("👁️ Starting continuous event monitoring...")
    print("🔄 This will check events every 30 seconds")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        while True:
            # Check events
            response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                event_count = len(events)
                
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] Events: {event_count}")
                
                if event_count != 45:
                    print(f"🚨 ALERT: Events changed to {event_count}! Restoring...")
                    
                    # Restore from backup
                    if os.path.exists('bulletproof_events_backup.json'):
                        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                            backup_events = backup_data.get('events', [])
                        
                        # Upload backup
                        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
                        upload_data = {'events': backup_events}
                        
                        response = requests.post(backend_url, json=upload_data, timeout=60)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('success'):
                                print(f"✅ Restored to {len(backup_events)} events")
                            else:
                                print("❌ Restore failed")
                        else:
                            print("❌ Restore failed")
                    else:
                        print("❌ No backup file found")
            
            # Wait 30 seconds
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error in continuous monitor: {e}")

if __name__ == "__main__":
    continuous_monitor()
