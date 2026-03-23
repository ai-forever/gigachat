"""Validate a GigaChat function definition before using it in chat.

This example shows how to call ``validate_function()`` and inspect
validation warnings or errors returned by the API.

Set GIGACHAT_CREDENTIALS (or other auth env vars) before running.
"""

from __future__ import annotations

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models import Function

load_dotenv()
FUNCTION = Function.model_validate(
    {
        "name": "weather_forecast",
        "description": "Return the weather forecast for a location and period.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City or region name.",
                },
                "num_days": {
                    "type": "integer",
                    "description": "Forecast period in days.",
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units.",
                    "enum": ["celsius", "fahrenheit"],
                },
            },
            "required": ["location", "num_days"],
        },
    }
)


def print_issues(title: str, issues: list | None) -> None:
    """Print validation issues in a compact format."""
    print(title)
    if not issues:
        print("  none")
        return

    for issue in issues:
        print(f"  - {issue.description} [{issue.schema_location}]")


def main() -> None:
    """Validate the example function and print the result."""
    with GigaChat() as client:
        result = client.validate_function(FUNCTION)

    print("=== Function validation ===")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")

    if result.json_ai_rules_version:
        print(f"Rules version: {result.json_ai_rules_version}")

    print_issues("Warnings:", result.warnings)
    print_issues("Errors:", result.errors)


if __name__ == "__main__":
    main()
