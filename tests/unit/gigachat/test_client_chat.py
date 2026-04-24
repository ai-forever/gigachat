import copy
import json
import warnings
from typing import Any, List, Optional, cast

import pytest
from pydantic import BaseModel, ValidationError
from pytest_httpx import HTTPXMock

from gigachat.api import chat_completions, legacy_chat
from gigachat.client import (
    GIGACHAT_MODEL,
    GigaChatAsyncClient,
    GigaChatSyncClient,
    _parse_chat,
    _parse_chat_completion,
)
from gigachat.context import chat_completions_url_cvar, chat_url_cvar
from gigachat.exceptions import AuthenticationError, LengthFinishReasonError
from gigachat.models import (
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Messages,
    MessagesRole,
)
from gigachat.models.chat_completions import ChatCompletionChunk as PrimaryChatCompletionChunk
from gigachat.settings import Settings
from tests.constants import (
    ACCESS_TOKEN,
    AUTH_URL,
    BASE_URL,
    CHAT,
    CHAT_COMPLETION,
    CHAT_COMPLETION_FUNCTION,
    CHAT_COMPLETION_STREAM,
    CHAT_FUNCTION,
    CHAT_URL,
    CREDENTIALS,
    HEADERS_STREAM,
    OAUTH_TOKEN_EXPIRED,
    OAUTH_TOKEN_VALID,
    PASSWORD,
    PASSWORD_TOKEN_EXPIRED,
    PASSWORD_TOKEN_VALID,
    TOKEN_URL,
    USER,
)

PRIMARY_CHAT_COMPLETION = {
    "model": "GigaChat-2-Max",
    "created_at": 1760434636,
    "thread_id": "thread-1",
    "message_id": "message-1",
    "messages": [
        {
            "role": "assistant",
            "content": [{"text": "primary response"}],
            "finish_reason": "stop",
        }
    ],
    "usage": {
        "input_tokens": 10,
        "output_tokens": 4,
        "total_tokens": 14,
    },
}

PRIMARY_CHAT_COMPLETION_STREAM = (
    b'data: {"model":"GigaChat-2-Max","created_at":1760434637,'
    b'"messages":[{"role":"assistant","content":"primary chunk"}]}\n\n'
    b"data: [DONE]\n\n"
)


class MathResult(BaseModel):
    steps: List[str]
    final_answer: str


@pytest.mark.parametrize(
    ("payload_value", "setting_value", "expected"),
    [
        (None, None, GIGACHAT_MODEL),
        (None, "setting_model", "setting_model"),
        ("payload_model", None, "payload_model"),
        ("payload_model", "setting_model", "payload_model"),
    ],
)
def test__parse_chat_model(payload_value: Optional[str], setting_value: Optional[str], expected: str) -> None:
    actual = _parse_chat(Chat(messages=[], model=payload_value), Settings(model=setting_value))
    assert actual.model is expected


@pytest.mark.parametrize(
    ("payload_value", "setting_value", "expected"),
    [
        (None, None, None),
        (None, False, False),
        (None, True, True),
        (False, None, False),
        (False, False, False),
        (False, True, False),
        (True, None, True),
        (True, False, True),
        (True, True, True),
    ],
)
def test__parse_chat_profanity_check(
    payload_value: Optional[bool],
    setting_value: Optional[bool],
    expected: Optional[bool],
) -> None:
    actual = _parse_chat(
        Chat(messages=[], profanity_check=payload_value),
        Settings(profanity_check=setting_value),
    )
    assert actual.profanity_check is expected


@pytest.mark.parametrize(
    ("payload_value", "setting_value", "expected"),
    [
        (None, None, GIGACHAT_MODEL),
        (None, "setting_model", "setting_model"),
        ("payload_model", None, "payload_model"),
        ("payload_model", "setting_model", "payload_model"),
    ],
)
def test__parse_chat_completion_model(
    payload_value: Optional[str],
    setting_value: Optional[str],
    expected: str,
) -> None:
    actual = _parse_chat_completion(
        ChatCompletionRequest(messages=[ChatMessage(role="user", content="text")], model=payload_value),
        Settings(model=setting_value),
    )
    assert actual.model == expected


