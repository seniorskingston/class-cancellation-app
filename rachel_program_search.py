"""Read-only class search for the public Rachel button.

Uses the saved program list only. It does not invent descriptions.
"""

from __future__ import annotations

import re

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
LOCATIONS = (
    ("seniors centre west", ("scw", "seniors centre west")),
    ("seniors centre east", ("sce", "seniors centre east")),
    ("seniors centre dome", ("scd", "seniors centre dome")),
    ("seniors centre st andrews", ("sca", "st andrews")),
    ("seniors centre harbour", ("sch", "harbour")),
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
RANK = {"exact-id": 5, "exact-name": 4, "strong-description": 3, "meaning": 2, "related": 1, "none": 0}
DROP_WORDS = {
    "i", "want", "a", "an", "the", "class", "classes", "program", "programs", "on", "at", "in", "for", "to", "my", "me",
    "while", "learn", "use", "using", "improve", "with", "and", "or", "of", "gentle", "exercise", "exercises",
    "morning", "mornings", "afternoon", "evening", "help", "stay", "feet",
    *WEEKDAYS,
    "seniors", "centre", "center", "west", "east", "dome", "andrews", "harbour",
}


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


def _weekday(query: str) -> str:
    text = f" {_plain(query)} "
    for day in WEEKDAYS:
        if f" {day} " in text:
            return day
    return ""


def _band(query: str) -> str:
    text = _plain(query)
    if "morning" in text:
        return "morning"
    if "afternoon" in text:
        return "afternoon"
    if "evening" in text:
        return "evening"
    return ""


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


def _location(query: str):
    text = _plain(query)
    for phrase, marks in LOCATIONS:
        if phrase in text:
            return marks
    return None


def _concepts(query: str):
    return [concept for concept in CONCEPTS if any(_has(query, phrase) for phrase in concept["asks"])]


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


def _activity_words(query: str) -> list[str]:
    return [word for word in _plain(query).split(" ") if len(word) > 2 and word not in DROP_WORDS]


def _name_match(name: str, query: str) -> bool:
    record = _plain(name)
    needle = _plain(query)
    if not needle or not record:
        return False
    if needle in record or record in needle:
        return True
    words = [word for word in needle.split(" ") if len(word) > 2]
    return bool(words) and all(word in record for word in words)


def search_programs(question: str, programs: list) -> list[dict]:
    hits = []
    for row in programs or []:
        hit = _score(row, question)
        if hit["level"] == "none":
            continue
        hits.append(hit)
    hits.sort(key=lambda item: (-RANK[item["level"]], _plain(item["program"])))
    return hits


def _score(row: dict, question: str) -> dict:
    name = str(row.get("program") or "")
    program_id = str(row.get("program_id") or "")
    description = str(row.get("description") or "")
    day = str(row.get("sheet") or "")
    start = str(row.get("time") or "")
    location = str(row.get("location") or "")
    status = str(row.get("program_status") or "")
    empty = {"level": "none", "program": name, "program_id": program_id, "reason": "", "excerpt": "", "row": row}
    if not str(question or "").strip():
        return empty
    weekday = _weekday(question)
    if weekday and _plain(day) != weekday:
        return empty
    band = _band(question)
    if band and _time_band(start) != band:
        return empty
    place = _location(question)
    if place and not any(_plain(mark) in _plain(location) for mark in place):
        return empty
    cancelled = " This program is cancelled." if _plain(status) == "cancelled" else ""
    if program_id and (f" {_plain(question)} ".find(f" {_plain(program_id)} ") >= 0 or _plain(question) == _plain(program_id)):
        return {**empty, "level": "exact-id", "reason": f"The program code {program_id} matches.{cancelled}"}
    asked = _concepts(question)
    blob = f"{name} {description}"
    supported = [concept for concept in asked if any(_has(blob, phrase) for phrase in concept["supports"])]
    if asked and len(supported) == len(asked):
        words = []
        for concept in supported:
            words.extend(phrase for phrase in concept["supports"] if _has(blob, phrase))
        meaning = any(not any(_has(question, phrase) and _has(blob, phrase) for phrase in concept["asks"]) for concept in supported)
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
    name_query = " ".join(_activity_words(question))
    if name_query and _name_match(name, name_query):
        return {
            **empty,
            "level": "exact-name",
            "reason": f"The program name matches {name}.{'' if description.strip() else ' No description is stored.'}{cancelled}",
            "excerpt": _excerpt(description, name_query.split(" ")),
        }
    words = _activity_words(question)
    if words and all(_has(description, word) for word in words):
        return {
            **empty,
            "level": "strong-description",
            "reason": f"The description includes {', '.join(words)}.{cancelled}",
            "excerpt": _excerpt(description, words),
        }
    return empty


def _line(hit: dict) -> str:
    row = hit["row"]
    place = " — ".join(part for part in (str(row.get("location") or "").strip(), str(row.get("class_room") or "").strip()) if part)
    bits = [str(row.get("sheet") or "").strip(), str(row.get("time") or "").strip(), place]
    schedule = ", ".join(bit for bit in bits if bit)
    title = f"{hit['program']} {hit['program_id']}".strip()
    parts = [title]
    if schedule:
        parts.append(schedule)
    if hit.get("reason"):
        parts.append(hit["reason"])
    if hit.get("excerpt"):
        parts.append(f"From the description: {hit['excerpt']}")
    return "\n".join(parts)


def answer(question: str, programs: list) -> dict:
    text = str(question or "").strip()
    if not text:
        return {"answer": "Ask about a class by its name, day, or what it is about."}
    if re.fullmatch(r"(hi|hello|hey|thanks|thank you)[.!]?", text, re.I):
        return {"answer": "Hello. Ask me about a class, such as a gentle exercise class on Tuesday morning."}
    hits = search_programs(text, programs)
    strong = [hit for hit in hits if hit["level"] != "related"][:5]
    related = [hit for hit in hits if hit["level"] == "related"][:3]
    chosen = strong or related
    if not chosen:
        return {"answer": "I could not find a class whose name or description matches that. Try the program name, the day, or words from the class description."}
    intro = "These classes may be related, but the description does not confirm the request." if not strong else "Here are the classes that match."
    body = "\n\n".join(_line(hit) for hit in chosen)
    return {"answer": f"{intro}\n\n{body}"}
