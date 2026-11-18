"""Supabase storage for programs, events, and analytics.

The backend uses this only when both environment variables are set:

    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY

The service role key stays on the server. It is never sent to the browser
and must not be committed to GitHub. Until the variables are set, callers
keep using the existing SQLite, JSON, and Google Cloud Storage paths.
"""

import hashlib
import os
from typing import Callable

import pandas as pd
import requests

PAGE_SIZE = 1000
TIMEOUT_SECONDS = 60


def _url() -> str:
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]
    return url.rstrip("/")


def _service_key() -> str:
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def enabled() -> bool:
    url = _url()
    key = _service_key()
    return bool(url.startswith("https://") and key)


class SupabaseError(RuntimeError):
    pass


def _headers(extra=None):
    key = _service_key()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


def _request(method: str, url: str, action: str, **kwargs):
    try:
        response = requests.request(method, url, timeout=TIMEOUT_SECONDS, **kwargs)
    except requests.RequestException as exc:
        raise SupabaseError(f"{action} failed: {exc}") from exc
    return _check(response, action)


def _check(response, action: str):
    if response.status_code >= 400:
        detail = (response.text or "")[:500]
        raise SupabaseError(f"{action} failed ({response.status_code}): {detail}")
    return response


def _fetch_all(table: str, order: str) -> list:
    rows = []
    start = 0
    while True:
        end = start + PAGE_SIZE - 1
        response = _request(
            "GET",
            f"{_url()}/rest/v1/{table}",
            f"Reading {table}",
            params={"select": "*", "order": order},
            headers=_headers({"Range": f"{start}-{end}"}),
        )
        batch = response.json()
        if not isinstance(batch, list):
            raise SupabaseError(f"Unexpected response while reading {table}")
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE


def _rpc(name: str, payload: dict):
    response = _request(
        "POST",
        f"{_url()}/rest/v1/rpc/{name}",
        name,
        json=payload,
        headers=_headers({"Prefer": "return=representation"}),
    )
    body = response.json()
    if isinstance(body, int):
        return body
    if isinstance(body, str) and body.isdigit():
        return int(body)
    raise SupabaseError(f"{name} returned an unexpected result")


def _text(value) -> str:
    if value is None:
        return ""
    return str(value)


def _event_from_row(row: dict) -> dict:
    return {
        "id": _text(row.get("id")),
        "title": _text(row.get("title")),
        "startDate": _text(row.get("start_date")),
        "endDate": _text(row.get("end_date")),
        "description": _text(row.get("description")),
        "location": _text(row.get("location")),
        "dateStr": _text(row.get("date_str")),
        "timeStr": _text(row.get("time_str")),
        "image_url": _text(row.get("image_url")),
        "price": _text(row.get("price")),
        "instructor": _text(row.get("instructor")),
        "registration": _text(row.get("registration")),
    }


def _program_from_row(row: dict) -> dict:
    return {
        "sheet": _text(row.get("sheet")),
        "program": _text(row.get("program")),
        "program_id": _text(row.get("program_id")),
        "date_range": _text(row.get("date_range")),
        "time": _text(row.get("time")),
        "location": _text(row.get("location")),
        "class_room": _text(row.get("class_room")),
        "instructor": _text(row.get("instructor")),
        "program_status": _text(row.get("program_status")),
        "class_cancellation": _text(row.get("class_cancellation")),
        "note": _text(row.get("note")),
        "withdrawal": _text(row.get("withdrawal")),
        "description": _text(row.get("description")),
        "fee": _text(row.get("fee")),
        "session": _text(row.get("session")),
    }


def assign_event_ids(events: list) -> list:
    """Give every event a stable id so later edits and deletes match the same row."""
    prepared = []
    seen = set()
    for event in events:
        item = dict(event)
        base = _text(item.get("id")).strip()
        if not base:
            raw = "|".join([
                _text(item.get("title")),
                _text(item.get("startDate")),
                _text(item.get("endDate")),
                _text(item.get("location")),
            ])
            base = "evt_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
        candidate = base
        suffix = 2
        while candidate in seen:
            candidate = f"{base}_{suffix}"
            suffix += 1
        seen.add(candidate)
        item["id"] = candidate
        prepared.append(item)
    return prepared


def fetch_events() -> list:
    rows = _fetch_all("events", "sort_order.asc,id.asc")
    return [_event_from_row(row) for row in rows]


def _chunks(items, size=200):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _delete_ids(table: str, ids: list) -> None:
    for chunk in _chunks([str(value) for value in ids], 100):
        _request(
            "DELETE",
            f"{_url()}/rest/v1/{table}",
            f"Removing old {table} rows",
            params={"id": f"in.({','.join(chunk)})"},
            headers=_headers({"Prefer": "return=minimal"}),
        )


def _insert_rows(table: str, rows: list, on_conflict: str = "") -> list:
    saved = []
    params = {"on_conflict": on_conflict} if on_conflict else None
    prefer = "return=representation"
    if on_conflict:
        prefer = "resolution=merge-duplicates,return=representation"
    for chunk in _chunks(rows, 200):
        response = _request(
            "POST",
            f"{_url()}/rest/v1/{table}",
            f"Saving {table}",
            params=params,
            json=chunk,
            headers=_headers({"Prefer": prefer}),
        )
        body = response.json()
        if isinstance(body, list):
            saved.extend(body)
    return saved


