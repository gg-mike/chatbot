from .utils import get_items


def create(service, name: str, mod: str = "a"):
    calendars = get_all(service)
    body = {"summary": name}

    if mod == "a" and name not in calendars:
        return service.calendars().insert(body=body).execute()["id"]
    elif mod in ["n", "o"]:
        if mod == "o":
            delete(service, name)
        return service.calendars().insert(body=body).execute()["id"]


def get_all(service):
    return get_items(lambda page_token: service.calendarList().list(pageToken=page_token))


def get(service, name: str, create_if_not_exists: bool = True):
    calendars = get_all(service)
    if name in calendars:
        return calendars[name]["id"]
    if create_if_not_exists:
        return create(service, name, "n")
    return None


def delete(service, name: str):
    calendar_id = get(service, name, False)
    if calendar_id is not None:
        response = service.calendars().delete(calendarId=calendar_id).execute()
        print(response)
    else:
        print(f"Calendar named '{name}' not found")
