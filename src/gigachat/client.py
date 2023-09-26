import logging
import uuid
from base64 import b64decode
from functools import cached_property
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    Optional,
    TypeVar,
    Union,
)

import httpx

from gigachat.api import post_auth, post_chat, post_token, stream_chat
from gigachat.exceptions import AuthenticationError
from gigachat.models import (
    AccessToken,
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    Token,
)
from gigachat.settings import Settings

T = TypeVar("T")

logger = logging.getLogger(__name__)


def _get_kwargs(settings: Settings) -> Dict[str, Any]:
    """Настройки для подключения к API GIGACHAT"""
    return {
        "base_url": settings.base_url,
        "verify": settings.verify_ssl,
        "timeout": httpx.Timeout(settings.timeout),
    }


def _get_oauth_kwargs(settings: Settings) -> Dict[str, Any]:
    """Настройки для подключения к серверу авторизации OAuth 2.0"""
    return {
        "verify": settings.verify_ssl,
        "timeout": httpx.Timeout(settings.timeout),
    }


def _generate_id() -> str:
    return str(uuid.uuid4())


def _get_client_id(credentials: Optional[str]) -> Optional[str]:
    if credentials:
        client_id, _, _ = b64decode(credentials).decode().rpartition(":")
        return client_id
    else:
        return None


def _parse_chat(chat: Union[Chat, Dict[str, Any]], model: Optional[str]) -> Chat:
    payload = Chat.parse_obj(chat)
    if model:
        payload.model = model
    return payload


def _build_access_token(token: Token) -> AccessToken:
    return AccessToken(access_token=token.tok, expires_at=token.exp)


class _BaseClient:
    _access_token: Optional[AccessToken] = None

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        auth_url: Optional[str] = None,
        credentials: Optional[str] = None,
        scope: Optional[str] = None,
        access_token: Optional[str] = None,
        model: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[float] = None,
        verify_ssl: Optional[bool] = None,
        use_auth: Optional[bool] = None,
        verbose: Optional[bool] = None,
    ) -> None:
        config = {k: v for k, v in locals().items() if k != "self" and v is not None}
        self._settings = Settings(**config)
        if self._settings.access_token:
            self._access_token = AccessToken(access_token=self._settings.access_token, expires_at=0)

    @cached_property
    def client_id(self) -> Optional[str]:
        return _get_client_id(self._settings.credentials)

    @cached_property
    def session_id(self) -> str:
        return _generate_id()

    @property
    def headers(self) -> Dict[str, str]:
        headers = {
            "X-Session-ID": self.session_id,
            "X-Request-ID": _generate_id(),
        }
        if self.client_id:
            headers["X-Client-ID"] = self.client_id

        if token := self.token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    @property
    def token(self) -> Optional[str]:
        if self._settings.use_auth and self._access_token:
            return self._access_token.access_token
        else:
            return None

    @property
    def _use_auth(self) -> bool:
        return self._settings.use_auth

    def _check_validity_token(self) -> bool:
        """Проверить время завершения действия токена"""
        if self._access_token:
            # _check_validity_token
            return True
        return False

    def _reset_token(self) -> None:
        """Сбросить токен"""
        self._access_token = None


class GigaChatSyncClient(_BaseClient):
    """Синхронный клиент GigaChat"""

    @cached_property
    def _client(self) -> httpx.Client:
        return httpx.Client(**_get_kwargs(self._settings))

    @cached_property
    def _auth_client(self) -> httpx.Client:
        return httpx.Client(**_get_oauth_kwargs(self._settings))

    def close(self) -> None:
        self._client.close()
        self._auth_client.close()

    def __enter__(self) -> "GigaChatSyncClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _update_token(self) -> None:
        if self._settings.credentials:
            self._access_token = post_auth.sync(
                self._auth_client,
                self._settings.auth_url,
                self._settings.credentials,
                self._settings.scope,
            )
            logger.info("OAUTH UPDATE TOKEN")
        elif self._settings.user and self._settings.password:
            self._access_token = _build_access_token(
                post_token.sync(self._client, self._settings.user, self._settings.password)
            )
            logger.info("UPDATE TOKEN")

    def chat(self, payload: Union[Chat, Dict[str, Any]]) -> ChatCompletion:
        chat = _parse_chat(payload, model=self._settings.model)

        if self._use_auth:
            if self._check_validity_token():
                try:
                    return post_chat.sync(self._client, chat, self.headers)
                except AuthenticationError:
                    logger.warning("AUTHENTICATION ERROR")
                    self._reset_token()
            self._update_token()

        return post_chat.sync(self._client, chat, self.headers)

    def stream(self, payload: Union[Chat, Dict[str, Any]]) -> Iterator[ChatCompletionChunk]:
        chat = _parse_chat(payload, model=self._settings.model)

        if self._use_auth:
            if self._check_validity_token():
                try:
                    for chunk in stream_chat.sync(self._client, chat, self.headers):
                        yield chunk
                    return
                except AuthenticationError:
                    logger.warning("AUTHENTICATION ERROR")
                    self._reset_token()
            self._update_token()

        for chunk in stream_chat.sync(self._client, chat, self.headers):
            yield chunk


class GigaChatAsyncClient(_BaseClient):
    """Асинхронный клиент GigaChat"""

    @cached_property
    def _aclient(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(**_get_kwargs(self._settings))

    @cached_property
    def _auth_aclient(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(**_get_oauth_kwargs(self._settings))

    async def aclose(self) -> None:
        await self._aclient.aclose()
        await self._auth_aclient.aclose()

    async def __aenter__(self) -> "GigaChatAsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def _aupdate_token(self) -> None:
        if self._settings.credentials:
            self._access_token = await post_auth.asyncio(
                self._auth_aclient,
                self._settings.auth_url,
                self._settings.credentials,
                self._settings.scope,
            )
            logger.info("OAUTH UPDATE TOKEN")
        elif self._settings.user and self._settings.password:
            self._access_token = _build_access_token(
                await post_token.asyncio(self._aclient, self._settings.user, self._settings.password)
            )
            logger.info("UPDATE TOKEN")

    async def achat(self, payload: Union[Chat, Dict[str, Any]]) -> ChatCompletion:
        chat = _parse_chat(payload, model=self._settings.model)

        if self._use_auth:
            if self._check_validity_token():
                try:
                    return await post_chat.asyncio(self._aclient, chat, self.headers)
                except AuthenticationError:
                    logger.warning("AUTHENTICATION ERROR")
                    self._reset_token()
            await self._aupdate_token()

        return await post_chat.asyncio(self._aclient, chat, self.headers)

    async def astream(self, payload: Union[Chat, Dict[str, Any]]) -> AsyncIterator[ChatCompletionChunk]:
        chat = _parse_chat(payload, model=self._settings.model)

        if self._use_auth:
            if self._check_validity_token():
                try:
                    async for chunk in stream_chat.asyncio(self._aclient, chat, self.headers):
                        yield chunk
                    return
                except AuthenticationError:
                    logger.warning("AUTHENTICATION ERROR")
                    self._reset_token()
            await self._aupdate_token()

        async for chunk in stream_chat.asyncio(self._aclient, chat, self.headers):
            yield chunk