def replace_events(events: list, allow_empty: bool = False) -> int:
    prepared = assign_event_ids(events)
    payload = []
    for index, event in enumerate(prepared):
        payload.append({
            "id": event["id"],
            "title": _text(event.get("title")),
            "start_date": _text(event.get("startDate")),
            "end_date": _text(event.get("endDate")),
            "description": _text(event.get("description")),
            "location": _text(event.get("location")),
            "date_str": _text(event.get("dateStr")),
            "time_str": _text(event.get("timeStr")),
            "image_url": _text(event.get("image_url")),
            "price": _text(event.get("price")),
            "instructor": _text(event.get("instructor")),
            "registration": _text(event.get("registration")),
            "sort_order": index,
        })
    if not payload:
        if not allow_empty:
            return 0
        existing = _fetch_all("events", "id.asc")
        _delete_ids("events", [row.get("id") for row in existing])
        return 0

    _insert_rows("events", payload, on_conflict="id")
    keep_ids = {row["id"] for row in payload}
    existing = _fetch_all("events", "id.asc")
    extras = [row.get("id") for row in existing if row.get("id") not in keep_ids]
    if extras:
        _delete_ids("events", extras)
    saved = fetch_events()
    if len(saved) != len(payload):
        raise SupabaseError(
            f"Event save verification failed: database has {len(saved)} rows, source has {len(payload)}"
        )
    return len(saved)


def fetch_programs() -> list:
    rows = _fetch_all("programs", "id.asc")
    return [_program_from_row(row) for row in rows]


def replace_programs(programs: list) -> int:
    if not programs:
        raise SupabaseError("Refusing to replace programs with an empty list")
    payload = [_program_from_row(program) for program in programs]
    inserted = _insert_rows("programs", payload)
    new_ids = [row.get("id") for row in inserted if row.get("id") is not None]
    if len(new_ids) != len(payload):
        if new_ids:
            _delete_ids("programs", new_ids)
        raise SupabaseError(
            f"Program save verification failed before removing older rows: saved {len(new_ids)} of {len(payload)}"
        )
    existing = _fetch_all("programs", "id.asc")
    keep_ids = {str(value) for value in new_ids}
    extras = [row.get("id") for row in existing if str(row.get("id")) not in keep_ids]
    if extras:
        _delete_ids("programs", extras)
    saved = fetch_programs()
    if len(saved) != len(payload):
        raise SupabaseError(
            f"Program save verification failed: database has {len(saved)} rows, source has {len(payload)}"
        )
    return len(saved)


def fetch_setting(key: str):
    response = _request(
        "GET",
        f"{_url()}/rest/v1/app_settings",
        f"Reading setting {key}",
        params={"select": "value", "key": f"eq.{key}"},
        headers=_headers(),
    )
    rows = response.json()
    if not rows:
        return None
    return rows[0].get("value")


def save_setting(key: str, value: dict) -> None:
    response = _request(
        "POST",
        f"{_url()}/rest/v1/app_settings",
        f"Saving setting {key}",
        params={"on_conflict": "key"},
        json={"key": key, "value": value},
        headers=_headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
    )


def programs_from_excel(file_path_or_content, withdrawal_fn: Callable[[str, str], str]) -> list:
    """Read the class workbook into the same program records the app already stores."""
    if isinstance(file_path_or_content, str):
        excel_data = pd.read_excel(file_path_or_content, sheet_name=None)
    else:
        import io
        excel_data = pd.read_excel(io.BytesIO(file_path_or_content), sheet_name=None)

    def safe_str(value):
        if pd.isna(value) or value == "nan" or value == "":
            return ""
        return str(value).strip()

    records = []
    for sheet_name, df in excel_data.items():
        first_col_name = df.columns[0] if len(df.columns) > 0 else None
        for _, row in df.iterrows():
            program = safe_str(row.get("Event", row.get("event", "")))
            program_id = safe_str(row.get("Course ID", row.get("course_id", "")))
            date_range = safe_str(row.get("Date", row.get("date", "")))
            time_value = safe_str(row.get("Time", row.get("time", "")))
            location = safe_str(row.get("Location", row.get("location", "")))
            class_room = safe_str(row.get("Facility", row.get("facility", "")))
            instructor = safe_str(row.get("Instructor", row.get("instructor", "")))
            actions = safe_str(row.get("Actions", row.get("actions", "")))
            class_cancellation = safe_str(row.get("Cancellation Date", row.get("cancellation_date", "")))
            if class_cancellation:
                class_cancellation = class_cancellation.replace(".", ",")
            program_status = "Cancelled" if actions.strip().upper() == "TRUE" else "Active"
            note = safe_str(row.get("Note", row.get("note", "")))
            description = safe_str(row.get("Description", row.get("description", "")))
            fee = safe_str(row.get("Fees", row.get("Fee", row.get("fee", row.get("fees", "")))))
            session = safe_str(row.get("Session", row.get("session", "")))
            if not session and first_col_name:
                session = safe_str(row.get(first_col_name, ""))
            if not session:
                try:
                    session = safe_str(row.iloc[0]) if hasattr(row, "iloc") else ""
                except Exception:
                    session = ""
            if not any([program, program_id, date_range, location, instructor]):
                continue
            records.append({
                "sheet": sheet_name,
                "program": program,
                "program_id": program_id,
                "date_range": date_range,
                "time": time_value,
                "location": location,
                "class_room": class_room,
                "instructor": instructor,
                "program_status": program_status,
                "class_cancellation": class_cancellation,
                "note": note,
                "withdrawal": withdrawal_fn(date_range, class_cancellation),
                "description": description,
                "fee": fee,
                "session": session,
            })
    return records
