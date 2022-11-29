import requests
from utility import create_debug_logger, get_access_token


TOKEN_VERIFIER_URL = "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token="

logger = create_debug_logger()


def isAuthorized(headers):
    """Check if request is valid."""

    # Debug mode
    if headers.get("Debug") is not None:
        logger.warning("Debug mode enabled")
        return True

    # TODO: in future this function should ensure that request was made from application
    try:
        token, err = get_access_token(headers)
        if err is not None:
            logger.error(f"Encountered error while retrieving token: {err}")
            return False

        logger.debug("Processing token")
        code = requests.get(f"{TOKEN_VERIFIER_URL}{token}").status_code
        logger.debug(f"Return code for given token: {code}")
        return code == 200
    except:
        return False


def handler(event: dict, context: object) -> dict:
    response = {"isAuthorized": isAuthorized(event["headers"])}
    logger.debug(f"Response: {response}")
    return response
