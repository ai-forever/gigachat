"""Handle realtime function calls over protobuf WebSocket."""

import asyncio
import json
import os
from typing import Any, Dict
from uuid import uuid4

from dotenv import load_dotenv

from gigachat import GigaChat
from gigachat.models.realtime import (
    FunctionCallEvent,
    OutputAdditionalDataEvent,
    OutputTranscriptionEvent,
    RealtimeErrorEvent,
)
from gigachat.types.realtime import RealtimeFunctionParam, RealtimeSettingsParam

WEATHER_FUNCTION: RealtimeFunctionParam = {
    "name": "get_weather",
    "description": "Get current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name.",
            }
        },
        "required": ["location"],
    },
}


def get_weather(location: str) -> Dict[str, Any]:
    """Return mock weather data for a city."""
    return {
        "location": location,
        "temperature": 18,
        "unit": "celsius",
        "conditions": "cloudy",
    }


def build_settings(prompt: str) -> RealtimeSettingsParam:
    """Build realtime settings with a client function."""
    return {
        "voice_call_id": str(uuid4()),
        "mode": "GIGACHAT_SYNTHESIS",
        "output_modalities": "TEXT",
        "first_speaker": {"type": "model"},
        "gigachat": {
            "model": os.getenv("GIGACHAT_MODEL", "GigaChat"),
            "functions": [WEATHER_FUNCTION],
        },
        "context": {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        },
    }


async def handle_function_call(connection: Any, event: FunctionCallEvent) -> None:
    """Execute a known function call and send the result."""
    if event.name != "get_weather":
        raise RuntimeError(f"Unexpected realtime function call: {event.name}")

    arguments = json.loads(event.arguments or "{}")
    await connection.function_result.create(get_weather(**arguments), function_name=event.name)


async def main() -> None:
    """Connect to a realtime WebSocket endpoint and answer function calls."""
    load_dotenv()

    prompt = os.getenv("GIGACHAT_REALTIME_PROMPT", "What is the weather in Moscow? Answer in one sentence.")

    async with GigaChat() as client:
        async with client.a_realtime.connect(settings=build_settings(prompt)) as connection:
            async for event in connection:
                if isinstance(event, OutputTranscriptionEvent):
                    print(event.text or "", end="", flush=True)

                elif isinstance(event, FunctionCallEvent):
                    await handle_function_call(connection, event)

                elif isinstance(event, OutputAdditionalDataEvent):
                    print()
                    print(f"finish_reason={event.finish_reason}")
                    break

                elif isinstance(event, RealtimeErrorEvent):
                    raise RuntimeError(event.message)


if __name__ == "__main__":
    asyncio.run(main())
