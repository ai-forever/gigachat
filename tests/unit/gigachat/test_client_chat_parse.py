"""Tests for chat_parse() / achat_parse() helpers."""

import copy
import json
from typing import List, Literal, Union

import pytest
from pydantic import BaseModel
from pytest_httpx import HTTPXMock

from gigachat.client import (
    GigaChatAsyncClient,
    GigaChatSyncClient,
    _parse_completion,
    _prepare_chat_for_parse,
)
from gigachat.exceptions import (
    ContentFilterFinishReasonError,
    ContentParseError,
    ContentValidationError,
    LengthFinishReasonError,
)
from gigachat.models import Chat, ChatCompletion, Messages, MessagesRole
from gigachat.settings import Settings
from tests.constants import ACCESS_TOKEN, BASE_URL, CHAT_URL
from tests.utils import get_json

CHAT_COMPLETION_JSON = get_json("chat_completion_json.json")


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


# ---------------------------------------------------------------------------
# _prepare_chat_for_parse
# ---------------------------------------------------------------------------


def test_prepare_chat_for_parse_sets_response_format() -> None:
    from gigachat.models.response_format import JsonSchemaResponseFormat

    settings = Settings(model="GigaChat")
    chat_data = _prepare_chat_for_parse("Solve 2+2", settings, MathResult, strict=True)
    assert chat_data.response_format is not None
    assert isinstance(chat_data.response_format, JsonSchemaResponseFormat)
    assert chat_data.response_format.type == "json_schema"
    assert isinstance(chat_data.response_format.schema_, dict)
    assert chat_data.response_format.schema_["type"] == "object"
    assert "steps" in chat_data.response_format.schema_.get("properties", {})
    assert chat_data.response_format.strict is True


def test_prepare_chat_for_parse_strict_false() -> None:
    from gigachat.models.response_format import JsonSchemaResponseFormat

    settings = Settings(model="GigaChat")
    chat_data = _prepare_chat_for_parse("Solve 2+2", settings, MathResult, strict=False)
    assert chat_data.response_format is not None
    assert isinstance(chat_data.response_format, JsonSchemaResponseFormat)
    assert chat_data.response_format.strict is False


def test_prepare_chat_for_parse_union_sets_response_format() -> None:
    from gigachat.models.response_format import JsonSchemaResponseFormat

    settings = Settings(model="GigaChat")
    chat_data = _prepare_chat_for_parse("Solve 2+2", settings, AgentStep, strict=True)
    assert chat_data.response_format is not None
    assert isinstance(chat_data.response_format, JsonSchemaResponseFormat)
    assert "anyOf" in chat_data.response_format.schema_
    assert chat_data.response_format.strict is True


# ---------------------------------------------------------------------------
# _parse_completion — happy path
# ---------------------------------------------------------------------------


def test_parse_completion_happy_path() -> None:
    completion = ChatCompletion.model_validate(CHAT_COMPLETION_JSON)
    parsed = _parse_completion(completion, MathResult)
    assert isinstance(parsed, MathResult)
    assert parsed.final_answer == "x = -3.75"
    assert len(parsed.steps) == 2


def test_parse_completion_union_happy_path() -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["message"]["content"] = json.dumps({"action": "final_answer", "answer": "42"})
    completion = ChatCompletion.model_validate(data)

    parsed = _parse_completion(completion, AgentStep)
    assert isinstance(parsed, FinalAnswerStep)
    assert parsed.answer == "42"


# ---------------------------------------------------------------------------
# _parse_completion — error paths
# ---------------------------------------------------------------------------


def test_parse_completion_length_finish_reason() -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["finish_reason"] = "length"
    data["choices"][0]["message"]["content"] = '{"steps": ["Ste'
    completion = ChatCompletion.model_validate(data)

    with pytest.raises(LengthFinishReasonError) as exc_info:
        _parse_completion(completion, MathResult)
    assert exc_info.value.completion is completion


def test_parse_completion_content_filter_finish_reason() -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["finish_reason"] = "content_filter"
    data["choices"][0]["message"]["content"] = ""
    completion = ChatCompletion.model_validate(data)

    with pytest.raises(ContentFilterFinishReasonError) as exc_info:
        _parse_completion(completion, MathResult)
    assert exc_info.value.completion is completion


def test_parse_completion_invalid_json() -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["message"]["content"] = "not valid json at all"
    completion = ChatCompletion.model_validate(data)

    with pytest.raises(ContentParseError) as exc_info:
        _parse_completion(completion, MathResult)
    assert exc_info.value.completion is completion
    assert exc_info.value.content == "not valid json at all"


