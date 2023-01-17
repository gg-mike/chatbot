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
                False, "Date", "Sorry, provided date is incorrectly formatted."
            )
        if parse(date) < datetime.today():
            return build_validation_result(
                False, "Date", "That date is in the past. Provide future date."
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
    logger.debug(f"userId={event['userId']}, intentName={event['currentIntent']['name']}")
    source = event.get("invocationSource", None)
    slots = event["currentIntent"]["slots"]

    session_attributes = event.get("sessionAttributes", {})
    logger.debug(f"source {source}")
    logger.debug(f"slots {slots}")

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

        date = slots.get("Date", None)
        city = slots.get("City", session_attributes.get("defaultLocation", None))
            
        response_message = ""

        response = events_table.query(KeyConditionExpression=Key("location").eq((city)))
        items = response["Items"]
        if date:
            items = [item for item in items if item.get("date_start", None) == date]
        else:
            # get ongoing events for next week
            response_message += "No date provided, getting events for next month."
            items = [
                item
                for item in items
                if datetime.today()
                <= parse(item.get("date_start", datetime.today()))
                <= datetime.today() + relativedelta(days=30)
            ]

        logger.debug(f"Items: {items}")

        if items:
            for count, item in enumerate(items):
                session_attributes[f"cultural_event_{count+1}"] = json.dumps(item)
                response_message += f"{count+1}) Event name: {item.get('event_name','Untitled')} "
                if item.get("date_start", None):
                    response_message += f"starts at: {item.get('date_start','no date specified')} {item.get('time_start', '')}) "
                if item.get("date_end", None):
                    response_message += (
                        f"ends at: {item.get('date_end','no date specified')} {item.get('time_end','')}\n"
                    )
                item['datetime_start'] = events.get_datetime(datetime(item['date_start']), datetime(item['time_start']))
                item['datetime_end'] = events.get_datetime(datetime(item['date_end']), datetime(item['time_end']))
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
                {"contentType": "CustomPayload", "content": json.dumps({
                    "type": "culturalEvent",
                    "header": f"List of cultural events in {city}",
                    "objects": json.dumps(items),
                    "response": response_message
                })
                })
