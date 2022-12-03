import boto3
import json
from utility import create_debug_logger, get_access_token

logger = create_debug_logger()


def handler(event, context):
    logger.debug(f"{event=}")

    token, err = get_access_token(event["headers"])
    if err is not None:
        return {"statusCode": 400, "body": err}
    logger.debug(f"{token=}")

    body = json.loads(event["body"])
    logger.debug(f"{body=}")

    lex_args = body["lex_args"]
    logger.debug(f"{lex_args=}")

    client = boto3.client("lex-runtime", region_name="eu-west-2")

    response = client.post_text(
        botName="Chatbot", botAlias="Chatbot", requestAttributes={"access_token": token}, **lex_args
    )
    logger.debug(f"{response=}")

    response_json = json.dumps(response, indent=4)
    logger.debug(f"{response_json=}")

    return {"statusCode": 200, "body": response_json}
