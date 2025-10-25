#!/usr/bin/env python3
"""
Get Real Seniors Banners - Extract actual banners from seniorskingston.ca/events
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re
import os

def get_real_seniors_banners():
    """Get the actual banners from the Seniors Kingston website"""
    try:
        print("🕷️ Getting real banners from seniorskingston.ca/events...")
        
        # Get the events page
        url = "https://seniorskingston.ca/events"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        print(f"🌐 Accessing: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print("✅ Successfully accessed the website")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Save the HTML for debugging
            with open('seniors_events_page.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("💾 Saved page HTML to seniors_events_page.html for debugging")
            
            # Look for all images on the page
            all_images = soup.find_all('img')
            print(f"🖼️ Found {len(all_images)} images on the page")
            
            # Extract image information
            event_images = []
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
                    
                    event_images.append({
                        'src': src,
                        'full_url': full_url,
                        'alt': alt,
                        'title': title,
                        'index': i
                    })
                    
                    print(f"   {i+1}. {alt or title or 'No description'}")
                    print(f"      URL: {full_url}")
            
            # Look for event containers with different selectors
            print("\n🔍 Looking for event containers...")
            
            # Try different selectors for event containers
            selectors = [
                'div[class*="event"]',
                'div[class*="card"]',
                'div[class*="post"]',
                'article',
                'div[class*="item"]',
                'div[class*="entry"]',
                'div[class*="content"]',
                'div[class*="box"]',
                'div[class*="container"]',
                'div[class*="wrapper"]',
                'div[class*="grid"]',
                'div[class*="list"]'
            ]
            
            events_found = []
            for selector in selectors:
                containers = soup.select(selector)
                if containers:
                    print(f"   Found {len(containers)} elements with selector: {selector}")
                    
                    for i, container in enumerate(containers[:5]):  # Check first 5
                        # Look for images in this container
                        images = container.find_all('img')
                        if images:
                            print(f"      Container {i+1} has {len(images)} images")
                            
                            # Look for text content that might be event titles
                            text_elements = container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div'])
                            text_content = []
                            for elem in text_elements:
                                text = elem.get_text(strip=True)
                                if text and len(text) > 5:
                                    text_content.append(text)
                            
                            if text_content:
                                print(f"         Text content: {text_content[:3]}")  # First 3 text elements
                
                # If we found containers, try to extract events
                if containers and not events_found:
                    for container in containers:
                        # Look for images and text together
                        img = container.find('img')
                        title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                        
                        if img and title_elem:
                            title = title_elem.get_text(strip=True)
                            img_src = img.get('src', '')
                            
                            if title and img_src:
                                # Convert relative URL to absolute
                                if img_src.startswith('/'):
                                    img_src = f"https://seniorskingston.ca{img_src}"
                                elif not img_src.startswith('http'):
                                    img_src = f"https://seniorskingston.ca/{img_src}"
                                
                                events_found.append({
                                    'title': title,
                                    'banner_url': img_src,
                                    'alt': img.get('alt', ''),
                                    'container_selector': selector
                                })
            
            print(f"\n📊 Found {len(events_found)} potential events with banners")
            
            # Save the found events
            if events_found:
                banner_data = {
                    "metadata": {
                        "scraped_at": datetime.now().isoformat(),
                        "source": "seniorskingston.ca/events",
                        "total_events": len(events_found),
                        "description": "Real event banners from Seniors Kingston website"
                    },
                    "events": events_found
                }
                
                with open('real_seniors_banners.json', 'w', encoding='utf-8') as f:
                    json.dump(banner_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Saved {len(events_found)} real banners to real_seniors_banners.json")
                
                # Show sample events
                print("\n📸 Sample real banners found:")
                for i, event in enumerate(events_found[:5]):
                    print(f"   {i+1}. {event['title']}")
                    print(f"      Banner: {event['banner_url']}")
                
                return events_found
            else:
                print("⚠️ No events with banners found")
                return []
                
        else:
            print(f"❌ Failed to access website: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error getting real banners: {e}")
        return []

def test_real_banner_urls(events):
    """Test if the real banner URLs are accessible"""
    try:
        print("\n🧪 Testing real banner URLs...")
        
        accessible_banners = []
        
        for i, event in enumerate(events[:10]):  # Test first 10
            title = event.get('title', 'No title')
            banner_url = event.get('banner_url', '')
            
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
        
        print(f"\n📊 Real banner accessibility results:")
        print(f"   ✅ Accessible: {len(accessible_banners)}")
        print(f"   ❌ Inaccessible: {len(events[:10]) - len(accessible_banners)}")
        
        return accessible_banners
        
    except Exception as e:
        print(f"❌ Error testing real banner URLs: {e}")
        return []

def main():
    """Main function to get real Seniors banners"""
    print("🕷️ Getting Real Seniors Kingston Banners")
    print("=" * 50)
    
    # Step 1: Get real banners from website
    print("\n🕷️ Step 1: Getting real banners from website...")
    events = get_real_seniors_banners()
    
    if not events:
        print("❌ No real banners found")
        return
    
    # Step 2: Test banner accessibility
    print("\n🧪 Step 2: Testing real banner accessibility...")
    accessible_events = test_real_banner_urls(events)
    
    print("\n🎉 Real banner extraction completed!")
    print(f"📊 Found {len(events)} events with real banners")
    print(f"✅ {len(accessible_events)} banners are accessible")
    print("📝 Next step: Update events with real banners")

if __name__ == "__main__":
    main()
