#!/usr/bin/env python3
"""
Get Real Seniors Banners - Manual system to get actual banners from website
"""

import json
import requests
import os
from datetime import datetime

def create_real_banner_instructions():
    """Create instructions for getting real banners"""
    try:
        print("📝 Creating instructions for getting real Seniors Kingston banners...")
        
        instructions = """# How to Get Real Seniors Kingston Event Banners

## The Problem
The current banners are random photos, not the actual event banners from the Seniors Kingston website.

## The Solution
You need to manually get the real banner URLs from the website.

## Step-by-Step Instructions

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
1. Open the file `real_banner_mapping.json`
2. Replace the placeholder URLs with the real banner URLs
3. Save the file

### Step 4: Apply the Real Banners
Run: `python apply_real_banners.py`

## Example Format
```json
{
  "Sound Escapes: Kenny & Dolly": "https://seniorskingston.ca/images/kenny-dolly-banner.jpg",
  "Wearable Tech": "https://seniorskingston.ca/images/tech-banner.jpg",
  "Legal Advice": "https://seniorskingston.ca/images/legal-banner.jpg"
}
```

## Current Events That Need Real Banners:
"""
        
        # Load current events and add them to instructions
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        for i, event in enumerate(events, 1):
            title = event.get('title', 'No title')
            instructions += f"{i}. {title}\n"
        
        with open('REAL_BANNER_INSTRUCTIONS.md', 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print("✅ Created REAL_BANNER_INSTRUCTIONS.md")
        return True
        
    except Exception as e:
        print(f"❌ Error creating instructions: {e}")
        return False

def create_real_banner_template():
    """Create a template for real banner URLs"""
    try:
        print("📝 Creating template for real banner URLs...")
        
        # Load current events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        # Create template with all event titles
        banner_template = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "Template for real Seniors Kingston event banners",
                "instructions": "Replace placeholder URLs with real banner URLs from seniorskingston.ca/events"
            },
            "banner_mapping": {}
        }
        
        # Add all event titles with placeholder URLs
        for event in events:
            title = event.get('title', 'No title')
            banner_template["banner_mapping"][title] = "REPLACE_WITH_REAL_SENIORS_BANNER_URL"
        
        # Save template
        with open('real_banner_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(banner_template, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created real_banner_mapping.json with {len(events)} events")
        return True
        
    except Exception as e:
        print(f"❌ Error creating template: {e}")
        return False

def create_apply_real_banners_script():
    """Create script to apply real banners"""
    try:
        print("🔧 Creating script to apply real banners...")
        
        apply_script = '''#!/usr/bin/env python3
"""
Apply Real Banners - Apply real Seniors Kingston banners to events
"""

import json
import requests

def apply_real_banners():
    """Apply real Seniors Kingston banners to events"""
    try:
        print("🔄 Applying real Seniors Kingston banners...")
        
        # Load real banner mapping
        with open('real_banner_mapping.json', 'r', encoding='utf-8') as f:
            banner_data = json.load(f)
            banner_mapping = banner_data.get('banner_mapping', {})
        
        # Load current events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events")
        
        # Apply real banners
        updated_count = 0
        for event in events:
            title = event.get('title', '')
            
            if title in banner_mapping:
                banner_url = banner_mapping[title]
                
                # Check if it's a real URL (not placeholder)
                if banner_url != "REPLACE_WITH_REAL_SENIORS_BANNER_URL" and banner_url.startswith('http'):
                    event['image_url'] = banner_url
                    updated_count += 1
                    print(f"   ✅ {title[:40]}... -> Real banner")
                else:
                    # Keep current banner if no real URL provided
                    print(f"   ⚠️ {title[:40]}... -> No real banner URL provided")
            else:
                print(f"   ⚠️ {title[:40]}... -> Not found in banner mapping")
        
        print(f"\\n📊 Updated {updated_count} events with real banners")
        
        # Save updated events
        with open('bulletproof_events_backup.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Upload to backend
        print("\\n☁️ Uploading events with real banners to backend...")
        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
        upload_data = {'events': events}
        
        response = requests.post(backend_url, json=upload_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully uploaded events with real banners")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error applying real banners: {e}")
        return False

if __name__ == "__main__":
    apply_real_banners()
'''
        
        # Save the apply script
        with open('apply_real_banners.py', 'w', encoding='utf-8') as f:
            f.write(apply_script)
        
        print("✅ Created apply_real_banners.py")
        return True
        
    except Exception as e:
        print(f"❌ Error creating apply script: {e}")
        return False

def reset_events_to_logo():
    """Reset events to use Seniors Kingston logo temporarily"""
    try:
        print("🔄 Resetting events to use Seniors Kingston logo temporarily...")
        
        # Load current events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        # Reset all events to use the logo
        for event in events:
            event['image_url'] = "/logo192.png"  # Seniors Kingston logo
        
        # Save updated events
        with open('bulletproof_events_backup.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Upload to backend
        print("☁️ Uploading events with Seniors Kingston logo...")
        backend_url = "https://class-cancellation-backend.onrender.com/api/events/bulk-update"
        upload_data = {'events': events}
        
        response = requests.post(backend_url, json=upload_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Successfully reset events to use Seniors Kingston logo")
                return True
            else:
                print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error resetting events: {e}")
        return False

def main():
    """Main function"""
    print("📝 Creating Real Banner System")
    print("=" * 40)
    
    # Step 1: Create instructions
    print("\\n📝 Step 1: Creating instructions...")
    if not create_real_banner_instructions():
        print("❌ Failed to create instructions")
        return
    
    # Step 2: Create template
    print("\\n📝 Step 2: Creating template...")
    if not create_real_banner_template():
        print("❌ Failed to create template")
        return
    
    # Step 3: Create apply script
    print("\\n🔧 Step 3: Creating apply script...")
    if not create_apply_real_banners_script():
        print("❌ Failed to create apply script")
        return
    
    # Step 4: Reset to logo temporarily
    print("\\n🔄 Step 4: Resetting to Seniors Kingston logo temporarily...")
    if not reset_events_to_logo():
        print("❌ Failed to reset to logo")
        return
    
    print("\\n🎉 Real banner system created!")
    print("📖 See REAL_BANNER_INSTRUCTIONS.md for detailed instructions")
    print("📝 Edit real_banner_mapping.json with real banner URLs")
    print("🔄 Run python apply_real_banners.py to apply real banners")
    print("✅ Events now use Seniors Kingston logo (better than random photos)")

if __name__ == "__main__":
    main()
