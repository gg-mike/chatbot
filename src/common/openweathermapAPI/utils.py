import time
import json
import boto3
from geopy.geocoders import Nominatim
from botocore.exceptions import ClientError
from dateutil.parser import parse


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
    client = session.client(
        service_name="secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Extracting the key/value from the secret
    secret = get_secret_value_response["SecretString"]
    secret_string = json.loads(secret)[secret_key]

    return secret_string


def _eval_location(city: str):
    """Get latitude and longitude basing on name of the city

    Args:
        city (str): city

    Returns:
        tuple : latitude and longitude or (None,None) if error occurs
    """
    try:
        geolocator = Nominatim(user_agent="myapplication")
        location = geolocator.geocode(city)
        return (location.latitude, location.longitude)
    except:
        return (None, None)


def _find_nearest_time(date: str, weather_data: dict) -> dict:
    """Finds the most fitting forecast record basing on date provided by user

    Args:
        date (str): correctly formatted date-like string
        weather_data (dict): data fetched from OpenWeatherMapAPI

    Returns:
        dict: key-value par of weather data from OpenWeatherMapAPI
    """
    date_to_search_unix = time.mktime(parse(date).timetuple())
    return min(weather_data["list"], key=lambda x: abs(x["dt"] - date_to_search_unix))
