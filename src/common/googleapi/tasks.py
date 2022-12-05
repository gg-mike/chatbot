from googleapi.utils import get_items

MAX_TASK_COUNT = 10
CHATBOT_TASKS_LIST = "Chatbot"


def get_task_lists_list(service):
    return get_items(lambda page_token: service.tasklists().list(pageToken=page_token))


def get_task_list(service, task_list_id: str, deadline_date: str):
    deadline = deadline_date + "T00:00:00.000Z"
    return get_items(
        lambda page_token: service.tasks().list(
            pageToken=page_token,
            tasklist=task_list_id,
            dueMax=deadline,
            maxResults=MAX_TASK_COUNT,
            showCompleted=True,
        )
    )


def get_task_list_id(service, task_list_name) -> str:
    item_list = get_task_lists_list(service)
    for item in item_list:
        if item["title"] == task_list_name:
            return item["id"]
    response = service.tasklists().insert(body={"title": task_list_name}).execute()
    return response["id"]


def create_task(service, title: str, deadline_date: str, description: str):
    task_list_id = get_task_list_id(service, CHATBOT_TASKS_LIST)
    task_body = {"title": title, "due": deadline_date + "T00:00:00.000Z", "notes": description}
    return service.tasks().insert(tasklist=task_list_id, body=task_body).execute()


def get_tasks(service, deadline_date: str):
    task_list_id = get_task_list_id(service, CHATBOT_TASKS_LIST)
    return get_task_list(service, task_list_id, deadline_date)
