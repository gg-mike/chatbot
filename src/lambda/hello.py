import simple_response


def handler(event, context):
    return simple_response.generate(
        {
            "info": "Hello from Serverless chatbot API",
            "request-body": event["body"] if "body" in event else "",
        }
    )
