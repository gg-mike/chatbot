from googleapi import tasks
from lex import close, return_unexpected_failure
from setup_handler import google_api_handler as setup
from utility import create_debug_logger, get_slots

CHATBOT_TASKS_LIST = "Chatbot"

logger = create_debug_logger()


def handler(event, context):
    logger.debug(f"{event=}")

    session_attributes, service, err = setup(event, "tasks", "v1")
    if err is not None:
        return return_unexpected_failure(session_attributes, err)

    slots = get_slots(event)
    logger.debug(f"{slots=}")

    try:
        task_list_id = tasks.get_task_list_id(service, CHATBOT_TASKS_LIST)
        tasks.create_task(service, task_list_id, slots["Title"], slots["Deadline"], slots["Description"])
        return close(
            session_attributes,
            "Fulfilled",
            {"contentType": "PlainText", "content": f"Created task '{slots['Title']}'"},
        )
    except Exception as err:
        return return_unexpected_failure(
            session_attributes, f"Failed to create task '{slots['Title']}'"
        )
