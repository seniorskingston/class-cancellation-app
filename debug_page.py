#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

def debug_page():
    print("🔍 Debugging Seniors Kingston events page...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get('https://www.seniorskingston.ca/events', headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Print the raw HTML
        print("\n📄 Raw HTML content:")
        print(response.text[:1000])
        print("...")
        
        # Look for any iframes or external content
        iframes = soup.find_all('iframe')
        print(f"\n🖼️ Iframes found: {len(iframes)}")
        for iframe in iframes:
            print(f"  - src: {iframe.get('src')}")
        
        # Look for any external scripts or widgets
        scripts = soup.find_all('script')
        print(f"\n📜 Scripts found: {len(scripts)}")
        for i, script in enumerate(scripts):
            if script.string:
                print(f"  Script {i+1}: {script.string[:200]}...")
        
        # Look for any data attributes or JSON
        elements_with_data = soup.find_all(attrs={"data-events": True})
        print(f"\n📊 Elements with data-events: {len(elements_with_data)}")
        
        # Check for any calendar widgets
        calendar_widgets = soup.find_all(['div', 'section'], class_=re.compile(r'calendar|widget|embed', re.I))
        print(f"\n📅 Calendar widgets: {len(calendar_widgets)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_page()
