#!/usr/bin/env python3
"""One-time repair: merge scraped_events_for_upload_fixed.json (old) + scraped_events_for_upload.json (new scrape) by month. Writes result to scraped_events_for_upload.json. Run from your project folder: python repair_merge_events_now.py"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

def get_ym(e):
    start = e.get("startDate") or ""
    if start:
        m = re.match(r"(\d{4})-(\d{2})", start)
        if m:
            return (int(m.group(1)), int(m.group(2)))
    ds = e.get("dateStr") or ""
    months = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,"July":7,"August":8,"September":9,"October":10,"November":11,"December":12,"Jan":1,"Feb":2,"Mar":3,"Apr":4,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
    for name, num in months.items():
        if name in ds:
            y = re.search(r"20\d{2}", ds)
            return (int(y.group(0)) if y else 2026, num)
    return (0, 0)

# Run from project folder, or pass folder as first argument
if sys.argv[1:]:
    here = Path(sys.argv[1]).resolve()
else:
    here = Path(__file__).resolve().parent
old_path = here / "scraped_events_for_upload_fixed.json"
new_path = here / "scraped_events_for_upload.json"

if not old_path.exists():
    print("No scraped_events_for_upload_fixed.json found. Nothing to repair.")
    exit(0)
if not new_path.exists():
    print("No scraped_events_for_upload.json found.")
    exit(1)

with open(old_path, "r", encoding="utf-8") as f:
    old_data = json.load(f)
with open(new_path, "r", encoding="utf-8") as f:
    new_data = json.load(f)

old_events = old_data.get("events", [])
new_events = new_data.get("events", [])
old_months = {get_ym(e) for e in old_events}

merged = list(old_events)
for e in new_events:
    ym = get_ym(e)
    if ym != (0, 0) and ym not in old_months:
        merged.append(e)

def sk(ev):
    s = ev.get("startDate") or ""
    return (s[:19] if s else "9999-99-99") + (ev.get("title") or "")
merged.sort(key=sk)

out = {
    "export_date": datetime.now().isoformat(),
    "total_events": len(merged),
    "events": merged,
}
with open(new_path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(f"Repaired: {len(old_events)} old + new months -> {len(merged)} total in scraped_events_for_upload.json")
