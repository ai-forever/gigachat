"""Structured Output (JSON Schema) — GigaChat example.

Demonstrate three ways to get structured JSON from GigaChat:

1. Raw dict schema  + ``json.loads`` (passthrough — no normalization).
2. Pydantic model as schema  (A+ — auto-normalized OpenAI-style).
3. ``chat_parse()`` helper  (B — one-step parse + validate).

Set GIGACHAT_CREDENTIALS (or other auth env vars) before running.
"""

from __future__ import annotations

import json

from pydantic import BaseModel

from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

# -- Pydantic model describing the desired output shape --------------------


class MathAnswer(BaseModel):
    steps: list[str]
    final_answer: str


PROMPT = "Solve the equation 8x + 7 = -23. Explain step by step in English."


def example_raw_dict_schema() -> None:
    """1. Pass a raw dict JSON Schema (sent as-is, no normalization)."""
    chat = Chat(
        model="GigaChat-2-Max",
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

    data = json.loads(resp.choices[0].message.content)
    print("=== Raw dict schema ===")
    print("Steps:", data["steps"])
    print("Answer:", data["final_answer"])
    print()


def example_pydantic_model_schema() -> None:
    """2. Pass a Pydantic BaseModel — SDK generates + normalizes JSON Schema."""
    chat = Chat(
        model="GigaChat-2-Max",
        messages=[Messages(role=MessagesRole.USER, content=PROMPT)],
        response_format={
            "type": "json_schema",
            "schema": MathAnswer,
            "strict": True,
        },
    )

    with GigaChat() as client:
        resp = client.chat(chat)

    data = json.loads(resp.choices[0].message.content)
    parsed = MathAnswer.model_validate(data)
    print("=== Pydantic model as schema ===")
    print("Steps:", parsed.steps)
    print("Answer:", parsed.final_answer)
    print()


def example_chat_parse() -> None:
    """3. Use chat_parse() — one call to send, parse, and validate."""
    with GigaChat(model="GigaChat-2-Max") as client:
        completion, parsed = client.chat_parse(
            PROMPT,
            response_model=MathAnswer,
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
