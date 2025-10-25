#!/usr/bin/env python3
"""
Advanced Seniors Events Scraper - Try different methods to get event banners
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re

def scrape_with_different_selectors():
    """Try different selectors to find events"""
    try:
        print("🕷️ Trying different selectors to find events...")
        
        url = "https://seniorskingston.ca/events"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different selectors
            selectors_to_try = [
                'div[class*="event"]',
                'div[class*="card"]',
                'div[class*="post"]',
                'article',
                'div[class*="item"]',
                'div[class*="entry"]',
                'div[class*="content"]',
                'div[class*="box"]',
                'div[class*="container"]',
                'div[class*="wrapper"]'
            ]
            
            events = []
            
            for selector in selectors_to_try:
                print(f"Trying selector: {selector}")
                containers = soup.select(selector)
                print(f"   Found {len(containers)} elements")
                
                for i, container in enumerate(containers[:5]):  # Check first 5
                    # Look for images in this container
                    images = container.find_all('img')
                    if images:
                        print(f"   Container {i+1} has {len(images)} images")
                        for img in images:
                            src = img.get('src', '')
                            alt = img.get('alt', '')
                            print(f"      Image: {src} (alt: {alt})")
            
            # Try to find all images on the page
            print("\n🖼️ All images on the page:")
            all_images = soup.find_all('img')
            for i, img in enumerate(all_images[:20]):  # First 20 images
                src = img.get('src', '')
                alt = img.get('alt', '')
                if src:
                    print(f"   {i+1}. {src} (alt: {alt})")
            
            return True
            
        else:
            print(f"❌ Failed to access website: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error scraping with different selectors: {e}")
        return False

def create_placeholder_banners():
    """Create placeholder banners based on event types"""
    try:
        print("\n🎨 Creating placeholder banners based on event types...")
        
        # Load current events
        with open('permanent_events_storage.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        # Create banner mapping based on event content
        banner_mapping = {
            'music': 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=200&fit=crop',
            'tech': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=200&fit=crop',
            'legal': 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=400&h=200&fit=crop',
            'food': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=200&fit=crop',
            'dance': 'https://images.unsplash.com/photo-1504609813442-a8924e83f76e?w=400&h=200&fit=crop',
            'education': 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=400&h=200&fit=crop',
            'health': 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400&h=200&fit=crop',
            'default': 'https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=400&h=200&fit=crop'
        }
        
        # Assign banners based on event content
        for event in events:
            title = event.get('title', '').lower()
            description = event.get('description', '').lower()
            content = f"{title} {description}"
            
            # Determine category
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
            elif any(word in content for word in ['health', 'hearing', 'clinic', 'medical']):
                category = 'health'
            else:
                category = 'default'
            
            # Assign banner
            event['image_url'] = banner_mapping[category]
            print(f"   {event.get('title', 'No title')[:40]}... -> {category}")
        
        # Save updated events
        with open('permanent_events_storage.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Assigned placeholder banners to {len(events)} events")
        return True
        
    except Exception as e:
        print(f"❌ Error creating placeholder banners: {e}")
        return False

def upload_placeholder_banners():
    """Upload events with placeholder banners"""
    try:
        print("\n☁️ Uploading events with placeholder banners...")
        
        # Load updated events
        with open('permanent_events_storage.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        # Upload to backend
        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
        upload_data = {'events': events}
        
        response = requests.post(backend_url, json=upload_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully uploaded events with placeholder banners")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading placeholder banners: {e}")
        return False

def main():
    """Main function"""
    print("🕷️ Advanced Seniors Events Scraper")
    print("=" * 40)
    
    # Step 1: Try different selectors
    print("\n🕷️ Step 1: Analyzing website structure...")
    scrape_with_different_selectors()
    
    # Step 2: Create placeholder banners
    print("\n🎨 Step 2: Creating placeholder banners...")
    if create_placeholder_banners():
        print("✅ Placeholder banners created")
    else:
        print("❌ Failed to create placeholder banners")
        return
    
    # Step 3: Upload placeholder banners
    print("\n☁️ Step 3: Uploading placeholder banners...")
    if upload_placeholder_banners():
        print("✅ Placeholder banners uploaded")
    else:
        print("❌ Failed to upload placeholder banners")
        return
    
    print("\n🎉 Placeholder banner system completed!")
    print("🖼️ Events now have appropriate placeholder banners")
    print("📝 Check your app to see the improved banners")

if __name__ == "__main__":
    main()
