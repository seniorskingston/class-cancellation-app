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
    "message": "The class list still has the last saved programs.",
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
    """Turn typed labels such as Session 1-2028 into one clean name."""
    cleaned = []
    seen = set()
    for value in values or []:
        match = re.search(r"(?:session\s*)?(\d+)\s*[-/ ]\s*(20\d{2})", str(value), re.I)
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
            "message": message or "PerfectMind sync failed. The class list was not changed.",
            "updated_at": _stamp(),
        })
        return dict(_job)


def succeed(program_count: int, ran_at: str = "", changes: list | None = None) -> dict:
    changes = list(changes or [])
    detail = "No class changes." if not changes else f"{len(changes)} class changes."
    when = f" Last run {ran_at}." if ran_at else ""
    with _lock:
        _job.update({
            "status": "success",
            "message": f"Saved {program_count} programs.{when} {detail} Notes and cancellation dates already entered were kept.",
            "program_count": program_count,
            "updated_at": _stamp(),
            "ran_at": ran_at,
            "changes": changes,
            "change_count": len(changes),
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
        if not key[0]:
            continue
        previous = saved.get(key)
        if previous and (
            str(previous.get("note") or "").strip() or str(previous.get("class_cancellation") or "").strip()
        ):
            continue
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
    """Replace only the days that were just read. Keep a missed day and any saved cancellation."""
    incoming_keys = {_staff_key(row) for row in incoming if _staff_key(row)[0]}
    incoming_days = set()
    for row in incoming:
        session = session_number(row.get("session"))
        day = str(row.get("sheet") or "").strip().lower()
        if session and day:
            incoming_days.add((session, day))
    combined = list(incoming)
    for row in existing:
        session = session_number(row.get("session"))
        day = str(row.get("sheet") or "").strip().lower()
        if (session, day) not in incoming_days:
            combined.append(row)
            continue
        if _staff_key(row) in incoming_keys:
            continue
        if str(row.get("note") or "").strip() or str(row.get("class_cancellation") or "").strip():
            combined.append(row)
    return combined


def _plain(value) -> str:
    return " ".join(str(value or "").split())


def _class_label(row: dict) -> str:
    day = str(row.get("sheet") or "").strip()
    session = session_number(row.get("session")) or str(row.get("session") or "").strip()
    name = str(row.get("program") or "").strip()
    program_id = _program_id(row.get("program_id"))
    return f"{day} Session {session} {name} {program_id}".strip()


def session_changes(existing: list, incoming: list) -> list[str]:
    """List added, removed, and changed classes for the days that were just read."""
    labels = (
        ("program", "Name"),
        ("time", "Time"),
        ("date_range", "Dates"),
        ("location", "Location"),
        ("class_room", "Room"),
        ("instructor", "Instructor"),
        ("program_status", "Status"),
        ("fee", "Fee"),
    )
    read_days = set()
    fresh = {}
    for row in incoming:
        session = session_number(row.get("session"))
        day = str(row.get("sheet") or "").strip().lower()
        key = _staff_key(row)
        if session and day:
            read_days.add((session, day))
        if key[0]:
            fresh[key] = row
    previous = {}
    for row in existing:
        session = session_number(row.get("session"))
        day = str(row.get("sheet") or "").strip().lower()
        if (session, day) not in read_days:
            continue
        key = _staff_key(row)
        if key[0]:
            previous[key] = row
    lines = []
    for key, row in fresh.items():
        old = previous.get(key)
        if not old:
            lines.append(f"Added {_class_label(row)}")
            continue
        parts = []
        for field, label in labels:
            before = _plain(old.get(field))
            after = _plain(row.get(field))
            if before.casefold() != after.casefold():
                parts.append(f"{label} was {before or 'blank'}, now {after or 'blank'}")
        if parts:
            lines.append(f"Changed {_class_label(row)}: " + "; ".join(parts))
    for key, row in previous.items():
        if key not in fresh:
            lines.append(f"Removed {_class_label(row)}")
    return sorted(lines)


def ran_label(now=None) -> str:
    current = _kingston_now(now)
    hour = current.strftime("%H:%M")
    return f"{current.strftime('%B')} {current.day}, {current.year}, {_clock_label(hour)}"


KINGSTON = ZoneInfo("America/Toronto")
SCHEDULE_FREQUENCIES = ("off", "daily", "interval", "weekly")
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


def _clocks(values, default: str) -> list[str]:
    cleaned = []
    for value in values or []:
        clock = _clock(value, "")
        if clock and clock not in cleaned:
            cleaned.append(clock)
    return cleaned or [default]


def clean_schedule(raw) -> dict:
    raw = raw or {}
    frequency = str(raw.get("frequency") or "off").strip().lower()
    if frequency == "twice":
        frequency = "daily"
    elif frequency == "every2hours":
        frequency = "interval"
    if frequency not in SCHEDULE_FREQUENCIES:
        frequency = "off"
    weekday = str(raw.get("weekday") or "monday").strip().lower()
    if weekday not in WEEKDAYS:
        weekday = "monday"
    entered_times = raw.get("times")
    if not isinstance(entered_times, list) or not entered_times:
        entered_times = [raw.get("time") or "08:00"]
        if str(raw.get("frequency") or "").lower() == "twice" and raw.get("second_time"):
            entered_times.append(raw.get("second_time"))
    times = _clocks(entered_times, "08:00")
    try:
        hours = int(raw.get("interval_hours") or (2 if str(raw.get("frequency") or "").lower() == "every2hours" else 1))
    except (TypeError, ValueError):
        hours = 1
    hours = min(24, max(1, hours))
    seasons = normalize_seasons(raw.get("seasons")) or ["Session 1-2026", "Session 2-2026"]
    return {
        "frequency": frequency,
        "times": times,
        "time": times[0],
        "interval_hours": hours,
        "window_start": _clock(raw.get("window_start"), "08:00"),
        "window_end": _clock(raw.get("window_end"), "20:00"),
        "weekday": weekday,
        "seasons": seasons,
        "visible_seasons": normalize_seasons(raw.get("visible_seasons")) or seasons,
        "skip_weekends": raw.get("skip_weekends") is True or str(raw.get("skip_weekends") or "").strip().lower() in ("1", "true", "yes", "on"),
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


def _passed_slot(slots, current, last) -> bool:
    passed = [slot for slot in slots if slot <= current]
    if not passed:
        return False
    return last is None or last < max(passed)


def schedule_is_due(raw, now=None) -> bool:
    schedule = clean_schedule(raw)
    current = _kingston_now(now)
    last = _last_run(schedule)
    frequency = schedule["frequency"]
    if frequency == "off":
        return False
    if schedule.get("skip_weekends") and current.weekday() >= 5:
        return False
    if frequency == "interval":
        start_at = _at(current, schedule["window_start"])
        end_at = _at(current, schedule["window_end"])
        if end_at < start_at:
            if current >= start_at:
                end_at += timedelta(days=1)
            else:
                start_at -= timedelta(days=1)
        if not (start_at <= current <= end_at):
            return False
        slots = []
        slot = start_at
        while slot <= end_at and len(slots) < 48:
            slots.append(slot)
            slot += timedelta(hours=schedule["interval_hours"])
        return _passed_slot(slots, current, last)
    if frequency == "daily":
        slots = [_at(current, value) for value in schedule["times"]]
        due_slots = [slot for slot in slots if slot <= current]
        if not due_slots:
            return False
        return last is None or last < max(due_slots)
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
        summary = "PerfectMind runs only when you click the button."
    elif frequency == "daily":
        labels = [_clock_label(value) for value in schedule["times"]]
        if len(labels) == 1:
            summary = f"PerfectMind runs every day at {labels[0]}."
        else:
            summary = "PerfectMind runs every day at " + " and ".join(labels) + "."
    elif frequency == "interval":
        hours = schedule["interval_hours"]
        gap = "hour" if hours == 1 else f"{hours} hours"
        summary = (
            f"PerfectMind runs every {gap} from {_clock_label(schedule['window_start'])} "
            f"to {_clock_label(schedule['window_end'])}."
        )
    else:
        day = schedule["weekday"].title()
        summary = f"PerfectMind runs once a week on {day} at {_clock_label(schedule['time'])}."
    if schedule.get("skip_weekends"):
        summary += " Saturday and Sunday are off."
    return summary


def session_matches(stored, labels) -> bool:
    """True when a saved program belongs to one of the typed sessions."""
    stored_text = str(stored or "").strip()
    if not stored_text:
        return False
    stored_number = session_number(stored_text)
    stored_year = re.search(r"20\d{2}", stored_text)
    for label in normalize_seasons(labels):
        if stored_text.lower() == label.lower():
            return True
        label_number = session_number(label)
        label_year = re.search(r"20\d{2}", label)
        if not stored_number or stored_number != label_number:
            continue
        if stored_year and label_year and stored_year.group() != label_year.group():
            continue
        return True
    return False


def session_label(stored) -> str:
    text = str(stored or "").strip()
    if not text:
        return ""
    if text.lower().startswith("session"):
        return text
    return f"Session {text}"


def mark_schedule_ran(raw, now=None) -> dict:
    schedule = clean_schedule(raw)
    schedule["last_run_at"] = _kingston_now(now).isoformat()
    return schedule


def public_schedule(raw, now=None) -> dict:
    schedule = clean_schedule(raw)
    schedule["due"] = schedule_is_due(schedule, now)
    schedule["summary"] = describe_schedule(schedule)
    return schedule
