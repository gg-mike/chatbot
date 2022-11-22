import requests


def isValidToken(token):
    response = requests.get(
        f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token.split(' ')[1]}"
    )
    if response.status_code == 200:
        return True
    return False


def handler(event, context):
    isAuthorized = False
    try:
        isAuthorized = isValidToken(event["headers"]["authorization"])
    except Exception as e:
        print(e)

    return {"isAuthorized": isAuthorized}
