#!/usr/bin/env python3
"""
Download Real Banners - Download actual banner images from seniorskingston.ca
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os
import re
from urllib.parse import urljoin, urlparse

def download_banner_image(url, filename):
    """Download a banner image"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
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

def scrape_and_download_banners():
    """Scrape and download real banners from seniorskingston.ca"""
    try:
        print("🕷️ Scraping and downloading real banners...")
        
        # Get the events page
        url = "https://seniorskingston.ca/events"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save the HTML for debugging
            with open('seniors_events_page_debug.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            print("💾 Saved page HTML for debugging")
            
            # Look for all images on the page
            all_images = soup.find_all('img')
            print(f"🖼️ Found {len(all_images)} images on the page")
            
            # Extract and download banner images
            downloaded_banners = []
            
            for i, img in enumerate(all_images):
                src = img.get('src', '')
                alt = img.get('alt', '')
                title = img.get('title', '')
                
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('/'):
                        full_url = f"https://seniorskingston.ca{src}"
                    elif src.startswith('http'):
                        full_url = src
                    else:
                        full_url = f"https://seniorskingston.ca/{src}"
                    
                    # Skip small images (likely icons)
                    if 'logo' in src.lower() or 'icon' in src.lower():
                        continue
                    
                    # Create filename
                    parsed_url = urlparse(full_url)
                    filename = os.path.basename(parsed_url.path)
                    
                    # If no filename, create one
                    if not filename or '.' not in filename:
                        filename = f"banner_{i+1}.jpg"
                    
                    # Ensure it has an extension
                    if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        filename += '.jpg'
                    
                    print(f"📥 Downloading {i+1}. {alt or title or 'No description'}")
                    print(f"   URL: {full_url}")
                    
                    # Download the image
                    local_path = download_banner_image(full_url, filename)
                    
                    if local_path:
                        downloaded_banners.append({
                            'original_url': full_url,
                            'local_path': local_path,
                            'filename': filename,
                            'alt': alt,
                            'title': title
                        })
            
            print(f"\n📊 Downloaded {len(downloaded_banners)} banner images")
            
            # Save the banner mapping
            banner_data = {
                "metadata": {
                    "downloaded_at": datetime.now().isoformat(),
                    "source": "seniorskingston.ca/events",
                    "total_banners": len(downloaded_banners),
                    "description": "Downloaded banner images from Seniors Kingston website"
                },
                "banners": downloaded_banners
            }
            
            with open('downloaded_banners.json', 'w', encoding='utf-8') as f:
                json.dump(banner_data, f, indent=2, ensure_ascii=False)
            
            print("✅ Saved banner mapping to downloaded_banners.json")
            return downloaded_banners
            
        else:
            print(f"❌ Failed to access website: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error scraping and downloading banners: {e}")
        return []

def match_banners_to_events(downloaded_banners):
    """Match downloaded banners to events"""
    try:
        print("\n🔗 Matching banners to events...")
        
        # Load current events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events")
        
        # Create a mapping of events to banners
        event_banner_mapping = {}
        
        for event in events:
            title = event.get('title', '').lower()
            
            # Try to find a matching banner based on title keywords
            best_match = None
            best_score = 0
            
            for banner in downloaded_banners:
                banner_text = f"{banner.get('alt', '')} {banner.get('title', '')}".lower()
                
                # Calculate match score
                score = 0
                title_words = title.split()
                
                for word in title_words:
                    if len(word) > 3 and word in banner_text:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = banner
            
            if best_match:
                event_banner_mapping[event.get('title', '')] = best_match['local_path']
                print(f"   ✅ {event.get('title', '')[:40]}... -> {best_match['filename']}")
            else:
                # Use a default banner if no match found
                if downloaded_banners:
                    event_banner_mapping[event.get('title', '')] = downloaded_banners[0]['local_path']
                    print(f"   ⚠️ {event.get('title', '')[:40]}... -> Default banner")
        
        # Update events with banner paths
        for event in events:
            title = event.get('title', '')
            if title in event_banner_mapping:
                event['image_url'] = event_banner_mapping[title]
        
        # Save updated events
        with open('bulletproof_events_backup.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated {len(events)} events with downloaded banners")
        return True
        
    except Exception as e:
        print(f"❌ Error matching banners to events: {e}")
        return False

def upload_events_with_downloaded_banners():
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

def main():
    """Main function"""
    print("🕷️ Download Real Event Banners")
    print("=" * 40)
    
    # Step 1: Scrape and download banners
    print("\n🕷️ Step 1: Scraping and downloading banners...")
    downloaded_banners = scrape_and_download_banners()
    
    if not downloaded_banners:
        print("❌ No banners downloaded")
        return
    
    # Step 2: Match banners to events
    print("\n🔗 Step 2: Matching banners to events...")
    if not match_banners_to_events(downloaded_banners):
        print("❌ Failed to match banners to events")
        return
    
    # Step 3: Upload events with banners
    print("\n☁️ Step 3: Uploading events with downloaded banners...")
    if not upload_events_with_downloaded_banners():
        print("❌ Failed to upload events")
        return
    
    print("\n🎉 Real banner download completed!")
    print("🖼️ Events now have downloaded banner images")
    print("📁 Banners saved in frontend/public/banners/")
    print("📝 Check your app - banners should now display properly")

if __name__ == "__main__":
    main()
