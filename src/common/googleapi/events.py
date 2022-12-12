from datetime import datetime, timedelta
from pytz import timezone

from googleapi.utils import get_items


def create(service, calendar_id: str, event: dict):
    return service.events().insert(calendarId=calendar_id, body=event).execute()


def get_datetime(date, time) -> str:
    dt = datetime.combine(date, time)
    return str(timezone("Europe/Warsaw").localize(dt)).replace(" ", "T")


def get(service, calendar_id: str, d_min: str = None, d_max: str = None):
    dt_now = datetime.now()

    dt_min = datetime.fromisoformat(d_min) if d_min is not None else dt_now
    dt_max = datetime.fromisoformat(d_max) if d_max is not None else dt_min + timedelta(days=7)

    t_min = get_datetime(dt_min.date(), datetime.min.time())
    t_max = get_datetime(dt_max.date(), datetime.max.time())

    return (
        get_items(
            lambda page_token: service.events().list(
                calendarId=calendar_id,
                pageToken=page_token,
                timeMax=t_max,
                timeMin=t_min,
                orderBy="startTime",
                singleEvents=True,
                maxResults=10,
            )
        ),
        t_min.split("T")[0],
        t_max.split("T")[0],
        dt_min.date() == dt_now.date(),
    )