def test_parse_completion_schema_mismatch() -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["message"]["content"] = json.dumps({"wrong_field": 42})
    completion = ChatCompletion.model_validate(data)

    with pytest.raises(ContentValidationError) as exc_info:
        _parse_completion(completion, MathResult)
    assert exc_info.value.completion is completion
    assert exc_info.value.content == '{"wrong_field": 42}'


def test_parse_completion_empty_choices() -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"] = []
    completion = ChatCompletion.model_validate(data)

    with pytest.raises(ContentParseError):
        _parse_completion(completion, MathResult)


# ---------------------------------------------------------------------------
# Sync client — chat_parse
# ---------------------------------------------------------------------------


def test_chat_parse_sync_happy(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION_JSON)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = client.chat_parse("Solve 8x+7=-23", response_format=MathResult)

    assert isinstance(completion, ChatCompletion)
    assert isinstance(parsed, MathResult)
    assert parsed.final_answer == "x = -3.75"

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)
    assert body["response_format"]["type"] == "json_schema"
    assert "schema" in body["response_format"]
    assert isinstance(body["response_format"]["schema"], dict)


def test_chat_parse_sync_union_response_format(httpx_mock: HTTPXMock) -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["message"]["content"] = json.dumps({"action": "final_answer", "answer": "42"})
    httpx_mock.add_response(url=CHAT_URL, json=data)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = client.chat_parse("Solve 8x+7=-23", response_format=AgentStep)

    assert isinstance(completion, ChatCompletion)
    assert isinstance(parsed, FinalAnswerStep)
    assert parsed.answer == "42"

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)
    assert body["response_format"]["type"] == "json_schema"
    assert "anyOf" in body["response_format"]["schema"]


def test_chat_parse_sync_strict(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION_JSON)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = client.chat_parse("Solve 8x+7=-23", response_format=MathResult, strict=True)

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)
    assert body["response_format"]["strict"] is True


def test_chat_parse_sync_invalid_json(httpx_mock: HTTPXMock) -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["message"]["content"] = "not json"
    httpx_mock.add_response(url=CHAT_URL, json=data)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ContentParseError):
            client.chat_parse("Solve 8x+7=-23", response_format=MathResult)


def test_chat_parse_sync_validation_error(httpx_mock: HTTPXMock) -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["message"]["content"] = json.dumps({"bad": "data"})
    httpx_mock.add_response(url=CHAT_URL, json=data)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ContentValidationError):
            client.chat_parse("Solve 8x+7=-23", response_format=MathResult)


def test_chat_parse_sync_length_error(httpx_mock: HTTPXMock) -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["finish_reason"] = "length"
    httpx_mock.add_response(url=CHAT_URL, json=data)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(LengthFinishReasonError):
            client.chat_parse("Solve 8x+7=-23", response_format=MathResult)


def test_chat_parse_sync_content_filter_error(httpx_mock: HTTPXMock) -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["finish_reason"] = "content_filter"
    httpx_mock.add_response(url=CHAT_URL, json=data)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ContentFilterFinishReasonError):
            client.chat_parse("Solve 8x+7=-23", response_format=MathResult)


def test_chat_parse_sync_with_chat_object(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION_JSON)

    chat_obj = Chat(
        model="GigaChat-2-Max",
        messages=[Messages(role=MessagesRole.USER, content="Solve 8x+7=-23")],
    )
    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = client.chat_parse(chat_obj, response_format=MathResult)

    assert isinstance(parsed, MathResult)


# ---------------------------------------------------------------------------
# Async client — achat_parse
# ---------------------------------------------------------------------------


async def test_achat_parse_happy(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION_JSON)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = await client.achat_parse("Solve 8x+7=-23", response_format=MathResult)

    assert isinstance(completion, ChatCompletion)
    assert isinstance(parsed, MathResult)
    assert parsed.final_answer == "x = -3.75"


async def test_achat_parse_invalid_json(httpx_mock: HTTPXMock) -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["message"]["content"] = "not json"
    httpx_mock.add_response(url=CHAT_URL, json=data)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ContentParseError):
            await client.achat_parse("Solve 8x+7=-23", response_format=MathResult)


async def test_achat_parse_validation_error(httpx_mock: HTTPXMock) -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["message"]["content"] = json.dumps({"bad": "data"})
    httpx_mock.add_response(url=CHAT_URL, json=data)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ContentValidationError):
            await client.achat_parse("Solve 8x+7=-23", response_format=MathResult)


async def test_achat_parse_length_error(httpx_mock: HTTPXMock) -> None:
    data = copy.deepcopy(CHAT_COMPLETION_JSON)
    data["choices"][0]["finish_reason"] = "length"
    httpx_mock.add_response(url=CHAT_URL, json=data)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(LengthFinishReasonError):
            await client.achat_parse("Solve 8x+7=-23", response_format=MathResult)