def test__parse_chat_completion_preserves_missing_model_for_assistant() -> None:
    actual = _parse_chat_completion(
        {
            "assistant_id": "assistant-1",
            "messages": [{"role": "user", "content": "text"}],
        },
        Settings(model="setting_model"),
    )

    assert actual.model is None
    assert actual.assistant_id == "assistant-1"


def test__parse_chat_completion_accepts_storage_bool() -> None:
    actual = _parse_chat_completion(
        {
            "messages": [{"role": "user", "content": "text"}],
            "storage": True,
        },
        Settings(model="setting_model"),
    )

    assert actual.storage is True
    assert actual.model == "setting_model"


def test_chat(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
        with pytest.warns(DeprecationWarning, match=r"client\.chat\(\.\.\.\)"):
            response = client.chat("text")

    assert isinstance(response, ChatCompletion)


def test_chat_root_shim_warns_and_uses_legacy_route_when_primary_route_differs(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(url=f"{BASE_URL}/chat/completions/legacy", json=CHAT_COMPLETION)

        with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            with pytest.warns(DeprecationWarning, match=r"client\.chat\(\.\.\.\)"):
                response = client.chat("text")
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert isinstance(response, ChatCompletion)
    assert not isinstance(response, ChatCompletionResponse)
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/legacy"


def test_chat_rejects_pydantic_response_format_on_chat() -> None:
    payload = {
        "messages": [{"role": "user", "content": "Solve 2+2"}],
        "response_format": MathResult,
    }

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(TypeError, match="client\\.chat\\.legacy\\.parse"):
            client.chat.legacy.create(payload)


def test_chat_legacy_create_does_not_warn(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = client.chat.legacy.create("text")

    assert isinstance(response, ChatCompletion)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_chat_create_uses_primary_route(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(url=f"{BASE_URL}/chat/completions/primary", json=PRIMARY_CHAT_COMPLETION)

        with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            response = client.chat.create("text")
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert isinstance(response, ChatCompletionResponse)
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/primary"


def test_chat_create_uses_v2_primary_route_with_legacy_v1_base_url_and_token(httpx_mock: HTTPXMock) -> None:
    versioned_base_url = "https://host/v1"
    httpx_mock.add_response(url=f"{versioned_base_url}/token", json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url="https://host/v2/chat/completions", json=PRIMARY_CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=versioned_base_url, user=USER, password=PASSWORD) as client:
        response = client.chat.create("text")

    requests = httpx_mock.get_requests()
    assert isinstance(response, ChatCompletionResponse)
    assert len(requests) == 2
    assert str(requests[0].url) == f"{versioned_base_url}/token"
    assert str(requests[1].url) == "https://host/v2/chat/completions"


def test_chat_create_normalizes_string_tools_in_request_body(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(url=f"{BASE_URL}/chat/completions/primary", json=PRIMARY_CHAT_COMPLETION)

        with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            response = client.chat.create(
                {
                    "messages": [{"role": "user", "content": "text"}],
                    "tools": ["code_interpreter", "web_search"],
                }
            )
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    request_body = json.loads(requests[0].content)

    assert isinstance(response, ChatCompletionResponse)
    assert request_body["tools"] == [
        {"code_interpreter": {}},
        {"web_search": {}},
    ]


def test_chat_legacy_create_uses_legacy_route_when_primary_route_differs(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(url=f"{BASE_URL}/chat/completions/legacy", json=CHAT_COMPLETION)

        with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            response = client.chat.legacy.create("text")
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert isinstance(response, ChatCompletion)
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/legacy"


def test_chat_stream_uses_primary_route(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions/primary",
            content=PRIMARY_CHAT_COMPLETION_STREAM,
            headers=HEADERS_STREAM,
        )

        with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            response = list(client.chat.stream("text"))
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert len(response) == 1
    assert all(isinstance(chunk, PrimaryChatCompletionChunk) for chunk in response)
    assert response[0].messages is not None
    assert response[0].messages[0].content is not None
    assert response[0].messages[0].content[0].text == "primary chunk"
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/primary"


def test_chat_legacy_stream_uses_legacy_route_when_primary_route_differs(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions/legacy",
            content=CHAT_COMPLETION_STREAM,
            headers=HEADERS_STREAM,
        )

        with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            response = list(client.chat.legacy.stream("text"))
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/legacy"


def test_chat_create_uses_explicit_primary_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_chat_sync(
        client: Any,
        *,
        chat: ChatCompletionRequest,
        access_token: Optional[str] = None,
    ) -> ChatCompletionResponse:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return ChatCompletionResponse.model_validate(PRIMARY_CHAT_COMPLETION)

    monkeypatch.setattr(chat_completions, "chat_sync", fake_chat_sync)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = client.chat.create("text")

    assert isinstance(response, ChatCompletionResponse)
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], ChatCompletionRequest)
    assert captured["chat"].messages[0].content is not None
    assert captured["chat"].messages[0].content[0].text == "text"


def test_chat_stream_uses_explicit_primary_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_stream_sync(
        client: Any,
        *,
        chat: ChatCompletionRequest,
        access_token: Optional[str] = None,
    ) -> Any:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return iter(
            [
                PrimaryChatCompletionChunk.model_validate(
                    {
                        "model": "GigaChat-2-Max",
                        "created_at": 1760434637,
                        "messages": [{"role": "assistant", "content": "primary chunk"}],
                    }
                )
            ]
        )

    monkeypatch.setattr(chat_completions, "stream_sync", fake_stream_sync)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = list(client.chat.stream("text"))

    assert len(response) == 1
    assert isinstance(response[0], PrimaryChatCompletionChunk)
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], ChatCompletionRequest)
    assert captured["chat"].messages[0].content is not None
    assert captured["chat"].messages[0].content[0].text == "text"


def test_chat_parse_uses_primary_route(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["content"] = [
        {"text": '{"steps": ["Переносим 7 в правую часть", "Делим на 8"], '},
        {"text": '"final_answer": "x = -3.75"}'},
    ]

    try:
        httpx_mock.add_response(url=f"{BASE_URL}/chat/completions/primary", json=response_payload)

        with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            completion, parsed = client.chat.parse("Solve 8x+7=-23", response_format=MathResult)
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    request_body = json.loads(requests[0].content)

    assert isinstance(completion, ChatCompletionResponse)
    assert isinstance(parsed, MathResult)
    assert parsed.final_answer == "x = -3.75"
    response_format = request_body["model_options"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert isinstance(response_format["schema"], dict)
    assert response_format["strict"] is True
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/primary"


def test_chat_parse_sets_primary_response_format_strict_false(httpx_mock: HTTPXMock) -> None:
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["content"] = [
        {"text": '{"steps": ["Шаг"], "final_answer": "4"}'},
    ]
    httpx_mock.add_response(url=CHAT_URL, json=response_payload)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = client.chat.parse("Solve 2+2", response_format=MathResult, strict=False)

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)

    assert isinstance(completion, ChatCompletionResponse)
    assert isinstance(parsed, MathResult)
    assert body["model_options"]["response_format"]["strict"] is False


def test_chat_parse_raises_for_invalid_primary_json(httpx_mock: HTTPXMock) -> None:
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["content"] = [{"text": "not json"}]
    httpx_mock.add_response(url=CHAT_URL, json=response_payload)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(json.JSONDecodeError):
            client.chat.parse("Solve 2+2", response_format=MathResult)


def test_chat_parse_raises_for_primary_schema_mismatch(httpx_mock: HTTPXMock) -> None:
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["content"] = [{"text": '{"wrong_field": 42}'}]
    httpx_mock.add_response(url=CHAT_URL, json=response_payload)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ValidationError):
            client.chat.parse("Solve 2+2", response_format=MathResult)


def test_chat_parse_raises_for_primary_length_finish_reason(httpx_mock: HTTPXMock) -> None:
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["finish_reason"] = "length"
    response_payload["messages"][0]["content"] = [{"text": '{"steps": ["Шаг"]'}]
    httpx_mock.add_response(url=CHAT_URL, json=response_payload)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(LengthFinishReasonError):
            client.chat.parse("Solve 2+2", response_format=MathResult)


def test_chat_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = client.chat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = client.chat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_credentials_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused across multiple API calls (no duplicate auth requests)."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = client.chat.legacy.create(CHAT)
        response2 = client.chat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_credentials_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers new auth request for each API call."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = client.chat.legacy.create(CHAT)
        response2 = client.chat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_user_password_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused with user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = client.chat.legacy.create(CHAT)
        response2 = client.chat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_user_password_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers refresh with user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = client.chat.legacy.create(CHAT)
        response2 = client.chat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


def test_chat_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response = client.chat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


def test_chat_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)


def test_chat_update_token_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        access_token=ACCESS_TOKEN,
        credentials=CREDENTIALS,
    ) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


