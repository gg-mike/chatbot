from datetime import datetime
from json import dumps, loads


def get_access_token(headers: dict) -> tuple:
    token_locations = ["Authorization", "authorization", "auth"]
    token = None
    err = f"Authorization key missing (use one of this keys: {', '.join(token_locations)})"

    for token_location in token_locations:
        _token = headers.get(token_location)
        if _token is not None:
            token = _token.split(" ")[-1]
            err = None
            break

    return token, err


def get_slots(event: dict) -> dict:
    if "currentIntent" in event:
        if "slots" in event["currentIntent"]:
            return event["currentIntent"]["slots"]

    if "body" in event:
        if event["body"]:
            event["body"] = loads(event["body"])
            if "slots" in event["body"]:
                return event["body"]["slots"]

    return {}


def value_guard(value: str, allowed_values: set, fallback: str) -> str:
    return value if value in allowed_values else fallback


def lex_response(action_type: str, fulfillment_state: str, content_type: str, content):
    """
    Response for Lambda formatted for Lex.
    See [AWS Documentation](https://docs.aws.amazon.com/lex/latest/dg/API_runtime_DialogAction.html) for more information.

    Action type, fulfillment state and content type are check if they contain allowed values.
    In the case where given value does not matched allowed values it is set to its fallback.

    Fallback:
    Action type: `Close`
    Fulfillment state: `Failed`
    Content type: `PlainText`
    """

    ALLOWED_ACTION_TYPES = {"ElicitIntent", "ConfirmIntent", "ElicitSlot", "Close", "Delegate"}
    ALLOWED_FULFILLMENT_STATE = {"Fulfilled", "Failed", "ReadyForFulfillment"}
    ALLOWED_CONTENT_TYPE = {"PlainText", "CustomPayload", "SSML", "Composite"}

    return {
        "dialogAction": {
            "type": value_guard(action_type, ALLOWED_ACTION_TYPES, "Close"),
            "fulfillmentState": value_guard(fulfillment_state, ALLOWED_FULFILLMENT_STATE, "Failed"),
            "message": {
                "contentType": value_guard(content_type, ALLOWED_CONTENT_TYPE, "PlainText"),
                "content": content,
            },
        }
    }


def error_lex_response(message) -> dict:
    return lex_response(
        "Close",
        "Fulfilled",
        "PlainText",
        message,
    )


def simple_response(output):
    data = {"output": output, "timestamp": datetime.utcnow().isoformat()}
    return {
        "statusCode": 200,
        "body": dumps(data),
        "headers": {"Content-Type": "application/json"},
    }
