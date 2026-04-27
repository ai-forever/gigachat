"""Force a client-defined function call."""

from typing import Any, Dict

from dotenv import load_dotenv

from examples._utils import first_message_text
from examples.tools.function_calling import add_function_result, extract_call
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatFunctionSpecification, ChatMessage, ChatTool, ChatToolConfig


def get_order_status(order_id: str) -> Dict[str, Any]:
    """Return mock order status."""
    return {
        "order_id": order_id,
        "status": "packed",
        "eta": "tomorrow",
    }


ORDER_STATUS_FUNCTION = {
    "name": "get_order_status",
    "description": "Get delivery status for an order.",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "Order identifier."},
        },
        "required": ["order_id"],
    },
    "return_parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "status": {"type": "string"},
            "eta": {"type": "string"},
        },
        "required": ["order_id", "status", "eta"],
    },
}


def main() -> None:
    """Run a forced function-calling roundtrip."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Check order A-1024 and answer naturally.")],
        tools=[ChatTool(functions={"specifications": [ChatFunctionSpecification(**ORDER_STATUS_FUNCTION)]})],
        tool_config=ChatToolConfig(mode="forced", function_name="get_order_status"),
    )

    with GigaChat() as client:
        first_response = client.chat.create(request)
        call = extract_call(first_response)
        result = get_order_status(**call["arguments"])
        final_response = client.chat.create(add_function_result(request, call, result))

    print(first_message_text(final_response))


if __name__ == "__main__":
    main()
