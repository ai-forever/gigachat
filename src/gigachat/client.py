import logging
import ssl
from functools import cached_property
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    TypeVar,
    Union,
    cast,
)

import httpx

from gigachat._types import FileTypes
from gigachat.api import (
    get_balance,
    get_image,
    get_model,
    get_models,
    post_auth,
    post_chat,
    post_embeddings,
    post_files,
    post_functions_convert,
    post_token,
    post_tokens_count,
    stream_chat,
)
from gigachat.assistants import AssistantsAsyncClient, AssistantsSyncClient
from gigachat.context import authorization_cvar
from gigachat.exceptions import AuthenticationError
from gigachat.models import (
    AccessToken,
    Balance,
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    Embeddings,
    Image,
    Messages,
    MessagesRole,
    Model,
    Models,
    OpenApiFunctions,
    Token,
    TokensCount,
    UploadedFile,
)
from gigachat.settings import Settings
from gigachat.threads import ThreadsAsyncClient, ThreadsSyncClient

T = TypeVar("T")

_logger = logging.getLogger(__name__)

GIGACHAT_MODEL = "GigaChat"


def _get_kwargs(settings: Settings) -> Dict[str, Any]:
    """Настройки для подключения к API GIGACHAT"""
    kwargs = {
        "base_url": settings.base_url,
        "verify": settings.verify_ssl_certs,
        "timeout": httpx.Timeout(settings.timeout),
    }
    if settings.ssl_context:
        kwargs["verify"] = settings.ssl_context
    if settings.ca_bundle_file:
        kwargs["verify"] = settings.ca_bundle_file
    if settings.cert_file:
        kwargs["cert"] = (
            settings.cert_file,
            settings.key_file,
            settings.key_file_password,
        )
    return kwargs


def _get_auth_kwargs(settings: Settings) -> Dict[str, Any]:
    """Настройки для подключения к серверу авторизации OAuth 2.0"""
    kwargs = {
        "verify": settings.verify_ssl_certs,
        "timeout": httpx.Timeout(settings.timeout),
    }
    if settings.ssl_context:
        kwargs["verify"] = settings.ssl_context
    if settings.ca_bundle_file:
        kwargs["verify"] = settings.ca_bundle_file
    return kwargs


