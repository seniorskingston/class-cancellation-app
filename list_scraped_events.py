#!/usr/bin/env python3
"""List all events found by scraping"""

from backend_sqlite import scrape_seniors_kingston_events

print("🔍 Scraping events from Seniors Kingston website...")
print("=" * 70)
print()

events = scrape_seniors_kingston_events()

if events:
    print(f"✅ Found {len(events)} events:\n")
    print("-" * 70)
    
    for i, event in enumerate(events, 1):
        title = event.get('title', 'N/A')
        date_str = event.get('dateStr', 'N/A')
        time_str = event.get('timeStr', 'N/A')
        location = event.get('location', 'N/A')
        description = event.get('description', '')
        
        print(f"{i}. {title}")
        print(f"   📅 Date: {date_str}")
        print(f"   🕐 Time: {time_str}")
        if location and location != "Seniors Kingston":
            print(f"   📍 Location: {location}")
        if description and len(description) > 0 and description != title:
            desc_preview = description[:100] + "..." if len(description) > 100 else description
            print(f"   📝 Description: {desc_preview}")
        print()
else:
    print("❌ No events found!")

