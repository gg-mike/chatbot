from googleapi import calendars, events
from json import dumps
from lex import close, return_unexpected_failure
from setup_handler import google_api_handler as setup
from utility import create_debug_logger, get_slots

logger = create_debug_logger()


def filter_dict(d: dict, allowed_keys: list) -> dict:
    return {k: d[k] for k in set(allowed_keys).intersection(d.keys())}


def handler(event: dict, context: object) -> dict:
    logger.debug(f"{event=}")

    session_attributes, service, err = setup(event, "calendar", "v3")
    if err is not None:
        return return_unexpected_failure(session_attributes, err)

    calendar_id = calendars.get(service, "Chatbot")
    slots = get_slots(event)
    logger.debug(f"{slots=}")

    try:
        items, t_min, t_max, is_current_events = events.get(
            service, calendar_id, slots.get("StartDate"), slots.get("EndDate")
        )

        if len(items) == 0:
            return close(
                session_attributes,
                "Fulfilled",
                {
                    "contentType": "PlainText",
                    "content": f"You have no events from {t_min} to {t_max}",
                },
            )

        items = {k: filter_dict(v, ["location", "start", "end"]) for k, v in items.items()}
        if is_current_events:
            session_attributes["upcomingEvent"] = dumps(list(items.values())[0])

        objects = []
        for k, v in items.items():
            v["name"] = k
            objects.append(v)

        return close(
            session_attributes,
            "Fulfilled",
            {
                "contentType": "CustomPayload",
                "content": dumps({"type": "event", "objects": objects}),
            },
        )
    except Exception as err:
        return return_unexpected_failure(session_attributes, f"Failed to get events ({err})")