def _parse_chat(payload: Union[Chat, Dict[str, Any], str], settings: Settings) -> Chat:
    if isinstance(payload, str):
        chat = Chat(messages=[Messages(role=MessagesRole.USER, content=payload)])
    else:
        chat = Chat.parse_obj(payload)
    if chat.model is None:
        chat.model = settings.model or GIGACHAT_MODEL
    if chat.profanity_check is None:
        chat.profanity_check = settings.profanity_check
    if chat.flags is None:
        chat.flags = settings.flags
    return chat


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
        profanity_check: Optional[bool] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[float] = None,
        verify_ssl_certs: Optional[bool] = None,
        verbose: Optional[bool] = None,
        ca_bundle_file: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        flags: Optional[List[str]] = None,
        **_unknown_kwargs: Any,
    ) -> None:
        if _unknown_kwargs:
            _logger.warning("GigaChat: unknown kwargs - %s", _unknown_kwargs)

        kwargs: Dict[str, Any] = {
            "base_url": base_url,
            "auth_url": auth_url,
            "credentials": credentials,
            "scope": scope,
            "access_token": access_token,
            "model": model,
            "profanity_check": profanity_check,
            "user": user,
            "password": password,
            "timeout": timeout,
            "verify_ssl_certs": verify_ssl_certs,
            "verbose": verbose,
            "ca_bundle_file": ca_bundle_file,
            "cert_file": cert_file,
            "key_file": key_file,
            "key_file_password": key_file_password,
            "ssl_context": ssl_context,
            "flags": flags,
        }
        config = {k: v for k, v in kwargs.items() if v is not None}
        self._settings = Settings(**config)
        if self._settings.access_token:
            self._access_token = AccessToken(access_token=self._settings.access_token, expires_at=0)

    @property
    def token(self) -> Optional[str]:
        if self._access_token:
            return self._access_token.access_token
        else:
            return None

    @property
    def _use_auth(self) -> bool:
        return bool(self._settings.credentials or (self._settings.user and self._settings.password))

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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.assistants = AssistantsSyncClient(self)
        self.threads = ThreadsSyncClient(self)

    @cached_property
    def _client(self) -> httpx.Client:
        return httpx.Client(**_get_kwargs(self._settings))

    @cached_property
    def _auth_client(self) -> httpx.Client:
        return httpx.Client(**_get_auth_kwargs(self._settings))

    def close(self) -> None:
        self._client.close()
        self._auth_client.close()

    def __enter__(self) -> "GigaChatSyncClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _update_token(self) -> None:
        if authorization_cvar.get() is not None:
            return
        if self._settings.credentials:
            self._access_token = post_auth.sync(
                self._auth_client,
                url=self._settings.auth_url,
                credentials=self._settings.credentials,
                scope=self._settings.scope,
            )
            _logger.debug("OAUTH UPDATE TOKEN")
        elif self._settings.user and self._settings.password:
            self._access_token = _build_access_token(
                post_token.sync(
                    self._client,
                    user=self._settings.user,
                    password=self._settings.password,
                )
            )
            _logger.debug("UPDATE TOKEN")

    def get_token(self) -> AccessToken:
        self._update_token()
        return cast(AccessToken, self._access_token)

    def _decorator(self, call: Callable[..., T]) -> T:
        if self._use_auth:
            if self._check_validity_token():
                try:
                    return call()
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    self._reset_token()
            self._update_token()
        return call()

    def tokens_count(self, input_: List[str], model: Optional[str] = None) -> List[TokensCount]:
        """Возвращает объект с информацией о количестве токенов"""
        if not model:
            model = self._settings.model or GIGACHAT_MODEL
        return self._decorator(
            lambda: post_tokens_count.sync(self._client, input_=input_, model=model, access_token=self.token)
        )

    def embeddings(self, texts: List[str], model: str = "Embeddings") -> Embeddings:
        """Возвращает эмбеддинги"""
        return self._decorator(
            lambda: post_embeddings.sync(self._client, access_token=self.token, input_=texts, model=model)
        )

    def get_models(self) -> Models:
        """Возвращает массив объектов с данными доступных моделей"""
        return self._decorator(lambda: get_models.sync(self._client, access_token=self.token))

    def get_model(self, model: str) -> Model:
        """Возвращает объект с описанием указанной модели"""
        return self._decorator(lambda: get_model.sync(self._client, model=model, access_token=self.token))

    def get_image(self, file_id: str) -> Image:
        """Возвращает изображение в кодировке base64"""
        return self._decorator(lambda: get_image.sync(self._client, file_id=file_id, access_token=self.token))

    def upload_file(
        self,
        file: FileTypes,
        purpose: Literal["general", "assistant"] = "general",
    ) -> UploadedFile:
        """Загружает файл"""
        return self._decorator(
            lambda: post_files.sync(self._client, file=file, purpose=purpose, access_token=self.token)
        )

    def chat(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion:
        """Возвращает ответ модели с учетом переданных сообщений"""
        chat = _parse_chat(payload, self._settings)
        return self._decorator(lambda: post_chat.sync(self._client, chat=chat, access_token=self.token))

    def get_balance(self) -> Balance:
        """Метод для получения баланса доступных для использования токенов.
        Только для клиентов с предоплатой иначе http 403"""
        return self._decorator(lambda: get_balance.sync(self._client, access_token=self.token))

    def openapi_function_convert(self, openapi_function: str) -> OpenApiFunctions:
        """Конвертация описание функции в формате OpenAPI в gigachat функцию"""
        return self._decorator(
            lambda: post_functions_convert.sync(
                self._client, openapi_function=openapi_function, access_token=self.token
            )
        )

    def stream(self, payload: Union[Chat, Dict[str, Any], str]) -> Iterator[ChatCompletionChunk]:
        """Возвращает ответ модели с учетом переданных сообщений"""
        chat = _parse_chat(payload, self._settings)

        if self._use_auth:
            if self._check_validity_token():
                try:
                    for chunk in stream_chat.sync(self._client, chat=chat, access_token=self.token):
                        yield chunk
                    return
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    self._reset_token()
            self._update_token()

        for chunk in stream_chat.sync(self._client, chat=chat, access_token=self.token):
            yield chunk


class GigaChatAsyncClient(_BaseClient):
    """Асинхронный клиент GigaChat"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.a_assistants = AssistantsAsyncClient(self)
        self.a_threads = ThreadsAsyncClient(self)

    @cached_property
    def _aclient(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(**_get_kwargs(self._settings))

    @cached_property
    def _auth_aclient(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(**_get_auth_kwargs(self._settings))

    async def aclose(self) -> None:
        await self._aclient.aclose()
        await self._auth_aclient.aclose()

    async def __aenter__(self) -> "GigaChatAsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def _aupdate_token(self) -> None:
        if authorization_cvar.get() is not None:
            return
        if self._settings.credentials:
            self._access_token = await post_auth.asyncio(
                self._auth_aclient,
                url=self._settings.auth_url,
                credentials=self._settings.credentials,
                scope=self._settings.scope,
            )
            _logger.debug("OAUTH UPDATE TOKEN")
        elif self._settings.user and self._settings.password:
            self._access_token = _build_access_token(
                await post_token.asyncio(
                    self._aclient,
                    user=self._settings.user,
                    password=self._settings.password,
                )
            )
            _logger.debug("UPDATE TOKEN")

    async def aget_token(self) -> AccessToken:
        await self._aupdate_token()
        return cast(AccessToken, self._access_token)

    async def _adecorator(self, acall: Callable[..., Awaitable[T]]) -> T:
        if self._use_auth:
            if self._check_validity_token():
                try:
                    return await acall()
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    self._reset_token()
            await self._aupdate_token()
        return await acall()

    async def atokens_count(self, input_: List[str], model: Optional[str] = None) -> List[TokensCount]:
        """Возвращает объект с информацией о количестве токенов"""
        if not model:
            model = self._settings.model or GIGACHAT_MODEL

        async def _acall() -> List[TokensCount]:
            return await post_tokens_count.asyncio(self._aclient, input_=input_, model=model, access_token=self.token)

        return await self._adecorator(_acall)

    async def aembeddings(self, texts: List[str], model: str = "Embeddings") -> Embeddings:
        """Возвращает эмбеддинги"""

        async def _acall() -> Embeddings:
            return await post_embeddings.asyncio(self._aclient, access_token=self.token, input_=texts, model=model)

        return await self._adecorator(_acall)

    async def aget_models(self) -> Models:
        """Возвращает массив объектов с данными доступных моделей"""

        async def _acall() -> Models:
            return await get_models.asyncio(self._aclient, access_token=self.token)

        return await self._adecorator(_acall)

    async def aget_image(self, file_id: str) -> Image:
        """Возвращает изображение в кодировке base64"""

        async def _acall() -> Image:
            return await get_image.asyncio(self._aclient, file_id=file_id, access_token=self.token)

        return await self._adecorator(_acall)

    async def aget_model(self, model: str) -> Model:
        """Возвращает объект с описанием указанной модели"""

        async def _acall() -> Model:
            return await get_model.asyncio(self._aclient, model=model, access_token=self.token)

        return await self._adecorator(_acall)

    async def achat(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion:
        """Возвращает ответ модели с учетом переданных сообщений"""
        chat = _parse_chat(payload, self._settings)

        async def _acall() -> ChatCompletion:
            return await post_chat.asyncio(self._aclient, chat=chat, access_token=self.token)

        return await self._adecorator(_acall)

    async def aupload_file(
        self,
        file: FileTypes,
        purpose: Literal["general", "assistant"] = "general",
    ) -> UploadedFile:
        """Загружает файл"""

        async def _acall() -> UploadedFile:
            return await post_files.asyncio(self._aclient, file=file, purpose=purpose, access_token=self.token)

        return await self._adecorator(_acall)

    async def aget_balance(self) -> Balance:
        """Метод для получения баланса доступных для использования токенов.
        Только для клиентов с предоплатой иначе http 403"""

        async def _acall() -> Balance:
            return await get_balance.asyncio(self._aclient, access_token=self.token)

        return await self._adecorator(_acall)

    async def aopenapi_function_convert(self, openapi_function: str) -> OpenApiFunctions:
        """Конвертация описание функции в формате OpenAPI в gigachat функцию"""

        async def _acall() -> OpenApiFunctions:
            return await post_functions_convert.asyncio(
                self._aclient, openapi_function=openapi_function, access_token=self.token
            )

        return await self._adecorator(_acall)

    async def astream(self, payload: Union[Chat, Dict[str, Any], str]) -> AsyncIterator[ChatCompletionChunk]:
        """Возвращает ответ модели с учетом переданных сообщений"""
        chat = _parse_chat(payload, self._settings)

        if self._use_auth:
            if self._check_validity_token():
                try:
                    async for chunk in stream_chat.asyncio(self._aclient, chat=chat, access_token=self.token):
                        yield chunk
                    return
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    self._reset_token()
            await self._aupdate_token()

        async for chunk in stream_chat.asyncio(self._aclient, chat=chat, access_token=self.token):
            yield chunk
