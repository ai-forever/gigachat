import warnings
from typing import Mapping

from gigachat.api.realtime import AsyncRealtimeConnectionManager, RealtimeConnectionManager
from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.resources.realtime import AsyncRealtimeResource, RealtimeResource
from gigachat.types.realtime import RealtimeSettingsParam


def _settings() -> RealtimeSettingsParam:
    return {"voice_call_id": "call-id"}


async def test_a_realtime_resource_is_cached_property() -> None:
    client = GigaChatAsyncClient()

    assert "a_realtime" not in client.__dict__

    resource = client.a_realtime

    assert resource is client.a_realtime
    assert isinstance(resource, AsyncRealtimeResource)


def test_realtime_resource_is_cached_property() -> None:
    client = GigaChatSyncClient()

    assert "realtime" not in client.__dict__

    resource = client.realtime

    assert resource is client.realtime
    assert isinstance(resource, RealtimeResource)


async def test_async_realtime_connect_returns_manager() -> None:
    client = GigaChatAsyncClient(realtime_url="wss://settings.test/realtime")
    headers: Mapping[str, str] = {"X-Test": "1"}
    options = {"ping_interval": 10}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        manager = client.a_realtime.connect(
            settings=_settings(),
            url="wss://argument.test/realtime",
            extra_headers=headers,
            websocket_connection_options=options,
            max_frame_size=1024,
            validate_audio_chunks=False,
        )

    assert isinstance(manager, AsyncRealtimeConnectionManager)
    assert manager._client is client
    assert manager._settings == {"voice_call_id": "call-id"}
    assert manager._url == "wss://argument.test/realtime"
    assert manager._extra_headers is headers
    assert manager._websocket_connection_options is options
    assert manager._max_frame_size == 1024
    assert manager._validate_audio_chunks is False
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]


def test_realtime_connect_returns_manager() -> None:
    client = GigaChatSyncClient(realtime_url="wss://settings.test/realtime")
    headers: Mapping[str, str] = {"X-Test": "1"}
    options = {"ping_interval": 10}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        manager = client.realtime.connect(
            settings=_settings(),
            url="wss://argument.test/realtime",
            extra_headers=headers,
            websocket_connection_options=options,
            max_frame_size=1024,
            validate_audio_chunks=False,
        )

    assert isinstance(manager, RealtimeConnectionManager)
    assert manager._client is client
    assert manager._settings == {"voice_call_id": "call-id"}
    assert manager._url == "wss://argument.test/realtime"
    assert manager._extra_headers is headers
    assert manager._websocket_connection_options is options
    assert manager._max_frame_size == 1024
    assert manager._validate_audio_chunks is False
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]
