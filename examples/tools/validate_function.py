"""Validate one function definition without generating or executing it."""

from dotenv import load_dotenv

from gigachat import GigaChat


def main() -> None:
    load_dotenv()
    function = {
        "name": "get_weather",
        "description": "Return the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }
    with GigaChat() as client:
        result = client.functions_validate(function)
    print(result.status, result.message)
    for issue in result.errors or []:
        print("Error:", issue.description, issue.schema_location)
    for issue in result.warnings or []:
        print("Warning:", issue.description, issue.schema_location)


if __name__ == "__main__":
    main()
