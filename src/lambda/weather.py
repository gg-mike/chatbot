from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from geopy.geocoders import Nominatim
from botocore.exceptions import ClientError
import boto3
import json
import requests
import time

from lex import elicit_slot, close, delegate, return_unexpected_failure, build_validation_result
from utility import create_debug_logger, isvalid_date


# urls for requests to OpenWeatherMap API
BASE_URL_WEATHER_NOW = "https://api.openweathermap.org/data/2.5/weather?"
BASE_URL_WEATHER_FORECAST = "https://api.openweathermap.org/data/2.5/forecast?"

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
        if parse(date) < datetime.today():
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


### UTILS ###


def _find_nearest_time(date: str, weather_data: dict) -> dict:
    """Finds most fitting forecast record basing on date provided by user

    Args:
        date (str): correctly formatted date-like string
        weather_data (dict): data fetched from OpenWeatherMapAPI

    Returns:
        dict: key-value par of weather data from OpenWeatherMapAPI
    """
    date_to_search_unix = time.mktime(parse(date).timetuple())
    return min(weather_data["list"], key=lambda x: abs(x["dt"] - date_to_search_unix))


def get_secret(secret_key: str) -> str:
    """Get secret value by its name from Amazon Secrets Manager

    Args:
        secret_key (str): key name of secret

    Returns:
        str: value of secret
    """
    # Your secret's name and region
    secret_name = "secrets/dev/openweathermapkey"
    region_name = "eu-west-2"

    # Set up our Session and Client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Extracting the key/value from the secret
    secret = get_secret_value_response["SecretString"]
    secret_string = json.loads(secret)[secret_key]

    return secret_string


def handle_weather_api_request(url: str) -> dict:
    """send request to OpenWeatherAPI

    Args:
        url (str): url for request

    Returns:
        dict: data fetched from API
    """
    try:
        open_weather_map_response = requests.get(url)
        open_weather_map_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logger.debug(f"Http Error {errh}")
        return None
    except requests.exceptions.ConnectionError as errc:
        logger.debug(f"Error Connecting {errc}")
        return None
    except requests.exceptions.Timeout as errt:
        logger.debug(f"Timeout Error: {errt}")
        return None
    except requests.exceptions.RequestException as err:
        logger.debug({err})
        return None

    return json.loads(open_weather_map_response.text)


### INTENTS ###


def get_weather_forecast(intent_request: dict) -> dict:
    """Handles user request for future weather forecast

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
        else dict()
    )

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
        city = slots.get("City", None)
        date = slots.get("Date", None)

        # get latitude and longitude of city provided by user
        geolocator = Nominatim(user_agent="myapplication")
        location = geolocator.geocode(city)
        latitude = location.latitude
        longitude = location.longitude

        API_KEY = get_secret("OPEN_WEATHER_MAP_API_KEY")
        url = (
            BASE_URL_WEATHER_FORECAST
            + "lat="
            + str(latitude)
            + "&lon="
            + str(longitude)
            + "&appid="
            + API_KEY
            + "&units=metric"
        )

        open_weather_map_data = handle_weather_api_request(url)
        if open_weather_map_data.get("list", None):
            nearest_weather = _find_nearest_time(date, open_weather_map_data)
            weather = nearest_weather["weather"][0]["main"]
            temp = nearest_weather["main"]["temp"]
            pressure = nearest_weather["main"]["pressure"]
            response = f"Weather in {open_weather_map_data['city']['name']} for {date}: {weather} temperature: {temp} pressure: {pressure}"
            return close(
                session_attributes, "Fulfilled", {"contentType": "PlainText", "content": response}
            )
        else:
            return_unexpected_failure(session_attributes, "Someting went wrong, try again later.")


def get_weather_now(intent_request: dict) -> dict:
    """Handles user request for future weather forecast

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

        city = slots["City"]
        API_KEY = get_secret("OPEN_WEATHER_MAP_API_KEY")

        url = BASE_URL_WEATHER_NOW + "q=" + city + "&appid=" + API_KEY + "&units=metric"
        open_weather_map_data = handle_weather_api_request(url)
        if open_weather_map_data.get("weather", None):
            weather = open_weather_map_data["weather"][0]["main"]
            temp = open_weather_map_data["main"]["temp"]
            pressure = open_weather_map_data["main"]["pressure"]

            response = f"Overall weather in {city} for today: {weather}, temperature: {temp} degrees Celsius, pressure: {pressure}hPa"
            logger.debug(f"response: {response}")

            return close(
                session_attributes, "Fulfilled", {"contentType": "PlainText", "content": response}
            )
        else:
            return_unexpected_failure(session_attributes, "Something went wrong, try again later.")


### DISPATCH ###
def dispatch(intent_request: dict) -> dict:
    """Called when specifying an intent.

    Args:
        intent_request (dict): data containg information about ongoing intent

    Raises:
        Exception: raised when intention name is not found

    Returns:
        dict: data to send to Lex
    """

    intent_name = intent_request["currentIntent"]["name"]

    if intent_name == "GetWeatherDate":
        return get_weather_forecast(intent_request)

    elif intent_name == "GetWeatherNow":
        return get_weather_now(intent_request)

    raise Exception("Intent with name " + intent_name + " is not supported")


### LAMBDA HANDLER ###


def handler(event: dict, context: object) -> dict:
    """Route the incoming request based on intent. The JSON body of the request is provided in the event slot."""

    logger.debug(f"event.bot.name={event['bot']['name']}")
    logger.debug(f"userId={event['userId']}, intentName={event['currentIntent']['name']}")

    return dispatch(event)
