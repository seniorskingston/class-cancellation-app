#!/usr/bin/env python3
"""
Simple script to trigger event scraping and save results
"""

import requests
import json

def trigger_scraping():
    """Trigger the scraping endpoint"""
    print("🔄 Triggering event scraping from Seniors Kingston website...")
    print("=" * 60)
    
    # Use local backend if running locally, otherwise use deployed URL
    backend_url = "http://localhost:8000"
    
    try:
        response = requests.post(f"{backend_url}/api/scrape-events", timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Scraping completed!")
            print(f"   📊 Total events: {result.get('events_count', 0)}")
            print(f"   ➕ Added: {result.get('added', 0)} new events")
            print(f"   🔄 Updated: {result.get('updated', 0)} existing events")
            print(f"   🚫 Skipped: {result.get('skipped', 0)} duplicates")
            print(f"\n   Message: {result.get('message', 'N/A')}")
            
            if result.get('updated_details'):
                print(f"\n   Updated events:")
                for detail in result.get('updated_details', [])[:5]:
                    print(f"      {detail}")
            
            return True
        else:
            print(f"❌ Scraping failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to backend at {backend_url}")
        print("   Make sure the backend is running!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    trigger_scraping()

