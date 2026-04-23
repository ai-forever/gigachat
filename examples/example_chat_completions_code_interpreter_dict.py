"""Use the built-in code_interpreter tool with a raw dict payload."""

from typing import Any, Dict, List

from gigachat import GigaChat


def _message_text(message: Dict[str, Any]) -> str:
    """Return combined text content from a primary message dict."""
    content = message.get("content")
    if content is None:
        return ""

    return "".join([part["text"] for part in content if part.get("text")])


def _message_files(message: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return generated files attached to the message."""
    content = message.get("content")
    if content is None:
        return []

    files: List[Dict[str, Any]] = []
    for part in content:
        files.extend(part.get("files") or [])
    return files


def main() -> None:
    """Run a code_interpreter example with a shorthand tool declaration."""
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            "Calculate the sum of the first 50 prime numbers. "
                            "Use code for the calculation and briefly explain the result."
                        )
                    }
                ],
            }
        ],
        "tools": ["code_interpreter"],
        "tool_config": {"mode": "auto"},
        "model_options": {
            "temperature": 0.1,
            "max_tokens": 250,
        },
    }

    with GigaChat() as client:
        response = client.chat.create(payload)

    response_data = response.model_dump(mode="json", exclude_none=True)
    message = response_data["messages"][0]

    print("Assistant:")
    print(_message_text(message))

    tool_execution = response_data.get("tool_execution") or message.get("tool_execution")
    if tool_execution is not None:
        print("\nTool execution:")
        print(tool_execution)

    files = _message_files(message)
    if files:
        print("\nGenerated files:")
        for file_data in files:
            print(f"- id={file_data.get('id')}, target={file_data.get('target')}, mime={file_data.get('mime')}")

    usage = response_data.get("usage")
    if usage is not None:
        print(
            f"\nUsage: input_tokens={usage.get('input_tokens')}, "
            f"output_tokens={usage.get('output_tokens')}, total_tokens={usage.get('total_tokens')}"
        )


if __name__ == "__main__":
    main()
