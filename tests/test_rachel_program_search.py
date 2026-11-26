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

    def test_every_condition_is_required(self):
        tuesday = _row(program="Chair Movement", program_id="41011", description="Gentle chair exercise while seated.")
        wednesday = _row(program="Chair Movement", program_id="41012", sheet="Wednesday", description="Gentle chair exercise while seated.")
        other_place = _row(program="Chair Movement", program_id="41013", location="SCD – Seniors Centre Dome", description="Gentle chair exercise while seated.")
        hits = rachel_program_search.search_programs(
            "gentle exercise Tuesday morning at the west",
            [tuesday, wednesday, other_place],
        )
        self.assertEqual([hit["program_id"] for hit in hits], ["41011"])

    def test_an_extra_word_must_also_match(self):
        yoga = _row(program="Gentle Yoga", program_id="41021", description="A gentle exercise class.")
        other = _row(program="Movement in a Chair", program_id="41022", description="Gentle chair exercise for people who want to move while seated.")
        hits = rachel_program_search.search_programs("gentle yoga on Tuesday morning", [yoga, other])
        self.assertEqual([hit["program_id"] for hit in hits], ["41021"])

    def test_follow_up_keeps_the_earlier_conditions(self):
        tuesday = _row(program="Chair Movement", program_id="41031", description="Gentle chair exercise while seated.")
        wednesday = _row(program="Chair Movement", program_id="41032", sheet="Wednesday", time="09:30 AM - 10:15 AM", description="Gentle chair exercise while seated.")
        result = rachel_program_search.answer(
            "what about Wednesday?",
            [tuesday, wednesday],
            ["gentle exercise Tuesday morning at Seniors Centre West"],
        )
        self.assertIn("41032", result["answer"])
        self.assertNotIn("41031", result["answer"])
        self.assertIn("Wednesday", result["answer"])
        self.assertIn("morning", result["answer"])

    def test_a_new_question_does_not_keep_the_old_day(self):
        tuesday = _row(program="Chair Movement", program_id="41041", description="Gentle chair exercise while seated.")
        painting = _row(program="Watercolour Studio", program_id="41042", sheet="Thursday", time="01:00 PM - 03:00 PM", description="Explore watercolour painting with a focus on colour and composition.")
        result = rachel_program_search.answer(
            "watercolour painting",
            [tuesday, painting],
            ["gentle exercise Tuesday morning"],
        )
        self.assertIn("41042", result["answer"])
        self.assertNotIn("41041", result["answer"])

    def test_first_one_uses_the_previous_matches(self):
        first = _row(program="Alpha Movement", program_id="41051", description="Gentle chair exercise while seated.")
        second = _row(program="Beta Movement", program_id="41052", description="Gentle chair exercise while seated.")
        result = rachel_program_search.answer(
            "tell me more about the first one",
            [first, second],
            ["gentle exercise Tuesday morning"],
        )
        self.assertIn("41051", result["answer"])
        self.assertNotIn("41052", result["answer"])


if __name__ == "__main__":
    unittest.main()
