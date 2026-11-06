"""Verify native test transport isolation and cassette matching contracts."""

from pathlib import Path

import httpx2
import pytest
import yaml

from tests.httpx_mock import CassetteReplay, HTTPXMock


def _cassette(
    tmp_path: Path, *, body: str | None = None, uri: str = "https://example.test/path?a=1&a=2"
) -> CassetteReplay:
    path = tmp_path / "cassette.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "interactions": [
                    {
                        "request": {"method": "POST", "uri": uri, "body": body},
                        "response": {
                            "status": {"code": 200},
                            "headers": {"Content-Type": ["application/json"]},
                            "body": {"string": '{"ok": true}'},
                        },
                    }
                ]
            }
        )
    )
    return CassetteReplay(path)


def test_native_fixture_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(method="POST", url="https://example.test", json={"ok": True})
    with httpx2.Client(trust_env=False) as client:
        assert client.post("https://example.test", json={"input": 1}).json() == {"ok": True}
    assert httpx_mock.get_requests()[0].content == b'{"input":1}'


async def test_native_fixture_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(method="GET", url="https://example.test", content=b"data: ok\n\n")
    async with httpx2.AsyncClient(trust_env=False) as client, client.stream("GET", "https://example.test") as response:
        assert [chunk async for chunk in response.aiter_bytes()] == [b"data: ok\n\n"]


def test_unexpected_request_never_reaches_network(httpx_mock: HTTPXMock) -> None:
    with httpx2.Client(trust_env=False) as client, pytest.raises(AssertionError, match="Unexpected HTTPX2 request"):
        client.get("https://unrecorded.invalid")


def test_unused_response_is_rejected() -> None:
    mock = HTTPXMock()
    mock.add_response(url="https://example.test")
    with pytest.raises(AssertionError, match="not requested"):
        mock.assert_all_responses_requested()


@pytest.mark.parametrize(
    ("method", "url", "body"),
    [
        ("GET", "https://example.test/path?a=1&a=2", b'{"a":1}'),
        ("POST", "http://example.test/path?a=1&a=2", b'{"a":1}'),
        ("POST", "https://other.test/path?a=1&a=2", b'{"a":1}'),
        ("POST", "https://example.test:444/path?a=1&a=2", b'{"a":1}'),
        ("POST", "https://example.test/other?a=1&a=2", b'{"a":1}'),
        ("POST", "https://example.test/path?a=1", b'{"a":1}'),
        ("POST", "https://example.test/path?a=1&a=3", b'{"a":1}'),
        ("POST", "https://example.test/path?a=1&a=2", b'{"a":2}'),
    ],
)
def test_cassette_rejects_mismatches(tmp_path: Path, method: str, url: str, body: bytes) -> None:
    replay = _cassette(tmp_path, body='{"a": 1}')
    with pytest.raises(AssertionError, match="Unexpected HTTPX2 request"):
        replay.handle_request(httpx2.Request(method, url, content=body))


def test_cassette_json_and_query_order_are_semantic(tmp_path: Path) -> None:
    replay = _cassette(tmp_path, body='{"a": 1, "b": 2}')
    response = replay.handle_request(httpx2.Request("POST", "https://example.test/path?a=2&a=1", json={"b": 2, "a": 1}))
    assert response.json() == {"ok": True}
    replay.assert_all_responses_requested()
    with pytest.raises(AssertionError, match="Unexpected HTTPX2 request"):
        replay.handle_request(httpx2.Request("POST", "https://example.test/path?a=2&a=1", json={"b": 2, "a": 1}))


def test_cassette_oauth_scope_redaction_keeps_other_fields_strict(tmp_path: Path) -> None:
    replay = _cassette(tmp_path, body="scope=REDACTED&other=1")
    with pytest.raises(AssertionError, match="Unexpected HTTPX2 request"):
        replay.handle_request(httpx2.Request("POST", "https://example.test/path?a=1&a=2", content=b"scope=ANY&other=2"))
    response = replay.handle_request(
        httpx2.Request("POST", "https://example.test/path?a=1&a=2", content=b"scope=ANY&other=1")
    )
    assert response.status_code == 200
    replay.assert_all_responses_requested()


def test_cassette_json_boolean_is_not_integer(tmp_path: Path) -> None:
    replay = _cassette(tmp_path, body='{"value": true}')
    with pytest.raises(AssertionError, match="Unexpected HTTPX2 request"):
        replay.handle_request(httpx2.Request("POST", "https://example.test/path?a=1&a=2", json={"value": 1}))


def test_native_fixture_supports_request_matchers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://example.test", method="POST", match_json={"value": True}, match_headers={"X-Test": "yes"}
    )
    with httpx2.Client(trust_env=False) as client:
        assert client.post("https://example.test", json={"value": True}, headers={"X-Test": "yes"}).status_code == 200
    assert httpx_mock.get_request(method="POST") is not None


def test_redundant_recorded_oauth_does_not_require_another_refresh(tmp_path: Path) -> None:
    replay = _cassette(tmp_path, body="scope=REDACTED", uri="https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
    replay._responses.append(replay._responses[0])
    replay.handle_request(
        httpx2.Request("POST", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth", content=b"scope=ANY")
    )
    replay.assert_all_responses_requested()


def test_unused_cassette_api_response_is_rejected(tmp_path: Path) -> None:
    replay = _cassette(tmp_path)
    with pytest.raises(AssertionError, match="not requested"):
        replay.assert_all_responses_requested()