def test_chat_update_token_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


def test_chat_update_token_false(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)
        assert client.token == ACCESS_TOKEN


def test_chat_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        response = client.chat.legacy.create(CHAT)

    assert client.token
    assert client.token != ACCESS_TOKEN
    assert isinstance(response, ChatCompletion)


def test_chat_update_token_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            client.chat.legacy.create(CHAT)

    assert client.token
    assert client.token != ACCESS_TOKEN


def test_chat_with_functions(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION_FUNCTION)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = client.chat.legacy.create(CHAT_FUNCTION)

    assert isinstance(response, ChatCompletion)
    assert response.choices[0].finish_reason == "function_call"
    assert response.choices[0].message.function_call is not None
    assert response.choices[0].message.function_call.name == "fc"
    assert response.choices[0].message.function_call.arguments is not None
    assert response.choices[0].message.function_call.arguments == {
        "location": "Москва",
        "num_days": 0,
    }


def test_stream_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.stream\(\.\.\.\)"):
            response = list(client.stream(CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_root_shim_warns_and_uses_legacy_route_when_primary_route_differs(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions/legacy",
            content=CHAT_COMPLETION_STREAM,
            headers=HEADERS_STREAM,
        )

        with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            with pytest.warns(DeprecationWarning, match=r"client\.stream\(\.\.\.\)"):
                response = list(client.stream("text"))
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert not any(isinstance(chunk, PrimaryChatCompletionChunk) for chunk in response)
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/legacy"


def test_chat_legacy_stream_does_not_warn(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = list(client.chat.legacy.stream(CHAT))

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_chat_legacy_create_uses_explicit_legacy_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_chat_sync(client: Any, *, chat: Chat, access_token: Optional[str] = None) -> ChatCompletion:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return ChatCompletion.model_validate(CHAT_COMPLETION)

    monkeypatch.setattr(legacy_chat, "chat_sync", fake_chat_sync)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = client.chat.legacy.create("text")

    assert isinstance(response, ChatCompletion)
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], Chat)


def test_chat_legacy_stream_uses_explicit_legacy_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_stream_sync(client: Any, *, chat: Chat, access_token: Optional[str] = None) -> Any:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return iter(
            [
                ChatCompletionChunk.model_validate(
                    {
                        "choices": [{"delta": {"content": "hello"}, "index": 0, "finish_reason": None}],
                        "created": 0,
                        "model": "test-model",
                        "object": "chat.completion.chunk",
                    }
                )
            ]
        )

    monkeypatch.setattr(legacy_chat, "stream_sync", fake_stream_sync)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = list(client.chat.legacy.stream("text"))

    assert len(response) == 1
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], Chat)


