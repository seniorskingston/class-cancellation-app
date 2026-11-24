"""Read published events from the Seniors Kingston website.

This catalog is separate from the class list and from the events uploaded
through the existing page. A sync adds new website events and updates the
fields that come from the website. It does not delete anything, and it does
not change class cancellations.
"""

import os
from datetime import datetime, timedelta
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

import requests

SOURCE = "https://cms.seniorskingston.ca/items/Events"
ZONE = ZoneInfo("America/Toronto")
PAGE_SIZE = 100
SETTING_KEY = "website_events"
WEBSITE_FIELDS = (
    "title",
    "start_date",
    "end_date",
    "status",
    "address",
    "price",
    "description",
    "categories",
    "thumbnail",
    "pdfs",
)


class WebsiteEventsError(Exception):
    pass


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        if tag in ("p", "div", "br", "li", "tr", "h1", "h2", "h3"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        if tag in ("p", "div", "li", "tr", "h1", "h2", "h3"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def sanitize_html(value) -> str:
    parser = _TextExtractor()
    parser.feed(str(value or ""))
    parser.close()
    lines = [" ".join(part.split()) for part in "".join(parser.parts).splitlines()]
    return "\n".join(line for line in lines if line).strip()


def kingston_now(moment=None) -> datetime:
    if moment is None:
        return datetime.now(ZONE)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=ZONE)
    return moment.astimezone(ZONE)


def month_window(moment=None):
    """Current month plus the following month, inclusive start and exclusive end."""
    now = kingston_now(moment)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    index = start.year * 12 + (start.month - 1) + 2
    end = start.replace(year=index // 12, month=(index % 12) + 1)
    return start, end


def window_label(start: datetime, end: datetime) -> str:
    last_day = end - timedelta(days=1)
    return (
        f"{start.strftime('%B')} {start.day}, {start.year} through "
        f"{last_day.strftime('%B')} {last_day.day}, {last_day.year}"
    )


def _asset_url(value) -> str:
    if isinstance(value, dict):
        nested = value.get("directus_files_id") or value.get("id") or ""
        return _asset_url(nested)
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return f"https://cms.seniorskingston.ca/assets/{text}"


def _pdfs(value) -> list:
    if not isinstance(value, list):
        return []
    urls = []
    for item in value:
        url = _asset_url(item)
        if url:
            urls.append(url)
    return urls


def _categories(value) -> list:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def map_row(row: dict) -> dict:
    external_id = str(row.get("id") or "").strip()
    if not external_id:
        raise WebsiteEventsError("A website event arrived without an id")
    title = str(row.get("Title") or "").strip()
    if not title:
        raise WebsiteEventsError(f"Website event {external_id} has no title")
    start_date = str(row.get("Start_Date") or "").strip()
    if not start_date:
        raise WebsiteEventsError(f"Website event {external_id} has no start date")
    return {
        "external_id": external_id,
        "title": title,
        "start_date": start_date,
        "end_date": str(row.get("End_Date") or "").strip(),
        "status": str(row.get("Status") or "").strip(),
        "address": str(row.get("Address") or "").strip(),
        "price": str(row.get("Price") or "").strip(),
        "description": sanitize_html(row.get("Description")),
        "categories": _categories(row.get("Categories")),
        "thumbnail": _asset_url(row.get("Thumbnail")),
        "pdfs": _pdfs(row.get("Pdfs")),
    }


def _owned(record: dict) -> dict:
    return {field: record.get(field) for field in WEBSITE_FIELDS}


def empty_catalog() -> dict:
    return {
        "events": {},
        "automatic": False,
        "time": "08:00",
        "last_success": "",
        "last_attempt": "",
        "counts": {"new": 0, "updated": 0, "unchanged": 0, "failed": 0},
        "errors": [],
        "window_label": "",
    }


def normalize_catalog(value) -> dict:
    catalog = empty_catalog()
    if isinstance(value, dict):
        events = value.get("events")
        if isinstance(events, dict):
            catalog["events"] = events
        catalog["automatic"] = bool(value.get("automatic"))
        clock = str(value.get("time") or "08:00")
        catalog["time"] = clock if len(clock) == 5 and clock[2] == ":" else "08:00"
        catalog["last_success"] = str(value.get("last_success") or "")
        catalog["last_attempt"] = str(value.get("last_attempt") or "")
        counts = value.get("counts") if isinstance(value.get("counts"), dict) else {}
        catalog["counts"] = {
            "new": int(counts.get("new") or 0),
            "updated": int(counts.get("updated") or 0),
            "unchanged": int(counts.get("unchanged") or 0),
            "failed": int(counts.get("failed") or 0),
        }
        errors = value.get("errors")
        catalog["errors"] = [str(item) for item in errors] if isinstance(errors, list) else []
        catalog["window_label"] = str(value.get("window_label") or "")
    return catalog


def merge_records(catalog: dict, records: list, failed: list, when: datetime) -> dict:
    """Add or update website-owned fields. Keep every existing record."""
    updated = normalize_catalog(catalog)
    events = dict(updated["events"])
    counts = {"new": 0, "updated": 0, "unchanged": 0, "failed": len(failed)}
    for record in records:
        external_id = record["external_id"]
        previous = events.get(external_id)
        manual_note = ""
        if isinstance(previous, dict):
            manual_note = str(previous.get("manual_note") or "")
        stored = dict(record)
        stored["manual_note"] = manual_note
        if not isinstance(previous, dict):
            counts["new"] += 1
        elif _owned(previous) != _owned(stored):
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1
        events[external_id] = stored
    start, end = month_window(when)
    updated["events"] = events
    updated["counts"] = counts
    updated["errors"] = failed
    updated["last_attempt"] = when.isoformat()
    updated["last_success"] = when.isoformat()
    updated["window_label"] = window_label(start, end)
    return updated


def _event_key(title, start) -> tuple:
    return (str(title or "").strip().lower(), str(start or "")[:10])


def calendar_event(record: dict) -> dict:
    """Shape a website event the way the public calendar already reads events."""
    start = str(record.get("start_date") or "").replace("Z", "")
    end = str(record.get("end_date") or "").replace("Z", "") or start
    try:
        parsed = datetime.fromisoformat(start)
    except ValueError:
        parsed = None
    time_str = ""
    date_str = start
    if parsed is not None:
        hour = parsed.strftime("%I").lstrip("0") or "12"
        time_str = f"{hour}:{parsed.strftime('%M %p').lower()}"
        date_str = f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}, {time_str}"
    return {
        "id": f"web-{record.get('external_id')}",
        "title": record.get("title") or "",
        "startDate": start,
        "endDate": end,
        "description": record.get("description") or "",
        "location": record.get("address") or "",
        "dateStr": date_str,
        "timeStr": time_str,
        "image_url": record.get("thumbnail") or "/logo192.png",
        "price": record.get("price") or "",
        "instructor": "",
        "registration": "",
    }


def merge_for_calendar(stored_events, catalog: dict, moment=None) -> list:
    """Show website events on the calendar and keep uploaded events that are not the same."""
    website_items = []
    keys = set()
    for record in events_in_window(catalog, moment):
        item = calendar_event(record)
        keys.add(_event_key(item["title"], item["startDate"]))
        website_items.append(item)
    kept = []
    for event in stored_events or []:
        if _event_key(event.get("title"), event.get("startDate")) in keys:
            continue
        kept.append(event)
    return kept + website_items


def events_in_window(catalog: dict, moment=None) -> list:
    start, end = month_window(moment)
    start_text = start.strftime("%Y-%m-%dT%H:%M:%S")
    end_text = end.strftime("%Y-%m-%dT%H:%M:%S")
    chosen = []
    for record in normalize_catalog(catalog)["events"].values():
        if not isinstance(record, dict):
            continue
        stamp = str(record.get("start_date") or "")
        if start_text <= stamp < end_text:
            chosen.append(record)
    chosen.sort(key=lambda item: (item.get("start_date") or "", item.get("title") or ""))
    return chosen


def fetch_rows(start: datetime, end: datetime, get=None) -> list:
    """Read every published event in the window. Optional token stays on the server."""
    getter = get or requests.get
    token = os.getenv("WEBSITE_EVENTS_TOKEN") or os.getenv("DIRECTUS_TOKEN") or ""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    source = os.getenv("WEBSITE_EVENTS_API") or SOURCE
    fields = "id,Title,Start_Date,End_Date,Status,Address,Price,Description,Categories,Thumbnail,Pdfs"
    rows = []
    offset = 0
    while offset < 5000:
        response = getter(
            source,
            params={
                "limit": PAGE_SIZE,
                "offset": offset,
                "sort": "Start_Date",
                "fields": fields,
                "filter[Status][_eq]": "published",
                "filter[Start_Date][_gte]": start.strftime("%Y-%m-%dT%H:%M:%S"),
                "filter[Start_Date][_lt]": end.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        page = response.json().get("data") or []
        if not isinstance(page, list):
            raise WebsiteEventsError("The website did not return an event list")
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE
    return rows


def _map_rows(rows: list):
    records = []
    failed = []
    for row in rows:
        try:
            records.append(map_row(row if isinstance(row, dict) else {}))
        except WebsiteEventsError as exc:
            failed.append(str(exc))
    return records, failed


def preview(catalog: dict, rows: list, moment=None) -> dict:
    """Show what a sync would do without saving."""
    when = kingston_now(moment)
    records, failed = _map_rows(rows)
    proposed = merge_records(catalog, records, failed, when)
    status = public_status(catalog, when, saved=False)
    status["counts"] = proposed["counts"]
    status["errors"] = failed
    status["events"] = events_in_window(proposed, when)
    status["window_label"] = proposed["window_label"]
    return status


def sync_catalog(catalog: dict, rows: list, moment=None) -> dict:
    when = kingston_now(moment)
    records, failed = _map_rows(rows)
    if not records and failed:
        updated = normalize_catalog(catalog)
        updated["last_attempt"] = when.isoformat()
        updated["errors"] = failed
        updated["counts"] = {
            "new": 0,
            "updated": 0,
            "unchanged": 0,
            "failed": len(failed),
        }
        return updated
    return merge_records(catalog, records, failed, when)


def public_status(catalog: dict, moment=None, saved=True) -> dict:
    when = kingston_now(moment)
    start, end = month_window(when)
    stored = normalize_catalog(catalog)
    return {
        "saved": saved,
        "automatic": stored["automatic"],
        "time": stored["time"],
        "last_success": stored["last_success"],
        "last_attempt": stored["last_attempt"],
        "counts": stored["counts"],
        "errors": stored["errors"],
        "window_label": window_label(start, end),
        "events": events_in_window(stored, when),
    }


def clean_schedule(value: dict) -> dict:
    clock = str((value or {}).get("time") or "08:00").strip()
    hour, _, minute = clock.partition(":")
    if not (hour.isdigit() and minute.isdigit()):
        clock = "08:00"
    else:
        hour_number = int(hour)
        minute_number = int(minute)
        if hour_number > 23 or minute_number > 59:
            clock = "08:00"
        else:
            clock = f"{hour_number:02d}:{minute_number:02d}"
    return {"automatic": bool((value or {}).get("automatic")), "time": clock}


def automatic_is_due(catalog: dict, moment=None) -> bool:
    stored = normalize_catalog(catalog)
    if not stored["automatic"]:
        return False
    when = kingston_now(moment)
    hour, minute = stored["time"].split(":")
    scheduled = when.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    if when < scheduled:
        return False
    last = stored["last_success"]
    if last:
        try:
            last_when = datetime.fromisoformat(last)
        except ValueError:
            last_when = None
        if last_when is not None and kingston_now(last_when).date() == when.date():
            return False
    return True
