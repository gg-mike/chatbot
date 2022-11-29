from googleapi import calendars, events, utils
import utility


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
        response = events.get(service, calendar_id, slots.get("TimeMin"), slots.get("TimeMax"))
        return utility.lex_response("Close", "Fulfilled", "PlainText", ", ".join(response.keys()))
    except Exception as err:
        return utility.error_lex_response(f"Failed to get events ({err})")
