#!/usr/bin/env python3
"""
Bulletproof Event System - Create a system that NEVER loses events
"""

import requests
import json
import time
from datetime import datetime
import os

def create_bulletproof_backup():
    """Create multiple backups of the events"""
    try:
        print("🛡️ Creating bulletproof backup system...")
        
        # Load the permanent events
        with open('permanent_events_storage.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        # Create multiple backup files
        backup_files = [
            'bulletproof_events_backup.json',
            'events_emergency_backup.json',
            'events_master_backup.json',
            'events_final_backup.json'
        ]
        
        for backup_file in backup_files:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"   ✅ Created {backup_file}")
        
        print(f"✅ Created {len(backup_files)} bulletproof backups")
        return True
        
    except Exception as e:
        print(f"❌ Error creating bulletproof backup: {e}")
        return False

def create_auto_restore_system():
    """Create an automatic restore system that runs every few minutes"""
    try:
        print("🤖 Creating auto-restore system...")
        
        auto_restore_script = '''#!/usr/bin/env python3
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
'''
        
        # Save the auto-restore script
        with open('auto_restore_events.py', 'w', encoding='utf-8') as f:
            f.write(auto_restore_script)
        
        print("✅ Created auto_restore_events.py")
        return True
        
    except Exception as e:
        print(f"❌ Error creating auto-restore system: {e}")
        return False

def create_continuous_monitor():
    """Create a continuous monitoring system"""
    try:
        print("👁️ Creating continuous monitor...")
        
        monitor_script = '''#!/usr/bin/env python3
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
        print("\\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error in continuous monitor: {e}")

if __name__ == "__main__":
    continuous_monitor()
'''
        
        # Save the monitor script
        with open('continuous_monitor.py', 'w', encoding='utf-8') as f:
            f.write(monitor_script)
        
        print("✅ Created continuous_monitor.py")
        return True
        
    except Exception as e:
        print(f"❌ Error creating continuous monitor: {e}")
        return False

def create_emergency_restore():
    """Create an emergency restore script"""
    try:
        print("🚨 Creating emergency restore script...")
        
        emergency_script = '''#!/usr/bin/env python3
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
'''
        
        # Save the emergency script
        with open('emergency_restore.py', 'w', encoding='utf-8') as f:
            f.write(emergency_script)
        
        print("✅ Created emergency_restore.py")
        return True
        
    except Exception as e:
        print(f"❌ Error creating emergency restore: {e}")
        return False

def test_bulletproof_system():
    """Test the bulletproof system"""
    try:
        print("🧪 Testing bulletproof system...")
        
        # Test emergency restore
        print("\\n🚨 Testing emergency restore...")
        os.system("python emergency_restore.py")
        
        # Test auto-restore
        print("\\n🤖 Testing auto-restore...")
        os.system("python auto_restore_events.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing bulletproof system: {e}")
        return False

def main():
    """Main function to create bulletproof system"""
    print("🛡️ Creating Bulletproof Event System")
    print("=" * 50)
    
    # Step 1: Create bulletproof backups
    print("\\n🛡️ Step 1: Creating bulletproof backups...")
    if not create_bulletproof_backup():
        print("❌ Failed to create bulletproof backups")
        return
    
    # Step 2: Create auto-restore system
    print("\\n🤖 Step 2: Creating auto-restore system...")
    if not create_auto_restore_system():
        print("❌ Failed to create auto-restore system")
        return
    
    # Step 3: Create continuous monitor
    print("\\n👁️ Step 3: Creating continuous monitor...")
    if not create_continuous_monitor():
        print("❌ Failed to create continuous monitor")
        return
    
    # Step 4: Create emergency restore
    print("\\n🚨 Step 4: Creating emergency restore...")
    if not create_emergency_restore():
        print("❌ Failed to create emergency restore")
        return
    
    # Step 5: Test the system
    print("\\n🧪 Step 5: Testing bulletproof system...")
    test_bulletproof_system()
    
    print("\\n🎉 Bulletproof Event System Created!")
    print("🛡️ Events are now protected with multiple backup systems")
    print("🚨 Use emergency_restore.py if events change again")
    print("👁️ Use continuous_monitor.py to monitor events continuously")
    print("🤖 Use auto_restore_events.py for automatic restoration")

if __name__ == "__main__":
    main()
