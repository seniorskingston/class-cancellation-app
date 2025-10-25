#!/usr/bin/env python3
"""
Check and Fix Banners - Check current banners and fix them
"""

import requests
import json

def check_current_banners():
    """Check what banners are currently being used"""
    try:
        print("🔍 Checking current banners...")
        
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            print(f"📊 Total events: {len(events)}")
            print("\n📸 Current banner URLs:")
            
            for i, event in enumerate(events[:10]):  # Show first 10
                title = event.get('title', 'No title')
                image_url = event.get('image_url', 'No image')
                print(f"   {i+1}. {title[:40]}...")
                print(f"      Banner: {image_url}")
            
            return events
        else:
            print(f"❌ Failed to get events: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error checking banners: {e}")
        return []

def fix_banners_to_logo():
    """Fix all banners to use the Seniors Kingston logo"""
    try:
        print("\n🔄 Fixing banners to use Seniors Kingston logo...")
        
        # Load events from backup
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events from backup")
        
        # Update all events to use the Seniors Kingston logo
        for event in events:
            event['image_url'] = "/logo192.png"  # Seniors Kingston logo
            print(f"   {event.get('title', 'No title')[:40]}... -> Seniors Kingston logo")
        
        # Save updated events
        with open('bulletproof_events_backup.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated {len(events)} events with Seniors Kingston logo")
        
        # Upload to backend
        print("\n☁️ Uploading fixed banners to backend...")
        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
        upload_data = {'events': events}
        
        response = requests.post(backend_url, json=upload_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully uploaded fixed banners")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing banners: {e}")
        return False

def verify_banner_fix():
    """Verify that banners are now fixed"""
    try:
        print("\n🔍 Verifying banner fix...")
        
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            # Check banner URLs
            logo_count = 0
            random_count = 0
            
            for event in events:
                image_url = event.get('image_url', '')
                if '/logo192.png' in image_url:
                    logo_count += 1
                elif 'unsplash.com' in image_url or 'images.unsplash.com' in image_url:
                    random_count += 1
            
            print(f"📊 Banner verification results:")
            print(f"   ✅ Seniors Kingston logo: {logo_count} events")
            print(f"   ❌ Random pictures: {random_count} events")
            
            if random_count == 0:
                print("🎉 SUCCESS! All banners are now using the Seniors Kingston logo!")
                return True
            else:
                print("⚠️ Some events still have random pictures")
                return False
                
        else:
            print(f"❌ Failed to verify: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying banners: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Check and Fix Banners")
    print("=" * 30)
    
    # Step 1: Check current banners
    print("\n🔍 Step 1: Checking current banners...")
    events = check_current_banners()
    
    if not events:
        print("❌ No events found")
        return
    
    # Step 2: Fix banners
    print("\n🔄 Step 2: Fixing banners...")
    if not fix_banners_to_logo():
        print("❌ Failed to fix banners")
        return
    
    # Step 3: Verify fix
    print("\n🔍 Step 3: Verifying banner fix...")
    if verify_banner_fix():
        print("✅ Banners are now fixed!")
    else:
        print("⚠️ Banners may need additional fixing")
    
    print("\n🎉 Banner fix completed!")
    print("📝 Check your app - banners should now show the Seniors Kingston logo")

if __name__ == "__main__":
    main()
