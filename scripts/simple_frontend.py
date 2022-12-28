import os
import requests
from dotenv import load_dotenv
from random import getrandbits

load_dotenv()

url = "https://ggcxf1l9ac.execute-api.eu-west-2.amazonaws.com/Prod/core"
access_token = os.getenv("ACCESS_TOKEN")


def send_request(user_id: str, input_text: str, session_attributes: dict):
    try:
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "Debug": "True",
            },
            json={
                "userId": user_id,
                "inputText": input_text,
                "sessionAttributes": session_attributes,
            },
        )
        response_json = response.json()
    except requests.exceptions.JSONDecodeError as e:
        return f'--Error: {e} (response="{response.text}", status_code={response.status_code})', {}

    message = (
        response_json.get("ResponseMetadata", {}).get("HTTPHeaders", {}).get("x-amz-lex-message")
    )
    session_attributes = response_json.get("sessionAttributes", {})
    if message is None:
        return "--No message", session_attributes
    return message, session_attributes


def main():
    user_id = f"{getrandbits(32):x}"
    session_attributes = {}
    running = True

    while running:
        print("> ", end="")
        user_input = input()
        if user_input.startswith("--"):
            if user_input == "--End":
                running = False
            elif user_input == "--New":
                user_id = f"{getrandbits(32):x}"
        else:
            message, session_attributes = send_request(user_id, user_input, session_attributes)
            if message.startswith("--"):
                running = False
                print(message[2:])
            else:
                print(message)


if __name__ == "__main__":
    main()
