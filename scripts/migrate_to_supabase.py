"""Copy the current Class Cancellation records into Supabase.

Reads the live event list and the local Excel schedule, writes a backup
under backups/, then loads Supabase. It does not delete the Excel file,
the SQLite database, or the JSON files.

Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the environment or in a
gitignored .env file before running:

    python scripts/migrate_to_supabase.py
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

BACKUP_DIR = os.path.join(ROOT, "backups")
EVENTS_URL = "https://class-cancellation-backend.onrender.com/api/events"
EXCEL_PATH = os.path.join(ROOT, "Class Cancellation App.xlsx")


def load_env_file():
    env_path = os.path.join(ROOT, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#") or "=" not in text:
                continue
            key, value = text.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def fetch_live_events():
    backup_path = os.path.join(BACKUP_DIR, "events-live.json")
    if os.path.exists(backup_path):
        with open(backup_path, "r", encoding="utf-8") as handle:
            cached = json.load(handle)
        events = cached.get("events", cached if isinstance(cached, list) else [])
        if events:
            print(f"Using saved event backup: {len(events)} events")
            return events
    print("Downloading the current event list from the hosted app...")
    with urllib.request.urlopen(EVENTS_URL, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    events = payload.get("events", [])
    print(f"Downloaded {len(events)} events")
    return events


def write_backup(name, payload):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    path = os.path.join(BACKUP_DIR, name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"Wrote backup {path}")
    return path


def main():
    load_env_file()
    import supabase_store
    from backend_sqlite import calculate_withdrawal

    events = fetch_live_events()
    programs = []
    if os.path.exists(EXCEL_PATH):
        programs = supabase_store.programs_from_excel(EXCEL_PATH, calculate_withdrawal)
        print(f"Read {len(programs)} programs from the Excel schedule")
    else:
        print("Excel schedule was not found. Programs will not be copied.")

    write_backup("events-live.json", {"events": events, "count": len(events)})
    write_backup("programs-from-excel.json", {"programs": programs, "count": len(programs)})

    if not supabase_store.enabled():
        print("")
        print("Backup files are ready. Supabase credentials are not set, so nothing was uploaded.")
        print("Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to .env, then run this script again.")
        return 2

    existing_events = supabase_store.fetch_events()
    existing_programs = supabase_store.fetch_programs()
    print(f"Supabase currently has {len(existing_events)} events and {len(existing_programs)} programs")

    if len(existing_events) > len(events):
        print("Supabase already has more events than this backup. No event rows were changed.")
        return 1
    if programs and len(existing_programs) > len(programs):
        print("Supabase already has more programs than this backup. No program rows were changed.")
        return 1

    saved_events = supabase_store.replace_events(events, allow_empty=False) if events else 0
    saved_programs = supabase_store.replace_programs(programs) if programs else 0

    checked_events = supabase_store.fetch_events()
    checked_programs = supabase_store.fetch_programs()
    report = {
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "source_events": len(events),
        "source_programs": len(programs),
        "saved_events": saved_events,
        "saved_programs": saved_programs,
        "verified_events": len(checked_events),
        "verified_programs": len(checked_programs),
    }
    write_backup("migration-report.json", report)
    print(
        f"Verified Supabase: {report['verified_events']} events, "
        f"{report['verified_programs']} programs"
    )

    if events and report["verified_events"] != len(events):
        print("Event verification failed. Local files were not deleted.")
        return 1
    if programs and report["verified_programs"] != len(programs):
        print("Program verification failed. Local files were not deleted.")
        return 1

    print("Migration verified. The Excel file, SQLite database, and JSON files are still in place.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Migration stopped: {exc}")
        print("Local files were not deleted.")
        sys.exit(1)
