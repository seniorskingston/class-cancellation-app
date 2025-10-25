# Quick Banner Guide

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
