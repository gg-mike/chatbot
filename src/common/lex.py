def elicit_slot(
    session_attributes: dict, intent_name: str, slots: dict, slot_to_elicit: str, message: dict
) -> dict:
    """Informs Amazon Lex that the user is expected to provide a slot value in the response

    Args:
        session_attributes (dict): session attributes that the client sends in the request
        intent_name (str): intent name
        slots (dict): map of slot names, configured for the intent,
            to slot values that Amazon Lex has recognized in the user conversation.
            A slot value remains null until the user provides a value.
        slot_to_elicit (str): slot to elicit
        message (dict): message to send to user. contains 2 non-empty keys: contentType and content.

    Returns:
        dict: data to send to Lex
    """
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def close(session_attributes: dict, fulfillment_state: str, message: dict) -> dict:
    """Indicates that there will not be a response from the user.

    Args:
        session_attributes (dict): session attributes that the client sends in the request
        fulfillment_state (str): the fulfillment state of the intent.
            The possible values are: 'Failed','Fulfilled','ReadyForFulfillment'
        message (dict): message to send to user.
            Contains 2 non-empty keys: 'contentType' and 'content'.

    Returns:
        dict: data to send to Lex
    """
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }


def delegate(session_attributes: dict, slots: dict) -> dict:
    """Indicates that the next action is determined by Amazon Lex.

    Args:
        session_attributes (dict): session attributes that the client sends in the request
        slots (dict): map of slot names, configured for the intent,
            to slot values that Amazon Lex has recognized in the user conversation.
            A slot value remains null until the user provides a value.

    Returns:
        dict: data to send to Lex
    """
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def return_unexpected_failure(session_attributes: dict, message_content: str) -> dict:
    """End intent with specific message due to unexpected error (like external api failure)

    Args:
        session_attributes (dict): session attributes that the client sends in the request
        message_content (str): message to send to Lex

    Returns:
        dict: _description_
    """
    return close(
        session_attributes, "Fulfilled", {"contentType": "PlainText", "content": message_content}
    )


def build_validation_result(isvalid: bool, violated_slot: str, message_content: str) -> dict:
    """Build validation result of user input data

    Args:
        isvalid (bool): flag to determine if user input is valid
        violated_slot (str): name of violated slot
        message_content (str): content of message returned to user (plaintext)

    Returns:
        dict: result of validation
    """
    return {
        "isValid": isvalid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }
