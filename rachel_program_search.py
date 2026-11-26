"""Read-only class search for the public Rachel button.

Uses the saved program list only. It does not invent descriptions.
A follow-up keeps the earlier day, time, location, and topic until the
user asks a new question.
"""

from __future__ import annotations

import re

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
DAY_TOKENS = {
    "monday": "monday", "mon": "monday",
    "tuesday": "tuesday", "tues": "tuesday", "tue": "tuesday",
    "wednesday": "wednesday", "wed": "wednesday",
    "thursday": "thursday", "thurs": "thursday", "thur": "thursday", "thu": "thursday",
    "friday": "friday", "fri": "friday",
    "saturday": "saturday", "sat": "saturday",
    "sunday": "sunday", "sun": "sunday",
}
LOCATIONS = (
    ("seniors centre west", "Seniors Centre West", ("scw", "seniors centre west")),
    ("seniors centre east", "Seniors Centre East", ("sce", "seniors centre east")),
    ("seniors centre dome", "Seniors Centre Dome", ("scd", "seniors centre dome")),
    ("seniors centre st andrews", "Seniors Centre St Andrews", ("sca", "st andrews")),
    ("st andrews", "Seniors Centre St Andrews", ("sca", "st andrews")),
    ("seniors centre harbour", "Seniors Centre Harbour", ("sch", "harbour")),
    ("the west", "Seniors Centre West", ("scw", "seniors centre west")),
    ("the east", "Seniors Centre East", ("sce", "seniors centre east")),
    ("the dome", "Seniors Centre Dome", ("scd", "seniors centre dome")),
    ("scw", "Seniors Centre West", ("scw", "seniors centre west")),
    ("sce", "Seniors Centre East", ("sce", "seniors centre east")),
    ("scd", "Seniors Centre Dome", ("scd", "seniors centre dome")),
    ("sca", "Seniors Centre St Andrews", ("sca", "st andrews")),
    ("sch", "Seniors Centre Harbour", ("sch", "harbour")),
    ("west", "Seniors Centre West", ("scw", "seniors centre west")),
    ("east", "Seniors Centre East", ("sce", "seniors centre east")),
    ("dome", "Seniors Centre Dome", ("scd", "seniors centre dome")),
    ("harbour", "Seniors Centre Harbour", ("sch", "harbour")),
    ("harbor", "Seniors Centre Harbour", ("sch", "harbour")),
)
CONCEPTS = (
    {"id": "seated", "asks": ("while sitting", "sitting", "seated", "chair"), "supports": ("seated", "chair", "sitting", "sit down")},
    {"id": "balance", "asks": ("balance", "balancing", "stability", "stay steady", "steady"), "supports": ("balance", "balancing", "stability", "fall prevention")},
    {"id": "beginner", "asks": ("beginner", "beginners", "no experience", "no painting experience", "never", "new to", "first time"), "supports": ("beginner", "beginners", "introductory", "introduction", "no experience", "no previous experience", "new to", "first time")},
    {"id": "iphone", "asks": ("apple phone", "iphone", "ios"), "supports": ("iphone", "apple phone", "ios")},
    {"id": "gentle", "asks": ("gentle", "low impact", "easy going"), "supports": ("gentle", "low impact", "low-impact", "easy pace")},
    {"id": "exercise", "asks": ("exercise", "exercises", "fitness", "workout"), "supports": ("exercise", "exercises", "fitness", "workout", "movement class")},
    {"id": "painting", "asks": ("paint", "painting"), "supports": ("paint", "painting")},
)
RANK = {"exact-id": 5, "exact-name": 4, "strong-description": 3, "schedule": 3, "meaning": 2, "related": 1, "none": 0}
DROP_WORDS = {
    "i", "want", "a", "an", "the", "class", "classes", "program", "programs", "on", "at", "in", "for", "to", "my", "me",
    "while", "learn", "use", "using", "improve", "with", "and", "or", "of", "gentle", "exercise", "exercises",
    "morning", "mornings", "afternoon", "evening", "help", "stay", "feet", "experience", "tell", "more", "about",
    "please", "show", "one", "ones", "first", "second", "third", "fourth", "fifth", "last", "that", "this", "instead",
    "only", "just", "same", "those", "what", "how", "there", "from", "does", "have", "any", "something", "anything",
    "kind", "like", "would", "could", "can", "looking", "need", "wanted", "which", "where", "when",
    *WEEKDAYS, *DAY_TOKENS.keys(),
    "seniors", "centre", "center", "west", "east", "dome", "andrews", "harbour", "harbor",
}
FOLLOW_CUES = (
    "what about", "how about", "instead", "the same", "same class", "those", "only", "also",
    "that one", "this one", "the first", "the second", "the third", "the last", "tell me more",
)


def _plain(value) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"&[a-z]+;", " ", text, flags=re.I)
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _has(haystack: str, phrase: str) -> bool:
    needle = _plain(phrase)
    if not needle:
        return False
    return f" {_plain(haystack)} ".find(f" {needle} ") >= 0


def _days(query: str) -> list[str]:
    found = []
    for token in _plain(query).split(" "):
        day = DAY_TOKENS.get(token)
        if day and day not in found:
            found.append(day)
    return found


def _bands(query: str) -> list[str]:
    text = _plain(query)
    return [band for band in ("morning", "afternoon", "evening") if band in text]


def _hour(time: str):
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)", str(time or ""), re.I)
    if not match:
        return None
    hour = int(match.group(1))
    ap = match.group(3).lower()
    if ap == "pm" and hour < 12:
        hour += 12
    if ap == "am" and hour == 12:
        hour = 0
    return hour


def _time_band(time: str) -> str:
    hour = _hour(time)
    if hour is None:
        return ""
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def _locations(query: str) -> list[dict]:
    text = f" {_plain(query)} "
    found = []
    occupied = []
    for phrase, label, marks in sorted(LOCATIONS, key=lambda item: -len(item[0])):
        needle = f" {_plain(phrase)} "
        start = text.find(needle)
        if start < 0:
            continue
        end = start + len(needle)
        if any(not (end <= left or start >= right) for left, right in occupied):
            continue
        occupied.append((start, end))
        if not any(item["label"] == label for item in found):
            found.append({"label": label, "marks": marks})
    return found


def _concepts(query: str):
    return [concept for concept in CONCEPTS if any(_has(query, phrase) for phrase in concept["asks"])]


def _program_id(query: str) -> str:
    match = re.search(r"\b(\d{4,6})\b", _plain(query))
    return match.group(1) if match else ""


def _constraints(query: str) -> dict:
    concepts = _concepts(query)
    covered = set()
    for concept in concepts:
        for phrase in concept["asks"]:
            covered.update(_plain(phrase).split(" "))
    words = []
    for token in _plain(query).split(" "):
        if len(token) <= 2 or token in DROP_WORDS or token in covered or token in words:
            continue
        if token.isdigit():
            continue
        words.append(token)
    return {
        "days": _days(query),
        "bands": _bands(query),
        "locations": _locations(query),
        "concepts": concepts,
        "words": words,
        "program_id": _program_id(query),
        "text": query,
    }


def _is_follow_up(query: str, current: dict) -> bool:
    plain = _plain(query)
    if any(cue in plain for cue in FOLLOW_CUES):
        return True
    has_topic = bool(current["concepts"] or current["words"] or current["program_id"])
    has_schedule = bool(current["days"] or current["bands"] or current["locations"])
    return has_schedule and not has_topic


def _merge(previous: dict | None, query: str) -> dict:
    current = _constraints(query)
    if not previous or not _is_follow_up(query, current):
        return current
    merged = {
        "days": current["days"] or previous["days"],
        "bands": current["bands"] or previous["bands"],
        "locations": current["locations"] or previous["locations"],
        "concepts": previous["concepts"],
        "words": previous["words"],
        "program_id": current["program_id"],
        "text": f"{previous.get('text', '')} {query}".strip(),
    }
    if current["concepts"] or current["words"] or current["program_id"]:
        merged["concepts"] = current["concepts"]
        merged["words"] = current["words"]
        merged["text"] = query
    return merged


def _fold(messages: list[str]) -> dict:
    current = None
    for message in messages:
        text = str(message or "").strip()
        if text:
            current = _merge(current, text)
    return current or _constraints("")


def _excerpt(description: str, words: list[str]) -> str:
    clean = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(description or ""))).strip()
    if not clean:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    chosen = next((sentence for sentence in sentences if any(_has(sentence, word) for word in words)), sentences[0])
    marked = chosen
    for word in words:
        if not word:
            continue
        marked = re.sub(rf"({re.escape(word)})", r"**\1**", marked, flags=re.I)
    return marked