def test_stream_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    with GigaChatSyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            list(client.chat.legacy.stream(CHAT))


def test_stream_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        response = list(client.chat.legacy.stream(CHAT))

    assert client.token
    assert client.token != ACCESS_TOKEN
    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


def test_stream_update_token_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    with GigaChatSyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            list(client.chat.legacy.stream(CHAT))

    assert client.token
    assert client.token != ACCESS_TOKEN


async def test_achat(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.achat\(\.\.\.\)"):
            response = await client.achat("text")

    assert isinstance(response, ChatCompletion)


async def test_achat_root_shim_warns_and_uses_legacy_route_when_primary_route_differs(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(url=f"{BASE_URL}/chat/completions/legacy", json=CHAT_COMPLETION)

        async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            with pytest.warns(DeprecationWarning, match=r"client\.achat\(\.\.\.\)"):
                response = await client.achat("text")
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert isinstance(response, ChatCompletion)
    assert not isinstance(response, ChatCompletionResponse)
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/legacy"


async def test_achat_rejects_pydantic_response_format_on_chat() -> None:
    class MathResult(BaseModel):
        answer: str

    payload = Chat.model_construct(
        messages=[Messages(role=MessagesRole.USER, content="Solve 2+2")],
        response_format=cast(Any, MathResult),
    )

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(TypeError, match="client\\.chat\\.legacy\\.parse"):
            await client.achat.legacy.create(payload)


async def test_achat_legacy_create_does_not_warn(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = await client.achat.legacy.create("text")

    assert isinstance(response, ChatCompletion)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_achat_create_uses_primary_route(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(url=f"{BASE_URL}/chat/completions/primary", json=PRIMARY_CHAT_COMPLETION)

        async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            response = await client.achat.create("text")
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert isinstance(response, ChatCompletionResponse)
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/primary"


async def test_achat_create_uses_v2_primary_route_with_legacy_v1_base_url_and_token(httpx_mock: HTTPXMock) -> None:
    versioned_base_url = "https://host/v1"
    httpx_mock.add_response(url=f"{versioned_base_url}/token", json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url="https://host/v2/chat/completions", json=PRIMARY_CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=versioned_base_url, user=USER, password=PASSWORD) as client:
        response = await client.achat.create("text")

    requests = httpx_mock.get_requests()
    assert isinstance(response, ChatCompletionResponse)
    assert len(requests) == 2
    assert str(requests[0].url) == f"{versioned_base_url}/token"
    assert str(requests[1].url) == "https://host/v2/chat/completions"


async def test_achat_legacy_create_uses_legacy_route_when_primary_route_differs(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(url=f"{BASE_URL}/chat/completions/legacy", json=CHAT_COMPLETION)

        async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            response = await client.achat.legacy.create("text")
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert isinstance(response, ChatCompletion)
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/legacy"


async def test_achat_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = await client.achat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


async def test_achat_legacy_create_uses_explicit_legacy_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    async def fake_chat_async(client: Any, *, chat: Chat, access_token: Optional[str] = None) -> ChatCompletion:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return ChatCompletion.model_validate(CHAT_COMPLETION)

    monkeypatch.setattr(legacy_chat, "chat_async", fake_chat_async)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = await client.achat.legacy.create("text")

    assert isinstance(response, ChatCompletion)
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], Chat)


async def test_achat_create_uses_explicit_primary_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    async def fake_chat_async(
        client: Any,
        *,
        chat: ChatCompletionRequest,
        access_token: Optional[str] = None,
    ) -> ChatCompletionResponse:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return ChatCompletionResponse.model_validate(PRIMARY_CHAT_COMPLETION)

    monkeypatch.setattr(chat_completions, "chat_async", fake_chat_async)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = await client.achat.create("text")

    assert isinstance(response, ChatCompletionResponse)
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], ChatCompletionRequest)
    assert captured["chat"].messages[0].content is not None
    assert captured["chat"].messages[0].content[0].text == "text"


async def test_achat_stream_uses_primary_route(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions/primary",
            content=PRIMARY_CHAT_COMPLETION_STREAM,
            headers=HEADERS_STREAM,
        )

        async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            response = [chunk async for chunk in client.achat.stream("text")]
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert len(response) == 1
    assert all(isinstance(chunk, PrimaryChatCompletionChunk) for chunk in response)
    assert response[0].messages is not None
    assert response[0].messages[0].content is not None
    assert response[0].messages[0].content[0].text == "primary chunk"
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/primary"


async def test_achat_stream_uses_explicit_primary_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    async def iterate() -> Any:
        yield PrimaryChatCompletionChunk.model_validate(
            {
                "model": "GigaChat-2-Max",
                "created_at": 1760434637,
                "messages": [{"role": "assistant", "content": "primary chunk"}],
            }
        )

    def fake_stream_async(
        client: Any,
        *,
        chat: ChatCompletionRequest,
        access_token: Optional[str] = None,
    ) -> Any:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return iterate()

    monkeypatch.setattr(chat_completions, "stream_async", fake_stream_async)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = [chunk async for chunk in client.achat.stream("text")]

    assert len(response) == 1
    assert isinstance(response[0], PrimaryChatCompletionChunk)
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], ChatCompletionRequest)
    assert captured["chat"].messages[0].content is not None
    assert captured["chat"].messages[0].content[0].text == "text"


