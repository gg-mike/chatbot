from googleapi import calendars, events
from lex import close, return_unexpected_failure
from setup_handler import google_api_handler as setup
from utility import get_slots


def create_event_body(data):
    body = {
        "summary": data["EventName"],
        "start": {"timeZone": "Europe/Warsaw"},
        "end": {"timeZone": "Europe/Warsaw"},
    }

    start_date = data["StartDate"]
    end_date = data["EndDate"]

    if data.get("StartTime") is not None:
        start_time = data["StartTime"]
        body["start"]["dateTime"] = f"{start_date}T{start_time}"
    else:
        body["start"]["date"] = start_date

    if data.get("EndTime") is not None:
        end_time = data["EndTime"]
        body["end"]["dateTime"] = f"{end_date}T{end_time}"
    else:
        body["end"]["date"] = end_date

    if data.get("Location") is not None:
        body["location"] = data["Location"]

    if data.get("Description") is not None:
        body["description"] = data["Description"]

    return body


def handler(event: dict, context: object) -> dict:
    session_attributes, token, service, err = utils.setup(event, "calendar", "v3")
    if err is not None:
        return return_unexpected_failure(session_attributes, err)

    calendar_id = calendars.get(service, "Chatbot")
    slots = get_slots(event)

    try:
        events.create(service, calendar_id, create_event_body(slots))
        return close(
            session_attributes,
            "Fulfilled",
            {"contentType": "PlainText", "content": f"Created event '{slots['EventName']}'"},
        )
    except Exception as err:
        return return_unexpected_failure(
            session_attributes, f"Failed to create event '{slots['EventName']}'"
        )
