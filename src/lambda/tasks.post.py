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

    slots = get_slots(event)
    logger.debug(f"{slots=}")

    try:
        response = tasks.create_task(
            service, slots["Title"], slots["Deadline"], slots["Description"]
        )
        logger.debug(f"{response=}")
        return close(
            session_attributes,
            "Fulfilled",
            {
                "contentType": "PlainText",
                "content": f"Created task {slots['Title']} with deadline {slots['Deadline']} and description {slots['Description']}",
            },
        )
    except Exception as err:
        return return_unexpected_failure(
            session_attributes, f"Failed to create task {slots['Title']}"
        )
