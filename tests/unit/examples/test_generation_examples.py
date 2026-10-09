import json

import pytest
from examples.chat_completions import model_options, reasoning, thread_storage
from pytest_httpx import HTTPXMock

from gigachat import GigaChat
from gigachat.api import chat, chat_completions
from gigachat.models import ChatCompletionRequest


def test_reasoning_examples_keep_distinct_v1_v2_budget_locations() -> None:
    v1 = chat._build_request_json(reasoning.request_v1())
    v2 = chat_completions._build_request_json(reasoning.request_with_models())
    dictionary = chat_completions._build_request_json(
        ChatCompletionRequest.model_validate(reasoning.request_with_dict())
    )
    assert v2 == dictionary
    assert v1["reasoning_max_tokens"] == 128
    assert v1["max_tokens"] == 512
    assert v2["model_options"]["reasoning"]["max_tokens"] == 128
    assert v2["model_options"]["max_tokens"] == 512
    assert "model" not in v1
    assert "model" not in v2


def test_model_options_examples_serialize_identically() -> None:
    nested = chat_completions._build_request_json(model_options.request_with_models())
    shorthand = chat_completions._build_request_json(
        ChatCompletionRequest.model_validate(model_options.request_with_dict())
    )
    assert nested == shorthand
    assert nested["model_options"]["max_tokens"] == 180
    assert "max_tokens" not in nested


def test_thread_example_continues_without_resending_model_or_history(httpx_mock: HTTPXMock) -> None:
    for content in ("Remembered", "Alex"):
        httpx_mock.add_response(
            url="https://example.test/v2/chat/completions",
            json={"thread_id": "thread-1", "messages": [{"role": "assistant", "content": content}]},
        )
    with GigaChat(base_url="https://example.test/v1", model="configured-model", session_id="session-1") as client:
        first, second = thread_storage.run(client)
    assert first.thread_id == second.thread_id == "thread-1"
    requests = httpx_mock.get_requests()
    first_body, second_body = [json.loads(request.content) for request in requests]
    assert first_body["model"] == "configured-model"
    assert first_body["storage"] == {}
    assert "model" not in second_body
    assert second_body["storage"] == {"thread_id": "thread-1"}
    assert second_body["messages"] == [{"role": "user", "content": [{"text": "What is my name?"}]}]
    assert all(request.headers["X-Session-ID"] == "session-1" for request in requests)


def test_thread_example_stops_if_storage_was_not_enabled(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="https://example.test/v2/chat/completions", json={"messages": []})
    with GigaChat(base_url="https://example.test/v1", model="configured-model") as client:
        with pytest.raises(RuntimeError, match="did not return a thread_id"):
            thread_storage.run(client)
    assert len(httpx_mock.get_requests()) == 1
