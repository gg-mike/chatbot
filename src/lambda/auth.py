import requests


def isAuthorized(headers):
    """Check if request is valid."""

    # Debug mode
    if headers.get("Debug") == True:
        return True

    # TODO: in future this function should ensure that request was made from application
    try:
        token = headers["Authorization"].split(" ")[1]
        response = requests.get(
            f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}"
        )
        if response.status_code == 200:
            return True
    except:
        return False

    return False


def handler(event, context):
    return {"isAuthorized": isAuthorized(event["headers"])}
