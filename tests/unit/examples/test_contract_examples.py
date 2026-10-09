import json

import pytest
from examples.chat_completions import additional_fields, response_metadata, session_headers
from pytest_httpx import HTTPXMock
from tests.constants import CHAT_COMPLETION

from gigachat import GigaChat, session_id_cvar
from gigachat.exceptions import BadRequestError

BASE_URL = "https://example.test/v1"
V1_URL = "https://example.test/v1/chat/completions"
V2_URL = "https://example.test/v2/chat/completions"


def test_extra_field_examples_use_correct_wire_locations(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=V1_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=V2_URL, json={"messages": []})
    with GigaChat(base_url=BASE_URL, model="test-model") as client:
        client.chat(additional_fields.v1_request())
        client.chat.create(additional_fields.v2_request())
    v1, v2 = [json.loads(request.content) for request in httpx_mock.get_requests()]
    assert v1["max_tokens"] == 32
    assert v2["model_options"]["max_tokens"] == 32
    assert "max_tokens" not in v2
    assert "additional_fields" not in v1
    assert "additional_fields" not in v2


def test_session_example_restores_default_session(httpx_mock: HTTPXMock) -> None:
    for _ in range(3):
        httpx_mock.add_response(url=V2_URL, json={"messages": []})
    with GigaChat(base_url=BASE_URL, model="test-model", session_id="default-session") as client:
        assert len(session_headers.run(client)) == 3
    headers = [request.headers["X-Session-ID"] for request in httpx_mock.get_requests()]
    assert headers[0] == headers[2] == "default-session"
    assert headers[1] != "default-session"
    assert session_id_cvar.get() is None


def test_session_example_resets_context_after_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=V2_URL, json={"messages": []})
    httpx_mock.add_response(url=V2_URL, status_code=400, json={"message": "Example error"})
    with GigaChat(base_url=BASE_URL, model="test-model", session_id="default-session") as client:
        with pytest.raises(BadRequestError):
            session_headers.run(client)
    assert session_id_cvar.get() is None


def test_metadata_example_reads_text_and_terminal_events(
    httpx_mock: HTTPXMock, capsys: pytest.CaptureFixture[str]
) -> None:
    httpx_mock.add_response(
        url=V2_URL,
        json={
            "messages": [{"role": "assistant", "content": [{"text": "hello"}], "finish_reason": "length"}],
            "additional_data": {"custom": {"value": None}},
        },
    )
    httpx_mock.add_response(
        url=V2_URL,
        headers={"Content-Type": "text/event-stream"},
        content=(
            b'data: {"messages":[{"role":"assistant","content":[{"text":"streamed"}]}]}\n\n'
            b'event: response.message.done\ndata: {"finish_reason":"error",'
            b'"usage":{"output_tokens":2},"error_details":{"user_message":"Retry later"}}\n\n'
            b"data: [DONE]\n\n"
        ),
    )
    with GigaChat(base_url=BASE_URL, model="test-model") as client:
        response_metadata.run(client)
    output = capsys.readouterr().out
    assert "assistant: hello" in output
    assert "assistant finish reason: length" in output
    assert "assistant: streamed" in output
    assert '"value": null' in output
    assert '"output_tokens":2' in output
    assert "Retry later" in output
    assert "Finish reason: error" in output


def test_metadata_example_prints_readable_http_errors(
    httpx_mock: HTTPXMock, capsys: pytest.CaptureFixture[str]
) -> None:
    content = '{"message":"Неверные параметры"}'.encode()
    httpx_mock.add_response(url=V2_URL, status_code=400, content=content)
    with GigaChat(base_url=BASE_URL, model="test-model") as client:
        with pytest.raises(BadRequestError) as exc_info:
            response_metadata.run(client)
    assert "Неверные параметры" in capsys.readouterr().out
    assert exc_info.value.content == content
