from googleapi import tasks
from lex import close, return_unexpected_failure
from setup_handler import google_api_handler as setup
from utility import create_debug_logger, get_slots

logger = create_debug_logger()


def prepare_response(google_response, deadline):
    if len(google_response) == 0:
        return f"No tasks found with deadline {deadline}"
    else:
        task_name_list = [task["title"] for task in google_response]
        response = f"Task list with deadline {deadline}: " + ", ".join(task_name_list)
        logger.debug(f"{response=}")
        return response


def handler(event, context):
    logger.debug(f"{event=}")

    session_attributes, service, err = setup(event, "tasks", "v1")
    if err is not None:
        return return_unexpected_failure(session_attributes, err)

    slots = get_slots(event)
    logger.debug(f"{slots=}")

    try:
        response = tasks.get_tasks(service, slots["Deadline"])
        logger.debug(f"{response=}")
        return close(
            session_attributes,
            "Fulfilled",
            {
                "contentType": "PlainText",
                "content": prepare_response(response, slots["Deadline"]),
            },
        )
    except Exception as err:
        return return_unexpected_failure(session_attributes, "Failed to get task list")