async def test_achat_parse_uses_primary_route(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["content"] = [
        {"text": '{"steps": ["Переносим 7 в правую часть", "Делим на 8"], '},
        {"text": '"final_answer": "x = -3.75"}'},
    ]

    try:
        httpx_mock.add_response(url=f"{BASE_URL}/chat/completions/primary", json=response_payload)

        async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            completion, parsed = await client.achat.parse("Solve 8x+7=-23", response_format=MathResult)
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    request_body = json.loads(requests[0].content)

    assert isinstance(completion, ChatCompletionResponse)
    assert isinstance(parsed, MathResult)
    assert parsed.final_answer == "x = -3.75"
    response_format = request_body["model_options"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert isinstance(response_format["schema"], dict)
    assert response_format["strict"] is True
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/primary"


async def test_achat_parse_sets_primary_response_format_strict_false(httpx_mock: HTTPXMock) -> None:
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["content"] = [
        {"text": '{"steps": ["Шаг"], "final_answer": "4"}'},
    ]
    httpx_mock.add_response(url=CHAT_URL, json=response_payload)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        completion, parsed = await client.achat.parse("Solve 2+2", response_format=MathResult, strict=False)

    request = httpx_mock.get_requests()[0]
    body = json.loads(request.content)

    assert isinstance(completion, ChatCompletionResponse)
    assert isinstance(parsed, MathResult)
    assert body["model_options"]["response_format"]["strict"] is False


async def test_achat_parse_raises_for_invalid_primary_json(httpx_mock: HTTPXMock) -> None:
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["content"] = [{"text": "not json"}]
    httpx_mock.add_response(url=CHAT_URL, json=response_payload)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(json.JSONDecodeError):
            await client.achat.parse("Solve 2+2", response_format=MathResult)


async def test_achat_parse_raises_for_primary_schema_mismatch(httpx_mock: HTTPXMock) -> None:
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["content"] = [{"text": '{"wrong_field": 42}'}]
    httpx_mock.add_response(url=CHAT_URL, json=response_payload)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(ValidationError):
            await client.achat.parse("Solve 2+2", response_format=MathResult)


async def test_achat_parse_raises_for_primary_length_finish_reason(httpx_mock: HTTPXMock) -> None:
    response_payload = copy.deepcopy(PRIMARY_CHAT_COMPLETION)
    response_payload["messages"][0]["finish_reason"] = "length"
    response_payload["messages"][0]["content"] = [{"text": '{"steps": ["Шаг"]'}]
    httpx_mock.add_response(url=CHAT_URL, json=response_payload)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with pytest.raises(LengthFinishReasonError):
            await client.achat.parse("Solve 2+2", response_format=MathResult)


async def test_achat_legacy_stream_uses_explicit_legacy_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    async def iterate() -> Any:
        yield ChatCompletionChunk.model_validate(
            {
                "choices": [{"delta": {"content": "hello"}, "index": 0, "finish_reason": None}],
                "created": 0,
                "model": "test-model",
                "object": "chat.completion.chunk",
            }
        )

    def fake_stream_async(client: Any, *, chat: Chat, access_token: Optional[str] = None) -> Any:
        captured["client"] = client
        captured["chat"] = chat
        captured["access_token"] = access_token
        return iterate()

    monkeypatch.setattr(legacy_chat, "stream_async", fake_stream_async)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        response = [chunk async for chunk in client.achat.legacy.stream("text")]

    assert len(response) == 1
    assert captured["access_token"] == ACCESS_TOKEN
    assert isinstance(captured["chat"], Chat)


async def test_achat_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response = await client.achat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


async def test_achat_credentials_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused across multiple async API calls (no duplicate auth requests)."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = await client.achat.legacy.create(CHAT)
        response2 = await client.achat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_credentials_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers new auth request for each async API call."""
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        response1 = await client.achat.legacy.create(CHAT)
        response2 = await client.achat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_user_password_token_reuse(httpx_mock: HTTPXMock) -> None:
    """Verify that valid token is reused with async user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = await client.achat.legacy.create(CHAT)
        response2 = await client.achat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_user_password_expired_token_refresh(httpx_mock: HTTPXMock) -> None:
    """Verify that expired token triggers refresh with async user/password auth."""
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_EXPIRED)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response1 = await client.achat.legacy.create(CHAT)
        response2 = await client.achat.legacy.create(CHAT)

    assert isinstance(response1, ChatCompletion)
    assert isinstance(response2, ChatCompletion)


async def test_achat_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)

    async with GigaChatAsyncClient(base_url=BASE_URL, user=USER, password=PASSWORD) as client:
        response = await client.achat.legacy.create(CHAT)

    assert isinstance(response, ChatCompletion)


