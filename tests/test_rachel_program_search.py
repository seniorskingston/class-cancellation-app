import unittest

import rachel_program_search


def _row(**kwargs):
    base = {
        "program": "Movement in a Chair",
        "program_id": "41001",
        "sheet": "Tuesday",
        "time": "09:30 AM - 10:15 AM",
        "location": "SCW – Seniors Centre West",
        "class_room": "",
        "description": "Gentle chair exercise for people who want to move while seated.",
        "program_status": "Active",
    }
    base.update(kwargs)
    return base


class RachelProgramSearchTests(unittest.TestCase):
    def test_gentle_tuesday_morning_at_west_uses_the_description(self):
        other = _row(program="Zumba Gold", program_id="30581", sheet="Wednesday", time="11:00 AM - 12:00 PM", description="An aerobic fitness program")
        result = rachel_program_search.answer(
            "I want a gentle exercise class on Tuesday mornings at Seniors Centre West",
            [_row(), other],
        )
        self.assertIn("41001", result["answer"])
        self.assertNotIn("30581", result["answer"])
        self.assertIn("chair", result["answer"].lower())

    def test_different_words_match_a_balance_description(self):
        hits = rachel_program_search.search_programs(
            "Help me stay steady on my feet",
            [_row(program="Supported Walking", program_id="41002", description="Practice balance and stability with support nearby.", sheet="Wednesday")],
        )
        self.assertEqual(hits[0]["level"], "meaning")

    def test_painting_without_beginner_is_only_related(self):
        hits = rachel_program_search.search_programs(
            "No painting experience",
            [_row(program="Watercolour Studio", program_id="41003", description="Explore watercolour painting with a focus on colour and composition.", sheet="Wednesday")],
        )
        self.assertEqual(hits[0]["level"], "related")
        self.assertIn("does not say", hits[0]["reason"])

    def test_apple_phone_matches_iphone_description(self):
        hits = rachel_program_search.search_programs(
            "Learn to use an Apple phone",
            [_row(program="Phone Skills", program_id="41004", description="Learn the buttons and settings on an iPhone.", sheet="Wednesday")],
        )
        self.assertEqual(hits[0]["level"], "meaning")

    def test_cancelled_match_says_cancelled(self):
        hits = rachel_program_search.search_programs(
            "Exercises while sitting",
            [_row(program="Chair Movement", program_id="41005", description="Seated exercise using a chair.", program_status="Cancelled", sheet="Wednesday")],
        )
        self.assertIn("cancelled", hits[0]["reason"].lower())

    def test_html_description_is_plain_text(self):
        hits = rachel_program_search.search_programs(
            "balance",
            [_row(description="<p>Chair <b>exercise</b> for balance.</p>", sheet="Wednesday")],
        )
        self.assertNotIn("<", hits[0]["excerpt"])
        self.assertIn("balance", hits[0]["excerpt"].lower())


if __name__ == "__main__":
    unittest.main()
