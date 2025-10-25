#!/usr/bin/env python3
"""
Check Event Consistency - Investigate why events keep changing
"""

import requests
import json
import time
from datetime import datetime

def check_backend_events():
    """Check current events in backend"""
    try:
        print("🔍 Checking current events in backend...")
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"📊 Backend currently has: {len(events)} events")
            
            # Show sample events
            print("\n📅 Sample events in backend:")
            for i, event in enumerate(events[:5]):
                print(f"   {i+1}. {event.get('title', 'No title')}")
            
            # Check for duplicates
            titles = [event.get('title', '') for event in events]
            unique_titles = set(titles)
            if len(titles) != len(unique_titles):
                print(f"⚠️ WARNING: Found {len(titles) - len(unique_titles)} duplicate events!")
            
            return events
        else:
            print(f"❌ Failed to get events: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking backend events: {e}")
        return None

def check_local_events():
    """Check local event files"""
    try:
        print("\n📁 Checking local event files...")
        
        # Check cleaned events
        if os.path.exists('editable_events_cleaned.json'):
            with open('editable_events_cleaned.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                events = data.get('events', [])
                print(f"📊 editable_events_cleaned.json: {len(events)} events")
        
        # Check fixed images events
        if os.path.exists('editable_events_fixed_images.json'):
            with open('editable_events_fixed_images.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                events = data.get('events', [])
                print(f"📊 editable_events_fixed_images.json: {len(events)} events")
        
        # Check backup
        if os.path.exists('events_backup_20251024_200136.json'):
            with open('events_backup_20251024_200136.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                events = data.get('events', [])
                print(f"📊 events_backup_20251024_200136.json: {len(events)} events")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking local events: {e}")
        return False

def force_upload_all_45_events():
    """Force upload all 45 events to ensure consistency"""
    try:
        print("\n🔄 Force uploading all 45 events to ensure consistency...")
        
        # Use the fixed images file (should have 45 events)
        with open('editable_events_fixed_images.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events from fixed images file")
        
        if len(events) != 45:
            print(f"⚠️ WARNING: Expected 45 events, but found {len(events)}")
        
        # Upload to backend
        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
        upload_data = {'events': events}
        
        print(f"☁️ Force uploading {len(events)} events to backend...")
        response = requests.post(backend_url, json=upload_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully force uploaded {result.get('count', len(events))} events")
                
                # Wait for database update
                time.sleep(5)
                
                # Verify immediately
                verify_upload()
                return True
            else:
                print(f"❌ Force upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Force upload failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error force uploading events: {e}")
        return False

def verify_upload():
    """Verify the upload immediately"""
    try:
        print("\n🔍 Verifying upload immediately...")
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"✅ Verification: Backend now has {len(events)} events")
            
            if len(events) == 45:
                print("🎉 SUCCESS: All 45 events are now in the backend!")
            else:
                print(f"⚠️ WARNING: Expected 45 events, but backend has {len(events)}")
            
            return len(events) == 45
        else:
            print(f"❌ Verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying upload: {e}")
        return False

def create_permanent_solution():
    """Create a permanent solution to prevent event changes"""
    try:
        print("\n🛡️ Creating permanent solution to prevent event changes...")
        
        # Create a monitoring script
        monitor_script = '''#!/usr/bin/env python3
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
'''
        
        # Save the monitor script
        with open('monitor_event_consistency.py', 'w', encoding='utf-8') as f:
            f.write(monitor_script)
        
        print("✅ Created monitor_event_consistency.py")
        print("📝 This script can be run periodically to ensure events stay at 45")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating permanent solution: {e}")
        return False

def main():
    """Main function to investigate and fix event consistency"""
    print("🔍 Investigating Event Consistency Issue")
    print("=" * 50)
    
    # Step 1: Check current state
    print("\n📊 Step 1: Checking current event state...")
    backend_events = check_backend_events()
    check_local_events()
    
    # Step 2: Force upload all 45 events
    print("\n🔄 Step 2: Force uploading all 45 events...")
    if not force_upload_all_45_events():
        print("❌ Failed to force upload events")
        return
    
    # Step 3: Create permanent solution
    print("\n🛡️ Step 3: Creating permanent solution...")
    create_permanent_solution()
    
    print("\n🎉 Event consistency investigation and fix completed!")
    print("✅ All 45 events should now be consistently available")
    print("📝 Use monitor_event_consistency.py to monitor and auto-fix if needed")

if __name__ == "__main__":
    import os
    main()
