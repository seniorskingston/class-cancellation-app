#!/usr/bin/env python3
"""
Manual Banner System - Easy way to add real event banners
"""

import json
import requests
from datetime import datetime

def create_manual_banner_template():
    """Create a template for manually adding real banners"""
    try:
        print("📝 Creating manual banner template...")
        
        # Load current events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        # Create a template with all event titles
        banner_template = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "Template for adding real event banners from seniorskingston.ca/events",
                "instructions": "Replace the placeholder URLs with real banner URLs from the website"
            },
            "banner_mapping": {}
        }
        
        # Add all event titles with placeholder URLs
        for event in events:
            title = event.get('title', 'No title')
            banner_template["banner_mapping"][title] = "REPLACE_WITH_REAL_BANNER_URL"
        
        # Save template
        with open('manual_banner_template.json', 'w', encoding='utf-8') as f:
            json.dump(banner_template, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created manual_banner_template.json with {len(events)} events")
        
        # Create instructions
        instructions = """# How to Add Real Event Banners

## Step 1: Get Banner URLs from Website
1. Go to https://seniorskingston.ca/events
2. Wait for the page to fully load
3. For each event:
   - Right-click on the event banner image
   - Select "Copy image address" or "Copy image URL"
   - Note the event title

## Step 2: Update the Template
1. Open `manual_banner_template.json`
2. Replace "REPLACE_WITH_REAL_BANNER_URL" with the actual banner URL
3. Save the file

## Step 3: Apply the Banners
Run: `python apply_manual_banners.py`

## Example:
```json
{
  "Sound Escapes: Kenny & Dolly": "https://seniorskingston.ca/images/kenny-dolly-banner.jpg",
  "Wearable Tech": "https://seniorskingston.ca/images/tech-banner.jpg"
}
```

## Current Events:
"""
        
        # Add all event titles to instructions
        for i, event in enumerate(events, 1):
            title = event.get('title', 'No title')
            instructions += f"{i}. {title}\n"
        
        with open('BANNER_INSTRUCTIONS.md', 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print("✅ Created BANNER_INSTRUCTIONS.md with detailed instructions")
        return True
        
    except Exception as e:
        print(f"❌ Error creating manual banner template: {e}")
        return False

def create_apply_script():
    """Create a script to apply manual banners"""
    try:
        print("🔧 Creating apply script...")
        
        apply_script = '''#!/usr/bin/env python3
"""
Apply Manual Banners - Apply manually added banners to events
"""

import json
import requests

def apply_manual_banners():
    """Apply manually added banners to events"""
    try:
        print("🔄 Applying manual banners...")
        
        # Load manual banner mapping
        with open('manual_banner_template.json', 'r', encoding='utf-8') as f:
            banner_data = json.load(f)
            banner_mapping = banner_data.get('banner_mapping', {})
        
        # Load current events
        with open('bulletproof_events_backup.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get('events', [])
        
        print(f"📁 Loaded {len(events)} events")
        
        # Apply banners
        updated_count = 0
        for event in events:
            title = event.get('title', '')
            
            if title in banner_mapping:
                banner_url = banner_mapping[title]
                
                # Check if it's a real URL (not placeholder)
                if banner_url != "REPLACE_WITH_REAL_BANNER_URL" and banner_url.startswith('http'):
                    event['image_url'] = banner_url
                    updated_count += 1
                    print(f"   ✅ {title[:40]}... -> {banner_url}")
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
        print("\\n☁️ Uploading updated events to backend...")
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
        print(f"❌ Error applying manual banners: {e}")
        return False

if __name__ == "__main__":
    apply_manual_banners()
'''
        
        # Save the apply script
        with open('apply_manual_banners.py', 'w', encoding='utf-8') as f:
            f.write(apply_script)
        
        print("✅ Created apply_manual_banners.py")
        return True
        
    except Exception as e:
        print(f"❌ Error creating apply script: {e}")
        return False

def create_quick_banner_guide():
    """Create a quick guide for adding banners"""
    try:
        print("📖 Creating quick banner guide...")
        
        guide = """# Quick Banner Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Get Banner URLs
1. Go to https://seniorskingston.ca/events
2. Right-click on each event banner → "Copy image address"
3. Note the event title

### Step 2: Update Template
1. Open `manual_banner_template.json`
2. Replace "REPLACE_WITH_REAL_BANNER_URL" with the copied URL
3. Save the file

### Step 3: Apply Banners
```bash
python apply_manual_banners.py
```

## 📝 Example:
```json
{
  "Sound Escapes: Kenny & Dolly": "https://seniorskingston.ca/images/kenny-dolly-banner.jpg",
  "Wearable Tech": "https://seniorskingston.ca/images/tech-banner.jpg"
}
```

## 🎯 Result:
- Each event will have its specific banner
- Banners will display in floating boxes
- Professional appearance with real event images

## 📁 Files:
- `manual_banner_template.json` - Edit this file
- `apply_manual_banners.py` - Run this to apply changes
- `BANNER_INSTRUCTIONS.md` - Detailed instructions
"""
        
        with open('QUICK_BANNER_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(guide)
        
        print("✅ Created QUICK_BANNER_GUIDE.md")
        return True
        
    except Exception as e:
        print(f"❌ Error creating quick guide: {e}")
        return False

def main():
    """Main function"""
    print("📝 Creating Manual Banner System")
    print("=" * 40)
    
    # Step 1: Create template
    print("\\n📝 Step 1: Creating manual banner template...")
    if not create_manual_banner_template():
        print("❌ Failed to create template")
        return
    
    # Step 2: Create apply script
    print("\\n🔧 Step 2: Creating apply script...")
    if not create_apply_script():
        print("❌ Failed to create apply script")
        return
    
    # Step 3: Create quick guide
    print("\\n📖 Step 3: Creating quick guide...")
    if not create_quick_banner_guide():
        print("❌ Failed to create quick guide")
        return
    
    print("\\n🎉 Manual banner system created!")
    print("📝 Edit manual_banner_template.json with real banner URLs")
    print("🔄 Run python apply_manual_banners.py to apply changes")
    print("📖 See QUICK_BANNER_GUIDE.md for instructions")

if __name__ == "__main__":
    main()
