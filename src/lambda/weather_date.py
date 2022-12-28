from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from lex import (
    elicit_slot,
    close,
    delegate,
    return_unexpected_failure,
    build_validation_result,
)
from utility import create_debug_logger, isvalid_date
from openweathermapAPI import weather_handler


logger = create_debug_logger()


def validate_user_input(slots: dict) -> dict:
    """Validate user input

    Args:
        slots (dict): map of slot names, configured for the intent, to slot values that Amazon Lex has recognized in the user conversation. A slot value remains null until the user provides a value.

    Returns:
        dict: result of validation
    """
    date = slots.get("Date", None)

    if date:
        if not isvalid_date(date):
            return build_validation_result(
                False, "Date", "Sorry, provided date is incorrectly formatted"
            )
        if parse(date) < datetime.today() - relativedelta(days=1):
            return build_validation_result(
                False, "Date", "That date is in the past. Provide future date"
            )
        if datetime.today() + relativedelta(days=5) < parse(date):
            return build_validation_result(
                False,
                "Date",
                f"Sorry, we currently don't support forecasts for dates further than 5 days from now.",
            )

    return {"isValid": True}


def handler(event: dict, context: object) -> dict:
    """Route the incoming request based on intent. The JSON body of the request is provided in the event slot."""

    logger.debug(f"event.bot.name={event['bot']['name']}")
    logger.debug(f"userId={event['userId']}, intentName={event['currentIntent']['name']}")

    source = event["invocationSource"]
    slots = event["currentIntent"]["slots"]
    session_attributes = event.get("sessionAttributes", {})

    if event["invocationSource"] == "DialogCodeHook":
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_user_input(event["currentIntent"]["slots"])
        if not validation_result["isValid"]:
            slots = event["currentIntent"]["slots"]
            slots[validation_result["violatedSlot"]] = None

            return elicit_slot(
                session_attributes,
                event["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )
        return delegate(session_attributes, slots)

    if source == "FulfillmentCodeHook":
        city = slots.get("City", None)
        date = slots.get("Date", None)

        open_weather_map_data = weather_handler.get_weather_date(date, city)

        if open_weather_map_data:
            weather = open_weather_map_data["weather"][0]["main"]
            temp = open_weather_map_data["main"]["temp"]
            pressure = open_weather_map_data["main"]["pressure"]
            response = (
                f"Weather in {city} for {date}: {weather} temperature: {temp} pressure: {pressure}"
            )
            return close(
                session_attributes,
                "Fulfilled",
                {"contentType": "PlainText", "content": response},
            )
        else:
            return return_unexpected_failure(
                session_attributes, "Something went wrong, try again later."
            )
