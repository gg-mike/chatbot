from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def create_service(access_token: str, service_name: str, version: str) -> tuple:
    try:
        return build(service_name, version, credentials=Credentials(token=access_token)), None
    except Exception as err:
        return None, err


def get_items(getter) -> dict:
    page_token = None
    items = {}
    while True:
        response = getter(page_token).execute()
        for entry in response["items"]:
            items[entry["summary"]] = entry
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return items
