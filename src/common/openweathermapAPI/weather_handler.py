from .utils import _find_nearest_time, get_secret, _eval_location
import json
import requests

# urls for requests to OpenWeatherMap API
BASE_URL_WEATHER_NOW = "https://api.openweathermap.org/data/2.5/weather?"
BASE_URL_WEATHER_FORECAST = "https://api.openweathermap.org/data/2.5/forecast?"


def get_weather_date(date: str = None, city: str = None, latitude: float = None, longitude: float = None):
    """get weather data basing on provided date

    Args:
        date (str, optional): date for forecast. Defaults to None.
        city (str, optional): city for forecast. Defaults to None.
        latitude (float, optional): latitude of city. Defaults to None.
        longitude (float, optional): longitud of city. Defaults to None.

    Returns:
        dict | list: weather data or None if error occurs
    """

    # get latitude and longitude of city provided by user
    if city and not latitude and not longitude:
        latitude, longitude = _eval_location(city)

    if not latitude and not longitude:
        return None

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

    if date:
        return _find_nearest_time(date, open_weather_map_data)
    else:
        return open_weather_map_data.get("list", None)


def get_weather_today(city: str):
    """get weather data on today

    Args:
        city (str): city for forecast

    Returns:
        dict: weather data or None if error occurs 
    """

    API_KEY = get_secret("OPEN_WEATHER_MAP_API_KEY")

    url = BASE_URL_WEATHER_NOW + "q=" + city + "&appid=" + API_KEY + "&units=metric"
    open_weather_map_data = handle_weather_api_request(url)
    if open_weather_map_data.get("weather", None):
        return open_weather_map_data
    else:
        return None


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
        return f"Http Error {errh}"
    except requests.exceptions.ConnectionError as errc:
        return f"Error Connecting {errc}"
    except requests.exceptions.Timeout as errt:
        return f"Timeout Error: {errt}"
    except requests.exceptions.RequestException as err:
        return {err}

    return json.loads(open_weather_map_response.text)
