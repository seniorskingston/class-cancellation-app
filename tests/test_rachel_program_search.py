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

    def test_misspelled_conditions_are_corrected_and_combined(self):
        match = _row(
            program="Intermediate Aquafit",
            program_id="42001",
            sheet="Thursday",
            time="09:00 AM - 09:45 AM",
            location="SCW – Seniors Centre West",
            description="Aquafit for intermediate participants.",
        )
        other_day = _row(program="Intermediate Aquafit", program_id="42002", sheet="Tuesday", time="09:00 AM - 09:45 AM", description="Aquafit for intermediate participants.")
        other_level = _row(program="Aquafit", program_id="42003", sheet="Thursday", time="09:00 AM - 09:45 AM", description="Exercising in a pool.")
        result = rachel_program_search.answer(
            "intermedit aqufit thrsday morning at SCW",
            [match, other_day, other_level],
        )
        self.assertIn("Showing results for", result["answer"])
        self.assertIn("42001", result["answer"])
        self.assertNotIn("42002", result["answer"])
        self.assertNotIn("42003", result["answer"])
        self.assertEqual(result["conditions"], ["Thursday", "morning", "Seniors Centre West", "intermediate", "aquafit"])

    def test_follow_up_spelling_keeps_earlier_conditions(self):
        match = _row(
            program="Intermediate Aquafit",
            program_id="42011",
            sheet="Thursday",
            time="09:00 AM - 09:45 AM",
            location="SCW – Seniors Centre West",
            description="Aquafit for intermediate participants.",
        )
        beginner = _row(program="Aquafit", program_id="42012", sheet="Thursday", time="09:00 AM - 09:45 AM", location="SCW – Seniors Centre West", description="Aquafit in the pool.")
        answers = []
        history = []
        for question in ("Find Aquafit classes", "intermedit", "thrsday", "morning", "SCW"):
            result = rachel_program_search.answer(question, [match, beginner], history)
            answers.append(result)
            history.append(question)
        self.assertIn("42011", answers[-1]["answer"])
        self.assertNotIn("42012", answers[-1]["answer"])
        self.assertEqual(answers[-1]["conditions"], ["Thursday", "morning", "Seniors Centre West", "aquafit", "intermediate"])

    def test_reversed_letters_and_description_only_keyword(self):
        row = _row(program="Pool Exercise", program_id="42021", description="This class builds strength in the water.", sheet="Wednesday")
        hits = rachel_program_search.search_programs("strenght", [row])
        self.assertEqual(hits[0]["program_id"], "42021")

    def test_spaced_activity_name(self):
        row = _row(program="Tai Chi Introduction", program_id="42031", description="Slow movement.", sheet="Wednesday")
        hits = rachel_program_search.search_programs("taichi", [row])
        self.assertEqual(hits[0]["program_id"], "42031")

    def test_ambiguous_spelling_asks_instead_of_guessing(self):
        rows = [
            _row(program="Martin Painting", program_id="42041", instructor="Ann Martin", description="Painting studio.", sheet="Wednesday"),
            _row(program="Marten Drawing", program_id="42042", instructor="Ann Marten", description="Drawing studio.", sheet="Wednesday"),
        ]
        result = rachel_program_search.answer("martn", rows)
        self.assertIn("could mean", result["answer"].lower())
        self.assertNotIn("42041", result["answer"])
        self.assertNotIn("42042", result["answer"])

    def test_wrong_program_code_is_not_changed(self):
        result = rachel_program_search.answer("99999", [_row()])
        self.assertIn("No exact match was found for program code 99999", result["answer"])
        self.assertNotIn("41001", result["answer"])

    def test_remove_a_search_condition(self):
        thursday = _row(program="Aquafit", program_id="42051", sheet="Thursday", time="09:00 AM - 09:45 AM", description="Aquafit in the pool.")
        tuesday = _row(program="Aquafit", program_id="42052", sheet="Tuesday", time="09:00 AM - 09:45 AM", description="Aquafit in the pool.")
        result = rachel_program_search.answer("remove Thursday", [thursday, tuesday], ["Aquafit Thursday morning"])
        self.assertIn("42052", result["answer"])
        self.assertNotIn("Thursday", result["conditions"])

    def test_beginner_and_pilates_typos_and_instructor(self):
        pilates = _row(program="Pilates Beginner", program_id="42061", description="A mat class.", sheet="Wednesday")
        other = _row(program="Aqua Movement", program_id="42062", instructor="Lorri Naumann", description="Pool exercise.", sheet="Wednesday")
        self.assertEqual(rachel_program_search.search_programs("begginer pilats", [pilates, other])[0]["program_id"], "42061")
        instructor = rachel_program_search.search_programs("lori naumann", [pilates, other])
        self.assertEqual(instructor[0]["program_id"], "42062")

    def test_incomplete_words_in_one_search_match_both(self):
        intermediate = _row(program="Pickleball Intermediate", program_id="43001", description="Enjoy friendly games of pickleball.", sheet="Thursday", time="09:00 AM - 10:30 AM", location="SCW – Seniors Centre West")
        skills = _row(program="Pickleball Skills Development", program_id="43002", description="Drills for intermediate players who already play pickleball.", sheet="Thursday", time="09:00 AM - 10:30 AM")
        beginner = _row(program="Pickleball Beginner", program_id="43003", description="For players who are new to pickleball.", sheet="Thursday", time="09:00 AM - 10:30 AM")
        rows = [intermediate, skills, beginner]
        spelled = {hit["program_id"] for hit in rachel_program_search.search_programs("intermediate pickleball", rows)}
        for question in ("intermedia pickleball", "intermediat pickleball", "intermedit pickleball", "intermed pickleball", "intermediate picklball", "intermedia pickelball", "interm picklebal"):
            found = {hit["program_id"] for hit in rachel_program_search.search_programs(question, rows)}
            self.assertEqual(found, spelled, question)
        self.assertIn("43001", spelled)
        self.assertIn("43002", spelled)
        self.assertNotIn("43003", spelled)

    def test_intermediat_uses_the_same_programs_as_intermediate(self):
        rows = [
            _row(program="Pickleball Intermediate", program_id="45001", description="Enjoy friendly games of pickleball."),
            _row(program="Acrylic Painting Intermediate", program_id="45002", description="Painting for people with some experience."),
            _row(program="Pickleball Beginner", program_id="45003", description="For players who are new to pickleball."),
        ]
        exact = rachel_program_search.answer("intermediate", rows)
        for question in ("intermediat", "intermedia", "intermedi", "intermed", "intermedit"):
            result = rachel_program_search.answer(question, rows)
            self.assertEqual(result.get("programs"), exact.get("programs"), question)
            self.assertIn("intermediate", result["conditions"])
            self.assertNotIn("45003", result.get("programs") or [])
        exact_pickle = rachel_program_search.answer("intermediate pickleball", rows)
        for question in ("intermediat pickleball", "intermedia pickleball"):
            result = rachel_program_search.answer(question, rows)
            self.assertEqual(result.get("programs"), ["45001"], question)
            self.assertEqual(result.get("programs"), exact_pickle.get("programs"))

    def test_level_typo_does_not_match_a_different_level(self):
        rows = [
            _row(program="Pickleball Beginner", program_id="43011", description="A beginner pickleball class."),
            _row(program="Pickleball Advanced", program_id="43012", description="An advanced pickleball class."),
        ]
        beginner = {hit["program_id"] for hit in rachel_program_search.search_programs("begginer pickleball", rows)}
        advanced = {hit["program_id"] for hit in rachel_program_search.search_programs("advanc pickleball", rows)}
        self.assertEqual(beginner, {"43011"})
        self.assertEqual(advanced, {"43012"})

    def test_misspelled_follow_up_keeps_pickleball_level(self):
        match = _row(program="Pickleball Intermediate", program_id="43021", sheet="Thursday", time="09:00 AM - 10:30 AM", location="SCW – Seniors Centre West", description="Enjoy friendly games of pickleball.")
        other = _row(program="Pickleball Intermediate", program_id="43022", sheet="Tuesday", time="01:00 PM - 02:30 PM", location="SCE – Seniors Centre East", description="Enjoy friendly games of pickleball.")
        history = []
        result = None
        for question in ("intermedia pickleball", "thrsday", "mornin", "SCW"):
            result = rachel_program_search.answer(question, [match, other], history)
            history.append(question)
        self.assertIn("43021", result["answer"])
        self.assertNotIn("43022", result["answer"])
        self.assertEqual(result["conditions"], ["Thursday", "morning", "Seniors Centre West", "intermediate", "pickleball"])

    def test_singular_and_plural_match_the_same_programs(self):
        weights = _row(program="Simply Weights", program_id="44001", location="SCW – Seniors Centre West", description="Lifting weights for strength.", sheet="Wednesday", time="12:00 PM - 01:00 PM")
        described = _row(program="Simply Strength", program_id="44002", location="SC – Seniors Centre", description="This class includes lifting weights.", sheet="Thursday", time="09:00 AM - 10:00 AM")
        other = _row(program="Watercolour Studio", program_id="44003", location="SC – Seniors Centre", description="Explore watercolour painting.", sheet="Thursday", time="09:00 AM - 10:00 AM")
        rows = [weights, described, other]
        spelled = {hit["program_id"] for hit in rachel_program_search.search_programs("weights", rows)}
        for question in ("weight", "weights", "wieght", "wieghts"):
            found = {hit["program_id"] for hit in rachel_program_search.search_programs(question, rows)}
            self.assertEqual(found, spelled, question)
        self.assertEqual(spelled, {"44001", "44002"})

    def test_sc_and_scw_are_different_locations(self):
        west = _row(program="Simply Weights", program_id="44011", location="SCW – Seniors Centre West", description="Lifting weights.", sheet="Thursday", time="09:00 AM - 10:00 AM")
        centre = _row(program="Simply Strength", program_id="44012", location="SC – Seniors Centre", description="Lifting weights.", sheet="Thursday", time="09:00 AM - 10:00 AM")
        rows = [west, centre]
        at_sc = {hit["program_id"] for hit in rachel_program_search.search_programs("weights at SC", rows)}
        at_scw = {hit["program_id"] for hit in rachel_program_search.search_programs("weights at SCW", rows)}
        self.assertEqual(at_sc, {"44012"})
        self.assertEqual(at_scw, {"44011"})

    def test_weight_follow_up_keeps_the_search_and_replaces_location(self):
        west = _row(program="Simply Weights", program_id="44021", location="SCW – Seniors Centre West", description="Lifting weights.", sheet="Thursday", time="09:00 AM - 10:00 AM")
        centre = _row(program="Simply Strength", program_id="44022", location="SC – Seniors Centre", description="Lifting weights.", sheet="Thursday", time="09:00 AM - 10:00 AM")
        afternoon = _row(program="Simply Weights", program_id="44023", location="SC – Seniors Centre", description="Lifting weights.", sheet="Thursday", time="01:00 PM - 02:00 PM")
        rows = [west, centre, afternoon]
        history = []
        result = None
        for question in ("weight", "SC", "Thursday", "Morning", "SCW"):
            result = rachel_program_search.answer(question, rows, history)
            history.append(question)
        self.assertEqual(result["conditions"], ["Thursday", "morning", "Seniors Centre West", "weights"])
        self.assertIn("44021", result["answer"])
        self.assertNotIn("44022", result["answer"])
        self.assertNotIn("44023", result["answer"])

    def test_a_new_topic_clears_the_previous_search(self):
        weights = _row(program="Simply Weights", program_id="44031", description="Lifting weights.", sheet="Thursday")
        painting = _row(program="Watercolour Studio", program_id="44032", description="Explore watercolour painting.", sheet="Friday")
        result = rachel_program_search.answer("watercolour painting", [weights, painting], ["weights Thursday"])
        self.assertIn("44032", result["answer"])
        self.assertNotIn("44031", result["answer"])
        self.assertNotIn("Thursday", result["conditions"])


