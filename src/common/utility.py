from datetime import datetime
from dateutil.parser import parse
from json import dumps, loads
from logging import getLogger, Logger, DEBUG


def create_debug_logger() -> Logger:
    """Create debug logger.

    Returns:
        Logger: debug root logger
    """
    logger = getLogger()
    logger.setLevel(DEBUG)
    return logger


def get_access_token(headers: dict) -> tuple:
    """Extract authorization token from event's header.

    If at any point of extraction occurs error, the error message will be sent back to the user
    and the token will be set to None.

    Args:
        headers (dict): header of the request

    Returns:
        tuple: extracted token and error message (if extraction was successful it is set to None)

    """
    token_locations = ["access_token", "Authorization", "authorization", "auth"]
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
    """Extract slots from the request.

    Args:
        event (dict): request (from Lex or API Gateway)

    Returns:
        dict: slots extracted from Lex request or API request or empty dictionary
    """
    if "currentIntent" in event:
        if "slots" in event["currentIntent"]:
            return event["currentIntent"]["slots"]

    if "body" in event:
        if event["body"]:
            event["body"] = loads(event["body"])
            if "slots" in event["body"]:
                return event["body"]["slots"]

    return {}


def simple_response(output) -> dict:
    """Creates simple response for Lambda.

    Args:
        output: JSON serializable data

    Returns:
        dict: response with timestamp
    """
    data = {"output": output, "timestamp": datetime.utcnow().isoformat()}
    return {
        "statusCode": 200,
        "body": dumps(data),
        "headers": {"Content-Type": "application/json"},
    }


def isvalid_date(date: str) -> bool:
    """Checks if provided date is correctly formatted

    Args:
        date (str): string containing date.

    Returns:
        bool: True if date is correctly formatted, False otherwise.
    """
    try:
        parse(date)
        return True
    except ValueError:
        return False
