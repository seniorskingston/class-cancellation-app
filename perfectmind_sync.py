"""Test-site job that accepts a PerfectMind program list.

The live site never starts this job. Staff notes and cancellation dates
already stored for the same class are copied onto the new rows.
"""

from __future__ import annotations

import re
import threading
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


_lock = threading.Lock()
_job = {
    "status": "idle",
    "message": "The test list still has the last saved programs.",
    "program_count": 0,
    "updated_at": "",
    "seasons": [],
}


def _stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def status() -> dict:
    with _lock:
        return dict(_job)


def normalize_seasons(values) -> list[str]:
    """Turn picked labels into Session 1-2026 style names."""
    cleaned = []
    seen = set()
    for value in values or []:
        match = re.search(r"session\s*(\d+)\D+(20\d{2})", str(value), re.I)
        if not match:
            continue
        label = f"Session {int(match.group(1))}-{match.group(2)}"
        if label.lower() in seen:
            continue
        seen.add(label.lower())
        cleaned.append(label)
    return cleaned


def request_sync(seasons: list[str] | None = None) -> dict:
    chosen = normalize_seasons(seasons) or ["Session 1-2026", "Session 2-2026"]
    with _lock:
        if _job["status"] in ("pending", "running"):
            return dict(_job)
        _job.update({
            "status": "pending",
            "message": "Waiting for this computer to open PerfectMind. Stay nearby if it asks you to check the login.",
            "program_count": 0,
            "updated_at": _stamp(),
            "seasons": chosen,
        })
        return dict(_job)


def claim() -> dict:
    with _lock:
        if _job["status"] != "pending":
            current = dict(_job)
            current["claimed"] = False
            return current
        _job.update({
            "status": "running",
            "message": "PerfectMind is opening. This can take a while.",
            "updated_at": _stamp(),
        })
        current = dict(_job)
        current["claimed"] = True
        return current


def progress(message: str) -> dict:
    with _lock:
        if _job["status"] == "running" and message:
            _job["message"] = message
            _job["updated_at"] = _stamp()
        return dict(_job)


def fail(message: str) -> dict:
    with _lock:
        _job.update({
            "status": "error",
            "message": message or "PerfectMind sync failed. The test list was not changed.",
            "updated_at": _stamp(),
        })
        return dict(_job)


def succeed(program_count: int) -> dict:
    with _lock:
        _job.update({
            "status": "success",
            "message": f"Saved {program_count} programs from PerfectMind to the test database. Notes and cancellation dates already entered were kept.",
            "program_count": program_count,
            "updated_at": _stamp(),
        })
        return dict(_job)


def session_number(value: str) -> str:
    text = str(value or "").strip()
    match = re.search(r"session\s*(\d+)", text, re.I)
    if match:
        return str(int(match.group(1)))
    if re.fullmatch(r"\d+", text):
        return str(int(text))
    return ""


def _program_id(value: str) -> str:
    text = str(value or "").strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _staff_key(program: dict) -> tuple:
    return (
        _program_id(program.get("program_id")),
        session_number(program.get("session")),
        str(program.get("sheet") or "").strip().lower(),
    )


def merge_staff_fields(incoming: list, existing: list, withdrawal_fn) -> list:
    """Copy saved notes and cancellation dates onto the matching PerfectMind rows."""
    saved = {}
    for row in existing:
        key = _staff_key(row)
        if key[0]:
            saved[key] = row
    merged = []
    for source in incoming:
        item = {
            "sheet": str(source.get("sheet") or "").strip(),
            "program": str(source.get("program") or "").strip(),
            "program_id": _program_id(source.get("program_id")),
            "date_range": str(source.get("date_range") or "").strip(),
            "time": str(source.get("time") or "").strip(),
            "location": str(source.get("location") or "").strip(),
            "class_room": str(source.get("class_room") or "").strip(),
            "instructor": str(source.get("instructor") or "").strip(),
            "program_status": str(source.get("program_status") or "Active").strip() or "Active",
            "class_cancellation": str(source.get("class_cancellation") or "").strip(),
            "note": str(source.get("note") or "").strip(),
            "description": str(source.get("description") or "").strip(),
            "fee": str(source.get("fee") or "").strip(),
            "session": session_number(source.get("session")),
        }
        if not item["program_id"] or not item["session"] or not item["sheet"]:
            continue
        previous = saved.get(_staff_key(item))
        if previous:
            if str(previous.get("note") or "").strip():
                item["note"] = str(previous.get("note") or "").strip()
            if str(previous.get("class_cancellation") or "").strip():
                item["class_cancellation"] = str(previous.get("class_cancellation") or "").strip()
            if str(previous.get("program_status") or "").strip() == "Cancelled":
                item["program_status"] = "Cancelled"
        try:
            item["withdrawal"] = withdrawal_fn(item["date_range"], item["class_cancellation"])
        except Exception:
            item["withdrawal"] = ""
        merged.append(item)
    return merged


