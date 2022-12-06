from googleapi import calendars, events
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
        items, t_min, t_max = events.get(
            service, calendar_id, slots.get("StartDate"), slots.get("EndDate")
        )
        logger.debug(f"{t_min=}")
        logger.debug(f"{t_max=}")
        
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
        return close(
            session_attributes,
            "Fulfilled",
            {"contentType": "CustomPayload", "content": f"{items}"},
        )
    except Exception as err:
        return return_unexpected_failure(session_attributes, f"Failed to get events ({err})")
