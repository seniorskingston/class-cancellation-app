#!/usr/bin/env python3
"""
Create Diverse Banners - Create more diverse banners for each event
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

def create_diverse_banners():
    """Create diverse banners for each event"""
    try:
        print("🎨 Creating diverse banners for each event...")
        
        # Load current events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events")
        
        # Create a much larger set of banner URLs for diversity
        banner_urls = {
            # Music banners
            'music1': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=600&h=200&fit=crop&crop=center',
            'music2': 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&h=200&fit=crop&crop=center',
            'music3': 'https://images.unsplash.com/photo-1571266028243-e68e85750bb2?w=600&h=200&fit=crop&crop=center',
            
            # Tech banners
            'tech1': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=600&h=200&fit=crop&crop=center',
            'tech2': 'https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=600&h=200&fit=crop&crop=center',
            'tech3': 'https://images.unsplash.com/photo-1551650975-87deedd944c3?w=600&h=200&fit=crop&crop=center',
            
            # Legal banners
            'legal1': 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&h=200&fit=crop&crop=center',
            'legal2': 'https://images.unsplash.com/photo-1589994965851-a8f479c573a9?w=600&h=200&fit=crop&crop=center',
            'legal3': 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=600&h=200&fit=crop&crop=center',
            
            # Food banners
            'food1': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&h=200&fit=crop&crop=center',
            'food2': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=600&h=200&fit=crop&crop=center',
            'food3': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=600&h=200&fit=crop&crop=center',
            'food4': 'https://images.unsplash.com/photo-1551782450-17144efb9c50?w=600&h=200&fit=crop&crop=center',
            
            # Dance banners
            'dance1': 'https://images.unsplash.com/photo-1504609813442-a8924e83f76e?w=600&h=200&fit=crop&crop=center',
            'dance2': 'https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=600&h=200&fit=crop&crop=center',
            'dance3': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&h=200&fit=crop&crop=center',
            
            # Education banners
            'education1': 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600&h=200&fit=crop&crop=center',
            'education2': 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=600&h=200&fit=crop&crop=center',
            'education3': 'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=600&h=200&fit=crop&crop=center',
            'education4': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=600&h=200&fit=crop&crop=center',
            'education5': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=200&fit=crop&crop=center',
            
            # Health banners
            'health1': 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=600&h=200&fit=crop&crop=center',
            'health2': 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?w=600&h=200&fit=crop&crop=center',
            'health3': 'https://images.unsplash.com/photo-1559757175-0eb30cd8c063?w=600&h=200&fit=crop&crop=center',
            
            # Art banners
            'art1': 'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=600&h=200&fit=crop&crop=center',
            'art2': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=600&h=200&fit=crop&crop=center',
            'art3': 'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=600&h=200&fit=crop&crop=center',
            
            # Social banners
            'social1': 'https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=600&h=200&fit=crop&crop=center',
            'social2': 'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=600&h=200&fit=crop&crop=center',
            'social3': 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600&h=200&fit=crop&crop=center',
            
            # Default banners
            'default1': 'https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=600&h=200&fit=crop&crop=center',
            'default2': 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600&h=200&fit=crop&crop=center',
            'default3': 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600&h=200&fit=crop&crop=center',
            'default4': 'https://images.unsplash.com/photo-1552664730-d307ca884978?w=600&h=200&fit=crop&crop=center',
            'default5': 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600&h=200&fit=crop&crop=center'
        }
        
        # Download all banners
        downloaded_banners = {}
        for category, url in banner_urls.items():
            filename = f"{category}_banner.jpg"
            local_path = download_banner_image(url, filename)
            if local_path:
                downloaded_banners[category] = local_path
        
        print(f"📥 Downloaded {len(downloaded_banners)} diverse banner images")
        
        # Assign banners to events with more variety
        banner_assignments = {}
        
        for i, event in enumerate(events):
            title = event.get('title', '').lower()
            description = event.get('description', '').lower()
            content = f"{title} {description}"
            
            # Determine category and specific banner
            if any(word in content for word in ['sound escapes', 'kenny', 'dolly', 'georgette fry', 'music', 'concert', 'tribute']):
                category = 'music'
                banner_options = ['music1', 'music2', 'music3']
            elif any(word in content for word in ['wearable tech', 'smartwatch', 'fitness tracker', 'technology', 'digital', 'online']):
                category = 'tech'
                banner_options = ['tech1', 'tech2', 'tech3']
            elif any(word in content for word in ['legal advice', 'lawyer', 'appointment']):
                category = 'legal'
                banner_options = ['legal1', 'legal2', 'legal3']
            elif any(word in content for word in ['fresh food market', 'food', 'lunch', 'tea', 'coffee']):
                category = 'food'
                banner_options = ['food1', 'food2', 'food3', 'food4']
            elif any(word in content for word in ['dance party', 'carole', 'dance']):
                category = 'dance'
                banner_options = ['dance1', 'dance2', 'dance3']
            elif any(word in content for word in ['astronomy', 'learn', 'workshop', 'planning', 'resilience', 'vision']):
                category = 'education'
                banner_options = ['education1', 'education2', 'education3', 'education4', 'education5']
            elif any(word in content for word in ['hearing clinic', 'health', 'medical', 'clinic']):
                category = 'health'
                banner_options = ['health1', 'health2', 'health3']
            elif any(word in content for word in ['art', 'artisan', 'expressive', 'mark making', 'cut fold glue']):
                category = 'art'
                banner_options = ['art1', 'art2', 'art3']
            elif any(word in content for word in ['mixer', 'friending', 'cafe', 'tuesday at tom']):
                category = 'social'
                banner_options = ['social1', 'social2', 'social3']
            else:
                category = 'default'
                banner_options = ['default1', 'default2', 'default3', 'default4', 'default5']
            
            # Choose a banner that hasn't been used much
            available_banners = [b for b in banner_options if b in downloaded_banners]
            if available_banners:
                # Use modulo to distribute banners evenly
                banner_choice = available_banners[i % len(available_banners)]
                event['image_url'] = downloaded_banners[banner_choice]
                banner_assignments[event.get('title', '')] = banner_choice
                print(f"   {event.get('title', '')[:40]}... -> {banner_choice}")
            else:
                # Fallback
                event['image_url'] = downloaded_banners.get('default1', '/logo192.png')
                print(f"   {event.get('title', '')[:40]}... -> default fallback")
        
        # Save updated events
        with open('bulletproof_events_backup.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated {len(events)} events with diverse banners")
        return True
        
    except Exception as e:
        print(f"❌ Error creating diverse banners: {e}")
        return False

def upload_diverse_banners():
    """Upload events with diverse banners"""
    try:
        print("\n☁️ Uploading events with diverse banners...")
        
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
                print(f"✅ Successfully uploaded events with diverse banners")
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

def verify_diverse_banners():
    """Verify that banners are diverse"""
    try:
        print("\n🔍 Verifying banner diversity...")
        
        response = requests.get("https://class-cancellation-backend.onrender.com/api/events", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            # Count unique banners
            unique_banners = set()
            banner_counts = {}
            
            for event in events:
                image_url = event.get('image_url', '')
                if image_url:
                    unique_banners.add(image_url)
                    banner_counts[image_url] = banner_counts.get(image_url, 0) + 1
            
            print(f"📊 Banner diversity results:")
            print(f"   🎨 Unique banners: {len(unique_banners)}")
            print(f"   📁 Total events: {len(events)}")
            
            print(f"\n📸 Banner distribution:")
            for banner, count in sorted(banner_counts.items()):
                print(f"   {banner}: {count} events")
            
            if len(unique_banners) > 20:
                print("🎉 EXCELLENT! Great banner diversity!")
                return True
            elif len(unique_banners) > 10:
                print("✅ GOOD! Good banner diversity!")
                return True
            else:
                print("⚠️ Limited banner diversity")
                return False
                
        else:
            print(f"❌ Failed to verify: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying banners: {e}")
        return False

def main():
    """Main function"""
    print("🎨 Create Diverse Event Banners")
    print("=" * 40)
    
    # Step 1: Create diverse banners
    print("\n🎨 Step 1: Creating diverse banners...")
    if not create_diverse_banners():
        print("❌ Failed to create diverse banners")
        return
    
    # Step 2: Upload diverse banners
    print("\n☁️ Step 2: Uploading diverse banners...")
    if not upload_diverse_banners():
        print("❌ Failed to upload diverse banners")
        return
    
    # Step 3: Verify diversity
    print("\n🔍 Step 3: Verifying banner diversity...")
    if verify_diverse_banners():
        print("✅ Banners are diverse!")
    else:
        print("⚠️ Banners may need more diversity")
    
    print("\n🎉 Diverse banner creation completed!")
    print("🖼️ Events now have much more diverse banners")
    print("📁 Banners saved in frontend/public/banners/")
    print("📝 Check your app - banners should now be much more diverse")

if __name__ == "__main__":
    main()
