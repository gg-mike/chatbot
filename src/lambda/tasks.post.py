from googleapi import tasks
from lex import close, return_unexpected_failure
from setup_handler import google_api_handler as setup
from utility import create_debug_logger, get_slots

logger = create_debug_logger()


def handler(event, context):
    logger.debug(f"{event=}")

    session_attributes, service, err = setup(event, "tasks", "v1")
    if err is not None:
        return return_unexpected_failure(session_attributes, err)

    task_list_id = tasks.get_task_list_id(service, "Chatbot")
    slots = get_slots(event)

    logger.debug(f"{slots=}")

    task_body = {
        "title": slots["Title"],
        "due": slots["Deadline"] + "T00:00:00.000Z",
        "notes": slots["Description"],
    }

    logger.debug(f"{task_body=}")

    try:
        tasks.create(service, task_list_id, task_body)
        return close(
            "Fulfilled",
            {"contentType": "PlainText", "content": f"Created task '{slots['Title']}'"},
        )
    except Exception as err:
        return return_unexpected_failure(
            session_attributes, f"Failed to create task '{slots['Title']}'"
        )
