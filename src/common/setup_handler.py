from googleapi.utils import create_service
from utility import get_access_token


def google_api_handler(event: dict, service_name: str, version: str) -> tuple:
    """Setup necessary variables for Lambdas connected with Google API

    Args:
        event (dict): request
        service_name (str): Google service name
        version (str): version of service

    Returns:
        tuple: access token, google service, session attributes and
            error message (None if no error occurred)
    """

    session_attributes = event["session_attributes"] if "session_attributes" in event else {}

    token, err = get_access_token(event["headers"])
    if err is not None:
        return session_attributes, None, None, f"Bad Request: {err}"

    service, err = create_service(token, service_name, version)
    if err is not None:
        return session_attributes, token, None, f"Could not create Google Service ({err})"

    return session_attributes, token, service, None
