#!/usr/bin/env python3
"""
Admin Panel Persistence - Save changes permanently
"""

import json
import requests
import os
from datetime import datetime

def save_admin_changes_persistently(events):
    """Save admin changes to multiple persistent locations"""
    try:
        print("💾 Saving Admin Changes Persistently")
        
        if not events:
            print("❌ No events to save")
            return False
        
        # Create persistent save data
        save_data = {
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "saved_by": "admin_panel",
                "total_events": len(events),
                "persistent_save": True,
                "render_compatible": True
            },
            "events": events
        }
        
        # Save to multiple locations
        save_files = [
            'render_persistent_master.json',
            'render_events_bulletproof.json',
            'admin_changes_backup.json',
            'bulletproof_events_backup.json',
            'render_final_backup.json'
        ]
        
        for save_file in save_files:
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved to: {save_file}")
        
        # Upload to backend
        print("\n🚀 Uploading to backend...")
        response = requests.post(
            'https://class-cancellation-backend.onrender.com/api/events/bulk-update',
            json={'events': events},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully uploaded {len(events)} events to backend")
                return True
        
        print(f"❌ Backend upload failed: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Error saving persistently: {e}")
        return False

if __name__ == "__main__":
    # Load events and save persistently
    with open('render_persistent_master.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        events = data.get('events', [])
    
    if events:
        save_admin_changes_persistently(events)