def _name_match(name: str, query: str) -> bool:
    record = _plain(name)
    needle = _plain(query)
    if not needle or not record:
        return False
    if needle in record or record in needle:
        return True
    words = [word for word in needle.split(" ") if len(word) > 2]
    return bool(words) and all(word in record for word in words)


def _blob(row: dict) -> str:
    return " ".join(str(row.get(key) or "") for key in ("program", "description", "instructor", "location"))


def _passes_schedule(row: dict, constraints: dict) -> bool:
    day = _plain(row.get("sheet"))
    if constraints["days"] and day not in constraints["days"]:
        return False
    band = _time_band(str(row.get("time") or ""))
    if constraints["bands"] and band not in constraints["bands"]:
        return False
    if constraints["locations"]:
        location = _plain(row.get("location"))
        if not any(any(_plain(mark) in location for mark in place["marks"]) for place in constraints["locations"]):
            return False
    return True


def _search(constraints: dict, programs: list) -> list[dict]:
    hits = []
    for row in programs or []:
        hit = _score(row, constraints)
        if hit["level"] == "none":
            continue
        hits.append(hit)
    hits.sort(key=lambda item: (-RANK[item["level"]], _plain(item["program"])))
    return hits


def search_programs(question: str, programs: list, history=None) -> list[dict]:
    return _search(_fold([*_history(history), question]), programs)


def _score(row: dict, constraints: dict) -> dict:
    name = str(row.get("program") or "")
    program_id = str(row.get("program_id") or "")
    description = str(row.get("description") or "")
    status = str(row.get("program_status") or "")
    empty = {"level": "none", "program": name, "program_id": program_id, "reason": "", "excerpt": "", "row": row}
    if not any(constraints[key] for key in ("days", "bands", "locations", "concepts", "words", "program_id")):
        return empty
    if not _passes_schedule(row, constraints):
        return empty
    cancelled = " This program is cancelled." if _plain(status) == "cancelled" else ""
    if constraints["program_id"]:
        if _plain(program_id) != _plain(constraints["program_id"]):
            return empty
        return {**empty, "level": "exact-id", "reason": f"The program code {program_id} matches.{cancelled}"}
    blob = _blob(row)
    if constraints["words"] and not all(_has(blob, word) for word in constraints["words"]):
        return empty
    asked = constraints["concepts"]
    supported = [concept for concept in asked if any(_has(blob, phrase) for phrase in concept["supports"])]
    if asked and len(supported) == len(asked):
        words = []
        for concept in supported:
            words.extend(phrase for phrase in concept["supports"] if _has(blob, phrase))
        asked_text = constraints.get("text") or ""
        meaning = any(
            not any(_has(asked_text, phrase) and _has(blob, phrase) for phrase in concept["asks"])
            for concept in supported
        )
        return {
            **empty,
            "level": "meaning" if meaning else "strong-description",
            "reason": f"The program information mentions {', '.join(words[:3])}.{cancelled}",
            "excerpt": _excerpt(description, words),
        }
    if asked and supported:
        words = []
        for concept in supported:
            words.extend(phrase for phrase in concept["supports"] if _has(blob, phrase))
        missing = [concept["id"] for concept in asked if concept not in supported]
        return {
            **empty,
            "level": "related",
            "reason": f"This may be related because the program information mentions {', '.join(words[:3])}. It does not say it covers {', '.join(missing)}.{cancelled}",
            "excerpt": _excerpt(description, words),
        }
    name_query = " ".join(constraints["words"])
    if name_query and _name_match(name, name_query):
        return {
            **empty,
            "level": "exact-name",
            "reason": f"The program name matches {name}.{'' if description.strip() else ' No description is stored.'}{cancelled}",
            "excerpt": _excerpt(description, constraints["words"]),
        }
    if constraints["words"] and all(_has(description, word) for word in constraints["words"]):
        return {
            **empty,
            "level": "strong-description",
            "reason": f"The description includes {', '.join(constraints['words'])}.{cancelled}",
            "excerpt": _excerpt(description, constraints["words"]),
        }
    if not asked and not constraints["words"] and (constraints["days"] or constraints["bands"] or constraints["locations"]):
        return {
            **empty,
            "level": "schedule",
            "reason": f"It matches the requested day, time, or location.{cancelled}",
        }
    return empty


