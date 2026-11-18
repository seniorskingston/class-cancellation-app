"""Test-site job that accepts a PerfectMind program list.

The live site never starts this job. Staff notes and cancellation dates
already stored for the same class are copied onto the new rows.
"""

from __future__ import annotations

import re
import threading
from datetime import datetime, timezone


_lock = threading.Lock()
_job = {
    "status": "idle",
    "message": "The test list still has the last saved programs.",
    "program_count": 0,
    "updated_at": "",
}


def _stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def status() -> dict:
    with _lock:
        return dict(_job)


def request_sync() -> dict:
    with _lock:
        if _job["status"] in ("pending", "running"):
            return dict(_job)
        _job.update({
            "status": "pending",
            "message": "Waiting for this computer to open PerfectMind. Stay nearby if it asks you to check the login.",
            "program_count": 0,
            "updated_at": _stamp(),
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
