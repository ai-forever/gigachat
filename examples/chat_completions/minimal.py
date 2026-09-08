"""Simplest GigaChat v2 chat-completions request."""

from dotenv import load_dotenv

from gigachat import GigaChat


def main() -> None:
    """Send one message and print the reply."""
    load_dotenv()

    with GigaChat() as client:
        response = client.chat.create("Привет, GigaChat!")

    print(response.messages[0].content[0].text)


if __name__ == "__main__":
    main()
