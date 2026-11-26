"""Read-only class search for the public Rachel button.

Uses the saved program list only. It does not invent descriptions.
Singular and plural forms match. Location codes such as SC and SCW are separate filters.
A follow-up keeps the earlier search. A new location replaces the previous location.
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
    ("seniors centre west", "Seniors Centre West", ("scw",)),
    ("seniors centre east", "Seniors Centre East", ("sce",)),
    ("seniors centre dome", "Seniors Centre Dome", ("scd",)),
    ("seniors centre st andrews", "Seniors Centre St Andrews", ("sca",)),
    ("st andrews", "Seniors Centre St Andrews", ("sca",)),
    ("seniors centre harbour", "Seniors Centre Harbour", ("sch",)),
    ("seniors centre wolfe island", "Seniors Centre Wolfe Island", ("sci",)),
    ("seniors centre loyalist", "Seniors Centre Loyalist", ("scl",)),
    ("seniors centre north", "Seniors Centre North", ("scn",)),
    ("seniors centre the spire", "Seniors Centre The Spire", ("scs",)),
    ("the spire", "Seniors Centre The Spire", ("scs",)),
    ("seniors centre", "Seniors Centre", ("sc",)),
    ("the west", "Seniors Centre West", ("scw",)),
    ("the east", "Seniors Centre East", ("sce",)),
    ("the dome", "Seniors Centre Dome", ("scd",)),
    ("scw", "Seniors Centre West", ("scw",)),
    ("sce", "Seniors Centre East", ("sce",)),
    ("scd", "Seniors Centre Dome", ("scd",)),
    ("sca", "Seniors Centre St Andrews", ("sca",)),
    ("sch", "Seniors Centre Harbour", ("sch",)),
    ("sci", "Seniors Centre Wolfe Island", ("sci",)),
    ("scl", "Seniors Centre Loyalist", ("scl",)),
    ("scn", "Seniors Centre North", ("scn",)),
    ("scs", "Seniors Centre The Spire", ("scs",)),
    ("sc", "Seniors Centre", ("sc",)),
    ("west", "Seniors Centre West", ("scw",)),
    ("east", "Seniors Centre East", ("sce",)),
    ("dome", "Seniors Centre Dome", ("scd",)),
    ("harbour", "Seniors Centre Harbour", ("sch",)),
    ("harbor", "Seniors Centre Harbour", ("sch",)),
    ("online", "Online", ("ol",)),
    ("offsite", "Offsite Location", ("os",)),
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
    "kind", "like", "would", "could", "can", "looking", "need", "wanted", "which", "where", "when", "find",
    *WEEKDAYS, *DAY_TOKENS.keys(),
    "seniors", "centre", "center", "west", "east", "dome", "andrews", "harbour", "harbor",
}
FOLLOW_CUES = (
    "what about", "how about", "instead", "the same", "same class", "those", "only", "also",
    "that one", "this one", "the first", "the second", "the third", "the last", "tell me more",
)
REPLACE_CUES = ("what about", "how about", "instead")


def _plain(value) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"&[a-z]+;", " ", text, flags=re.I)
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _stem(token: str) -> str:
    if len(token) <= 3 or token.isdigit():
        return token
    if token.endswith("ies"):
        return token[:-3] + "y"
    if token.endswith("es") and (token[-3] in "sxz" or token.endswith(("ches", "shes"))):
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _has(haystack: str, phrase: str) -> bool:
    needle = [_stem(token) for token in _plain(phrase).split(" ") if token]
    if not needle:
        return False
    stems = [_stem(token) for token in _plain(haystack).split(" ") if token]
    width = len(needle)
    return any(stems[index:index + width] == needle for index in range(len(stems) - width + 1))


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
        if len(token) <= 2 or token in DROP_WORDS or token in covered or token in words or token in DAY_TOKENS:
            continue
        if token.isdigit() or any(token == _plain(mark) or token in _plain(phrase).split(" ") for phrase, _label, marks in LOCATIONS for mark in marks):
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


def _is_additive(current: dict) -> bool:
    if current["program_id"]:
        return False
    topic = len(current["words"]) + len(current["concepts"])
    return topic == 1


def _union(old: list, new: list) -> list:
    merged = list(old)
    for item in new:
        if item not in merged:
            merged.append(item)
    return merged


def _union_concepts(old: list, new: list) -> list:
    merged = list(old)
    seen = {concept["id"] for concept in merged}
    for concept in new:
        if concept["id"] not in seen:
            merged.append(concept)
            seen.add(concept["id"])
    return merged


def _removed_target(query: str) -> str:
    plain = _plain(query)
    for prefix in ("remove ", "drop ", "without ", "except ", "not "):
        if plain.startswith(prefix):
            return plain[len(prefix):].strip()
    return ""


def _without(previous: dict, target: str) -> dict:
    day = DAY_TOKENS.get(target, target)
    updated = {
        "days": [item for item in previous["days"] if item != day],
        "bands": [item for item in previous["bands"] if item != target],
        "locations": [
            item for item in previous["locations"]
            if target not in _plain(item["label"]) and all(_plain(mark) != target for mark in item["marks"])
        ],
        "concepts": [item for item in previous["concepts"] if item["id"] != target and all(not _has(phrase, target) for phrase in item["asks"])],
        "words": [item for item in previous["words"] if item != target],
        "program_id": "" if previous.get("program_id") == target else previous.get("program_id", ""),
        "text": previous.get("text", ""),
    }
    updated["removal_applied"] = updated["days"] != previous["days"] or updated["bands"] != previous["bands"] or updated["locations"] != previous["locations"] or updated["concepts"] != previous["concepts"] or updated["words"] != previous["words"] or updated["program_id"] != previous.get("program_id", "")
    return updated


def _merge(previous: dict | None, query: str) -> dict:
    current = _constraints(query)
    removed = _removed_target(query)
    if previous and removed:
        return _without(previous, removed)
    if not previous or not (_is_follow_up(query, current) or _is_additive(current)):
        return current
    replace = any(cue in _plain(query) for cue in REPLACE_CUES)
    replace_topic = replace and (current["words"] or current["concepts"])
    return {
        "days": current["days"] if replace and current["days"] else _union(previous["days"], current["days"]),
        "bands": current["bands"] if replace and current["bands"] else _union(previous["bands"], current["bands"]),
        "locations": current["locations"] if current["locations"] else previous["locations"],
        "concepts": current["concepts"] if replace_topic else _union_concepts(previous["concepts"], current["concepts"]),
        "words": current["words"] if replace_topic else _union(previous["words"], current["words"]),
        "program_id": current["program_id"],
        "text": f"{previous.get('text', '')} {query}".strip(),
    }


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
        tokens = set(_plain(row.get("location")).split(" "))
        if not any(any(_plain(mark) in tokens for mark in place["marks"]) for place in constraints["locations"]):
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


def _edit_distance(left: str, right: str, limit: int) -> int:
    if abs(len(left) - len(right)) > limit:
        return limit + 1
    previous = list(range(len(right) + 1))
    before = previous
    for index, first in enumerate(left, 1):
        current = [index]
        smallest = index
        for column, second in enumerate(right, 1):
            cost = 0 if first == second else 1
            value = min(current[column - 1] + 1, previous[column] + 1, previous[column - 1] + cost)
            if index > 1 and column > 1 and left[index - 1] == right[column - 2] and left[index - 2] == right[column - 1]:
                value = min(value, before[column - 2] + 1)
            current.append(value)
            smallest = min(smallest, value)
        if smallest > limit:
            return limit + 1
        before, previous = previous, current
    return previous[-1]


def _distance_limit(word: str) -> int:
    if len(word) < 8:
        return 1
    return 2


def _remember(vocab: dict, word: str, replacement: str, display: str, weight: int, keep: bool = False, phrase: bool = False) -> None:
    key = _plain(word)
    if len(key) < 4 or key.isdigit() or (not keep and key in DROP_WORDS):
        return
    current = vocab.get(key)
    if current and current["weight"] >= weight and not (current.get("phrase") and not phrase):
        return
    vocab[key] = {"replacement": replacement, "display": display, "weight": weight, "phrase": phrase}
    stem = _stem(key)
    if stem != key and not phrase and (stem not in vocab or (not vocab[stem].get("phrase") and vocab[stem]["weight"] < weight)):
        vocab[stem] = vocab[key]


def _vocabulary(programs: list) -> dict:
    vocab = {}
    for day in WEEKDAYS:
        _remember(vocab, day, day, day.title(), 6, keep=True)
    for phrase, label, _marks in LOCATIONS:
        _remember(vocab, phrase, phrase, label, 6, keep=True)
    for concept in CONCEPTS:
        for phrase in concept["asks"] + concept["supports"]:
            _remember(vocab, phrase, _plain(phrase), phrase, 4, keep=True)
    for band in ("morning", "afternoon", "evening"):
        _remember(vocab, band, band, band, 6, keep=True)
    for row in programs or []:
        name = str(row.get("program") or "")
        name_tokens = [token for token in _plain(name).split(" ") if token]
        for token in name_tokens:
            _remember(vocab, token, token, token.title(), 5)
        for left, right in zip(name_tokens, name_tokens[1:]):
            if len(left) >= 3 and len(right) >= 3:
                _remember(vocab, left + right, f"{left} {right}", f"{left.title()} {right.title()}", 5, phrase=True)
        for token in _plain(row.get("instructor")).split(" "):
            _remember(vocab, token, token, token.title(), 4)
        for token in _plain(row.get("description")).split(" "):
            if len(token) >= 5:
                _remember(vocab, token, token, token.title(), 1)
    return vocab


def _real_words(vocab: dict) -> dict:
    return {key: entry for key, entry in vocab.items() if not entry.get("phrase")}


def _unique_prefix(token: str, vocab: dict):
    if len(token) < 4:
        return None, None
    prefixes = [(key, entry) for key, entry in _real_words(vocab).items() if key.startswith(token) and key != token]
    strong = [item for item in prefixes if item[1]["weight"] >= 5]
    pool = strong or [item for item in prefixes if item[1]["weight"] >= 4]
    if not pool:
        return None, None
    keys = [key for key, _entry in pool]
    kept = [(key, entry) for key, entry in pool if not any(other != key and key.startswith(other) for other in keys)]
    if len({key for key, _entry in kept}) == 1:
        return kept[0][1], "normalized"
    return None, [(-entry["weight"], key, entry) for key, entry in kept]


def _best_correction(token: str, vocab: dict):
    words = _real_words(vocab)
    stem = _stem(token)
    stemmed = [entry for key, entry in words.items() if _stem(key) == stem]
    if stemmed:
        stemmed.sort(key=lambda entry: -entry["weight"])
        return stemmed[0], "exact" if token in words else "normalized"
    if token.endswith("s") and token[:-1] in words:
        return words[token[:-1]], "normalized"
    if token.endswith("es") and token[:-2] in words:
        return words[token[:-2]], "normalized"
    prefix, kind = _unique_prefix(token, vocab)
    if prefix or isinstance(kind, list):
        return prefix, kind
    limit = _distance_limit(token)
    ranked = []
    for key, entry in words.items():
        if abs(len(key) - len(token)) > limit:
            continue
        distance = _edit_distance(token, key, limit)
        if distance <= limit:
            ranked.append((distance, -entry["weight"], key, entry))
    if not ranked:
        return None, None
    ranked.sort()
    best_distance = ranked[0][0]
    best_weight = -ranked[0][1]
    closest = [item for item in ranked if item[0] == best_distance and -item[1] == best_weight]
    replacements = {item[3]["replacement"] for item in closest}
    if len(replacements) == 1:
        return closest[0][3], "fuzzy" if best_distance else "exact"
    return None, closest


def _correct_query(query: str, vocab: dict):
    parts = re.findall(r"[A-Za-z0-9]+|[^A-Za-z0-9]+", query)
    changed = []
    index = 0
    while index < len(parts):
        part = parts[index]
        if not part[:1].isalnum():
            index += 1
            continue
        token = _plain(part)
        nxt = parts[index + 2] if index + 2 < len(parts) and not parts[index + 1][:1].isalnum() else ""
        joined = _plain(token + nxt)
        if nxt and joined in vocab and token not in vocab:
            parts[index] = vocab[joined]["display"]
            parts[index + 1] = ""
            parts[index + 2] = ""
            changed.append(vocab[joined]["display"])
            index += 3
            continue
        if len(token) < 4 or token.isdigit() or token in DAY_TOKENS or token in DROP_WORDS:
            index += 1
            continue
        if token in vocab:
            entry = vocab[token]
            if entry["replacement"] != token:
                parts[index] = entry["display"]
                changed.append(entry["display"])
            index += 1
            continue
        found, kind = _best_correction(token, vocab)
        if isinstance(kind, list):
            choices = []
            for item in kind:
                entry = item[3] if len(item) == 4 else item[2]
                label = entry["display"]
                if label not in choices:
                    choices.append(label)
            if len(choices) == 1:
                parts[index] = choices[0]
                changed.append(choices[0])
                index += 1
                continue
            return {"text": query, "changed": [], "ambiguous": choices[:4], "token": part}
        if found and found["replacement"] != token:
            parts[index] = found["display"]
            changed.append(found["display"])
        index += 1
    return {"text": "".join(parts), "changed": changed, "ambiguous": [], "token": ""}


def _correct_messages(messages: list[str], programs: list):
    vocab = _vocabulary(programs)
    corrected = []
    changed = []
    for message in messages:
        result = _correct_query(message, vocab)
        if result["ambiguous"]:
            return corrected, changed, result
        corrected.append(result["text"])
        changed.extend(result["changed"])
    return corrected, changed, None


def search_programs(question: str, programs: list, history=None) -> list[dict]:
    messages, _changed, ambiguous = _correct_messages([*_history(history), question], programs)
    if ambiguous:
        return []
    return _search(_fold(messages), programs)


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
    if asked:
        return empty
    name_query = " ".join(constraints["words"])
    if name_query and all(_has(blob, word) for word in constraints["words"]):
        in_name = all(_has(name, word) for word in constraints["words"])
        return {
            **empty,
            "level": "exact-name" if in_name else "strong-description",
            "reason": f"The program name matches {name}.{'' if description.strip() else ' No description is stored.'}{cancelled}" if in_name else f"The program information includes {', '.join(constraints['words'])}.{cancelled}",
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


def _condition_list(constraints: dict) -> list[str]:
    parts = [day.title() for day in constraints["days"]]
    parts.extend(constraints["bands"])
    parts.extend(place["label"] for place in constraints["locations"])
    parts.extend(concept["id"] for concept in constraints["concepts"])
    parts.extend(constraints["words"])
    if constraints["program_id"]:
        parts.append(f"program {constraints['program_id']}")
    return parts


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
        return {"answer": "Ask about a class by its name, day, or what it is about.", "conditions": []}
    if re.fullmatch(r"(hi|hello|hey|thanks|thank you)[.!]?", text, re.I):
        return {"answer": "Hello. Ask me about a class, such as a gentle exercise class on Tuesday morning.", "conditions": []}
    prior = _history(history)
    if prior and _plain(prior[-1]) == _plain(text):
        prior = prior[:-1]
    vocab = _vocabulary(programs)
    prior_corrected = []
    for message in prior:
        result = _correct_query(message, vocab)
        if result["ambiguous"]:
            choices = " or ".join(result["ambiguous"])
            return {"answer": f"'{result['token']}' could mean {choices}. Tell me which one you mean.", "conditions": []}
        prior_corrected.append(result["text"])
    current = _correct_query(text, vocab)
    if current["ambiguous"]:
        choices = " or ".join(current["ambiguous"])
        return {"answer": f"'{current['token']}' could mean {choices}. Tell me which one you mean.", "conditions": []}
    constraints = _fold([*prior_corrected, current["text"]])
    if constraints.get("removal_applied") is False:
        return {"answer": "That is not one of the current search conditions.", "conditions": _condition_list(constraints)}
    hits = _search(constraints, programs)
    confirmed = [hit for hit in hits if hit["level"] != "related"]
    listed = confirmed or [hit for hit in hits if hit["level"] == "related"]
    pick = _selection(text) if prior and _is_follow_up(current["text"], _constraints(current["text"])) else None
    conditions = _condition_list(constraints)
    showing = f"Showing results for {' '.join(current['changed'])}.\n\n" if current["changed"] else ""
    if constraints.get("program_id") and not any(str(row.get("program_id") or "") == constraints["program_id"] for row in programs or []):
        return {
            "answer": f"{showing}No exact match was found for program code {constraints['program_id']}.",
            "conditions": conditions,
        }
    if pick is not None:
        if not listed:
            return {"answer": f"{showing}I do not have an earlier matching class list. Conditions: {', '.join(conditions)}.", "conditions": conditions}
        index = pick if pick >= 0 else len(listed) - 1
        if index >= len(listed):
            return {"answer": f"I only found {len(listed)} matching classes. Ask for the first one, or name the class.", "conditions": conditions}
        chosen = listed[index]
        return {"answer": f"From the classes I just found:\n\n{_detail(chosen)}", "programs": [chosen["program_id"]], "conditions": conditions}
    if not listed:
        if conditions:
            return {"answer": f"{showing}Nothing matches all of these conditions: {', '.join(conditions)}.", "conditions": conditions}
        return {"answer": "I could not find a class whose name or description matches that. Try the program name, the day, or words from the class description.", "conditions": []}
    intro = "These classes may be related, but the description does not confirm the request." if not confirmed else "Here are the classes that match."
    prefix = showing + (f"Conditions: {', '.join(conditions)}\n\n" if conditions else "")
    body = "\n\n".join(_line(hit) for hit in listed[:5])
    return {"answer": f"{prefix}{intro}\n\n{body}", "programs": [hit["program_id"] for hit in listed[:5]], "conditions": conditions}
