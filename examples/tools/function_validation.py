"""Validate a custom function schema synchronously."""

from dotenv import load_dotenv

from gigachat import CustomFunction, GigaChat

WEATHER_FUNCTION = CustomFunction(
    name="get_weather",
    description="Get weather for a city",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string", "minLength": 1}},
        "required": ["city"],
        "additionalProperties": False,
    },
)


def main() -> None:
    """Validate the example function and print diagnostics."""
    load_dotenv()

    with GigaChat() as client:
        result = client.validate_function(WEATHER_FUNCTION)

    print(result.message)
    for issue in result.errors or []:
        print(f"error at {issue.schema_location}: {issue.description}")
    for issue in result.warnings or []:
        print(f"warning at {issue.schema_location}: {issue.description}")


if __name__ == "__main__":
    main()
