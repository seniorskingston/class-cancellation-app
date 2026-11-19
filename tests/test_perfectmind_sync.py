import unittest

import perfectmind_sync


class PerfectMindSyncTests(unittest.TestCase):
    def test_session_number_reads_the_perfectmind_label(self):
        self.assertEqual(perfectmind_sync.session_number("Session 2 - 2026"), "2")
        self.assertEqual(perfectmind_sync.session_number("1"), "1")

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
            perfectmind_sync.normalize_seasons(["Session 2 - 2026", "session 2-2026", "Monday"]),
            ["Session 2-2026"],
        )

    def test_other_sessions_stay_when_one_session_is_replaced(self):
        existing = [
            {"program_id": "1", "session": "1", "sheet": "Monday"},
            {"program_id": "2", "session": "2", "sheet": "Monday"},
        ]
        incoming = [{"program_id": "9", "session": "2", "sheet": "Tuesday"}]
        combined = perfectmind_sync.combine_with_other_sessions(existing, incoming)
        self.assertEqual([row["program_id"] for row in combined], ["9", "1"])


if __name__ == "__main__":
    unittest.main()