def _catalog():
    return [
        _row(program="Simply Weights", program_id="51001", description="Lifting weights.", location="SC – Seniors Centre", sheet="Wednesday", time="12:00 PM - 01:00 PM"),
        _row(program="Badminton", program_id="51002", description="Games of badminton.", location="SCW – Seniors Centre West", sheet="Friday", time="10:00 AM - 11:00 AM"),
        _row(program="Badminton", program_id="51012", description="Games of badminton.", location="SC – Seniors Centre", sheet="Tuesday", time="06:00 PM - 07:00 PM"),
        _row(program="Aquafit", program_id="51003", description="Exercise in the pool.", location="SCW – Seniors Centre West", sheet="Thursday", time="09:00 AM - 09:45 AM"),
        _row(program="Aquafit", program_id="51004", description="Exercise in the pool.", location="SCW – Seniors Centre West", sheet="Friday", time="09:00 AM - 09:45 AM"),
        _row(program="Aquafit", program_id="51014", description="Exercise in the pool.", location="SCW – Seniors Centre West", sheet="Thursday", time="06:00 PM - 07:00 PM"),
        _row(program="Aquafit", program_id="51015", description="Exercise in the pool.", location="SC – Seniors Centre", sheet="Wednesday", time="11:00 AM - 12:00 PM"),
        _row(program="Pickleball Intermediate", program_id="51005", description="Enjoy friendly games of pickleball.", sheet="Tuesday", time="01:00 PM - 02:30 PM", location="SC – Seniors Centre"),
        _row(program="Pickleball Beginner", program_id="51006", description="For players who are new to pickleball.", sheet="Tuesday", time="09:00 AM - 10:30 AM", location="SC – Seniors Centre"),
        _row(program="Yoga Beginner", program_id="51007", description="A gentle yoga class.", sheet="Thursday", time="09:00 AM - 10:00 AM", location="SCE – Seniors Centre East"),
        _row(program="Yoga Flow", program_id="51008", description="A flowing yoga class.", sheet="Thursday", time="06:00 PM - 07:00 PM", location="SCE – Seniors Centre East"),
        _row(program="Watercolour Studio", program_id="51009", description="Explore watercolour painting.", sheet="Friday", time="01:00 PM - 03:00 PM", location="SC – Seniors Centre"),
        _row(program="Computer Basics", program_id="51010", description="Learn to use a computer.", sheet="Wednesday", time="02:00 PM - 03:00 PM", location="SC – Seniors Centre"),
        _row(program="Tai Chi Introduction", program_id="51011", description="Slow movement.", sheet="Wednesday", time="11:00 AM - 12:00 PM", location="SCW – Seniors Centre West"),
    ]


