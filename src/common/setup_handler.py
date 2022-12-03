from googleapi.utils import create_service
from utility import get_access_token


def google_api_handler(event: dict, service_name: str, version: str) -> tuple:
    """Setup necessary variables for Lambdas connected with Google API

    Args:
        event (dict): request
        service_name (str): Google service name
        version (str): version of service

    Returns:
        tuple: session attributes, google service and error message (None if no error occurred)
    """

    session_attributes = event["session_attributes"] if "session_attributes" in event else {}

    auth_locations = ["requestAttributes", "headers"]
    token = None
    err = f"Token location key missing (use one of this keys: {', '.join(auth_locations)})"

    for location in auth_locations:
        if location in event:
            token, err = get_access_token(event[location])
            if err is None:
                break

    if err is not None:
        return session_attributes, None, f"Bad Request: {err}"

    service, err = create_service(token, service_name, version)
    if err is not None:
        return session_attributes, None, f"Could not create Google Service ({err})"

    return session_attributes, service, None
