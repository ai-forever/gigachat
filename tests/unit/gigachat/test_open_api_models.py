"""Exercise public response variants and schema preservation on the wire."""

import copy
import json
from collections.abc import Callable
from typing import Any

import httpx2
import pytest

from gigachat import GigaChat, RequestOptions
from gigachat.exceptions import APIResponseValidationError
from gigachat.models.embeddings import Embedding, EmbeddingError


async def call(
    asynchronous: bool, handler: Callable[[httpx2.Request], httpx2.Response], operation: str, *args: Any, **kwargs: Any
) -> Any:
    if asynchronous:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as transport:
            async with GigaChat(
                async_http_client=transport, access_token="token", model="model", base_url="https://example.test/v1"
            ) as client:
                return await getattr(client, "a" + operation)(*args, **kwargs)
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as sync_transport:
        with GigaChat(
            http_client=sync_transport, access_token="token", model="model", base_url="https://example.test/v1"
        ) as client:
            return getattr(client, operation)(*args, **kwargs)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("input_", ["hello", ["hello", "too long"]])
async def test_embeddings_wire_variants(asynchronous: bool, input_: str | list[str]) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/v1/embeddings"
        assert request.headers["content-type"] == "application/json"
        assert request.headers["x-test"] == "options"
        assert json.loads(request.content) == {
            "input": input_,
            "model": "Embeddings",
            "encoding_format": "base64",
            "truncate": "discard",
        }
        return httpx2.Response(
            200,
            headers={"x-request-id": "embedding-request"},
            json={
                "object": "list",
                "data": [
                    {"object": "embedding", "index": 0, "embedding": "AACAPw==", "usage": {"prompt_tokens": 1}},
                    {
                        "object": "embedding",
                        "index": 1,
                        "embedding": [0.5],
                        "usage": {"prompt_tokens": 1},
                        "truncated": True,
                    },
                    {"object": "error", "index": 2, "error": {"message": "too long"}, "future": 1},
                ],
            },
        )

    result = await call(
        asynchronous,
        handler,
        "embeddings",
        input_,
        encoding_format="base64",
        truncate="discard",
        request_options=RequestOptions(extra_headers={"x-test": "options"}),
    )
    assert isinstance(result.data[0], Embedding)
    assert result.data[0].embedding == "AACAPw=="
    assert result.data[0].truncated is None
    assert result.data[1].embedding == [0.5]
    assert result.data[1].truncated is True
    assert isinstance(result.data[2], EmbeddingError)
    assert result.data[2].error == {"message": "too long"}
    assert result.data[2].model_extra == {"future": 1}
    assert result.x_headers["x-request-id"] == "embedding-request"


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("array", [False, True])
async def test_tokens_scalar_and_array_response(asynchronous: bool, array: bool) -> None:
    row = {"tokens": 1, "characters": 5, "object": "tokens"}

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/v1/tokens/count"
        assert json.loads(request.content) == {"input": "hello", "model": "model"}
        return httpx2.Response(200, json=[row] if array else row, headers={"x-request-id": "count-request"})

    result = await call(asynchronous, handler, "tokens_count", "hello")
    assert len(result) == 1
    assert result[0].tokens == 1
    assert result[0].x_headers["x-request-id"] == "count-request"


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("payload", [None, "invalid", [None], {"tokens": "invalid"}])
async def test_invalid_token_response_preserves_sdk_error_metadata(asynchronous: bool, payload: Any) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, content=json.dumps(payload), headers={"x-request-id": "invalid-request"})

    with pytest.raises(APIResponseValidationError) as caught:
        await call(asynchronous, handler, "tokens_count", "hello")
    assert caught.value.__cause__ is not None
    assert caught.value.request_id == "invalid-request"


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("operation", ["get_model", "get_models", "get_file", "get_files"])
async def test_model_and_file_metadata(asynchronous: bool, operation: str) -> None:
    model = {
        "id": "model",
        "object": "model",
        "owned_by": "provider",
        "type": "future-type",
        "features": ["future"],
        "next": {"value": 1},
    }
    file = {
        "id": "file",
        "object": "file",
        "bytes": 12,
        "created_at": 1,
        "filename": "a.txt",
        "purpose": "general",
        "modalities": ["text", "future"],
        "access_policy": "private",
    }
    item = model if "model" in operation else file
    listing = operation.endswith("s")

    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json={"object": "list", "data": [item]} if listing else item)

    result = await call(asynchronous, handler, operation, *([] if listing else ["item"]))
    entry = result.data[0] if listing else result
    if "model" in operation:
        assert entry.type == "future-type"
        assert entry.features == ["future"]
        assert entry.model_extra == {"next": {"value": 1}}
    else:
        assert entry.modalities == ["text", "future"]
        assert entry.access_policy == "private"


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_functions_convert_sends_raw_yaml(asynchronous: bool) -> None:
    source = "openapi: 3.0.0\ninfo:\n  title: example\n"

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/v1/functions/convert"
        assert request.headers["content-type"] == "application/x-yaml"
        assert request.content == source.encode()
        return httpx2.Response(200, json={"functions": []})

    result = await call(asynchronous, handler, "openapi_function_convert", source)
    assert result.functions == []


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("flat", [False, True])
async def test_native_schema_and_primary_ranker_on_wire(asynchronous: bool, flat: bool) -> None:
    schema = {
        "type": "object",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": {"value": {"anyOf": [{"type": "string"}, {"type": "null"}]}},
        "properties": {"value": {"$ref": "#/$defs/value"}, "allowed": True, "blocked": False},
        "anyOf": [{"required": ["value"]}, {"required": ["allowed"]}],
        "oneOf": [{"properties": {"value": {"const": "x"}}}, {"properties": {"value": {"const": None}}}],
        "allOf": [{"additionalProperties": False}],
        "x-provider": {"enabled": True},
    }
    function = {"name": "lookup", "description": "Lookup a value", **(schema if flat else {"parameters": schema})}
    original = copy.deepcopy(function)
    payload = {
        "messages": [],
        "model_options": {"unnormalized_history": False},
        "ranker_options": {"mode": "future-mode", "ignored_functions": ["excluded"]},
        "tools": [{"functions": {"specifications": [function]}}],
    }

    def handler(request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        assert request.url.path == "/v2/chat/completions"
        assert body["model_options"] == {"unnormalized_history": False}
        assert body["ranker_options"] == {"mode": "future-mode", "ignored_functions": ["excluded"]}
        assert body["tools"][0]["functions"]["specifications"][0] == {
            "name": "lookup",
            "description": "Lookup a value",
            "parameters": schema,
        }
        return httpx2.Response(200, json={"messages": []})

    if asynchronous:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as transport:
            async with GigaChat(
                async_http_client=transport, model="model", access_token="token", base_url="https://example.test/v1"
            ) as client:
                await client.achat.create(payload)
    else:
        with httpx2.Client(transport=httpx2.MockTransport(handler)) as sync_transport:
            with GigaChat(
                http_client=sync_transport, model="model", access_token="token", base_url="https://example.test/v1"
            ) as client:
                client.chat.create(payload)
    assert function == original


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_legacy_open_ranker_mode_and_history(asynchronous: bool) -> None:
    from tests.constants import CHAT_COMPLETION

    def handler(request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        assert request.url.path == "/v1/chat/completions"
        assert body["unnormalized_history"] is False
        assert body["function_ranker"] == {"mode": "future-mode"}
        return httpx2.Response(200, json=CHAT_COMPLETION)

    await call(
        asynchronous,
        handler,
        "chat",
        {"messages": [], "unnormalized_history": False, "function_ranker": {"mode": "future-mode"}},
    )
