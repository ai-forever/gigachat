"""Generate and save an image with the built-in image tool."""

from pathlib import Path

from dotenv import load_dotenv

from examples._utils import first_message_text, message_file_ids
from gigachat import GigaChat
from gigachat.models import ChatCompletionRequest, ChatMessage, ChatTool, ChatToolConfig


def main() -> None:
    """Run an image generation request and save returned files."""
    load_dotenv()

    request = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Create a simple square icon concept for a Python SDK release.",
            )
        ],
        tools=[ChatTool(image_generate={})],
        tool_config=ChatToolConfig(mode="forced", tool_name="image_generate"),
    )

    with GigaChat() as client:
        response = client.chat.create(request)
        print(first_message_text(response))
        for index, file_id in enumerate(message_file_ids(response.messages[0]), start=1):
            image = client.get_image(file_id)
            output = image.save(Path(f"generated-image-{index}.jpg"))
            print(f"Saved generated file {file_id} to {output}")


if __name__ == "__main__":
    main()
