"""Tests for chat_parse_v2() / achat_parse_v2() helpers."""

import copy
import json
from typing import List, Literal, Union

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from gigachat.client import (
    GigaChatAsyncClient,
    GigaChatSyncClient,
    _parse_completion_v2,
    _prepare_chat_v2_for_parse,
)
from gigachat.exceptions import (
    ContentFilterFinishReasonError,
    ContentParseError,
    ContentValidationError,
    LengthFinishReasonError,
)
from gigachat.models.chat_v2 import ChatCompletionV2
from gigachat.settings import Settings
from tests.constants import ACCESS_TOKEN, CHAT_COMPLETION_V2, CHAT_V2_BASE_URL, CHAT_V2_URL


class MathResult(BaseModel):
    steps: List[str]
    final_answer: str


class CalculateStep(BaseModel):
    action: Literal["calculate"]
    expression: str


class FinalAnswerStep(BaseModel):
    action: Literal["final_answer"]
    answer: str


AgentStep = Union[CalculateStep, FinalAnswerStep]


def _make_chat_completion_v2(*, text: str, finish_reason: str = "stop") -> dict:
    data = copy.deepcopy(CHAT_COMPLETION_V2)
    data["messages"] = [
        {
            "message_id": "msg-1",
            "role": "assistant",
            "content": [{"text": text}],
        }
    ]
    data["finish_reason"] = finish_reason
    return data


# ---------------------------------------------------------------------------
# _prepare_chat_v2_for_parse
# ---------------------------------------------------------------------------


def test_prepare_chat_v2_for_parse_sets_response_format() -> None:
    settings = Settings(model="GigaChat-2-Max")

    chat_data = _prepare_chat_v2_for_parse("Solve 2+2", settings, MathResult, strict=True)

    assert chat_data.model_options is not None
    assert chat_data.model_options.response_format is not None
    assert chat_data.model_options.response_format.type == "json_schema"
    assert isinstance(chat_data.model_options.response_format.schema_, dict)
    assert chat_data.model_options.response_format.schema_["type"] == "object"
    assert "steps" in chat_data.model_options.response_format.schema_.get("properties", {})
    assert chat_data.model_options.response_format.strict is True


def test_prepare_chat_v2_for_parse_preserves_existing_model_options() -> None:
    settings = Settings(model="GigaChat-2-Max")

    chat_data = _prepare_chat_v2_for_parse(
        {
            "messages": [{"role": "user", "content": "Solve 2+2"}],
            "model_options": {"temperature": 0.2},
        },
        settings,
        MathResult,
        strict=None,
    )

    assert chat_data.model_options is not None
    assert chat_data.model_options.temperature == 0.2
    assert chat_data.model_options.response_format is not None
    assert chat_data.model_options.response_format.strict is None


def test_prepare_chat_v2_for_parse_union_sets_response_format() -> None:
    settings = Settings(model="GigaChat-2-Max")

    chat_data = _prepare_chat_v2_for_parse("Solve 2+2", settings, AgentStep, strict=True)

    assert chat_data.model_options is not None
    assert chat_data.model_options.response_format is not None
    assert "anyOf" in chat_data.model_options.response_format.schema_
    assert chat_data.model_options.response_format.strict is True


# ---------------------------------------------------------------------------
# _parse_completion_v2
# ---------------------------------------------------------------------------


def test_parse_completion_v2_happy_path() -> None:
    completion = ChatCompletionV2.model_validate(
        _make_chat_completion_v2(
            text=json.dumps(
                {
                    "steps": ["8x = -30", "x = -3.75"],
                    "final_answer": "x = -3.75",
                }
            )
        )
    )

    parsed = _parse_completion_v2(completion, MathResult)

    assert isinstance(parsed, MathResult)
    assert parsed.final_answer == "x = -3.75"
    assert len(parsed.steps) == 2


def test_parse_completion_v2_skips_non_text_messages() -> None:
    data = copy.deepcopy(CHAT_COMPLETION_V2)
    data["messages"] = [
        {
            "message_id": "msg-1",
            "role": "assistant",
            "content": [
                {
                    "function_call": {
                        "name": "weather-get",
                        "arguments": {"location": "Moscow"},
                    }
                }
            ],
        },
        {
            "message_id": "msg-2",
            "role": "assistant",
            "content": [{"text": json.dumps({"action": "final_answer", "answer": "42"})}],
        },
    ]
    completion = ChatCompletionV2.model_validate(data)

    parsed = _parse_completion_v2(completion, AgentStep)

    assert isinstance(parsed, FinalAnswerStep)
    assert parsed.answer == "42"