def combine_with_other_sessions(existing: list, incoming: list) -> list:
    """Replace only the sessions that were just read. Leave the other sessions in place."""
    replaced = {session_number(row.get("session")) for row in incoming}
    replaced.discard("")
    combined = list(incoming)
    for row in existing:
        if session_number(row.get("session")) in replaced:
            continue
        combined.append(row)
    return combined


KINGSTON = ZoneInfo("America/Toronto")
SCHEDULE_FREQUENCIES = ("off", "daily", "twice", "every2hours", "weekly")
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _clock(value, default: str) -> str:
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", str(value or "").strip())
    if not match:
        return default
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return default
    return f"{hour:02d}:{minute:02d}"


def _clock_label(value: str) -> str:
    hour, minute = [int(part) for part in value.split(":")]
    suffix = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return f"{hour12}:{minute:02d} {suffix}"


def clean_schedule(raw) -> dict:
    raw = raw or {}
    frequency = str(raw.get("frequency") or "off").strip().lower()
    if frequency not in SCHEDULE_FREQUENCIES:
        frequency = "off"
    weekday = str(raw.get("weekday") or "monday").strip().lower()
    if weekday not in WEEKDAYS:
        weekday = "monday"
    seasons = normalize_seasons(raw.get("seasons")) or ["Session 1-2026", "Session 2-2026"]
    return {
        "frequency": frequency,
        "time": _clock(raw.get("time"), "08:00"),
        "second_time": _clock(raw.get("second_time"), "13:00"),
        "weekday": weekday,
        "seasons": seasons,
        "last_run_at": str(raw.get("last_run_at") or ""),
    }


def _kingston_now(now=None) -> datetime:
    current = now or datetime.now(KINGSTON)
    if current.tzinfo is None:
        return current.replace(tzinfo=KINGSTON)
    return current.astimezone(KINGSTON)


def _at(day: datetime, hhmm: str) -> datetime:
    hour, minute = [int(part) for part in hhmm.split(":")]
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _last_run(schedule: dict):
    text = schedule.get("last_run_at") or ""
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KINGSTON)
    return parsed.astimezone(KINGSTON)


def schedule_is_due(raw, now=None) -> bool:
    schedule = clean_schedule(raw)
    current = _kingston_now(now)
    last = _last_run(schedule)
    frequency = schedule["frequency"]
    if frequency == "off":
        return False
    if frequency == "every2hours":
        if current.hour < 8 or current.hour >= 18:
            return False
        slot_hour = current.hour - (current.hour % 2)
        slot = current.replace(hour=slot_hour, minute=0, second=0, microsecond=0)
        return last is None or last < slot
    if frequency == "daily":
        slot = _at(current, schedule["time"])
        if current < slot:
            return False
        return last is None or last < slot
    if frequency == "twice":
        slots = [_at(current, schedule["time"]), _at(current, schedule["second_time"])]
        slots = [slot for slot in slots if slot <= current]
        if not slots:
            return False
        return last is None or last < max(slots)
    if frequency == "weekly":
        wanted = WEEKDAYS.index(schedule["weekday"])
        slot = _at(current, schedule["time"])
        slot = slot - timedelta(days=(current.weekday() - wanted) % 7)
        if slot > current:
            slot = slot - timedelta(days=7)
        return last is None or last < slot
    return False


def describe_schedule(raw) -> str:
    schedule = clean_schedule(raw)
    frequency = schedule["frequency"]
    if frequency == "off":
        return "PerfectMind runs only when you click the button."
    if frequency == "daily":
        return f"PerfectMind runs once a day at {_clock_label(schedule['time'])}."
    if frequency == "twice":
        return (
            f"PerfectMind runs twice a day at {_clock_label(schedule['time'])} "
            f"and {_clock_label(schedule['second_time'])}."
        )
    if frequency == "every2hours":
        return "PerfectMind runs every 2 hours from 8:00 AM to 4:00 PM."
    day = schedule["weekday"].title()
    return f"PerfectMind runs once a week on {day} at {_clock_label(schedule['time'])}."


def mark_schedule_ran(raw, now=None) -> dict:
    schedule = clean_schedule(raw)
    schedule["last_run_at"] = _kingston_now(now).isoformat()
    return schedule


def public_schedule(raw, now=None) -> dict:
    schedule = clean_schedule(raw)
    schedule["due"] = schedule_is_due(schedule, now)
    schedule["summary"] = describe_schedule(schedule)
    return schedule
