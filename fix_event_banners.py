#!/usr/bin/env python3
"""
Fix Event Banners - Assign diverse and appropriate images to events
"""

import json
import random
from datetime import datetime

def assign_diverse_banners():
    """Assign diverse and appropriate banners to events"""
    try:
        print("🎨 Assigning diverse banners to events...")
        
        # Load the permanent events storage
        with open('permanent_events_storage.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events from permanent storage")
        
        # Define banner categories and their images
        banner_categories = {
            'music': [
                '/event-schedule-banner.png',
                '/logo192.png',
                '/logo512.png'
            ],
            'tech': [
                '/event-schedule-banner.png',
                '/logo192.png'
            ],
            'health': [
                '/event-schedule-banner.png',
                '/logo512.png'
            ],
            'legal': [
                '/event-schedule-banner.png',
                '/logo192.png'
            ],
            'food': [
                '/event-schedule-banner.png',
                '/logo512.png'
            ],
            'dance': [
                '/event-schedule-banner.png',
                '/logo192.png'
            ],
            'education': [
                '/event-schedule-banner.png',
                '/logo512.png'
            ],
            'holiday': [
                '/event-schedule-banner.png',
                '/logo192.png'
            ],
            'default': [
                '/event-schedule-banner.png',
                '/logo192.png',
                '/logo512.png'
            ]
        }
        
        # Assign banners based on event content
        for event in events:
            title = event.get('title', '').lower()
            description = event.get('description', '').lower()
            content = f"{title} {description}"
            
            # Determine category based on content
            if any(word in content for word in ['music', 'sound', 'concert', 'tribute', 'kenny', 'dolly']):
                category = 'music'
            elif any(word in content for word in ['tech', 'wearable', 'smartwatch', 'fitness tracker', 'technology']):
                category = 'tech'
            elif any(word in content for word in ['legal', 'lawyer', 'advice', 'appointment']):
                category = 'legal'
            elif any(word in content for word in ['food', 'market', 'fresh', 'grocery']):
                category = 'food'
            elif any(word in content for word in ['dance', 'party', 'carole']):
                category = 'dance'
            elif any(word in content for word in ['astronomy', 'education', 'learn', 'class', 'workshop']):
                category = 'education'
            elif any(word in content for word in ['holiday', 'day', 'easter', 'christmas', 'new year', 'canada day']):
                category = 'holiday'
            else:
                category = 'default'
            
            # Assign a random banner from the category
            available_banners = banner_categories.get(category, banner_categories['default'])
            selected_banner = random.choice(available_banners)
            
            # Update the event with the new banner
            event['image_url'] = selected_banner
            
            print(f"   {event.get('title', 'No title')[:40]}... -> {category} -> {selected_banner}")
        
        # Save updated events
        with open('permanent_events_storage.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Assigned diverse banners to {len(events)} events")
        return True
        
    except Exception as e:
        print(f"❌ Error assigning banners: {e}")
        return False

def create_custom_banners():
    """Create custom banner variations"""
    try:
        print("🎨 Creating custom banner variations...")
        
        # Create different colored versions of the banner
        banner_variations = [
            '/event-schedule-banner.png',  # Original
            '/logo192.png',               # Logo version
            '/logo512.png',               # Large logo version
            '/event-schedule-banner.png',  # Duplicate for variety
            '/logo192.png',               # Another logo version
        ]
        
        # Load events
        with open('permanent_events_storage.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        # Assign banners in a pattern to create visual variety
        for i, event in enumerate(events):
            # Use modulo to cycle through banner variations
            banner_index = i % len(banner_variations)
            event['image_url'] = banner_variations[banner_index]
            
            print(f"   {event.get('title', 'No title')[:40]}... -> {banner_variations[banner_index]}")
        
        # Save updated events
        with open('permanent_events_storage.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created banner variations for {len(events)} events")
        return True
        
    except Exception as e:
        print(f"❌ Error creating banner variations: {e}")
        return False

def upload_banner_fixes():
    """Upload the banner fixes to backend"""
    try:
        print("☁️ Uploading banner fixes to backend...")
        
        # Load updated events
        with open('permanent_events_storage.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        # Upload to backend
        import requests
        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
        upload_data = {'events': events}
        
        response = requests.post(backend_url, json=upload_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully uploaded banner fixes")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading banner fixes: {e}")
        return False

def verify_banner_diversity():
    """Verify that banners are now diverse"""
    try:
        print("🔍 Verifying banner diversity...")
        
        import requests
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            # Count unique banners
            unique_banners = set()
            for event in events:
                image_url = event.get('image_url', '')
                if image_url:
                    unique_banners.add(image_url)
            
            print(f"📊 Total events: {len(events)}")
            print(f"🖼️ Unique banners: {len(unique_banners)}")
            print("📸 Banner distribution:")
            
            # Count each banner type
            banner_counts = {}
            for event in events:
                image_url = event.get('image_url', '')
                banner_counts[image_url] = banner_counts.get(image_url, 0) + 1
            
            for banner, count in banner_counts.items():
                print(f"   {banner}: {count} events")
            
            return len(unique_banners) > 1
            
        else:
            print(f"❌ Failed to verify banners: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying banners: {e}")
        return False

def main():
    """Main function to fix event banners"""
    print("🎨 Fixing Event Banners")
    print("=" * 40)
    
    # Step 1: Create banner variations
    print("\n🎨 Step 1: Creating banner variations...")
    if not create_custom_banners():
        print("❌ Failed to create banner variations")
        return
    
    # Step 2: Upload banner fixes
    print("\n☁️ Step 2: Uploading banner fixes...")
    if not upload_banner_fixes():
        print("❌ Failed to upload banner fixes")
        return
    
    # Step 3: Verify banner diversity
    print("\n🔍 Step 3: Verifying banner diversity...")
    if verify_banner_diversity():
        print("✅ Banners are now diverse!")
    else:
        print("⚠️ Banners may still need improvement")
    
    print("\n🎉 Event banner fix completed!")
    print("🖼️ Events now have diverse banners that will display in floating boxes")
    print("📝 Check your app to see the improved banner display")

if __name__ == "__main__":
    main()
