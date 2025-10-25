#!/usr/bin/env python3
"""
Get Seniors Banners with Selenium - Wait for JavaScript to load
"""

import json
import time
from datetime import datetime
import os

def get_seniors_banners_with_selenium():
    """Get banners using Selenium to wait for JavaScript"""
    try:
        print("🕷️ Getting Seniors banners with Selenium...")
        
        # Check if selenium is available
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
        except ImportError:
            print("❌ Selenium not installed. Installing...")
            os.system("pip install selenium")
            print("✅ Selenium installed. Please run the script again.")
            return []
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Create driver
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"❌ Chrome driver not found: {e}")
            print("💡 Please install ChromeDriver or use a different approach")
            return []
        
        try:
            # Navigate to the page
            url = "https://seniorskingston.ca/events"
            print(f"🌐 Navigating to: {url}")
            driver.get(url)
            
            # Wait for the page to load
            print("⏳ Waiting for page to load...")
            time.sleep(10)  # Wait 10 seconds for JavaScript to load
            
            # Try to find event elements
            print("🔍 Looking for event elements...")
            
            # Wait for any content to load
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                print("⚠️ Timeout waiting for page to load")
            
            # Get page source after JavaScript execution
            page_source = driver.page_source
            
            # Save the rendered HTML
            with open('seniors_events_rendered.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("💾 Saved rendered HTML to seniors_events_rendered.html")
            
            # Look for images in the rendered HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all images
            images = soup.find_all('img')
            print(f"🖼️ Found {len(images)} images in rendered HTML")
            
            # Extract image information
            event_images = []
            for i, img in enumerate(images):
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
            
            # Look for event containers
            print("\n🔍 Looking for event containers...")
            
            # Try different selectors
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
                            
                            # Look for text content
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
                        "source": "seniorskingston.ca/events (with Selenium)",
                        "total_events": len(events_found),
                        "description": "Real event banners from Seniors Kingston website (JavaScript rendered)"
                    },
                    "events": events_found
                }
                
                with open('real_seniors_banners_selenium.json', 'w', encoding='utf-8') as f:
                    json.dump(banner_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Saved {len(events_found)} real banners to real_seniors_banners_selenium.json")
                
                # Show sample events
                print("\n📸 Sample real banners found:")
                for i, event in enumerate(events_found[:5]):
                    print(f"   {i+1}. {event['title']}")
                    print(f"      Banner: {event['banner_url']}")
                
                return events_found
            else:
                print("⚠️ No events with banners found")
                return []
                
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"❌ Error getting banners with Selenium: {e}")
        return []

def create_manual_banner_system():
    """Create a manual system for adding real banners"""
    try:
        print("\n📝 Creating manual banner system...")
        
        manual_guide = """# Manual Banner System for Seniors Kingston Events

## Current Status
The Seniors Kingston website uses JavaScript to load content dynamically, making it difficult to scrape automatically.

## Manual Process to Get Real Banners

### Step 1: Visit the Website
1. Go to https://seniorskingston.ca/events
2. Wait for the page to fully load
3. You should see event boxes with banners at the top

### Step 2: Get Banner URLs
For each event:
1. Right-click on the event banner image
2. Select "Copy image address" or "Copy image URL"
3. Note the event title

### Step 3: Update the System
1. Open the file `manual_banner_mapping.json`
2. Add the event title and banner URL
3. Run `python apply_manual_banners.py`

## Example Format
```json
{
  "Sound Escapes: Kenny & Dolly": "https://seniorskingston.ca/images/kenny-dolly-banner.jpg",
  "Wearable Tech": "https://seniorskingston.ca/images/tech-banner.jpg",
  "Legal Advice": "https://seniorskingston.ca/images/legal-banner.jpg"
}
```

## Alternative: Use Placeholder Banners
If you can't get the real banners, the current system uses appropriate placeholder banners based on event types:
- Music events: Music-themed images
- Tech events: Technology-themed images
- Legal events: Legal-themed images
- Food events: Food-themed images
- etc.

These placeholders are professional and appropriate for each event type.
"""
        
        with open('MANUAL_BANNER_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(manual_guide)
        
        print("✅ Created MANUAL_BANNER_GUIDE.md")
        
        # Create manual banner mapping file
        manual_mapping = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "Manual mapping of event titles to real banner URLs",
                "instructions": "Add event titles and their corresponding banner URLs from seniorskingston.ca/events"
            },
            "banner_mapping": {
                # Example entries - replace with real URLs
                "Sound Escapes: Kenny & Dolly": "https://seniorskingston.ca/images/kenny-dolly-banner.jpg",
                "Wearable Tech": "https://seniorskingston.ca/images/tech-banner.jpg",
                "Legal Advice": "https://seniorskingston.ca/images/legal-banner.jpg"
            }
        }
        
        with open('manual_banner_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(manual_mapping, f, indent=2, ensure_ascii=False)
        
        print("✅ Created manual_banner_mapping.json")
        return True
        
    except Exception as e:
        print(f"❌ Error creating manual banner system: {e}")
        return False

def main():
    """Main function"""
    print("🕷️ Getting Real Seniors Banners (Advanced)")
    print("=" * 50)
    
    # Step 1: Try Selenium approach
    print("\n🕷️ Step 1: Trying Selenium approach...")
    events = get_seniors_banners_with_selenium()
    
    if not events:
        print("⚠️ Selenium approach didn't find banners")
    
    # Step 2: Create manual system
    print("\n📝 Step 2: Creating manual banner system...")
    create_manual_banner_system()
    
    print("\n🎉 Banner system setup completed!")
    print("📖 See MANUAL_BANNER_GUIDE.md for instructions on getting real banners")
    print("📝 Use manual_banner_mapping.json to add real banner URLs")

if __name__ == "__main__":
    main()
