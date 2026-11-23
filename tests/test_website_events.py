from datetime import datetime
from zoneinfo import ZoneInfo

import website_events

ZONE = ZoneInfo("America/Toronto")


def _row(event_id, title="Open House", start="2026-11-21T10:00:00", **extra):
    item = {
        "id": event_id,
        "Title": title,
        "Start_Date": start,
        "End_Date": "2026-11-21T12:00:00",
        "Status": "published",
        "Address": "56 Francis St",
        "Price": "Free",
        "Description": "<p>Hello</p><script>alert(1)</script>",
        "Categories": ["Event"],
        "Thumbnail": "abc",
        "Pdfs": [],
    }
    item.update(extra)
    return item


def test_november_window_includes_december_only():
    start, end = website_events.month_window(datetime(2026, 11, 23, 15, tzinfo=ZONE))
    assert start.strftime("%Y-%m-%d") == "2026-11-01"
    assert end.strftime("%Y-%m-%d") == "2027-01-01"
    assert "December 31, 2026" in website_events.window_label(start, end)


def test_december_switches_to_january():
    start, end = website_events.month_window(datetime(2026, 12, 1, 0, 30, tzinfo=ZONE))
    assert start.strftime("%Y-%m-%d") == "2026-12-01"
    assert end.strftime("%Y-%m-%d") == "2027-02-01"


def test_description_drops_script_and_keeps_text():
    text = website_events.sanitize_html("<p>Hello <b>there</b></p><script>alert(1)</script>")
    assert text == "Hello there"
    assert "script" not in text
    assert "alert" not in text


def test_sync_adds_updates_and_keeps_old_and_manual_note():
    when = datetime(2026, 11, 23, 9, tzinfo=ZONE)
    first = website_events.sync_catalog({}, [_row(59)], when)
    first["events"]["59"]["manual_note"] = "Staff added this"
    first["events"]["10"] = {
        "external_id": "10",
        "title": "Old event",
        "start_date": "2025-01-02T10:00:00",
        "end_date": "",
        "status": "published",
        "address": "",
        "price": "",
        "description": "Keep me",
        "categories": [],
        "thumbnail": "",
        "pdfs": [],
        "manual_note": "Do not erase",
    }
    second = website_events.sync_catalog(
        first,
        [_row(59, title="Holiday Fair"), _row(60, title="Concert")],
        when,
    )
    assert second["counts"] == {"new": 1, "updated": 1, "unchanged": 0, "failed": 0}
    assert second["events"]["59"]["title"] == "Holiday Fair"
    assert second["events"]["59"]["manual_note"] == "Staff added this"
    assert second["events"]["10"]["title"] == "Old event"
    assert second["events"]["10"]["manual_note"] == "Do not erase"
    assert "alert" not in second["events"]["59"]["description"]


def test_unchanged_event_is_counted_and_not_duplicated():
    when = datetime(2026, 11, 23, 9, tzinfo=ZONE)
    first = website_events.sync_catalog({}, [_row(59)], when)
    second = website_events.sync_catalog(first, [_row(59)], when)
    assert second["counts"]["unchanged"] == 1
    assert second["counts"]["new"] == 0
    assert len(second["events"]) == 1


def test_bad_row_is_reported_and_good_row_is_kept():
    when = datetime(2026, 11, 23, 9, tzinfo=ZONE)
    saved = website_events.sync_catalog({}, [_row(59), {"Title": "Missing id"}], when)
    assert saved["counts"]["new"] == 1
    assert saved["counts"]["failed"] == 1
    assert saved["errors"]


def test_preview_does_not_need_the_saved_catalog_to_change():
    when = datetime(2026, 11, 23, 9, tzinfo=ZONE)
    catalog = {}
    report = website_events.preview(catalog, [_row(59)], when)
    assert report["saved"] is False
    assert report["counts"]["new"] == 1
    assert catalog == {}
    assert report["events"][0]["title"] == "Open House"
    assert report["events"][0]["thumbnail"].endswith("/assets/abc")


def test_automatic_stays_off_until_turned_on():
    when = datetime(2026, 11, 23, 9, tzinfo=ZONE)
    assert website_events.automatic_is_due({}, when) is False
    saved = website_events.normalize_catalog({"automatic": True, "time": "08:00"})
    assert website_events.automatic_is_due(saved, when) is True
    saved["last_success"] = when.isoformat()
    assert website_events.automatic_is_due(saved, when) is False


def test_fetch_follows_every_page_and_filters_start_date():
    calls = []

    class Response:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            return None

        def json(self):
            return {"data": self._data}

    def get(url, params, headers, timeout):
        calls.append(params)
        if params["offset"] == 0:
            return Response([{"id": 1}] * 100)
        return Response([{"id": 2}])

    rows = website_events.fetch_rows(
        datetime(2026, 11, 1, tzinfo=ZONE),
        datetime(2027, 1, 1, tzinfo=ZONE),
        get=get,
    )
    assert len(rows) == 101
    assert calls[0]["filter[Status][_eq]"] == "published"
    assert calls[0]["filter[Start_Date][_gte]"] == "2026-11-01T00:00:00"
    assert calls[0]["filter[Start_Date][_lt]"] == "2027-01-01T00:00:00"
    assert "Publish_On" not in calls[0]
    assert calls[1]["offset"] == 100
