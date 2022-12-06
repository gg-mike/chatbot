import requests

from utility import create_debug_logger, get_access_token

TOKEN_VERIFIER_URL = "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token="
GOOGLE_TOKEN_AUDIENCE = "529321912966-hlh7d2v96mkutruodo99ug9t6vjsen7r.apps.googleusercontent.com"
MINIMUM_EXPIRATION_TIME = 15

logger = create_debug_logger()


def isTokenValid(token):
    logger.debug("Processing token")
    response = requests.get(f"{TOKEN_VERIFIER_URL}{token}")
    logger.debug(f"{response=}")
    body = response.json()
    if (
        response.status_code == requests.codes["ok"]
        and body["expires_in"] > MINIMUM_EXPIRATION_TIME
        and body["audience"] == GOOGLE_TOKEN_AUDIENCE
    ):
        return True
    return False


def isAuthorized(headers):
    """Check if request is valid."""

    # Debug mode
    if headers.get("Debug") is not None:
        logger.warning("Debug mode enabled")
        return True

    try:
        token, err = get_access_token(headers)
        if err is not None:
            logger.error(f"Encountered error while retrieving token: {err}")
            return False

        return isTokenValid(token)
    except Exception as err:
        logger.error(f"Encountered error while validating token: {err}")
        return False


def handler(event: dict, context: object) -> dict:
    logger.debug(f"{event=}")
    response = {"isAuthorized": isAuthorized(event["headers"])}
    logger.debug(f"{response=}")
    return response
