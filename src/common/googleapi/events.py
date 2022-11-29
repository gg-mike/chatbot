from datetime import date, datetime
from pytz import timezone

from googleapi.utils import get_items


def create(service, calendar_id: str, event: dict):
    return service.events().insert(calendarId=calendar_id, body=event).execute()


def get_datetime(date_str: str, dt_time: datetime.time) -> str:
    dt_tz = timezone("Europe/Warsaw")
    dt = datetime.combine(date.fromisoformat(date_str), dt_time)
    return str(dt_tz.localize(dt)).replace(" ", "T")


def get(service, calendar_id: str, date_min: str = None, date_max: str = None):
    t_min = get_datetime(date_min, datetime.min.time()) if date_min is not None else None
    t_max = get_datetime(date_max, datetime.max.time()) if date_max is not None else None

    return get_items(
        lambda page_token: service.events().list(
            calendarId=calendar_id, pageToken=page_token, timeMax=t_max, timeMin=t_min
        )
    )
