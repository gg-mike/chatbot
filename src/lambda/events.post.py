from googleapi import calendars, events, utils
import utility


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


def handler(event, context):
    token, err = utility.get_access_token(event["headers"])
    if err is not None:
        return utility.error_lex_response(f"Bad Request: {err}")

    service, err = utils.create_service(token, "calendar", "v3")
    if err is not None:
        return utility.error_lex_response(f"Could not create Google Service ({err})")

    calendar_id = calendars.get(service, "Chatbot")
    slots = utility.get_slots(event)

    try:
        events.create(service, calendar_id, create_event_body(slots))
        return utility.lex_response(
            "Close",
            "Fulfilled",
            "PlainText",
            f"Created event '{slots['EventName']}'",
        )
    except Exception as err:
        return utility.error_lex_response(f"Failed to create event '{slots['EventName']}'")
