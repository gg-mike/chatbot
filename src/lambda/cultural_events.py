from boto3.dynamodb.conditions import Key
from datetime import datetime
from dateutil.parser import parse
from unidecode import unidecode
import boto3

from lex import elicit_slot, close, delegate, build_validation_result
from utility import create_debug_logger, isvalid_date


logger = create_debug_logger()

# connect to dynamoDB
TABLE_NAME = "cultural_events"
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

    if date:
        if not isvalid_date(date):
            return build_validation_result(
                False, "Date", "Sorry, provided date is incorrectly formatted"
            )
        if parse(date) < datetime.today():
            return build_validation_result(
                False, "Date", "That date is in the past. Provide future date"
            )

    return {"isValid": True}


def get_cultural_events_by_date(intent_request: dict) -> dict:
    """Handles user request for future cultural event by specific date, city is optional

    Args:
        intent_request (dict): data containg information about ongoing intent

    Returns:
        dict: data to send to Lex
    """

    source = intent_request["invocationSource"]
    slots = intent_request["currentIntent"]["slots"]

    session_attributes = (
        intent_request["sessionAttributes"]
        if intent_request["sessionAttributes"] is not None
        else {}
    )

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
        logger.debug("FulfillmentCodeHook activated")

        date = slots.get("Date", None)
        city = slots.get("City", None)

        response = events_table.query(KeyConditionExpression=Key("start_date").eq(date))
        items = response["Items"]
        logger.debug(f"Items: {items}")

        if city:
            items = [
                item
                for item in items
                if unidecode(item.get("location", "poznań")).lower() == city.lower()
            ]

        if items:
            response_message = ""
            for count, item in enumerate(items):
                response_message += f"{count+1}) Event name: {item['event_name']}\n "
                if item.get("start_time", None):
                    response_message += f"starts at: {item['start_time']}\n "
                if item.get("end_time", None):
                    response_message += f"ends at: {item['end_time']}\n "
                if item.get("link", None):
                    response_message += f"read more: {item['link']}\n "

        else:
            response_message = f"There are no ongoing events on {date}"
            if city:
                response_message += f" in {city}"
        return close(
            session_attributes,
            "Fulfilled",
            {"contentType": "PlainText", "content": response_message},
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
    if intent_name == "GetCulturalEventDate":
        return get_cultural_events_by_date(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


def handler(event: dict, context: object) -> dict:
    """Route the incoming request based on intent. The JSON body of the request is provided in the event slot."""
    logger.debug("event.bot.name={}".format(event["bot"]["name"]))
    return dispatch(event)
