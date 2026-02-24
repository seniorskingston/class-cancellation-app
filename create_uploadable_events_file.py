#!/usr/bin/env python3
"""
Create an uploadable events JSON file from scraped events
This file can be uploaded through the admin panel.
Merges by month: keeps all existing events (previous months) and adds only new months from the scrape.
"""

from backend_sqlite import scrape_seniors_kingston_events, _merge_events_by_month
import json
import os
from datetime import datetime

def create_uploadable_events_file():
    """Scrape events and create a JSON file ready for upload (merge by month if file exists)"""
    print("🔄 Creating uploadable events file...")
    print("=" * 60)
    
    # Step 1: Scrape events
    print("\n📥 Step 1: Scraping events from Seniors Kingston website...")
    scraped_events = scrape_seniors_kingston_events()
    
    if not scraped_events or len(scraped_events) == 0:
        print("❌ No events found during scraping!")
        return False
    
    print(f"✅ Found {len(scraped_events)} events")
    
    # Step 2: Merge by month if existing file present (keep old months, add new months only)
    filename = "scraped_events_for_upload.json"
    events_to_save = scraped_events
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_events = existing_data.get("events", [])
            if existing_events:
                events_to_save = _merge_events_by_month(existing_events, scraped_events)
                print(f"\n📎 Merged by month: kept {len(existing_events)} existing, added new months → {len(events_to_save)} total")
        except Exception as e:
            print(f"⚠️ Could not merge with existing file: {e}. Saving scrape only.")
    
    # Step 3: Save to file
    print(f"\n💾 Step 3: Saving to {filename}...")
    
    upload_data = {
        "export_date": datetime.now().isoformat(),
        "total_events": len(events_to_save),
        "events": events_to_save
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(upload_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully created {filename}")
        print(f"   📊 Contains {len(events_to_save)} events")
        print(f"   📁 File size: {len(json.dumps(upload_data, indent=2))} bytes")
        
        # Show first few events as preview
        print(f"\n📋 Preview of events:")
        for i, event in enumerate(events_to_save[:5], 1):
            title = event.get('title', 'N/A')
            date = event.get('dateStr', 'N/A')
            time = event.get('timeStr', 'N/A')
            print(f"   {i}. {title} - {date} {time}")
        
        if len(events_to_save) > 5:
            print(f"   ... and {len(events_to_save) - 5} more events")
        
        print(f"\n✅ File ready for upload!")
        print(f"   📤 Next steps:")
        print(f"   1. Go to Admin Panel")
        print(f"   2. Click '🔄 Scrape & Edit Events'")
        print(f"   3. Click '📤 Upload Events JSON' button")
        print(f"   4. Select this file: {filename}")
        print(f"   5. The events will replace all existing events")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_uploadable_events_file()
    if success:
        print("\n🎉 Done! Your events file is ready to upload.")
    else:
        print("\n❌ Failed to create events file. Check the errors above.")


