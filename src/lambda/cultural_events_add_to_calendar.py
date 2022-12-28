from boto3.dynamodb.conditions import Key
import boto3
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import json
from googleapi import calendars, events
from setup_handler import google_api_handler as setup
from lex import (
    elicit_slot,
    close,
    delegate,
    build_validation_result,
    return_unexpected_failure,
)
from utility import create_debug_logger, isvalid_date, get_slots

logger = create_debug_logger()

# connect to dynamoDB
TABLE_NAME = "CulturalEvents"
dynamodb_client = boto3.resource("dynamodb")
events_table = dynamodb_client.Table(TABLE_NAME)


def validate_user_input(slots: dict) -> dict:
    """Validate user input

    Args:
        slots (dict): map of slot names, configured for the intent, to slot values that Amazon Lex has recognized in the user conversation. A slot value remains null until the user provides a value.

    Returns:
        dict: result of validation
    """

    date = slots.get("Date", None)
    cultural_event_index = slots.get("CulturalEventIndex", None)
    if date:
        if not isvalid_date(date):
            return build_validation_result(
                False, "Date", "Sorry, provided date is incorrectly formatted"
            )
        if parse(date) < datetime.today():
            return build_validation_result(
                False, "Date", "That date is in the past. Provide future date"
            )
    if cultural_event_index:
        try:
            string_int = int(cultural_event_index)
        except ValueError:
            return build_validation_result(
                False,
                "CulturalEventIndex",
                "Provided index is not an integer number. Provide valid index.",
            )
    return {"isValid": True}


def handler(event: dict, context: object) -> dict:
    """Route the incoming request based on intent. The JSON body of the request is provided in the event slot."""
    logger.debug("event.bot.name={}".format(event["bot"]["name"]))
    source = event.get("invocationSource", None)
    logger.debug(f"source {source}")
    logger.debug(f"slots {slots}")

    session_attributes, service, err = setup(event, "calendar", "v3")
    if err:
        logger.debug(f"setup error: {err}")
        return return_unexpected_failure(session_attributes, err)

    if source == "DialogCodeHook":
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

        calendar_id = calendars.get(service, "Chatbot")
        slots = get_slots(event)
        logger.debug(f"slots {slots}")
        logger.debug(f"session attributes {session_attributes}")

        cultural_event_index = int(slots.get("CulturalEventIndex", None))
        cultural_event_json = session_attributes.get(
            f"cultural_event_{cultural_event_index}", None
        )
        if not cultural_event_json:
            return close(
                session_attributes,
                "Fulfilled",
                {
                    "contentType": "PlainText",
                    "content": f"sorry, couldn't add cultural event ({cultural_event_json}) to calendar.",
                },
            )
        cultural_event = json.loads(cultural_event_json)

        logger.debug(
            f"cultural event with index ({cultural_event_index}): {cultural_event}"
        )

        try:
            body = {
                "summary": cultural_event.get("event_name", "Untitled"),
                "start": {"timeZone": "Europe/Warsaw"},
                "end": {"timeZone": "Europe/Warsaw"},
            }

            start_date = cultural_event["date_start"]
            end_date = cultural_event["date_end"]

            if cultural_event.get("time_start") is not None:
                start_time = cultural_event["time_start"]
                body["start"]["dateTime"] = f"{start_date}T{start_time}"
            else:
                body["start"]["date"] = start_date

            if cultural_event.get("time_end") is not None:
                end_time = cultural_event["time_end"]
                body["end"]["dateTime"] = f"{end_date}T{end_time}"
            else:
                body["end"]["date"] = end_date

            if cultural_event.get("location") is not None:
                body["location"] = cultural_event["location"]
            events.create(service, calendar_id, body)
            return close(
                session_attributes,
                "Fulfilled",
                {
                    "contentType": "PlainText",
                    "content": f'''Created event "{cultural_event.get("event_name","Untitled")}"''',
                },
            )
        except Exception as err:
            logger.debug(f"Error while adding cultural event to calendar: {err}")
            return return_unexpected_failure(
                session_attributes,
                f'''Failed to add event "{cultural_event.get("event_name","Untitled")}"''',
            )