async def test_achat_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            await client.achat.legacy.create(CHAT)


async def test_achat_update_token_false(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, access_token=ACCESS_TOKEN) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            await client.achat.legacy.create(CHAT)
        assert client.token == ACCESS_TOKEN


async def test_achat_update_token_credentials(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(
        base_url=BASE_URL,
        auth_url=AUTH_URL,
        access_token=ACCESS_TOKEN,
        credentials=CREDENTIALS,
    ) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            await client.achat.legacy.create(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


async def test_achat_update_token_user_password(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            await client.achat.legacy.create(CHAT)
        assert client.token
        assert client.token != ACCESS_TOKEN


async def test_astream_access_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        with pytest.warns(DeprecationWarning, match=r"client\.astream\(\.\.\.\)"):
            response = [chunk async for chunk in client.astream(CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


async def test_astream_root_shim_warns_and_uses_legacy_route_when_primary_route_differs(httpx_mock: HTTPXMock) -> None:
    primary_url_token = chat_completions_url_cvar.set("/chat/completions/primary")
    legacy_url_token = chat_url_cvar.set("/chat/completions/legacy")

    try:
        httpx_mock.add_response(
            url=f"{BASE_URL}/chat/completions/legacy",
            content=CHAT_COMPLETION_STREAM,
            headers=HEADERS_STREAM,
        )

        async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
            with pytest.warns(DeprecationWarning, match=r"client\.astream\(\.\.\.\)"):
                response = [chunk async for chunk in client.astream("text")]
    finally:
        chat_completions_url_cvar.reset(primary_url_token)
        chat_url_cvar.reset(legacy_url_token)

    requests = httpx_mock.get_requests()
    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert not any(isinstance(chunk, PrimaryChatCompletionChunk) for chunk in response)
    assert len(requests) == 1
    assert str(requests[0].url) == f"{BASE_URL}/chat/completions/legacy"


async def test_achat_legacy_stream_does_not_warn(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(base_url=BASE_URL, access_token=ACCESS_TOKEN) as client:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            response = [chunk async for chunk in client.achat.legacy.stream(CHAT)]

    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


async def test_astream_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=AUTH_URL, json=OAUTH_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, status_code=401)

    async with GigaChatAsyncClient(base_url=BASE_URL, auth_url=AUTH_URL, credentials=CREDENTIALS) as client:
        with pytest.raises(AuthenticationError):
            _ = [chunk async for chunk in client.achat.legacy.stream(CHAT)]


async def test_astream_update_token_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)
    httpx_mock.add_response(url=CHAT_URL, content=CHAT_COMPLETION_STREAM, headers=HEADERS_STREAM)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        assert client.token == ACCESS_TOKEN
        response = [chunk async for chunk in client.achat.legacy.stream(CHAT)]

    assert client.token
    assert client.token != ACCESS_TOKEN
    assert len(response) == 3
    assert all(isinstance(chunk, ChatCompletionChunk) for chunk in response)
    assert response[2].choices[0].finish_reason == "stop"


async def test_astream_update_token_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=CHAT_URL, status_code=401)
    httpx_mock.add_response(url=TOKEN_URL, json=PASSWORD_TOKEN_VALID)

    async with GigaChatAsyncClient(
        base_url=BASE_URL, access_token=ACCESS_TOKEN, user=USER, password=PASSWORD
    ) as client:
        assert client.token == ACCESS_TOKEN
        with pytest.raises(AuthenticationError):
            _ = [chunk async for chunk in client.achat.legacy.stream(CHAT)]
        assert client.token
        assert client.token != ACCESS_TOKEN
