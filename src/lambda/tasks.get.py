from googleapi import tasks
from lex import close, return_unexpected_failure
from setup_handler import google_api_handler as setup
from utility import create_debug_logger, get_slots

logger = create_debug_logger()


def prepare_task(task):
    date = task["due"].split('T')[0]
    return tasks.Task(task["title"], task["notes"], date)


def prepare_response(google_response, deadline):
    if len(google_response) == 0:
        return {
            "contentType": "PlainText",
            "content": f"No tasks found with deadline: {deadline}",
        }
    else:
        task_list: [tasks.Task] = [prepare_task(task) for task in google_response]
        logger.debug(f"{task_list=}")
        return tasks.prepare_json_message(f"Task list with deadline: {deadline}", task_list)


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
