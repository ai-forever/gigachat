"""Structured Output (JSON Schema) — GigaChat example.

Demonstrate three ways to get structured JSON from GigaChat:

1. Raw dict schema + ``json.loads``.
2. Pydantic model as schema.
3. ``chat_parse()`` helper (one-step parse + validate).

Set GIGACHAT_CREDENTIALS (or other auth env vars) before running.
"""

from __future__ import annotations

import json
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
load_dotenv()
# -- Pydantic model describing the desired output shape --------------------


class MathAnswer(BaseModel):
    steps: List[str]
    final_answer: str


PROMPT = "Solve the equation 8x + 7 = -23. Explain step by step in English."


def example_raw_dict_schema() -> None:
    """1. Pass a raw dict JSON Schema (sent as-is)."""
    chat = Chat(
        messages=[Messages(role=MessagesRole.USER, content=PROMPT)],
        response_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "final_answer": {"type": "string"},
                },
                "required": ["steps", "final_answer"],
            },
            "strict": False,
        },
    )

    with GigaChat() as client:
        resp = client.chat(chat)
    print(resp)
    data = json.loads(resp.choices[0].message.content)
    print("=== Raw dict schema ===")
    print("Steps:", data["steps"])
    print("Answer:", data["final_answer"])
    print()


def example_pydantic_model_schema() -> None:
    """2. Pass a Pydantic BaseModel and let the SDK generate the JSON Schema."""
    chat = Chat(
        messages=[Messages(role=MessagesRole.USER, content=PROMPT)],
        response_format={
            "type": "json_schema",
            "schema": MathAnswer,
            "strict": True,
        },
    )

    with GigaChat() as client:
        resp = client.chat(chat)
    print(resp)
    data = json.loads(resp.choices[0].message.content)
    parsed = MathAnswer.model_validate(data)
    print("=== Pydantic model as schema ===")
    print("Steps:", parsed.steps)
    print("Answer:", parsed.final_answer)
    print()


def example_chat_parse() -> None:
    """3. Use chat_parse() — one call to send, parse, and validate."""
    with GigaChat() as client:
        completion, parsed = client.chat_parse(
            PROMPT,
            response_format=MathAnswer,
            strict=True,
        )

    print("=== chat_parse() helper ===")
    print("Steps:", parsed.steps)
    print("Answer:", parsed.final_answer)
    print(f"Tokens used: {completion.usage.total_tokens}")
    print()


if __name__ == "__main__":
    example_raw_dict_schema()
    example_pydantic_model_schema()
    example_chat_parse()
