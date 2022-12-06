MAX_TASK_COUNT = 10
CHATBOT_TASKS_LIST = "Chatbot"
TIME_STRING = "T00:00:00.000Z"


def get_item_list(getter) -> []:
    page_token = None
    items = []
    while True:
        response = getter(page_token).execute()
        for entry in response["items"]:
            items.append(entry)
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return items


def get_datetime(date) -> str:
    return date + TIME_STRING


def get_task_lists_list(service):
    return get_item_list(lambda page_token: service.tasklists().list(pageToken=page_token))


def get_task_list(service, task_list_id: str, deadline_date: str):
    return get_item_list(
        lambda page_token: service.tasks().list(
            pageToken=page_token,
            tasklist=task_list_id,
            dueMax=get_datetime(deadline_date),
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
    task_body = {"title": title, "due": get_datetime(deadline_date), "notes": description}
    return service.tasks().insert(tasklist=task_list_id, body=task_body).execute()


def get_tasks(service, deadline_date: str):
    task_list_id = get_task_list_id(service, CHATBOT_TASKS_LIST)
    return get_task_list(service, task_list_id, deadline_date)
