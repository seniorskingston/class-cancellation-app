#!/usr/bin/env python3
"""
Apply Manual Banners - Apply manually added banners to events
"""

import json
import requests

def apply_manual_banners():
    """Apply manually added banners to events"""
    try:
        print("🔄 Applying manual banners...")
        
        # Load manual banner mapping
        with open('manual_banner_template.json', 'r', encoding='utf-8') as f:
            banner_data = json.load(f)
            banner_mapping = banner_data.get('banner_mapping', {})
        
        # Load current events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events")
        
        # Apply banners
        updated_count = 0
        for event in events:
            title = event.get('title', '')
            
            if title in banner_mapping:
                banner_url = banner_mapping[title]
                
                # Check if it's a real URL (not placeholder)
                if banner_url != "REPLACE_WITH_REAL_BANNER_URL" and banner_url.startswith('http'):
                    event['image_url'] = banner_url
                    updated_count += 1
                    print(f"   ✅ {title[:40]}... -> {banner_url}")
                else:
                    # Keep current banner if no real URL provided
                    print(f"   ⚠️ {title[:40]}... -> No real banner URL provided")
            else:
                print(f"   ⚠️ {title[:40]}... -> Not found in banner mapping")
        
        print(f"\n📊 Updated {updated_count} events with real banners")
        
        # Save updated events
        with open('bulletproof_events_backup.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Upload to backend
        print("\n☁️ Uploading updated events to backend...")
        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
        upload_data = {'events': events}
        
        response = requests.post(backend_url, json=upload_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully uploaded events with real banners")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error applying manual banners: {e}")
        return False

if __name__ == "__main__":
    apply_manual_banners()
