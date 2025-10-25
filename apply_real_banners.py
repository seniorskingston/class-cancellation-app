#!/usr/bin/env python3
"""
Apply Real Banners - Apply the scraped real banners to events
"""

import json
import requests

def apply_real_banners():
    """Apply the scraped real banners to events"""
    try:
        print("🎯 Applying Real Event Banners")
        print("=" * 30)
        
        # Load banner mapping from Selenium scraping
        with open('selenium_banners.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            banner_mapping = data.get('banner_mapping', {})
        
        print(f"📊 Loaded {len(banner_mapping)} real banner mappings")
        
        # Load current events from bulletproof backup
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📊 Loaded {len(events)} events")
        
        # Apply banners to events
        updated_count = 0
        for event in events:
            event_title = event.get('title', '')
            
            # Try to find matching banner
            for banner_title, banner_url in banner_mapping.items():
                # Clean up titles for better matching
                clean_event_title = event_title.lower().strip()
                clean_banner_title = banner_title.lower().strip()
                
                # Check for exact matches first
                if clean_event_title == clean_banner_title:
                    event['image_url'] = banner_url
                    print(f"✅ Exact match: {event_title} -> {banner_url}")
                    updated_count += 1
                    break
                
                # Check for partial matches
                elif (clean_banner_title in clean_event_title or 
                      clean_event_title in clean_banner_title or
                      any(word in clean_event_title for word in clean_banner_title.split() if len(word) > 3)):
                    
                    event['image_url'] = banner_url
                    print(f"✅ Partial match: {event_title} -> {banner_url}")
                    updated_count += 1
                    break
        
        print(f"\\n📊 Applied {updated_count} real banners to events")
        
        # Save updated events
        updated_data = {
            "metadata": {
                "updated_at": "2025-01-24T20:30:00Z",
                "total_events": len(events),
                "banners_applied": updated_count,
                "description": "Events with real Seniors Kingston banners applied",
                "source": "selenium_banners.json"
            },
            "events": events
        }
        
        with open('events_with_real_banners.json', 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Saved events with real banners to events_with_real_banners.json")
        
        # Upload to backend
        print("\\n🚀 Uploading to backend...")
        response = requests.post(
            'https://class-cancellation-backend.onrender.com/api/events/bulk-update',
            json={'events': events},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully uploaded {len(events)} events with real banners!")
                
                # Update bulletproof backup with new banners
                with open('bulletproof_events_backup.json', 'w', encoding='utf-8') as f:
                    json.dump(updated_data, f, indent=2, ensure_ascii=False)
                
                print("✅ Updated bulletproof backup with real banners")
                return True
        
        print(f"❌ Upload failed: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Error applying banners: {e}")
        return False

def show_banner_preview():
    """Show a preview of the banners that will be applied"""
    try:
        print("\\n🖼️ Banner Preview:")
        print("=" * 20)
        
        with open('selenium_banners.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            banner_mapping = data.get('banner_mapping', {})
        
        count = 0
        for title, url in banner_mapping.items():
            if count < 10:  # Show first 10
                print(f"   🎯 {title}")
                print(f"      🖼️ {url}")
                print()
                count += 1
            else:
                print(f"   ... and {len(banner_mapping) - 10} more banners")
                break
        
    except Exception as e:
        print(f"❌ Error showing preview: {e}")

if __name__ == "__main__":
    show_banner_preview()
    apply_real_banners()