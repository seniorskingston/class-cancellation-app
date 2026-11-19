"""Find one class so a cancellation date and note can be saved on that class only."""


def program_id_key(value) -> str:
    text = str(value or "").strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.lstrip("0") or "0"


def search_programs(programs, query: str) -> list:
    term = str(query or "").strip().lower()
    if not term:
        return []
    wanted_id = program_id_key(term)
    found = []
    for row in programs or []:
        name = str(row.get("program") or "").lower()
        program_id = str(row.get("program_id") or "")
        if term in name or term in program_id.lower() or program_id_key(program_id) == wanted_id:
            found.append(row)
    return found


def matching_class(programs, program_id, sheet, session) -> list:
    wanted_sheet = str(sheet or "").strip()
    wanted_session = str(session or "").strip()
    wanted_id = program_id_key(program_id)
    return [
        row for row in programs or []
        if program_id_key(row.get("program_id")) == wanted_id
        and str(row.get("sheet") or "").strip() == wanted_sheet
        and str(row.get("session") or "").strip() == wanted_session
    ]


def public_class(row: dict) -> dict:
    return {
        "program": str(row.get("program") or ""),
        "program_id": str(row.get("program_id") or ""),
        "sheet": str(row.get("sheet") or ""),
        "session": str(row.get("session") or ""),
        "time": str(row.get("time") or ""),
        "class_cancellation": str(row.get("class_cancellation") or ""),
        "note": str(row.get("note") or ""),
    }
