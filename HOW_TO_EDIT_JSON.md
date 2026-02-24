# How to Edit the JSON Events File

## Merge by Month (Scraping)

When you **scrape** or run `create_uploadable_events_file.py`, the app now **merges by month** instead of replacing the whole file:

- **Existing months** in `scraped_events_for_upload.json` are kept (e.g. December, January).
- **New months** from the scrape are added (e.g. February, March).
- Months already in the file are never overwritten by the scrape.

So you keep all previous events and only add new months.

### If You Already Overwrote the File (One-Time Repair)

If you already ran a scrape and lost earlier months, you can repair using your backup `scraped_events_for_upload_fixed.json`:

1. From your **project folder** (where the JSON files are), run:
   ```bash
   python repair_merge_events_now.py
   ```
2. This merges: keeps all events from `scraped_events_for_upload_fixed.json` (old months) and adds from `scraped_events_for_upload.json` only events in **new** months. Result is written to `scraped_events_for_upload.json`.

---

## Step 1: Download Current Events

Run this command to download the current events (including February) from the app:

```bash
python download_current_events.py
```

This will create/update `scraped_events_for_upload.json` with all current events from the backend.

## Step 2: Edit the JSON File

### Option A: Use a Text Editor (Recommended)
1. Open `scraped_events_for_upload.json` in any text editor (Notepad, VS Code, etc.)
2. Make your changes
3. **IMPORTANT**: Be careful with JSON syntax:
   - Use **double quotes** `"` for all strings (not single quotes)
   - Use **commas** `,` between items (but NOT after the last item)
   - Make sure all brackets `{ }` and `[ ]` are properly closed
   - Don't add trailing commas

### Option B: Use an Online JSON Editor
1. Go to https://jsoneditoronline.org/
2. Copy the contents of `scraped_events_for_upload.json`
3. Paste into the editor
4. Make your changes (it will validate JSON automatically)
5. Copy the edited JSON back to the file

## Step 3: Validate Your JSON

Before uploading, validate your JSON:

```bash
python -c "import json; f = open('scraped_events_for_upload.json', 'r', encoding='utf-8'); json.load(f); print('✅ JSON is valid!')"
```

## Step 4: Upload the Edited File

1. Go to the Admin Panel in your app
2. Click "🔄 Scrape & Edit Events"
3. Click "📤 Upload Events JSON"
4. Select your edited `scraped_events_for_upload.json` file
5. The events will be updated in the app

## Common JSON Editing Tasks

### Change an Event Title
```json
{
  "title": "New Title Here",
  ...
}
```

### Change an Event Description
```json
{
  "description": "New description text here",
  ...
}
```

### Make URLs Clickable in Description

**The app automatically makes URLs clickable!** Just include the full URL in your description:

**Example:**
```json
{
  "title": "Session 3 Online Registration",
  "description": "Online registration for Session 3 begins February 2 at 8am. You can bring your device to The Seniors Centre to use our free WIFI to register. CLICK HERE https://seniorskingston.ca/programs for program information",
  ...
}
```

**URL formats that work:**
- `https://seniorskingston.ca/programs` ✅ (automatically clickable)
- `http://seniorskingston.ca/programs` ✅ (automatically clickable)
- `www.seniorskingston.ca/programs` ✅ (automatically becomes https://)
- `seniorskingston.ca/programs` ❌ (needs http:// or https://)

**Tips:**
- Always include `https://` or `http://` at the start of URLs
- URLs will open in a new tab when clicked
- You can put the URL anywhere in the description text

### Change an Event Date
```json
{
  "startDate": "2026-02-15T10:00:00Z",
  "endDate": "2026-02-15T11:00:00Z",
  "dateStr": "February 15, 2026",
  "timeStr": "10:00 AM"
}
```

### Change an Event Price

Add or modify the `priceStr` field in the event object. Place it after `timeStr`:

**Example 1: Event without price (add price)**
```json
{
  "title": "Setting your Intention for 2026 Workshop",
  "description": "January 21, 2:00 pm Instructor: Daphne Gardiner",
  "image_url": "https://...",
  "startDate": "2026-01-21T14:00:00Z",
  "endDate": "2026-01-21T15:00:00Z",
  "location": "Seniors Kingston",
  "dateStr": "January 21, 2026",
  "timeStr": "2:00 PM",
  "priceStr": "$20/member"
}
```

**Example 2: Event with price (modify price)**
```json
{
  "title": "Legal Advice",
  "description": "January 26, 1:00 pm",
  "image_url": "https://...",
  "startDate": "2026-01-26T13:00:00Z",
  "endDate": "2026-01-26T14:00:00Z",
  "location": "Phone Call",
  "dateStr": "January 26, 2026",
  "timeStr": "1:00 PM",
  "priceStr": "Free"
}
```

**Common price formats:**
- `"priceStr": "$10"` - Simple price
- `"priceStr": "$20/member"` - Price with member note
- `"priceStr": "$16/member |$18/non-member"` - Multiple prices
- `"priceStr": "Free"` - Free event
- `"priceStr": "$5"` - Single price

**Note:** If an event doesn't have a `priceStr` field, you can add it. If you want to remove a price, you can delete the entire `"priceStr": "..."` line (including the comma before it if it's not the last field).

### Remove an Event
- Delete the entire event object `{ ... }` including the comma before it (if it's not the last event)

### Add an Event
- Copy an existing event object
- Modify the fields
- Add a comma after the previous event
- Paste the new event

## JSON Structure

```json
{
  "export_date": "2026-01-20T13:30:37.859194",
  "total_events": 32,
  "events": [
    {
      "title": "Event Title",
      "description": "Event description",
      "image_url": "https://...",
      "startDate": "2026-01-20T10:00:00Z",
      "endDate": "2026-01-20T11:00:00Z",
      "location": "Seniors Kingston",
      "dateStr": "January 20, 2026",
      "timeStr": "10:00 AM",
      "priceStr": "$10"  // Optional
    },
    // ... more events
  ]
}
```

## Tips

- **Always backup** the file before editing
- **Validate JSON** before uploading
- **Check for commas** - missing or extra commas are the #1 JSON error
- **Use a JSON validator** if you're unsure about syntax
