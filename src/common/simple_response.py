import json
import datetime


def generate(name):
    data = {"output": name, "timestamp": datetime.datetime.utcnow().isoformat()}
    return {
        "statusCode": 200,
        "body": json.dumps(data),
        "headers": {"Content-Type": "application/json"},
    }