def test_parse_completion_v2_length_finish_reason() -> None:
    completion = ChatCompletionV2.model_validate(
        _make_chat_completion_v2(text='{"steps": ["Ste', finish_reason="length")
    )

    with pytest.raises(LengthFinishReasonError) as exc_info:
        _parse_completion_v2(completion, MathResult)

    assert exc_info.value.completion is completion


def test_parse_completion_v2_content_filter_finish_reason() -> None:
    completion = ChatCompletionV2.model_validate(_make_chat_completion_v2(text="", finish_reason="content_filter"))

    with pytest.raises(ContentFilterFinishReasonError) as exc_info:
        _parse_completion_v2(completion, MathResult)

    assert exc_info.value.completion is completion


def test_parse_completion_v2_invalid_json() -> None:
    completion = ChatCompletionV2.model_validate(_make_chat_completion_v2(text="not valid json"))

    with pytest.raises(ContentParseError) as exc_info:
        _parse_completion_v2(completion, MathResult)

    assert exc_info.value.completion is completion
    assert exc_info.value.content == "not valid json"


def test_parse_completion_v2_schema_mismatch() -> None:
    completion = ChatCompletionV2.model_validate(_make_chat_completion_v2(text=json.dumps({"wrong_field": 42})))

    with pytest.raises(ContentValidationError) as exc_info:
        _parse_completion_v2(completion, MathResult)

    assert exc_info.value.completion is completion
    assert exc_info.value.content == '{"wrong_field": 42}'


def test_parse_completion_v2_empty_messages() -> None:
    data = copy.deepcopy(CHAT_COMPLETION_V2)
    data["messages"] = []
    completion = ChatCompletionV2.model_validate(data)

    with pytest.raises(ContentParseError):
        _parse_completion_v2(completion, MathResult)


# ---------------------------------------------------------------------------
# Sync client — chat_parse_v2
# ---------------------------------------------------------------------------


def test_chat_parse_v2_sync_happy(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=CHAT_V2_URL,
        json=_make_chat_completion_v2(
            text=json.dumps(
                {
                    "steps": ["8x = -30", "x = -3.75"],
                    "final_answer": "x = -3.75",
                }
            )
        ),
    )

    with GigaChatSyncClient(base_url=CHAT_V2_BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = client.chat_parse_v2("Solve 8x+7=-23", response_model=MathResult, strict=True)

    assert isinstance(completion, ChatCompletionV2)
    assert isinstance(parsed, MathResult)
    assert parsed.final_answer == "x = -3.75"

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)
    assert body["model_options"]["response_format"]["type"] == "json_schema"
    assert body["model_options"]["response_format"]["strict"] is True
    assert isinstance(body["model_options"]["response_format"]["schema"], dict)


def test_chat_parse_v2_sync_preserves_existing_model_options(httpx_mock: HTTPXMock) -> None:
    data = _make_chat_completion_v2(text=json.dumps({"action": "final_answer", "answer": "42"}))
    httpx_mock.add_response(url=CHAT_V2_URL, json=data)

    payload = {
        "messages": [{"role": "user", "content": "Solve 8x+7=-23"}],
        "model_options": {"temperature": 0.2},
    }

    with GigaChatSyncClient(base_url=CHAT_V2_BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = client.chat_parse_v2(payload, response_model=AgentStep)

    assert isinstance(completion, ChatCompletionV2)
    assert isinstance(parsed, FinalAnswerStep)
    assert parsed.answer == "42"

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)
    assert body["model_options"]["temperature"] == 0.2
    assert body["model_options"]["response_format"]["type"] == "json_schema"
    assert "anyOf" in body["model_options"]["response_format"]["schema"]


def test_chat_parse_v2_sync_invalid_json(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, json=_make_chat_completion_v2(text="not json"))

    with GigaChatSyncClient(base_url=CHAT_V2_BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ContentParseError):
            client.chat_parse_v2("Solve 8x+7=-23", response_model=MathResult)


# ---------------------------------------------------------------------------
# Async client — achat_parse_v2
# ---------------------------------------------------------------------------


async def test_achat_parse_v2_happy(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=CHAT_V2_URL,
        json=_make_chat_completion_v2(
            text=json.dumps(
                {
                    "steps": ["8x = -30", "x = -3.75"],
                    "final_answer": "x = -3.75",
                }
            )
        ),
    )

    async with GigaChatAsyncClient(base_url=CHAT_V2_BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = await client.achat_parse_v2("Solve 8x+7=-23", response_model=MathResult)

    assert isinstance(completion, ChatCompletionV2)
    assert isinstance(parsed, MathResult)
    assert parsed.final_answer == "x = -3.75"


async def test_achat_parse_v2_invalid_json(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_V2_URL, json=_make_chat_completion_v2(text="not json"))

    async with GigaChatAsyncClient(base_url=CHAT_V2_BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ContentParseError):
            await client.achat_parse_v2("Solve 8x+7=-23", response_model=MathResult)
