#!/usr/bin/env python3
"""
Merge events into scraped_events_for_upload.json by month:
- Keep all events from the existing file (previous months).
- From the new scrape, add only events in months that are NOT already in the file.
So existing months are never replaced; only new months are added.
"""

import json
import re
from datetime import datetime
from pathlib import Path


def get_event_year_month(event):
    """Return (year, month) for an event from startDate or dateStr."""
    # Prefer ISO startDate: "2026-02-25T09:00:00Z" or "2026-01-01T12:00:00+00:00Z"
    start = event.get("startDate") or ""
    if start:
        m = re.match(r"(\d{4})-(\d{2})", start)
        if m:
            return (int(m.group(1)), int(m.group(2)))
    # Fallback: dateStr like "February 25, 2026" or "January 08, 2026"
    date_str = event.get("dateStr") or ""
    if not date_str:
        return (0, 0)
    months = {
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "Jun": 6, "Jul": 7, "Aug": 8,
        "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }
    for name, num in months.items():
        if name in date_str:
            y = re.search(r"20\d{2}", date_str)
            year = int(y.group(0)) if y else datetime.now().year
            return (year, num)
    return (0, 0)


def merge_events_by_month(existing_events, new_events):
    """
    Keep all existing events. Add from new_events only those in (year, month)
    that do not appear in existing_events.
    """
    existing_months = {get_event_year_month(e) for e in existing_events}
    existing_months.discard((0, 0))

    merged = list(existing_events)
    for e in new_events:
        ym = get_event_year_month(e)
        if ym != (0, 0) and ym not in existing_months:
            merged.append(e)

    # Sort by startDate for consistent order
    def sort_key(ev):
        s = ev.get("startDate") or ""
        return (s[:19] if s else "9999-99-99") + (ev.get("title") or "")

    merged.sort(key=sort_key)
    return merged


def load_events_file(path):
    """Load events array from a scraped_events_for_upload-style JSON file."""
    path = Path(path)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("events", [])


def save_events_file(path, events, export_date=None):
    """Save events to scraped_events_for_upload.json format."""
    path = Path(path)
    export_date = export_date or datetime.now().isoformat()
    data = {
        "export_date": export_date,
        "total_events": len(events),
        "events": events,
        "source": "merged_by_month",
        "merged_at": datetime.now().isoformat(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return len(events)


def main():
    main_file = Path("scraped_events_for_upload.json")
    old_file = Path("scraped_events_for_upload_fixed.json")

    existing = load_events_file(main_file)
    # If we have an "old" backup with earlier months, use it as the existing base
    if old_file.exists():
        old_events = load_events_file(old_file)
        old_months = {get_event_year_month(e) for e in old_events}
        cur_months = {get_event_year_month(e) for e in existing}
        # Use old file as existing only if it has months not in current (i.e. current was overwritten by scrape)
        if old_months - cur_months:
            existing = old_events
            new_events = load_events_file(main_file)
            print(f"Using {old_file} as existing ({len(existing)} events), merging with current file ({len(new_events)} events).")
        else:
            new_events = []
            print(f"Current file already has all months. No merge from {old_file}.")
    else:
        new_events = existing
        existing = []

    if not new_events and not existing:
        print("No events to merge.")
        return

    if existing and new_events:
        merged = merge_events_by_month(existing, new_events)
    else:
        merged = existing or new_events

    count = save_events_file(main_file, merged)
    print(f"Saved {count} events to {main_file}.")

    # Summary by month
    by_month = {}
    for e in merged:
        ym = get_event_year_month(e)
        if ym != (0, 0):
            by_month[ym] = by_month.get(ym, 0) + 1
    print("Events by (year, month):")
    for (y, m), n in sorted(by_month.items()):
        print(f"  {y}-{m:02d}: {n}")


if __name__ == "__main__":
    main()
