from googleapi import calendars, events
from json import loads
from lex import close, return_unexpected_failure
from openweathermapAPI import weather_handler
from setup_handler import google_api_handler as setup
from utility import create_debug_logger

logger = create_debug_logger()


def get_info_on_upcoming_event(default_location: str, session_attributes: dict, service) -> tuple:
    if "upcomingEvent" in session_attributes:
        upcoming_event = loads(session_attributes["upcomingEvent"])

        return upcoming_event.get("location", default_location), upcoming_event["start"], None

    calendar_id = calendars.get(service, "Chatbot")
    try:
        items, *_ = events.get(service, calendar_id, days_delta=5)
    except Exception as err:
        return (
            None,
            None,
            return_unexpected_failure(
                session_attributes, f"Failed to get weather for the upcoming event ({err})"
            ),
        )

    if len(items) == 0:
        return (
            None,
            None,
            close(
                session_attributes,
                "Fulfilled",
                {
                    "contentType": "PlainText",
                    "content": f"You have no upcoming events within a five-day window",
                },
            ),
        )

    return items[0]["location"], items[0]["start"], None


def handler(event: dict, context: object) -> dict:
    logger.debug(f"{event=}")

    session_attributes, service, err = setup(event, "calendar", "v3")
    if err is not None:
        return return_unexpected_failure(session_attributes, err)

    location, startDict, message = get_info_on_upcoming_event("Poznań", session_attributes, service)  # TODO: Change default location from Poznań to location of client's app

    if message is not None:
        return message

    if "date" in startDict:
        start = startDict["date"]
    else:
        start = startDict["dateTime"].split("T")[0]

    open_weather_map_data = weather_handler.get_weather_date(start, location)

    if open_weather_map_data:
        weather = open_weather_map_data["weather"][0]["main"]
        temp = open_weather_map_data["main"]["temp"]
        pressure = open_weather_map_data["main"]["pressure"]
        response = f"Weather for upcoming event ({start} in {location}) : {weather} temperature: {temp} pressure: {pressure}"
        return close(
            session_attributes, "Fulfilled", {"contentType": "PlainText", "content": response}
        )

    return return_unexpected_failure(session_attributes, "Something went wrong, try again later.")
