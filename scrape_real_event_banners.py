#!/usr/bin/env python3
"""
Scrape Real Event Banners - Get actual event banners from seniorskingston.ca/events
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re

def scrape_event_banners():
    """Scrape actual event banners from the Seniors Kingston website"""
    try:
        print("🕷️ Scraping real event banners from seniorskingston.ca/events...")
        
        # Get the events page
        url = "https://seniorskingston.ca/events"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all event containers
            events = []
            
            # Look for different possible event container patterns
            event_containers = soup.find_all(['div', 'article'], class_=re.compile(r'event|card|item', re.I))
            
            if not event_containers:
                # Try alternative selectors
                event_containers = soup.find_all('div', class_=re.compile(r'post|entry|content', re.I))
            
            print(f"📊 Found {len(event_containers)} potential event containers")
            
            for i, container in enumerate(event_containers):
                try:
                    # Extract event information
                    event_data = {}
                    
                    # Get title
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|heading', re.I))
                    if not title_elem:
                        title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                    
                    if title_elem:
                        event_data['title'] = title_elem.get_text(strip=True)
                    
                    # Get banner image
                    img_elem = container.find('img')
                    if img_elem:
                        img_src = img_elem.get('src', '')
                        if img_src:
                            # Convert relative URLs to absolute
                            if img_src.startswith('/'):
                                img_src = f"https://seniorskingston.ca{img_src}"
                            elif not img_src.startswith('http'):
                                img_src = f"https://seniorskingston.ca/{img_src}"
                            
                            event_data['banner_url'] = img_src
                            event_data['alt_text'] = img_elem.get('alt', '')
                    
                    # Get description
                    desc_elem = container.find(['p', 'div'], class_=re.compile(r'desc|content|text', re.I))
                    if not desc_elem:
                        desc_elem = container.find('p')
                    
                    if desc_elem:
                        event_data['description'] = desc_elem.get_text(strip=True)
                    
                    # Only add if we have at least a title
                    if event_data.get('title'):
                        events.append(event_data)
                        print(f"   {i+1}. {event_data.get('title', 'No title')[:50]}...")
                        if event_data.get('banner_url'):
                            print(f"      Banner: {event_data['banner_url']}")
                
                except Exception as e:
                    print(f"   Error processing container {i+1}: {e}")
                    continue
            
            print(f"\n📊 Successfully scraped {len(events)} events with banners")
            return events
            
        else:
            print(f"❌ Failed to access website: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error scraping event banners: {e}")
        return []

def test_banner_urls(events):
    """Test if the scraped banner URLs are accessible"""
    try:
        print("\n🧪 Testing scraped banner URLs...")
        
        accessible_banners = []
        
        for i, event in enumerate(events[:10]):  # Test first 10
            banner_url = event.get('banner_url', '')
            title = event.get('title', 'No title')
            
            if banner_url:
                print(f"Testing {i+1}. {title[:40]}...")
                
                try:
                    response = requests.head(banner_url, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"   ✅ Accessible: {banner_url}")
                        accessible_banners.append(event)
                    else:
                        print(f"   ❌ Not accessible (status {response.status_code}): {banner_url}")
                        
                except Exception as e:
                    print(f"   ❌ Error testing: {e}")
            else:
                print(f"   ⚠️ No banner URL for: {title}")
        
        print(f"\n📊 Banner accessibility results:")
        print(f"   ✅ Accessible banners: {len(accessible_banners)}")
        print(f"   ❌ Inaccessible banners: {len(events[:10]) - len(accessible_banners)}")
        
        return accessible_banners
        
    except Exception as e:
        print(f"❌ Error testing banner URLs: {e}")
        return []

def save_scraped_banners(events):
    """Save scraped banners to a file"""
    try:
        print("\n💾 Saving scraped banners...")
        
        banner_data = {
            "metadata": {
                "scraped_at": datetime.now().isoformat(),
                "source": "seniorskingston.ca/events",
                "total_events": len(events),
                "description": "Real event banners scraped from Seniors Kingston website"
            },
            "events": events
        }
        
        with open('scraped_event_banners.json', 'w', encoding='utf-8') as f:
            json.dump(banner_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(events)} scraped banners to scraped_event_banners.json")
        return True
        
    except Exception as e:
        print(f"❌ Error saving scraped banners: {e}")
        return False

def main():
    """Main function to scrape real event banners"""
    print("🕷️ Scraping Real Event Banners from Seniors Kingston")
    print("=" * 60)
    
    # Step 1: Scrape event banners
    print("\n🕷️ Step 1: Scraping event banners from website...")
    events = scrape_event_banners()
    
    if not events:
        print("❌ No events found - website structure may have changed")
        return
    
    # Step 2: Test banner URLs
    print("\n🧪 Step 2: Testing banner accessibility...")
    accessible_events = test_banner_urls(events)
    
    # Step 3: Save scraped data
    print("\n💾 Step 3: Saving scraped banners...")
    if save_scraped_banners(events):
        print("✅ Scraped banners saved successfully")
    else:
        print("❌ Failed to save scraped banners")
    
    print("\n🎉 Banner scraping completed!")
    print(f"📊 Found {len(events)} events with banners")
    print(f"✅ {len(accessible_events)} banners are accessible")
    print("📝 Next step: Update events with real banners")

if __name__ == "__main__":
    main()
