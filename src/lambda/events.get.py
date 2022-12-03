from googleapi import calendars, events
from lex import close, return_unexpected_failure
from setup_handler import google_api_handler as setup
from utility import get_slots


def handler(event: dict, context: object) -> dict:
    session_attributes, service, err = setup(event, "calendar", "v3")
    if err is not None:
        return return_unexpected_failure(session_attributes, err)

    calendar_id = calendars.get(service, "Chatbot")
    slots = get_slots(event)

    try:
        response = events.get(service, calendar_id, slots.get("TimeMin"), slots.get("TimeMax"))
        return close(
            session_attributes,
            "Fulfilled",
            {"contentType": "PlainText", "content": ", ".join(response.keys())},
        )
    except Exception as err:
        return return_unexpected_failure(session_attributes, f"Failed to get events ({err})")
