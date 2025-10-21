#!/usr/bin/env python3
"""
Event Management Script
Easy way to scrape, edit, and upload events
"""

import json
import os
import sys
from datetime import datetime

def show_menu():
    """Show the main menu"""
    print("\n" + "="*60)
    print("🎯 SENIORS KINGSTON EVENT MANAGER")
    print("="*60)
    print("1. 🔄 Scrape events from website and save to file")
    print("2. 📝 Edit events in the JSON file")
    print("3. ☁️  Upload events to cloud backend")
    print("4. 📊 View current events")
    print("5. 🚀 Scrape, save, and upload (all-in-one)")
    print("6. ❌ Exit")
    print("="*60)

def scrape_and_save():
    """Scrape events and save to file"""
    print("\n🔄 Scraping events from Seniors Kingston website...")
    
    try:
        # Import the scraping functions
        from backend_sqlite import scrape_seniors_kingston_events
        
        events = scrape_seniors_kingston_events()
        
        if events:
            # Save to file
            data = {
                "metadata": {
                    "scraped_at": datetime.now().isoformat(),
                    "total_events": len(events),
                    "source": "local_scraping",
                    "description": "Events scraped from Seniors Kingston website"
                },
                "events": events
            }
            
            with open("events_data.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Successfully scraped and saved {len(events)} events to events_data.json")
            
            # Show sample events
            print("\n📅 Sample events found:")
            for i, event in enumerate(events[:5]):
                print(f"   {i+1}. {event['title']} - {event.get('dateStr', 'TBA')}")
            if len(events) > 5:
                print(f"   ... and {len(events) - 5} more events")
            
            return True
        else:
            print("❌ No events found")
            return False
            
    except Exception as e:
        print(f"❌ Error scraping events: {e}")
        return False

def edit_events():
    """Help user edit events"""
    filename = "events_data.json"
    
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found. Please scrape events first.")
        return False
    
    print(f"\n📝 Opening {filename} for editing...")
    print("💡 You can now edit the events in the JSON file using any text editor.")
    print("💡 The file contains all event data including titles, dates, descriptions, and images.")
    
    # Load and display current events
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        events = data.get('events', [])
        metadata = data.get('metadata', {})
        
        print(f"\n📊 Current events ({len(events)} total):")
        print(f"📅 Last scraped: {metadata.get('scraped_at', 'Unknown')}")
        
        for i, event in enumerate(events[:10]):  # Show first 10
            print(f"   {i+1}. {event.get('title', 'No title')} - {event.get('dateStr', 'No date')}")
        if len(events) > 10:
            print(f"   ... and {len(events) - 10} more events")
        
        print(f"\n💡 To edit: Open {filename} in any text editor (Notepad, VS Code, etc.)")
        print("💡 After editing, choose option 3 to upload to cloud")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading events file: {e}")
        return False

def upload_events():
    """Upload events to cloud backend"""
    filename = "events_data.json"
    
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found. Please scrape events first.")
        return False
    
    try:
        import requests
        
        # Load events from file
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        events = data.get('events', [])
        
        if not events:
            print("❌ No events found in file")
            return False
        
        print(f"\n☁️ Uploading {len(events)} events to cloud backend...")
        
        # Prepare the data for the bulk update endpoint
        payload = {
            "events": events
        }
        
        # Upload to the cloud backend
        response = requests.post(
            "https://class-cancellation-backend.onrender.com/api/events/update",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully uploaded {result.get('count', len(events))} events to cloud")
                print("🌐 Your app should now show the updated events!")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading to cloud: {e}")
        return False

def view_events():
    """View current events"""
    filename = "events_data.json"
    
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found. Please scrape events first.")
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        events = data.get('events', [])
        metadata = data.get('metadata', {})
        
        print(f"\n📊 Current Events ({len(events)} total)")
        print(f"📅 Last scraped: {metadata.get('scraped_at', 'Unknown')}")
        print(f"📝 Source: {metadata.get('source', 'Unknown')}")
        print("-" * 60)
        
        for i, event in enumerate(events):
            print(f"{i+1:2d}. {event.get('title', 'No title')}")
            print(f"    📅 {event.get('dateStr', 'No date')} at {event.get('timeStr', 'TBA')}")
            print(f"    📍 {event.get('location', 'No location')}")
            if event.get('description'):
                desc = event['description'][:100] + "..." if len(event['description']) > 100 else event['description']
                print(f"    📝 {desc}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading events file: {e}")
        return False

def scrape_save_upload():
    """All-in-one: scrape, save, and upload"""
    print("\n🚀 Running complete workflow: scrape → save → upload")
    
    # Step 1: Scrape and save
    if not scrape_and_save():
        return False
    
    # Step 2: Upload
    if not upload_events():
        return False
    
    print("\n🎉 Complete workflow finished successfully!")
    print("🌐 Your app should now show the latest events!")
    return True

def main():
    """Main function"""
    while True:
        show_menu()
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                scrape_and_save()
            elif choice == "2":
                edit_events()
            elif choice == "3":
                upload_events()
            elif choice == "4":
                view_events()
            elif choice == "5":
                scrape_save_upload()
            elif choice == "6":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-6.")
            
            input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
