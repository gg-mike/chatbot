import requests
from utility import get_access_token


TOKEN_VERIFIER_URL = "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token="


def isAuthorized(headers):
    """Check if request is valid."""

    # Debug mode
    if headers.get("Debug") is not None:
        print("!!! DEBUG MODE ENABLED !!!")
        return True

    # TODO: in future this function should ensure that request was made from application
    try:
        token, err = get_access_token(headers)
        if err is not None:
            print(f"Encountered error while retrieving token: {err}")
            return False

        print("Processing token")
        code = requests.get(f"{TOKEN_VERIFIER_URL}{token}").status_code
        print(f"Return code for given token: {code}")
        return code == 200
    except:
        return False


def handler(event, context):
    response = {"isAuthorized": isAuthorized(event["headers"])}
    print(f"Response: {response}")
    return response
