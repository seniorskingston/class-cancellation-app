"""Add locations from the admin page without editing the location file."""


def clean_places(raw) -> dict:
    if not isinstance(raw, dict):
        return {}
    places = raw.get("places") if isinstance(raw.get("places"), dict) else raw
    if not isinstance(places, dict):
        return {}
    cleaned = {}
    for key, value in places.items():
        name = str(key or "").strip()
        address = str(value or "").strip()
        if name and address and name != "places":
            cleaned[name] = address
    return cleaned


def add_place(builtin: dict, extra: dict, name: str, address: str):
    name = str(name or "").strip()
    address = str(address or "").strip()
    if not name or not address:
        return extra, "Type the location name and the address."
    if "center" in name.lower():
        return extra, "Use Centre in the name. A name with Center is hidden from the class list."
    current = {}
    current.update(builtin or {})
    current.update(extra or {})
    for key in current:
        if key.lower() == name.lower():
            return extra, "That location is already in the list."
    updated = dict(extra or {})
    updated[name] = address
    return updated, ""


def remove_place(extra: dict, name: str):
    name = str(name or "").strip()
    match = next((key for key in (extra or {}) if key.lower() == name.lower()), None)
    if not match:
        return extra or {}, "Only a location added on this page can be removed."
    updated = dict(extra)
    del updated[match]
    return updated, ""
