import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

import perfectmind_sync

KINGSTON = ZoneInfo("America/Toronto")


class PerfectMindSyncTests(unittest.TestCase):
    def test_session_number_reads_the_perfectmind_label(self):
        self.assertEqual(perfectmind_sync.session_number("Session 2 - 2026"), "2")
        self.assertEqual(perfectmind_sync.session_number("1"), "1")
        self.assertEqual(perfectmind_sync.session_number("2.0"), "2")

    def test_saved_notes_stay_with_the_same_class(self):
        incoming = [{
            "sheet": "Monday",
            "program": "Exercise",
            "program_id": "30962",
            "date_range": "Mon 23/11/2026 - Fri 12/02/2027",
            "time": "08:30 AM - 09:15 AM",
            "location": "OL- Online",
            "class_room": "",
            "instructor": "Cheryl Descent",
            "program_status": "Active",
            "class_cancellation": "",
            "note": "",
            "description": "Online",
            "fee": "$104.40",
            "session": "Session 2 - 2026",
        }]
        existing = [{
            "sheet": "Monday",
            "program_id": "30962",
            "session": "2",
            "note": "Room change",
            "class_cancellation": "Dec 2, 2026",
            "program_status": "Cancelled",
        }]

        merged = perfectmind_sync.merge_staff_fields(incoming, existing, lambda dates, cancelled: "Yes")

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["session"], "2")
        self.assertEqual(merged[0]["note"], "Room change")
        self.assertEqual(merged[0]["class_cancellation"], "Dec 2, 2026")
        self.assertEqual(merged[0]["program_status"], "Cancelled")
        self.assertEqual(merged[0]["withdrawal"], "Yes")

    def test_picked_session_labels_are_cleaned(self):
        self.assertEqual(
            perfectmind_sync.normalize_seasons(["Session 1-2028", "1-2028", "Monday"]),
            ["Session 1-2028"],
        )

    def test_other_sessions_stay_when_one_session_is_replaced(self):
        existing = [
            {"program_id": "1", "session": "1", "sheet": "Monday"},
            {"program_id": "2", "session": "2", "sheet": "Monday", "class_cancellation": "2026-11-19"},
            {"program_id": "3", "session": "2", "sheet": "Tuesday"},
        ]
        incoming = [{"program_id": "9", "session": "2", "sheet": "Tuesday"}]
        combined = perfectmind_sync.combine_with_other_sessions(existing, incoming)
        self.assertEqual([row["program_id"] for row in combined], ["9", "1", "2"])

    def test_daily_schedule_runs_after_its_time(self):
        morning = datetime(2026, 11, 19, 7, 30, tzinfo=KINGSTON)
        afternoon = datetime(2026, 11, 19, 9, 0, tzinfo=KINGSTON)
        schedule = {"frequency": "daily", "time": "08:00", "seasons": ["Session 1-2026"]}
        self.assertFalse(perfectmind_sync.schedule_is_due(schedule, morning))
        self.assertTrue(perfectmind_sync.schedule_is_due(schedule, afternoon))
        done = perfectmind_sync.mark_schedule_ran(schedule, afternoon)
        self.assertFalse(perfectmind_sync.schedule_is_due(done, afternoon))

    def test_every_twelve_hours_uses_the_times_entered(self):
        before = datetime(2026, 11, 19, 7, 0, tzinfo=KINGSTON)
        morning = datetime(2026, 11, 19, 8, 15, tzinfo=KINGSTON)
        evening = datetime(2026, 11, 19, 20, 0, tzinfo=KINGSTON)
        schedule = {
            "frequency": "interval",
            "interval_hours": 12,
            "window_start": "08:00",
            "window_end": "20:00",
            "seasons": ["Session 1-2028"],
        }
        self.assertFalse(perfectmind_sync.schedule_is_due(schedule, before))
        self.assertTrue(perfectmind_sync.schedule_is_due(schedule, morning))
        ran = perfectmind_sync.mark_schedule_ran(schedule, morning)
        self.assertFalse(perfectmind_sync.schedule_is_due(ran, morning))
        self.assertTrue(perfectmind_sync.schedule_is_due(ran, evening))

    def test_a_read_lists_changes_for_the_same_session(self):
        existing = [
            {"program_id": "30962", "session": "2", "sheet": "Monday", "program": "Exercise", "time": "08:30 AM - 09:15 AM", "class_cancellation": "2026-11-19"},
            {"program_id": "30913", "session": "2", "sheet": "Tuesday", "program": "Pickleball", "time": "08:30 AM - 10:30 AM"},
            {"program_id": "100", "session": "1", "sheet": "Monday", "program": "Travel", "time": "10:00 AM"},
        ]
        incoming = [
            {"program_id": "30962", "session": "Session 2 - 2026", "sheet": "Monday", "program": "Exercise", "time": "09:00 AM - 09:45 AM"},
            {"program_id": "40000", "session": "2", "sheet": "Monday", "program": "New Class", "time": "01:00 PM"},
        ]
        changes = perfectmind_sync.session_changes(existing, incoming)
        self.assertTrue(any(line.startswith("Changed Monday Session 2 Exercise 30962") and "Time was" in line for line in changes))
        self.assertTrue(any(line.startswith("Added Monday Session 2 New Class 40000") for line in changes))
        self.assertFalse(any("Pickleball" in line or "Travel" in line for line in changes))
        self.assertFalse(any("2026-11-19" in line for line in changes))

    def test_weekend_can_be_turned_off(self):
        saturday = datetime(2026, 11, 21, 8, 5, tzinfo=KINGSTON)
        monday = datetime(2026, 11, 23, 8, 5, tzinfo=KINGSTON)
        schedule = {"frequency": "daily", "time": "08:00", "skip_weekends": True, "seasons": ["Session 2-2026"]}
        self.assertFalse(perfectmind_sync.schedule_is_due(schedule, saturday))
        self.assertTrue(perfectmind_sync.schedule_is_due(schedule, monday))

    def test_hidden_session_stays_out_of_the_chosen_list(self):
        self.assertTrue(perfectmind_sync.session_matches("2", ["Session 2-2026"]))
        self.assertFalse(perfectmind_sync.session_matches("1", ["Session 2-2026"]))
        self.assertFalse(perfectmind_sync.session_matches("1-2026", ["Session 1-2028"]))

    def test_weekly_schedule_matches_the_chosen_day(self):
        monday = datetime(2026, 11, 16, 8, 5, tzinfo=KINGSTON)
        tuesday = datetime(2026, 11, 17, 8, 5, tzinfo=KINGSTON)
        schedule = {"frequency": "weekly", "weekday": "monday", "time": "08:00", "seasons": ["Session 2-2026"]}
        self.assertTrue(perfectmind_sync.schedule_is_due(schedule, monday))
        ran = perfectmind_sync.mark_schedule_ran(schedule, monday)
        self.assertFalse(perfectmind_sync.schedule_is_due(ran, tuesday))

    def _row(self, **extra):
        row = {
            "sheet": "Monday",
            "program": "Chair Yoga",
            "program_id": "30001",
            "date_range": "Mon 23/11/2026 - Mon 08/02/2027",
            "time": "9:00 AM - 10:00 AM",
            "location": "SC - Seniors Centre",
            "class_room": "Room A",
            "instructor": "Ada",
            "program_status": "Active",
            "class_cancellation": "",
            "note": "keep me",
            "fee": "$10.00",
            "session": "2",
        }
        row.update(extra)
        return row

    def test_guide_cases(self):
        original = [self._row()]
        later = [self._row(time="10:00 AM - 11:00 AM")]
        same = perfectmind_sync.compare_guide(later, later, "Tuesday")
        self.assertEqual(same["message"], perfectmind_sync.NO_GUIDE_UPDATES)
        moved = perfectmind_sync.compare_guide(original, later, "Wednesday")
        self.assertEqual(moved["counts"]["changes"], 1)
        self.assertEqual(moved["changes"][0]["fields"][0]["before"], "9:00 AM - 10:00 AM")
        self.assertEqual(moved["changes"][0]["fields"][0]["after"], "10:00 AM - 11:00 AM")
        back = perfectmind_sync.compare_guide(original, original)
        self.assertEqual(back["counts"]["total"], 0)
        formatting = perfectmind_sync.compare_guide(
            [self._row(time="09:00 AM - 10:00 AM", fee="$10")],
            [self._row(time="9:00 am - 10:00 am", fee="$10.00")],
        )
        self.assertEqual(formatting["counts"]["total"], 0)
        added = perfectmind_sync.compare_guide([], [self._row(program_id="30002", program="New Class")])
        self.assertEqual(added["counts"]["additions"], 1)
        added_again = perfectmind_sync.compare_guide(
            [],
            [self._row(program_id="30002", program="New Class", time="11:00 AM - 12:00 PM")],
        )
        self.assertEqual(added_again["counts"]["additions"], 1)
        self.assertEqual(added_again["counts"]["changes"], 0)
        self.assertEqual(added_again["additions"][0]["time"], "11:00 AM - 12:00 PM")
        cancelled_new = perfectmind_sync.compare_guide(
            [],
            [self._row(program_id="30002", program="New Class", program_status="Cancelled")],
        )
        self.assertEqual(cancelled_new["counts"]["cancelled"], 1)
        self.assertEqual(cancelled_new["counts"]["additions"], 0)
        whole = perfectmind_sync.compare_guide(original, [self._row(program_status="Cancelled")])
        self.assertEqual(whole["counts"]["cancelled"], 1)
        self.assertEqual(whole["counts"]["changes"], 0)
        date_only = perfectmind_sync.compare_guide(original, [self._row(class_cancellation="2026-11-29")])
        self.assertEqual(date_only["counts"]["total"], 0)
        reinstated = perfectmind_sync.latest_report(
            [self._row(program_status="Cancelled")],
            [self._row(program_status="Active")],
            "Thursday",
        )
        self.assertEqual(reinstated["counts"]["changes"], 1)
        self.assertEqual(reinstated["changes"][0]["fields"][0]["summary"], "Status changed")
        many = perfectmind_sync.compare_guide(
            original,
            [self._row(time="11:00 AM - 12:00 PM", instructor="Bea", location="SC - Seniors Centre")],
        )
        self.assertEqual(len(many["changes"]), 1)
        self.assertEqual({item["label"] for item in many["changes"][0]["fields"]}, {"Time", "Instructor"})
        room = perfectmind_sync.compare_guide(original, [self._row(class_room="Room B")])
        self.assertEqual(room["changes"][0]["fields"][0]["label"], "Room")
        other_session = perfectmind_sync.rows_for_session(
            [self._row(), self._row(session="1", program_id="9")],
            "Session 2-2026",
        )
        self.assertEqual([row["program_id"] for row in other_session], ["30001"])
        first = perfectmind_sync.latest_report([], [self._row(), self._row(program_id="2")], "First")
        self.assertEqual(first["counts"]["total"], 0)
        self.assertEqual(first["message"], perfectmind_sync.NO_NEW_UPDATES)
        quiet = perfectmind_sync.latest_report(original, original, "Run 2")
        self.assertEqual(quiet["message"], perfectmind_sync.NO_NEW_UPDATES)
        step = perfectmind_sync.latest_report(later, [self._row(time="11:00 AM - 12:00 PM")], "Run 3")
        self.assertEqual(step["changes"][0]["fields"][0]["before"], "10:00 AM - 11:00 AM")
        self.assertEqual(step["changes"][0]["fields"][0]["after"], "11:00 AM - 12:00 PM")
        hidden = perfectmind_sync.compare_guide(
            [],
            [
                self._row(program_id="28154", program="Request to Withdraw from Program"),
                self._row(program_id="28154", program="Request to Withdraw from Program", program_status="Cancelled", sheet="Tuesday"),
                self._row(program_id="30002", program="New Class"),
            ],
        )
        self.assertEqual(hidden["counts"]["additions"], 1)
        self.assertEqual(hidden["counts"]["cancelled"], 0)
        self.assertEqual(hidden["additions"][0]["program_id"], "30002")
        changed_hidden = perfectmind_sync.compare_guide(
            [self._row(program_id="28154", program="Request to Withdraw from Program", time="9:00 AM - 10:00 AM")],
            [self._row(program_id="28154", program="Request to Withdraw from Program", time="1:00 PM - 2:00 PM")],
        )
        self.assertEqual(changed_hidden["counts"]["total"], 0)

    def test_admin_can_add_a_program_guide_update(self):
        added = perfectmind_sync.add_manual_update([], {
            "kind": "addition",
            "program": "New Class",
            "program_id": "40000",
            "session": "Session 2-2026",
            "day": "Monday",
            "time": "1:00 PM - 2:00 PM",
            "note": "Starts in January",
        }, "November 25, 2026", "item-1")
        self.assertEqual(added["kind"], "addition")
        report = perfectmind_sync.merge_manual_updates(
            perfectmind_sync.compare_guide([], []),
            [added],
        )
        self.assertEqual(report["counts"]["additions"], 1)
        self.assertEqual(report["additions"][0]["note"], "Starts in January")
        with self.assertRaises(ValueError):
            perfectmind_sync.add_manual_update([added], {
                "kind": "change",
                "program": "New Class",
                "program_id": "40000",
                "session": "2",
                "day": "Monday",
                "note": "Time changed",
            }, "November 25, 2026", "item-2")
        changed = perfectmind_sync.manual_update_item({
            "kind": "change",
            "program": "Exercise",
            "program_id": "30962",
            "session": "2",
            "day": "Tuesday",
            "time": "10:00 AM - 11:00 AM",
            "before_time": "9:00 AM - 10:00 AM",
        }, "November 25, 2026", "item-3")
        self.assertEqual(changed["fields"][0]["label"], "Time")
        automatic = perfectmind_sync.compare_guide(
            [],
            [self._row(program_id="30962", program="Exercise", sheet="Tuesday")],
        )
        merged = perfectmind_sync.merge_manual_updates(automatic, [changed])
        self.assertEqual(merged["counts"]["additions"], 0)
        self.assertEqual(merged["counts"]["changes"], 1)
        self.assertEqual(merged["changes"][0]["source"], "admin")
        with self.assertRaises(ValueError):
            perfectmind_sync.manual_update_item({
                "kind": "change",
                "program": "Exercise",
                "program_id": "30962",
                "session": "2",
                "day": "Tuesday",
            }, "November 25, 2026", "item-4")


if __name__ == "__main__":
    unittest.main()
