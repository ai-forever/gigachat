"""OpenAI-style agent loop using ``chat_parse()`` and structured output.

The agent decides its next action by returning a typed JSON object.
Each iteration:

1. Call ``chat_parse()`` with a ``Union[...]`` response model.
2. Inspect the parsed result to determine the action type.
3. Execute the action (call a tool, compute something, etc.).
4. Append the tool result back to the conversation.
5. Repeat until the model returns ``FinalAnswer``.

Set GIGACHAT_CREDENTIALS (or other auth env vars) before running.
"""

from __future__ import annotations

import json
import math
from typing import Literal, Union

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from gigachat import GigaChat
from gigachat.models import Messages, MessagesRole
load_dotenv()
# -- Action models (what the agent can do) ---------------------------------


class Calculate(BaseModel):
    """Ask for a mathematical expression to be evaluated."""

    action: Literal["calculate"] = "calculate"
    expression: str = Field(description="A Python math expression, e.g. '2**10 + 3'")


class FinalAnswer(BaseModel):
    """Return the final answer to the user."""

    action: Literal["final_answer"] = "final_answer"
    answer: str = Field(description="Human-readable final answer")
    reasoning: str = Field(description="Brief explanation of the reasoning")


AgentStep = Union[Calculate, FinalAnswer]

SYSTEM_PROMPT = """\
You are a helpful math assistant. You solve problems step by step.

On each turn you MUST return a JSON object matching one of these actions:
- {"action": "calculate", "expression": "<python math expression>"}
  Use this to evaluate any arithmetic or math expression you need.
- {"action": "final_answer", "answer": "<answer>", "reasoning": "<explanation>"}
  Use this when you have the complete answer.

Solve the user's problem by calling "calculate" as many times as needed,
then return "final_answer".\
"""


# -- Tool implementations -------------------------------------------------


def execute_calculate(expr: str) -> str:
    """Evaluate a Python math expression safely (only math module)."""
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    allowed_names["abs"] = abs
    allowed_names["round"] = round
    try:
        result = eval(expr, {"__builtins__": {}}, allowed_names)  # noqa: S307
        return str(result)
    except Exception as exc:
        return f"Error: {exc}"


# -- Agent loop ------------------------------------------------------------


def run_agent(question: str, *, model: str = "GigaChat-2-Max", max_steps: int = 10) -> str:
    """Run the agent loop and return the final answer."""
    messages: list[Messages] = [
        Messages(role=MessagesRole.SYSTEM, content=SYSTEM_PROMPT),
        Messages(role=MessagesRole.USER, content=question),
    ]

    with GigaChat(model=model) as client:
        for step in range(1, max_steps + 1):
            print(f"--- Step {step} ---")

            from gigachat.models import Chat

            chat = Chat(model=model, messages=messages)
            completion, parsed = client.chat_parse(chat, response_model=AgentStep)

            if isinstance(parsed, FinalAnswer):
                print(f"Final answer: {parsed.answer}")
                print(f"Reasoning: {parsed.reasoning}")
                return parsed.answer

            if isinstance(parsed, Calculate):
                result = execute_calculate(parsed.expression)
                print(f"Calculate: {parsed.expression} = {result}")

                messages.append(
                    Messages(
                        role=MessagesRole.ASSISTANT,
                        content=json.dumps(parsed.model_dump(), ensure_ascii=False),
                    )
                )
                messages.append(
                    Messages(
                        role=MessagesRole.USER,
                        content=f"Result of calculation: {result}",
                    )
                )

    raise RuntimeError(f"Agent did not reach a final answer within {max_steps} steps")


# -- Main ------------------------------------------------------------------

if __name__ == "__main__":
    question = "What is the sum of the first 10 prime numbers, divided by the square root of 144?"
    print(f"Question: {question}\n")
    answer = run_agent(question)
    print(f"\n=== Answer: {answer} ===")
