# from googleapi import calendars, events, utils
# import utility


def handler(event, context):
    return {
        "statusCode": 200,
        "body": {},
        "headers": {"Content-Type": "application/json"},
    }
    # token, err = utility.get_access_token(event["headers"])
    # if err is not None:
    #     return utility.error_lex_response(f"Bad Request: {err}")
    # return { "body": token }

    # service, err = utils.create_service(token, "calendar", "v3")
    # if err is not None:
    #     return utility.error_lex_response(f"Could not create Google Service ({err})")

    # calendar_id = calendars.get(service, "Chatbot")
    # slots = utility.get_slots(event)

    # try:
    #     response = events.get(service, calendar_id, slots.get("timeMin"), slots.get("timeMax"))
    #     return utility.lex_response("Close", "Fulfilled", "CustomPayload", response.keys())
    # except Exception as err:
    #     return utility.error_lex_response(f"Failed to get events")
