import base64
import json

import boto3
from utility import create_debug_logger, get_access_token

logger = create_debug_logger()

CHATBOT_NAME = "Chatbot"
CHATBOT_ALIAS = "Chatbot"
CHATBOT_SERVICE = "lex-runtime"
CHATBOT_REGION = "eu-west-2"


def create_lex_args(body, token):
    logger.debug(f"{body=}")
    lex_args = {
        "botName": CHATBOT_NAME,
        "botAlias": CHATBOT_ALIAS,
        "requestAttributes": {"access_token": token},
        "userId": body["userId"]
    }
    if "accept" in body:
        lex_args["accept"] = body["accept"]
    if "inputText" in body:
        lex_args["contentType"] = "text/plain; charset=utf-8"
        lex_args["inputStream"] = body["inputText"]
    elif "inputAudio" in body:
        lex_args["contentType"] = body["inputAudio"]["contentType"]
        lex_args["inputStream"] = base64.b64decode(body["inputAudio"]["base64Audio"])
    logger.debug(f"{lex_args=}")
    return lex_args


def prepare_response(response):
    logger.debug(f"{response=}")
    response["audioStream"] = base64.b64encode(response["audioStream"].read()).decode()
    response_json = json.dumps(response, indent=4)
    logger.debug(f"{response_json=}")
    return {"statusCode": 200, "body": response_json}


def handler(event, context):
    logger.debug(f"{event=}")

    token, err = get_access_token(event["headers"])
    if err is not None:
        return {"statusCode": 401, "body": err}
    logger.debug(f"{token=}")

    try:
        body = json.loads(event["body"])
        lex_args = create_lex_args(body, token)
        client = boto3.client(CHATBOT_SERVICE, region_name=CHATBOT_REGION)
        response = client.post_content(**lex_args)
    except Exception as err:
        return {"statusCode": 400}

    return prepare_response(response)
