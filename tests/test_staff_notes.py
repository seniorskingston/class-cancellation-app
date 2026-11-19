import unittest

import staff_notes


class StaffNoteTests(unittest.TestCase):
    def test_search_finds_a_program_number_or_name(self):
        programs = [
            {"program": "Life Drawing", "program_id": "30375.0", "sheet": "Monday", "session": "2"},
            {"program": "Travel Club", "program_id": "31039", "sheet": "Monday", "session": "1"},
        ]
        by_number = staff_notes.search_programs(programs, "30375")
        by_name = staff_notes.search_programs(programs, "drawing")
        self.assertEqual(len(by_number), 1)
        self.assertEqual(by_number[0]["program"], "Life Drawing")
        self.assertEqual(len(by_name), 1)

    def test_save_matches_one_day_and_session(self):
        programs = [
            {"id": 1, "program_id": "30375", "sheet": "Monday", "session": "2"},
            {"id": 2, "program_id": "30375", "sheet": "Friday", "session": "2"},
        ]
        monday = staff_notes.matching_class(programs, "30375.0", "Monday", "2")
        self.assertEqual([row["id"] for row in monday], [1])
        self.assertEqual(staff_notes.matching_class(programs, "30375", "Wednesday", "2"), [])


if __name__ == "__main__":
    unittest.main()
