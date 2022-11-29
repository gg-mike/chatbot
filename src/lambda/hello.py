import utility


def handler(event, context):
    return utility.simple_response(
        {
            "info": "Hello from Serverless chatbot API",
            "request-body": event["body"] if "body" in event else "",
        }
    )
