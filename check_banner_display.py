#!/usr/bin/env python3
"""
Check Banner Display - Check if event banners are properly configured
"""

import requests
import json
from datetime import datetime

def check_event_images():
    """Check current event images in backend"""
    try:
        print("🖼️ Checking event images in backend...")
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"📊 Total events: {len(events)}")
            
            # Check events with images
            events_with_images = [e for e in events if e.get('image_url')]
            print(f"🖼️ Events with images: {len(events_with_images)}")
            
            # Show sample image URLs
            print("\n📸 Sample image URLs:")
            for i, event in enumerate(events_with_images[:10]):
                title = event.get('title', 'No title')
                image_url = event.get('image_url', 'No image')
                print(f"   {i+1}. {title[:50]}...")
                print(f"      Image: {image_url}")
                print()
            
            # Check for common image issues
            print("🔍 Checking for image issues...")
            
            # Check for missing images
            events_without_images = [e for e in events if not e.get('image_url')]
            if events_without_images:
                print(f"⚠️ Events without images: {len(events_without_images)}")
                print("   Sample events without images:")
                for i, event in enumerate(events_without_images[:5]):
                    print(f"   - {event.get('title', 'No title')}")
            
            # Check for invalid image URLs
            invalid_urls = []
            for event in events_with_images:
                image_url = event.get('image_url', '')
                if not image_url.startswith('http') and not image_url.startswith('/'):
                    invalid_urls.append(event)
            
            if invalid_urls:
                print(f"⚠️ Events with invalid image URLs: {len(invalid_urls)}")
                for event in invalid_urls[:3]:
                    print(f"   - {event.get('title', 'No title')}: {event.get('image_url', 'No image')}")
            
            return events_with_images, events_without_images
            
        else:
            print(f"❌ Failed to get events: {response.status_code}")
            return [], []
            
    except Exception as e:
        print(f"❌ Error checking event images: {e}")
        return [], []

def test_image_urls(events_with_images):
    """Test if image URLs are accessible"""
    try:
        print("\n🧪 Testing image URL accessibility...")
        
        accessible_count = 0
        inaccessible_count = 0
        
        for i, event in enumerate(events_with_images[:5]):  # Test first 5 images
            image_url = event.get('image_url', '')
            title = event.get('title', 'No title')
            
            print(f"Testing {i+1}. {title[:30]}...")
            
            try:
                # Test the image URL
                if image_url.startswith('http'):
                    test_url = image_url
                else:
                    test_url = f"https://class-cancellation-frontend.onrender.com{image_url}"
                
                response = requests.head(test_url, timeout=10)
                
                if response.status_code == 200:
                    print(f"   ✅ Accessible: {test_url}")
                    accessible_count += 1
                else:
                    print(f"   ❌ Not accessible (status {response.status_code}): {test_url}")
                    inaccessible_count += 1
                    
            except Exception as e:
                print(f"   ❌ Error testing: {e}")
                inaccessible_count += 1
        
        print(f"\n📊 Image accessibility test results:")
        print(f"   ✅ Accessible: {accessible_count}")
        print(f"   ❌ Inaccessible: {inaccessible_count}")
        
        return accessible_count, inaccessible_count
        
    except Exception as e:
        print(f"❌ Error testing image URLs: {e}")
        return 0, 0

def fix_image_urls():
    """Fix image URLs if needed"""
    try:
        print("\n🔧 Checking if image URLs need fixing...")
        
        # Load the permanent events storage
        with open('permanent_events_storage.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events from permanent storage")
        
        # Check current image URLs
        events_with_images = [e for e in events if e.get('image_url')]
        print(f"🖼️ Events with images: {len(events_with_images)}")
        
        # Check if images need fixing
        needs_fixing = False
        for event in events_with_images:
            image_url = event.get('image_url', '')
            if not image_url.startswith('http') and not image_url.startswith('/'):
                needs_fixing = True
                break
        
        if needs_fixing:
            print("⚠️ Some image URLs need fixing...")
            
            # Fix image URLs
            for event in events:
                if event.get('image_url'):
                    image_url = event['image_url']
                    if not image_url.startswith('http') and not image_url.startswith('/'):
                        # Fix the URL
                        event['image_url'] = f"/assets/{image_url}"
                        print(f"   Fixed: {event.get('title', 'No title')} -> {event['image_url']}")
            
            # Save fixed events
            with open('permanent_events_storage.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("✅ Fixed image URLs in permanent storage")
            
            # Upload fixed events
            print("☁️ Uploading fixed events to backend...")
            backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
            upload_data = {'events': events}
            
            response = requests.post(backend_url, json=upload_data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Successfully uploaded fixed events")
                    return True
                else:
                    print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Upload failed with status code: {response.status_code}")
                return False
        else:
            print("✅ Image URLs look good - no fixing needed")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing image URLs: {e}")
        return False

def main():
    """Main function to check and fix banner display"""
    print("🖼️ Checking Event Banner Display")
    print("=" * 50)
    
    # Step 1: Check current event images
    print("\n📊 Step 1: Checking current event images...")
    events_with_images, events_without_images = check_event_images()
    
    # Step 2: Test image accessibility
    if events_with_images:
        print("\n🧪 Step 2: Testing image accessibility...")
        accessible_count, inaccessible_count = test_image_urls(events_with_images)
    
    # Step 3: Fix image URLs if needed
    print("\n🔧 Step 3: Checking if fixes are needed...")
    if fix_image_urls():
        print("✅ Image URLs are properly configured")
    else:
        print("❌ Failed to fix image URLs")
    
    print("\n🎉 Banner display check completed!")
    print("🖼️ Event banners should now display properly in floating boxes")
    print("📝 Check your app to see if banners are showing correctly")

if __name__ == "__main__":
    main()
