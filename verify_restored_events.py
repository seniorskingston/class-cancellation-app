#!/usr/bin/env python3
"""
Verify Restored Events - Check the restored events and their images
"""

import requests
import json

def verify_restored_events():
    """Verify the restored events and their images"""
    try:
        print("🔍 Verifying restored events...")
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
            
            # Check for unique images
            unique_images = set()
            for event in events_with_images:
                image_url = event.get('image_url', '')
                if image_url:
                    unique_images.add(image_url)
            
            print(f"🖼️ Unique image URLs: {len(unique_images)}")
            print("📸 Unique images:")
            for img_url in list(unique_images)[:10]:
                print(f"   - {img_url}")
            
            return True
            
        else:
            print(f"❌ Failed to get events: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying events: {e}")
        return False

if __name__ == "__main__":
    verify_restored_events()