def _conversation(questions):
    history = []
    result = None
    for question in questions:
        result = rachel_program_search.answer(question, _catalog(), history)
        history.append(question)
    return result


class RachelSearchIntentTests(unittest.TestCase):
    def test_a_different_activity_starts_a_new_search(self):
        cases = {
            ("weights", "badminton"): {"badminton"},
            ("weights at SC", "badminton"): {"badminton"},
            ("aquafit", "pickleball"): {"pickleball"},
            ("Thursday morning Aquafit at SCW", "Find painting classes"): {"painting"},
            ("intermediate pickleball", "beginner yoga"): {"beginner", "yoga"},
        }
        for questions, expected in cases.items():
            result = _conversation(questions)
            self.assertEqual(set(result["conditions"]), expected, questions)
            self.assertNotIn("51001", result.get("programs") or [])

    def test_new_activity_returns_the_new_programs_only(self):
        badminton = _conversation(["weights", "badminton"])
        self.assertIn("51002", badminton["programs"])
        self.assertNotIn("51001", badminton["answer"])
        painting = _conversation(["Thursday morning Aquafit at SCW", "Find painting classes"])
        self.assertEqual(painting["programs"], ["51009"])
        self.assertNotIn("51003", painting["answer"])
        yoga = _conversation(["intermediate pickleball", "beginner yoga"])
        self.assertEqual(yoga["programs"], ["51007"])
        self.assertNotIn("51005", yoga["answer"])
        self.assertNotIn("51006", yoga["answer"])

    def test_explicit_new_search_instructions_drop_the_previous_activity(self):
        cases = [
            (("weights", "new check for badminton"), ["badminton"], "51002"),
            (("aquafit", "new search for painting"), ["painting"], "51009"),
            (("yoga", "Find me some computer classes"), ["computer"], "51010"),
            (("pickleball", "Look for Tai Chi"), ["tai", "chi"], "51011"),
            (("weights", "new chek for badmnton"), ["badminton"], "51002"),
        ]
        for questions, conditions, program_id in cases:
            result = _conversation(questions)
            self.assertEqual(result["conditions"], conditions, questions)
            self.assertIn(program_id, result["programs"])
            self.assertNotIn("check", result["conditions"])
            self.assertNotIn("new", result["conditions"])
            self.assertNotIn("51001", result["answer"])

    def test_schedule_and_level_refine_the_current_search(self):
        weights = _conversation(["weights", "SC"])
        self.assertEqual(weights["conditions"], ["Seniors Centre", "weights"])
        self.assertIn("51001", weights["programs"])
        self.assertNotIn("51002", weights["answer"])
        thursday = _conversation(["aquafit", "Thursday"])
        self.assertEqual(thursday["conditions"], ["Thursday", "aquafit"])
        self.assertIn("51003", thursday["programs"])
        self.assertNotIn("51004", thursday["answer"])
        friday = _conversation(["aquafit", "Thursday", "Friday"])
        self.assertEqual(friday["conditions"], ["Friday", "aquafit"])
        self.assertIn("51004", friday["programs"])
        self.assertNotIn("51003", friday["answer"])
        level = _conversation(["pickleball", "intermediate"])
        self.assertEqual(level["conditions"], ["pickleball", "intermediate"])
        self.assertEqual(level["programs"], ["51005"])
        morning = _conversation(["yoga", "morning"])
        self.assertEqual(morning["conditions"], ["morning", "yoga"])
        self.assertIn("51007", morning["programs"])
        self.assertNotIn("51008", morning["answer"])

    def test_same_location_time_and_any_location_keep_only_the_named_filter(self):
        same_place = _conversation(["weights at SC", "badminton at the same location"])
        self.assertEqual(same_place["conditions"], ["Seniors Centre", "badminton"])
        self.assertEqual(same_place["programs"], ["51012"])
        same_time = _conversation(["Thursday morning yoga", "aquafit at the same time"])
        self.assertEqual(same_time["conditions"], ["Thursday", "morning", "aquafit"])
        self.assertEqual(same_time["programs"], ["51003"])
        anywhere = _conversation(["aquafit at SCW", "any location"])
        self.assertEqual(anywhere["conditions"], ["aquafit"])
        self.assertIn("51015", anywhere["programs"])
        self.assertIn("51003", anywhere["programs"])

    def test_instruction_words_are_not_search_keywords(self):
        cases = {
            "check badminton": ["badminton"],
            "new check for badminton": ["badminton"],
            "find intermediate pickleball": ["intermediate", "pickleball"],
            "show me weights classes": ["weights"],
            "can you find yoga classes?": ["yoga"],
        }
        for question, conditions in cases.items():
            result = rachel_program_search.answer(question, _catalog())
            self.assertEqual(result["conditions"], conditions, question)
            for leftover in ("check", "new", "find", "show", "look", "search", "some"):
                self.assertNotIn(leftover, result["conditions"], question)

    def test_an_instruction_with_no_activity_asks_instead_of_guessing(self):
        result = _conversation(["weights", "check"])
        self.assertIn("new search", result["answer"].lower())
        self.assertEqual(result["conditions"], ["weights"])
        self.assertNotIn("check", result["conditions"])

    def test_context_words_are_not_changed_into_other_programs(self):
        rows = [
            _row(program="Jazz Composers", program_id="52001", description="A class about music composers.", sheet="Wednesday"),
            _row(program="Mahjong Tiles", program_id="52003", description="Play with tiles.", sheet="Thursday", time="09:00 AM - 10:00 AM"),
            _row(program="Yoga", program_id="52004", description="A yoga class.", sheet="Thursday", time="09:00 AM - 10:00 AM"),
            _row(program="Aquafit", program_id="52005", description="Exercise in the pool.", sheet="Thursday", time="09:00 AM - 09:45 AM"),
            _row(program="Aquafit", program_id="52006", description="Exercise in the pool.", sheet="Friday", time="09:00 AM - 09:45 AM"),
        ]
        computer = rachel_program_search.answer("find me some computer classes", rows)
        self.assertEqual(computer["conditions"], ["computer"])
        self.assertNotIn("52001", computer.get("programs") or [])
        history = []
        result = None
        for question in ("Thursday morning yoga", "aquafit at the same time"):
            result = rachel_program_search.answer(question, rows, history)
            history.append(question)
        self.assertEqual(result["conditions"], ["Thursday", "morning", "aquafit"])
        self.assertEqual(result["programs"], ["52005"])
        self.assertNotIn("tiles", result["conditions"])

    def test_start_over_clears_the_search(self):
        result = _conversation(["weights", "start over"])
        self.assertEqual(result["conditions"], [])
        self.assertIn("new search", result["answer"].lower())
        fresh = _conversation(["weights", "start over", "badminton"])
        self.assertEqual(fresh["conditions"], ["badminton"])
        self.assertIn("51002", fresh["programs"])
        self.assertNotIn("51001", fresh["answer"])


if __name__ == "__main__":
    unittest.main()
