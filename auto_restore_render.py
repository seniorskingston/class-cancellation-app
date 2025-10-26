#!/usr/bin/env python3
"""
Auto-Restore System - Automatically restore data when needed
"""

import json
import requests
import os
import time
from datetime import datetime

def check_and_restore_data():
    """Check if data needs to be restored and restore it"""
    try:
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking data integrity...")
        
        # Check current events
        try:
            response = requests.get('https://class-cancellation-backend.onrender.com/api/events', timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Backend not responding: {response.status_code}")
                return False
            
            data = response.json()
            events = data.get('events', [])
            current_count = len(events)
            
            print(f"📊 Current events: {current_count}")
            
            if current_count != 45:
                print(f"⚠️ DATA LOST! Events dropped to {current_count}, restoring...")
                
                # Try to restore from backups
                backup_files = [
                    'render_persistent_master.json',
                    'render_events_bulletproof.json',
                    'render_emergency_backup.json',
                    'bulletproof_events_backup.json'
                ]
                
                restored = False
                for backup_file in backup_files:
                    if os.path.exists(backup_file):
                        try:
                            print(f"📁 Trying restore from: {backup_file}")
                            with open(backup_file, 'r', encoding='utf-8') as f:
                                backup_data = json.load(f)
                                backup_events = backup_data.get('events', [])
                            
                            if len(backup_events) == 45:
                                # Upload to backend
                                upload_response = requests.post(
                                    'https://class-cancellation-backend.onrender.com/api/events/bulk-update',
                                    json={'events': backup_events},
                                    timeout=60
                                )
                                
                                if upload_response.status_code == 200:
                                    result = upload_response.json()
                                    if result.get('success'):
                                        print(f"✅ RESTORED from {backup_file}")
                                        restored = True
                                        break
                        except Exception as e:
                            print(f"   ❌ Failed to restore from {backup_file}: {e}")
                            continue
                
                if restored:
                    print("🎉 Data restoration successful!")
                    return True
                else:
                    print("❌ All restoration attempts failed!")
                    return False
            else:
                print("✅ Data integrity check passed")
                return True
                
        except requests.exceptions.Timeout:
            print("⚠️ Backend timeout - will retry later")
            return False
        except Exception as e:
            print(f"❌ Error checking data: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error in auto-restore: {e}")
        return False

if __name__ == "__main__":
    check_and_restore_data()
