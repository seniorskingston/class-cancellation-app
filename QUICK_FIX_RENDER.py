#!/usr/bin/env python3
"""
Quick Fix System - Immediate solution for Render data loss
"""

import json
import requests
import os
from datetime import datetime

def quick_fix_render():
    """Quick fix for Render data loss"""
    try:
        print("🚨 QUICK FIX FOR RENDER DATA LOSS")
        print("=" * 35)
        
        # Load from persistent backup
        backup_files = [
            'render_persistent_master.json',
            'render_events_bulletproof.json',
            'bulletproof_events_backup.json'
        ]
        
        events = None
        for backup_file in backup_files:
            if os.path.exists(backup_file):
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        events = data.get('events', [])
                    
                    if len(events) == 45:
                        print(f"✅ Loaded {len(events)} events from {backup_file}")
                        break
                except Exception as e:
                    print(f"❌ Error loading {backup_file}: {e}")
                    continue
        
        if not events:
            print("❌ No valid events found")
            return False
        
        # Upload to backend
        print("\n🚀 Uploading to backend...")
        try:
            response = requests.post(
                'https://class-cancellation-backend.onrender.com/api/events/bulk-update',
                json={'events': events},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"🎉 QUICK FIX SUCCESSFUL!")
                    print(f"✅ Restored {len(events)} events with real banners")
                    return True
                else:
                    print(f"❌ Upload failed: {result}")
                    return False
            else:
                print(f"❌ Backend error: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print("⚠️ Backend timeout - try again later")
            return False
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Quick fix error: {e}")
        return False

if __name__ == "__main__":
    quick_fix_render()
