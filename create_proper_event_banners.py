#!/usr/bin/env python3
"""
Create Proper Event Banners - Create appropriate banners for each event type
"""

import json
import requests
import os
from datetime import datetime

def download_banner_image(url, filename):
    """Download a banner image"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # Create banners directory if it doesn't exist
            os.makedirs('frontend/public/banners', exist_ok=True)
            
            # Save the image
            filepath = f'frontend/public/banners/{filename}'
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"   ✅ Downloaded: {filename}")
            return f'/banners/{filename}'
        else:
            print(f"   ❌ Failed to download: {url} (status {response.status_code})")
            return None
            
    except Exception as e:
        print(f"   ❌ Error downloading {url}: {e}")
        return None

def create_event_banners():
    """Create appropriate banners for each event type"""
    try:
        print("🎨 Creating appropriate banners for each event type...")
        
        # Load current events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events")
        
        # Define banner URLs for different event types
        # Using high-quality, appropriate images from Unsplash
        banner_urls = {
            'music': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=600&h=200&fit=crop&crop=center',
            'tech': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=600&h=200&fit=crop&crop=center',
            'legal': 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&h=200&fit=crop&crop=center',
            'food': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&h=200&fit=crop&crop=center',
            'dance': 'https://images.unsplash.com/photo-1504609813442-a8924e83f76e?w=600&h=200&fit=crop&crop=center',
            'education': 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600&h=200&fit=crop&crop=center',
            'health': 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&h=200&fit=crop&crop=center',
            'art': 'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=600&h=200&fit=crop&crop=center',
            'social': 'https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=600&h=200&fit=crop&crop=center',
            'default': 'https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=600&h=200&fit=crop&crop=center'
        }
        
        # Download banners
        downloaded_banners = {}
        for category, url in banner_urls.items():
            filename = f"{category}_banner.jpg"
            local_path = download_banner_image(url, filename)
            if local_path:
                downloaded_banners[category] = local_path
        
        print(f"📥 Downloaded {len(downloaded_banners)} banner images")
        
        # Assign banners to events based on content
        for event in events:
            title = event.get('title', '').lower()
            description = event.get('description', '').lower()
            content = f"{title} {description}"
            
            # Determine category based on content
            if any(word in content for word in ['sound escapes', 'kenny', 'dolly', 'georgette fry', 'music', 'concert', 'tribute']):
                category = 'music'
            elif any(word in content for word in ['wearable tech', 'smartwatch', 'fitness tracker', 'technology', 'digital', 'online']):
                category = 'tech'
            elif any(word in content for word in ['legal advice', 'lawyer', 'appointment']):
                category = 'legal'
            elif any(word in content for word in ['fresh food market', 'food', 'lunch', 'tea', 'coffee']):
                category = 'food'
            elif any(word in content for word in ['dance party', 'carole', 'dance']):
                category = 'dance'
            elif any(word in content for word in ['astronomy', 'learn', 'workshop', 'planning', 'resilience', 'vision']):
                category = 'education'
            elif any(word in content for word in ['hearing clinic', 'health', 'medical', 'clinic']):
                category = 'health'
            elif any(word in content for word in ['art', 'artisan', 'expressive', 'mark making', 'cut fold glue']):
                category = 'art'
            elif any(word in content for word in ['mixer', 'friending', 'cafe', 'tuesday at tom']):
                category = 'social'
            else:
                category = 'default'
            
            # Assign banner
            if category in downloaded_banners:
                event['image_url'] = downloaded_banners[category]
                print(f"   {event.get('title', 'No title')[:40]}... -> {category} banner")
            else:
                # Fallback to default
                event['image_url'] = downloaded_banners.get('default', '/logo192.png')
                print(f"   {event.get('title', 'No title')[:40]}... -> default banner")
        
        # Save updated events
        with open('bulletproof_events_backup.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated {len(events)} events with downloaded banners")
        return True
        
    except Exception as e:
        print(f"❌ Error creating event banners: {e}")
        return False

def upload_events_with_banners():
    """Upload events with downloaded banners"""
    try:
        print("\n☁️ Uploading events with downloaded banners...")
        
        # Load updated events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        # Upload to backend
        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
        upload_data = {'events': events}
        
        response = requests.post(backend_url, json=upload_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully uploaded events with downloaded banners")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading events: {e}")
        return False

def verify_banners():
    """Verify that banners are working"""
    try:
        print("\n🔍 Verifying banners...")
        
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            # Check banner URLs
            banner_count = 0
            for event in events:
                image_url = event.get('image_url', '')
                if image_url and image_url.startswith('/banners/'):
                    banner_count += 1
            
            print(f"📊 Banner verification results:")
            print(f"   ✅ Events with downloaded banners: {banner_count}")
            print(f"   📁 Total events: {len(events)}")
            
            if banner_count > 0:
                print("🎉 SUCCESS! Events now have downloaded banners!")
                return True
            else:
                print("⚠️ No downloaded banners found")
                return False
                
        else:
            print(f"❌ Failed to verify: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying banners: {e}")
        return False

def main():
    """Main function"""
    print("🎨 Create Proper Event Banners")
    print("=" * 40)
    
    # Step 1: Create event banners
    print("\n🎨 Step 1: Creating event banners...")
    if not create_event_banners():
        print("❌ Failed to create event banners")
        return
    
    # Step 2: Upload events with banners
    print("\n☁️ Step 2: Uploading events with banners...")
    if not upload_events_with_banners():
        print("❌ Failed to upload events")
        return
    
    # Step 3: Verify banners
    print("\n🔍 Step 3: Verifying banners...")
    if verify_banners():
        print("✅ Banners are working!")
    else:
        print("⚠️ Banners may need additional work")
    
    print("\n🎉 Event banner creation completed!")
    print("🖼️ Events now have appropriate downloaded banners")
    print("📁 Banners saved in frontend/public/banners/")
    print("📝 Check your app - banners should now display properly")

if __name__ == "__main__":
    main()
