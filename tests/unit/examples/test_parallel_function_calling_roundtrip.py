import json
from threading import Barrier
from typing import Any, Dict

import pytest
from examples.tools.any_function_call import request_with_any
from examples.tools.parallel_function_calling import build_request
from examples.tools.parallel_function_calling_roundtrip import build_follow_up_request, run
from pytest_httpx import HTTPXMock

from gigachat import GigaChat
from gigachat.models import ChatCompletionResponse, PrimaryChatFunctionCall

BASE_URL = "https://example.test/v1"
CHAT_URL = "https://example.test/v2/chat/completions"
CALLS: Dict[str, Any] = {
    "messages": [
        {"role": "reasoning", "content": [{"text": "Need two cities"}]},
        {
            "role": "assistant",
            "tools_state_id": "state-1",
            "content": [
                {"function_call": {"id": "call-1", "name": "get_weather", "arguments": {"city": "Москва"}}},
                {"function_call": {"id": "call-2", "name": "get_weather", "arguments": {"city": "Казань"}}},
            ],
        },
    ]
}


def test_full_loop_keeps_calls_results_state_and_reasoning(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CALLS)
    httpx_mock.add_response(
        url=CHAT_URL,
        json={
            "messages": [
                {
                    "role": "assistant",
                    "tools_state_id": "state-2",
                    "content": [
                        {"function_call": {"id": "call-3", "name": "get_rate", "arguments": {"currency": "USD"}}}
                    ],
                }
            ]
        },
    )
    httpx_mock.add_response(
        url=CHAT_URL,
        json={
            "messages": [
                {"role": "reasoning", "content": "Ready to answer"},
                {"role": "assistant", "content": "Final comparison", "finish_reason": "stop"},
            ]
        },
    )
    with GigaChat(base_url=BASE_URL, model="test-model") as client:
        assert run(client, request_with_any()) == "Final comparison"
    first, second, third = [json.loads(request.content) for request in httpx_mock.get_requests()]
    assert first["tool_config"] == {"mode": "any", "functions_names_any": ["get_weather", "get_rate"]}
    assert "tool_config" not in second
    assert second["messages"][1:3] == CALLS["messages"]
    tool = second["messages"][3]
    assert tool["tools_state_id"] == "state-1"
    results = [part["function_result"] for part in tool["content"]]
    assert [result["id"] for result in results] == ["call-1", "call-2"]
    assert [result["result"]["city"] for result in results] == ["Москва", "Казань"]
    assert third["messages"][:4] == second["messages"]
    assert third["messages"][-1]["tools_state_id"] == "state-2"
    assert third["messages"][-1]["content"][0]["function_result"]["id"] == "call-3"


def test_functions_really_execute_concurrently(monkeypatch: pytest.MonkeyPatch) -> None:
    barrier = Barrier(2)

    def execute(call: PrimaryChatFunctionCall) -> Dict[str, Any]:
        barrier.wait(timeout=5)
        return {"city": call.arguments["city"]}

    monkeypatch.setattr("examples.tools.parallel_function_calling_roundtrip.execute_function", execute)
    request = build_request()
    before = request.model_dump()
    follow_up = build_follow_up_request(request, ChatCompletionResponse.model_validate(CALLS))
    assert request.model_dump() == before
    assert follow_up.messages[-1].content is not None
    assert len(follow_up.messages[-1].content) == 2


def test_state_is_taken_from_each_originating_message() -> None:
    response = ChatCompletionResponse.model_validate(
        {
            "messages": [
                {"role": "assistant", "tools_state_id": "state-a", "content": [CALLS["messages"][1]["content"][0]]},
                {"role": "assistant", "tools_state_id": "state-b", "content": [CALLS["messages"][1]["content"][1]]},
            ]
        }
    )
    follow_up = build_follow_up_request(build_request(), response)
    assert [message.tools_state_id for message in follow_up.messages[-2:]] == ["state-a", "state-b"]


def test_loop_stops_at_limit(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CALLS)
    with GigaChat(base_url=BASE_URL, model="test-model") as client:
        with pytest.raises(RuntimeError, match="exceeded max_steps"):
            run(client, max_steps=1)
    assert len(httpx_mock.get_requests()) == 1


def test_any_example_checks_that_initial_selection_is_honored(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json={"messages": [{"role": "assistant", "content": "No tools"}]})
    with GigaChat(base_url=BASE_URL, model="test-model") as client:
        with pytest.raises(RuntimeError, match="did not honor"):
            run(client, request_with_any())


@pytest.mark.parametrize("finish_reason", ["length", "error"])
def test_incomplete_generation_is_not_presented_as_final(httpx_mock: HTTPXMock, finish_reason: str) -> None:
    httpx_mock.add_response(
        url=CHAT_URL,
        json={
            "messages": [
                {
                    "role": "assistant",
                    "content": "Partial",
                    "finish_reason": finish_reason,
                }
            ]
        },
    )
    with GigaChat(base_url=BASE_URL, model="test-model") as client:
        with pytest.raises(RuntimeError, match="before completion"):
            run(client)
