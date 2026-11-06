"""HTTPX2-native request mocking and strict replay of existing VCR cassettes."""

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

import httpx2
import pytest
import yaml


def _url_key(url: str) -> tuple[Any, ...]:
    parts = urlsplit(url)
    port = parts.port or {"http": 80, "https": 443}.get(parts.scheme)
    return (
        parts.scheme.lower(),
        parts.hostname,
        port,
        parts.path,
        sorted(parse_qsl(parts.query, keep_blank_values=True)),
    )


def _body_key(body: Any) -> Any:
    if body is None:
        return ("bytes", b"")
    if isinstance(body, str):
        body = body.encode()
    try:
        return ("json", json.dumps(json.loads(body), sort_keys=True, separators=(",", ":")))
    except (ValueError, UnicodeDecodeError):
        return ("bytes", body)


class HTTPXMock:
    """Match queued responses with native HTTPX2 requests and reject unexpected I/O."""

    def __init__(self) -> None:
        self._responses: list[tuple[dict[str, Any], Any]] = []
        self._requests: list[httpx2.Request] = []
        self._transport = httpx2.MockTransport(self._pop)

    def add_response(self, *, url: Any = None, method: str | None = None, **kwargs: Any) -> None:
        kwargs.setdefault("status_code", 200)
        matchers = {"url": url, "method": method}
        for key in ("match_content", "match_json", "match_headers"):
            if key in kwargs:
                matchers[key] = kwargs.pop(key)
        self._responses.append((matchers, lambda request: httpx2.Response(request=request, **kwargs)))

    def add_callback(self, callback: Callable[..., Any], **matchers: Any) -> None:
        self._responses.append((matchers, callback))

    def add_exception(self, exception: Exception, **matchers: Any) -> None:
        def raise_exception(request: httpx2.Request) -> httpx2.Response:
            raise exception

        self.add_callback(raise_exception, **matchers)

    @staticmethod
    def _matches(request: httpx2.Request, matchers: dict[str, Any]) -> bool:
        url = matchers.get("url")
        if url is not None:
            if isinstance(url, re.Pattern):
                if not url.fullmatch(str(request.url)):
                    return False
            elif _url_key(str(request.url)) != _url_key(str(url)):
                return False
        if matchers.get("method") and request.method != matchers["method"].upper():
            return False
        if "match_content" in matchers and request.content != matchers["match_content"]:
            return False
        if "match_json" in matchers and _body_key(request.content) != _body_key(json.dumps(matchers["match_json"])):
            return False
        return all(request.headers.get(key) == value for key, value in matchers.get("match_headers", {}).items())

    def _pop(self, request: httpx2.Request) -> Any:
        self._requests.append(request)
        for index, (matchers, callback) in enumerate(self._responses):
            if self._matches(request, matchers):
                self._responses.pop(index)
                return callback(request)
        raise AssertionError(f"Unexpected HTTPX2 request: {request.method} {request.url}")

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        return self._transport.handle_request(request)

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        return await self._transport.handle_async_request(request)

    def get_requests(self, **matchers: Any) -> list[httpx2.Request]:
        return [request for request in self._requests if self._matches(request, matchers)]

    def get_request(self, **matchers: Any) -> httpx2.Request | None:
        requests = self.get_requests(**matchers)
        assert len(requests) <= 1, "More than one request matched; use get_requests()"
        return requests[0] if requests else None

    def assert_all_responses_requested(self) -> None:
        assert not self._responses, f"{len(self._responses)} mocked HTTP response(s) were not requested"


def install_mock(monkeypatch: pytest.MonkeyPatch, mock: HTTPXMock) -> None:
    """Intercept native HTTPX2 network transports without changing module identities."""
    monkeypatch.setattr(httpx2.HTTPTransport, "handle_request", lambda self, request: mock.handle_request(request))

    async def handle_async_request(self: Any, request: httpx2.Request) -> httpx2.Response:
        return await mock.handle_async_request(request)

    monkeypatch.setattr(httpx2.AsyncHTTPTransport, "handle_async_request", handle_async_request)


class CassetteReplay(HTTPXMock):
    """Replay each recorded interaction once with method, URL, query and body matching."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        data = yaml.safe_load(path.read_text())
        for interaction in data["interactions"]:
            recorded = interaction["request"]
            response = interaction["response"]
            body = response.get("body", {}).get("string", b"")
            if isinstance(body, str):
                body = body.encode()
            headers = [
                (name, value)
                for name, values in response.get("headers", {}).items()
                if name.lower() not in {"content-length", "transfer-encoding", "content-encoding"}
                for value in values
            ]
            self._responses.append(
                (
                    {"method": recorded["method"], "url": recorded["uri"], "cassette_body": recorded.get("body")},
                    lambda request, status=response["status"]["code"], body=body, headers=headers: httpx2.Response(
                        status, content=body, headers=headers, request=request
                    ),
                )
            )

    @staticmethod
    def _matches(request: httpx2.Request, matchers: dict[str, Any]) -> bool:
        if not HTTPXMock._matches(request, matchers):
            return False
        expected = matchers.get("cassette_body")
        actual = request.content
        # The checked-in OAuth requests deliberately redact only scope; other body
        # fields remain part of the strict replay contract.
        expected_bytes = expected.encode() if isinstance(expected, str) else expected
        if expected_bytes and b"scope=REDACTED" in expected_bytes:
            actual = re.sub(rb"scope=[^&\s]*", b"scope=REDACTED", actual)
        return bool(_body_key(actual) == _body_key(expected))

    def assert_all_responses_requested(self) -> None:
        # Old recordings refreshed the same OAuth token for every request when
        # exp was interpreted as milliseconds. The fixed SDK reuses that token;
        # allow only these redundant OAuth entries, keeping API responses strict.
        oauth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self._responses = [
            (matchers, callback)
            for matchers, callback in self._responses
            if not (
                matchers.get("url") == oauth_url
                and matchers.get("method") == "POST"
                and any(self._matches(request, matchers) for request in self._requests)
            )
        ]
        super().assert_all_responses_requested()
