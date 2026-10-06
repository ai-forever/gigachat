"""Request an eligible function, then allow the model to give its final answer."""

from dotenv import load_dotenv

from examples.tools.parallel_function_calling import build_request
from examples.tools.parallel_function_calling_roundtrip import run
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatToolConfig


def request_with_any() -> ChatCompletionRequest:
    """Require at least one eligible function in the initial v2 response."""
    request = build_request()
    request.tool_config = ChatToolConfig(mode="any", functions_names_any=["get_weather", "get_rate"])
    return request


def main() -> None:
    """Run the same tool loop with any-mode initial selection."""
    load_dotenv()
    print("Using local demonstration weather and exchange-rate data.")
    with GigaChat() as client:
        print(run(client, request_with_any()))


if __name__ == "__main__":
    main()