def _history(history) -> list[str]:
    messages = []
    for item in history or []:
        if isinstance(item, str):
            text = item
        elif isinstance(item, dict):
            text = str(item.get("text") or item.get("question") or "")
        else:
            continue
        text = text.strip()[:300]
        if text:
            messages.append(text)
    return messages[:8]


def _line(hit: dict) -> str:
    row = hit["row"]
    place = " — ".join(part for part in (str(row.get("location") or "").strip(), str(row.get("class_room") or "").strip()) if part)
    bits = [str(row.get("sheet") or "").strip(), str(row.get("time") or "").strip(), place]
    schedule = ", ".join(bit for bit in bits if bit)
    instructor = str(row.get("instructor") or "").strip()
    title = f"{hit['program']} {hit['program_id']}".strip()
    parts = [title]
    if schedule:
        parts.append(schedule)
    if instructor:
        parts.append(f"Instructor: {instructor}")
    if hit.get("reason"):
        parts.append(hit["reason"])
    if hit.get("excerpt"):
        parts.append(f"From the description: {hit['excerpt']}")
    return "\n".join(parts)


def _detail(hit: dict) -> str:
    row = hit["row"]
    description = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(row.get("description") or ""))).strip()
    parts = [_line(hit)]
    if description and description not in _line(hit):
        parts.append(description)
    return "\n".join(parts)


def _conditions(constraints: dict) -> str:
    parts = [day.title() for day in constraints["days"]]
    parts.extend(constraints["bands"])
    parts.extend(place["label"] for place in constraints["locations"])
    parts.extend(concept["id"] for concept in constraints["concepts"])
    parts.extend(constraints["words"])
    if constraints["program_id"]:
        parts.append(f"program {constraints['program_id']}")
    return ", ".join(parts)


def _selection(query: str):
    plain = f" {_plain(query)} "
    if "first time" in plain:
        return None
    if " that one " in plain or " this one " in plain or " tell me more " in plain:
        return 0
    ordinals = (("first", 0), ("second", 1), ("third", 2), ("fourth", 3), ("fifth", 4), ("last", -1))
    for word, index in ordinals:
        if f" {word} " in plain:
            return index
    return None


def answer(question: str, programs: list, history=None) -> dict:
    text = str(question or "").strip()
    if not text:
        return {"answer": "Ask about a class by its name, day, or what it is about."}
    if re.fullmatch(r"(hi|hello|hey|thanks|thank you)[.!]?", text, re.I):
        return {"answer": "Hello. Ask me about a class, such as a gentle exercise class on Tuesday morning."}
    prior = _history(history)
    if prior and _plain(prior[-1]) == _plain(text):
        prior = prior[:-1]
    constraints = _fold([*prior, text])
    hits = _search(constraints, programs)
    confirmed = [hit for hit in hits if hit["level"] != "related"]
    listed = confirmed or [hit for hit in hits if hit["level"] == "related"]
    pick = _selection(text) if prior and _is_follow_up(text, _constraints(text)) else None
    conditions = _conditions(constraints)
    if pick is not None:
        if not listed:
            return {"answer": f"I do not have an earlier matching class list. Conditions: {conditions}."}
        index = pick if pick >= 0 else len(listed) - 1
        if index >= len(listed):
            return {"answer": f"I only found {len(listed)} matching classes. Ask for the first one, or name the class."}
        chosen = listed[index]
        return {"answer": f"From the classes I just found:\n\n{_detail(chosen)}", "programs": [chosen["program_id"]]}
    if not listed:
        if conditions:
            return {"answer": f"Nothing matches all of these conditions: {conditions}."}
        return {"answer": "I could not find a class whose name or description matches that. Try the program name, the day, or words from the class description."}
    intro = "These classes may be related, but the description does not confirm the request." if not confirmed else "Here are the classes that match."
    prefix = f"Conditions: {conditions}\n\n" if conditions else ""
    body = "\n\n".join(_line(hit) for hit in listed[:5])
    return {"answer": f"{prefix}{intro}\n\n{body}", "programs": [hit["program_id"] for hit in listed[:5]]}
