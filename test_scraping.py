#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

def test_scraping():
    print("🔍 Testing Seniors Kingston events scraping...")
    
    try:
        # Headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Try to fetch the events page
        print("Fetching https://www.seniorskingston.ca/events...")
        response = requests.get('https://www.seniorskingston.ca/events', headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"Response status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Print the page title
        title = soup.find('title')
        print(f"Page title: {title.get_text() if title else 'No title found'}")
        
        # Look for common event container patterns
        event_selectors = [
            '.event-item',
            '.event',
            '.calendar-event',
            '.event-card',
            '[class*="event"]',
            '.post',
            '.entry',
            'article'
        ]
        
        print("\n🔍 Searching for event elements...")
        event_elements = []
        for selector in event_selectors:
            elements = soup.select(selector)
            if elements:
                event_elements = elements
                print(f"Found {len(elements)} elements using selector: {selector}")
                break
        
        if not event_elements:
            print("No event elements found with standard selectors")
            # Look for any elements that might contain event info
            event_elements = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'event|post|entry|card', re.I))
            print(f"Fallback: Found {len(event_elements)} potential event elements")
        
        # Print first few elements to see structure
        print(f"\n📋 First 3 elements structure:")
        for i, element in enumerate(event_elements[:3]):
            print(f"\n--- Element {i+1} ---")
            print(f"Tag: {element.name}")
            print(f"Classes: {element.get('class', [])}")
            print(f"Text preview: {element.get_text()[:200]}...")
            
            # Look for common event data
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'])
            if title_elem:
                print(f"Title: {title_elem.get_text(strip=True)}")
            
            date_elem = element.find(class_=re.compile(r'date', re.I))
            if date_elem:
                print(f"Date: {date_elem.get_text(strip=True)}")
        
        # Look for any text that might be event-related
        print(f"\n🔍 Looking for event-related text...")
        all_text = soup.get_text()
        event_keywords = ['event', 'meeting', 'class', 'workshop', 'seminar', 'activity']
        for keyword in event_keywords:
            if keyword.lower() in all_text.lower():
                print(f"Found '{keyword}' in page text")
        
        # Check if there's a calendar or events widget
        calendar_elements = soup.find_all(['div', 'iframe'], class_=re.compile(r'calendar|event', re.I))
        print(f"\n📅 Calendar elements found: {len(calendar_elements)}")
        
        # Look for any JavaScript that might load events
        scripts = soup.find_all('script')
        print(f"\n📜 Scripts found: {len(scripts)}")
        for script in scripts:
            if script.string and ('event' in script.string.lower() or 'calendar' in script.string.lower()):
                print(f"Script contains event/calendar keywords")
                break
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_scraping()
