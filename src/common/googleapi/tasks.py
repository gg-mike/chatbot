CHATBOT_TASKS_LIST = "Chatbot"


def get_tasklists_list(service) -> [object]:
    response = service.tasklists().list().execute()
    return response.get("items")


def get_task_list_id(service) -> str:
    item_list = get_tasklists_list(service)
    for item in item_list:
        if item["title"] == CHATBOT_TASKS_LIST:
            return item["id"]
    print("adding CHATBOT_TASKS_LIST")
    response = service.tasklists().insert(body={"title": CHATBOT_TASKS_LIST}).execute()
    print(f"response={response}")
    return response["id"]


def create(service, task_list_id: str, title: str, due_date: str, description: str):
    task_body = {"title": title, "due": due_date + "T00:00:00.000Z", "notes": description}
    print(f"task_body={task_body}")
    response = service.tasks().insert(tasklist=task_list_id, body=task_body).execute()
    print(f"response={response}")
