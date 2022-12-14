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
                "Provided index is not an integeer number. Provide valid index.",
            )
    return {"isValid": True}


def get_cultural_events_by_city(intent_request: dict) -> dict:
    """Handles user request for future cultural event by specific date, city is optional

    Args:
        intent_request (dict): data containg information about ongoing intent

    Returns:
        dict: data to send to Lex
    """

    source = intent_request.get("invocationSource", None)
    slots = intent_request.get(["currentIntent"]["slots"], None)

    session_attributes = intent_request.get("sessionAttributes", {})
    logger.debug(f"source {source}")
    logger.debug(f"slots {slots}")

    if intent_request["invocationSource"] == "DialogCodeHook":
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_user_input(intent_request["currentIntent"]["slots"])
        if not validation_result["isValid"]:
            slots = intent_request["currentIntent"]["slots"]
            slots[validation_result["violatedSlot"]] = None

            return elicit_slot(
                session_attributes,
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )
        return delegate(session_attributes, slots)

    if source == "FulfillmentCodeHook":

        date = slots.get("Date", None)
        city = slots.get("City", None)
        response_message = ""

        response = events_table.query(KeyConditionExpression=Key("location").eq((city)))
        items = response["Items"]
        if date:
            items = [item for item in items if item.get("date_start", None) == date]
        else:
            # get ongoing events for next week
            response_message += "No date provided, getting events for next week "
            items = [
                item
                for item in items
                if datetime.today()
                <= parse(item.get("date_start", datetime.today()))
                <= datetime.today() + relativedelta(days=7)
            ]

        logger.debug(f"Items: {items}")

        if items:
            for count, item in enumerate(items):
                session_attributes[f"cultural_event_{count+1}"] = json.dumps(item)
                response_message += f"{count+1}) Event name: {item.get('event_name','no title')}\n "
                if item.get("time_start", None):
                    response_message += f"starts at {item.get('date_start','no date specified')} {item['time_start']}\n "
                if item.get("time_end", None):
                    response_message += (
                        f"ends at {item.get('date_end','no date specified')} {item['time_end']}\n "
                    )
                if item.get("link", None):
                    response_message += f"read more: {item['link']}\n "

        else:
            response_message = f"There are no ongoing events in {city}"
            if date:
                response_message += f" on {date}"

        logger.debug(f"items before close {items}")
        logger.debug(f"response message before close {response_message}")
        logger.debug(f"session attributes {session_attributes}")
        return close(
            session_attributes,
            "Fulfilled",
            {"contentType": "PlainText", "content": response_message},
        )


def add_cultural_event_to_calendar(intent_request: dict) -> dict:

    source = intent_request.get("invocationSource", None)
    slots = intent_request.get(["currentIntent"]["slots"], None)
    logger.debug(f"source {source}")
    logger.debug(f"slots {slots}")

    session_attributes, service, err = setup(intent_request, "calendar", "v3")
    if err is not None:
        return return_unexpected_failure(session_attributes, err)

    if intent_request["invocationSource"] == "DialogCodeHook":
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_user_input(intent_request["currentIntent"]["slots"])
        if not validation_result["isValid"]:
            slots = intent_request["currentIntent"]["slots"]
            slots[validation_result["violatedSlot"]] = None

            return elicit_slot(
                session_attributes,
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )
        return delegate(session_attributes, slots)

    if source == "FulfillmentCodeHook":

        calendar_id = calendars.get(service, "Chatbot")
        slots = get_slots(intent_request)
        logger.debug(f"slots {slots}")
        logger.debug(f"session attributes {session_attributes}")

        cultural_event_index = int(slots.get("CulturalEventIndex", None))
        cultural_event_json = session_attributes.get(f"cultural_event_{cultural_event_index}", None)

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

        logger.debug(f"cultural event with index ({cultural_event}): {cultural_event}")

        try:
            body = {
                "summary": cultural_event.get("event_name", "Untitiled"),
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
                body["location"] = cultural_event["Location"]
                events.create(service, calendar_id, body)
        except Exception as err:
            return return_unexpected_failure(
                session_attributes,
                f'''Failed to add event "{cultural_event.get("event_name","Untitiled")}"''',
            )

        return close(
            session_attributes,
            "Fulfilled",
            {
                "contentType": "PlainText",
                "content": f'''Created event "{cultural_event.get("event_name","Untitiled")}"''',
            },
        )


def dispatch(intent_request: dict) -> dict:
    """Called when specifying an intent.

    Args:
        intent_request (dict): data containg information about ongoing intent

    Raises:
        Exception: raised when intention name is not found

    Returns:
        dict: data to send to Lex
    """
    logger.debug(
        "dispatch userId={}, intentName={}".format(
            intent_request["userId"], intent_request["currentIntent"]["name"]
        )
    )

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to your bot's intent handlers
    if intent_name == "GetCulturalEventsCity":
        return get_cultural_events_by_city(intent_request)
    elif intent_name == "AddCulturalEventToCalendar":
        return add_cultural_event_to_calendar(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


def handler(event: dict, context: object) -> dict:
    """Route the incoming request based on intent. The JSON body of the request is provided in the event slot."""
    logger.debug("event.bot.name={}".format(event["bot"]["name"]))
    return dispatch(event)
