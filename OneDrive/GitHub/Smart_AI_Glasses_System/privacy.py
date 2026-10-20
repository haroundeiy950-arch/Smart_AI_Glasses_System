from typing import Dict, Any


def safe_person_text(person: Dict[str, Any]) -> str:
    """
    Return safe text to display on the camera.
    Private people show limited data.
    Public people can show more information.
    """
    name = person.get("name", "Unknown Person")
    job = person.get("job", "")
    person_type = person.get("type", "private")
    basic_info = person.get("basic_info", "")
    last_notes = person.get("last_notes", "")

    if person_type == "public":
        return f"{name} | {job} | {basic_info}"

    if job:
        return f"{name} | {job}"

    return name


def can_show_sensitive_info(person: Dict[str, Any]) -> bool:
    return person.get("type") == "public"
