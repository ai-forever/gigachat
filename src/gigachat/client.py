import asyncio
import logging
import ssl
import threading
import time
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import httpx
from typing_extensions import Self

from gigachat._types import FileTypes
from gigachat.api import auth, chat, embeddings, files, models, tools
from gigachat.assistants import AssistantsAsyncClient, AssistantsSyncClient
from gigachat.authentication import _awith_auth, _awith_auth_stream, _with_auth, _with_auth_stream
from gigachat.context import authorization_cvar
from gigachat.models.auth import AccessToken, Token
from gigachat.models.chat import (
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    Messages,
    MessagesRole,
)
from gigachat.models.embeddings import Embeddings
from gigachat.models.files import DeletedFile, Image, UploadedFile, UploadedFiles
from gigachat.models.models import Model, Models
from gigachat.models.tools import AICheckResult, Balance, OpenApiFunctions, TokensCount
from gigachat.retry import _awith_retry, _awith_retry_stream, _with_retry, _with_retry_stream
from gigachat.settings import Settings
from gigachat.threads import ThreadsAsyncClient, ThreadsSyncClient

T = TypeVar("T")

logger = logging.getLogger(__name__)

GIGACHAT_MODEL = "GigaChat"


def _get_kwargs(settings: Settings) -> Dict[str, Any]:
    """Return settings for connecting to the GigaChat API."""
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
    if settings.max_connections is not None:
        kwargs["limits"] = httpx.Limits(max_connections=settings.max_connections)
    return kwargs


def _get_auth_kwargs(settings: Settings) -> Dict[str, Any]:
    """Return settings for connecting to the OAuth 2.0 authorization server."""
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
        chat = Chat.model_validate(payload)
    using_assistant = chat.storage is not None and (chat.storage.assistant_id or chat.storage.thread_id)
    if not using_assistant and chat.model is None:
        chat.model = settings.model or GIGACHAT_MODEL
    if chat.profanity_check is None:
        chat.profanity_check = settings.profanity_check
    if chat.flags is None:
        chat.flags = settings.flags
    return chat


def _build_access_token(token: Token) -> AccessToken:
    return AccessToken(access_token=token.tok, expires_at=token.exp, x_headers=token.x_headers)


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
        ca_bundle_file: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        flags: Optional[List[str]] = None,
        max_connections: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_backoff_factor: Optional[float] = None,
        retry_on_status_codes: Optional[Tuple[int, ...]] = None,
        **_unknown_kwargs: Any,
    ) -> None:
        if _unknown_kwargs:
            logger.warning("GigaChat: unknown kwargs - %s", _unknown_kwargs)

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
            "ca_bundle_file": ca_bundle_file,
            "cert_file": cert_file,
            "key_file": key_file,
            "key_file_password": key_file_password,
            "ssl_context": ssl_context,
            "flags": flags,
            "max_connections": max_connections,
            "max_retries": max_retries,
            "retry_backoff_factor": retry_backoff_factor,
            "retry_on_status_codes": retry_on_status_codes,
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

    def _is_token_usable(self) -> bool:
        """Check if cached token is usable (exists and not expiring within buffer)."""
        if self._access_token and (
            self._access_token.expires_at == 0
            or self._access_token.expires_at > (time.time() * 1000) + self._settings.token_expiry_buffer_ms
        ):
            return True
        return False

    def _reset_token(self) -> None:
        """Reset the token."""
        self._access_token = None


class GigaChatSyncClient(_BaseClient):
    """
    Synchronous GigaChat client.

    Args:
        base_url: Address against which requests are executed.
        auth_url: Address for requesting OAuth 2.0 access token.
        credentials: Authorization data.
        scope: API version to which access is provided.
        access_token: JWE token.
        model: Name of the model to receive a response from.
        profanity_check: Censorship parameter.
        user: User name for authorization.
        password: Password for authorization.
        timeout: Timeout for requests.
        verify_ssl_certs: Check SSL certificates.
        ca_bundle_file: Path to CA bundle file.
        cert_file: Path to certificate file.
        key_file: Path to key file.
        key_file_password: Password for key file.
        ssl_context: SSL context.
        flags: Flags for GigaChat API.
        max_connections: Maximum number of simultaneous connections to the GigaChat API.
        max_retries: Maximum number of retries for transient errors.
        retry_backoff_factor: Backoff factor for retry delays.
        retry_on_status_codes: HTTP status codes that trigger a retry.
        **kwargs: Additional keyword arguments passed to parent classes.
    """

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
        ca_bundle_file: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        flags: Optional[List[str]] = None,
        max_connections: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_backoff_factor: Optional[float] = None,
        retry_on_status_codes: Optional[Tuple[int, ...]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            base_url=base_url,
            auth_url=auth_url,
            credentials=credentials,
            scope=scope,
            access_token=access_token,
            model=model,
            profanity_check=profanity_check,
            user=user,
            password=password,
            timeout=timeout,
            verify_ssl_certs=verify_ssl_certs,
            ca_bundle_file=ca_bundle_file,
            cert_file=cert_file,
            key_file=key_file,
            key_file_password=key_file_password,
            ssl_context=ssl_context,
            flags=flags,
            max_connections=max_connections,
            max_retries=max_retries,
            retry_backoff_factor=retry_backoff_factor,
            retry_on_status_codes=retry_on_status_codes,
            **kwargs,
        )
        self.assistants = AssistantsSyncClient(self)
        self.threads = ThreadsSyncClient(self)
        self._sync_token_lock = threading.RLock()
        self._client_instance: Optional[httpx.Client] = None
        self._auth_client_instance: Optional[httpx.Client] = None

    @property
    def _client(self) -> httpx.Client:
        if self._client_instance is None:
            with self._sync_token_lock:
                if self._client_instance is None:
                    self._client_instance = httpx.Client(**_get_kwargs(self._settings))
        return self._client_instance

    @property
    def _auth_client(self) -> httpx.Client:
        if self._auth_client_instance is None:
            with self._sync_token_lock:
                if self._auth_client_instance is None:
                    self._auth_client_instance = httpx.Client(**_get_auth_kwargs(self._settings))
        return self._auth_client_instance

    def close(self) -> None:
        if self._client_instance:
            self._client_instance.close()
        if self._auth_client_instance:
            self._auth_client_instance.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _update_token(self) -> None:
        if authorization_cvar.get() is not None:
            return

        with self._sync_token_lock:
            if self._is_token_usable():
                return

            if self._settings.credentials:
                self._access_token = auth.auth_sync(
                    self._auth_client,
                    url=self._settings.auth_url,
                    credentials=self._settings.credentials,
                    scope=self._settings.scope,
                )
                logger.debug("Token refreshed via OAuth")
            elif self._settings.user and self._settings.password:
                self._access_token = _build_access_token(
                    auth.token_sync(
                        self._client,
                        user=self._settings.user,
                        password=self._settings.password,
                    )
                )
                logger.debug("Token refreshed via password auth")

    def get_token(self) -> Optional[AccessToken]:
        """
        Return a valid access token, refreshing if necessary.

        Returns:
            Optional[AccessToken]: The access token if authentication is configured and successful.
                Returns None if:
                1. Authentication is managed via context variable (`authorization_cvar`).
                2. No authentication credentials are provided.
        """
        self._update_token()
        return self._access_token

    @_with_retry
    @_with_auth
    def tokens_count(self, input_: List[str], model: Optional[str] = None) -> List[TokensCount]:
        """Return the number of tokens in a string."""
        if not model:
            model = self._settings.model or GIGACHAT_MODEL
        return tools.tokens_count_sync(self._client, input_=input_, model=model, access_token=self.token)

    @_with_retry
    @_with_auth
    def embeddings(self, texts: List[str], model: str = "Embeddings") -> Embeddings:
        """Return embeddings."""
        return embeddings.embeddings_sync(self._client, access_token=self.token, input_=texts, model=model)

    @_with_retry
    @_with_auth
    def get_models(self) -> Models:
        """Return a list of available models."""
        return models.get_models_sync(self._client, access_token=self.token)

    @_with_retry
    @_with_auth
    def get_model(self, model: str) -> Model:
        """Return a description of a specific model."""
        return models.get_model_sync(self._client, model=model, access_token=self.token)

    @_with_retry
    @_with_auth
    def get_image(self, file_id: str) -> Image:
        """Return an image in base64 encoding."""
        return files.get_image_sync(self._client, file_id=file_id, access_token=self.token)

    @_with_retry
    @_with_auth
    def upload_file(
        self,
        file: FileTypes,
        purpose: Literal["general", "assistant"] = "general",
    ) -> UploadedFile:
        """Upload a file."""
        return files.upload_file_sync(self._client, file=file, purpose=purpose, access_token=self.token)

    @_with_retry
    @_with_auth
    def get_file(self, file: str) -> UploadedFile:
        """Return information about a file."""
        return files.get_file_sync(self._client, file=file, access_token=self.token)

    @_with_retry
    @_with_auth
    def get_files(self) -> UploadedFiles:
        """Return a list of uploaded files."""
        return files.get_files_sync(self._client, access_token=self.token)

    @_with_retry
    @_with_auth
    def delete_file(
        self,
        file: str,
    ) -> DeletedFile:
        """Delete a file."""
        return files.delete_file_sync(self._client, file=file, access_token=self.token)

    @_with_retry
    @_with_auth
    def chat(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion:
        """Return a model response based on the provided messages."""
        chat_data = _parse_chat(payload, self._settings)
        return chat.chat_sync(self._client, chat=chat_data, access_token=self.token)

    @_with_retry
    @_with_auth
    def get_balance(self) -> Balance:
        """
        Return the balance of available tokens.

        Only for prepaid clients, otherwise HTTP 403.
        """
        return tools.get_balance_sync(self._client, access_token=self.token)

    @_with_retry
    @_with_auth
    def openapi_function_convert(self, openapi_function: str) -> OpenApiFunctions:
        """Convert an OpenAPI function description to a GigaChat function."""
        return tools.functions_convert_sync(self._client, openapi_function=openapi_function, access_token=self.token)

    @_with_retry
    @_with_auth
    def check_ai(self, text: str, model: str) -> AICheckResult:
        """Check the provided text for content generated by AI models."""
        return tools.ai_check_sync(self._client, input_=text, model=model, access_token=self.token)

    @_with_retry_stream
    @_with_auth_stream
    def stream(self, payload: Union[Chat, Dict[str, Any], str]) -> Iterator[ChatCompletionChunk]:
        """Return a model response based on the provided messages (streaming)."""
        chat_data = _parse_chat(payload, self._settings)

        yield from chat.stream_sync(self._client, chat=chat_data, access_token=self.token)


class GigaChatAsyncClient(_BaseClient):
    """
    Asynchronous GigaChat client.

    Args:
        base_url: Address against which requests are executed.
        auth_url: Address for requesting OAuth 2.0 access token.
        credentials: Authorization data.
        scope: API version to which access is provided.
        access_token: JWE token.
        model: Name of the model to receive a response from.
        profanity_check: Censorship parameter.
        user: User name for authorization.
        password: Password for authorization.
        timeout: Timeout for requests.
        verify_ssl_certs: Check SSL certificates.
        ca_bundle_file: Path to CA bundle file.
        cert_file: Path to certificate file.
        key_file: Path to key file.
        key_file_password: Password for key file.
        ssl_context: SSL context.
        flags: Flags for GigaChat API.
        max_connections: Maximum number of simultaneous connections to the GigaChat API.
        max_retries: Maximum number of retries for transient errors.
        retry_backoff_factor: Backoff factor for retry delays.
        retry_on_status_codes: HTTP status codes that trigger a retry.
        **kwargs: Additional keyword arguments passed to parent classes.
    """

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
        ca_bundle_file: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        flags: Optional[List[str]] = None,
        max_connections: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_backoff_factor: Optional[float] = None,
        retry_on_status_codes: Optional[Tuple[int, ...]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            base_url=base_url,
            auth_url=auth_url,
            credentials=credentials,
            scope=scope,
            access_token=access_token,
            model=model,
            profanity_check=profanity_check,
            user=user,
            password=password,
            timeout=timeout,
            verify_ssl_certs=verify_ssl_certs,
            ca_bundle_file=ca_bundle_file,
            cert_file=cert_file,
            key_file=key_file,
            key_file_password=key_file_password,
            ssl_context=ssl_context,
            flags=flags,
            max_connections=max_connections,
            max_retries=max_retries,
            retry_backoff_factor=retry_backoff_factor,
            retry_on_status_codes=retry_on_status_codes,
            **kwargs,
        )
        self.a_assistants = AssistantsAsyncClient(self)
        self.a_threads = ThreadsAsyncClient(self)
        self._async_token_lock = asyncio.Lock()
        self._aclient_instance: Optional[httpx.AsyncClient] = None
        self._auth_aclient_instance: Optional[httpx.AsyncClient] = None

    @property
    def _aclient(self) -> httpx.AsyncClient:
        if self._aclient_instance is None:
            self._aclient_instance = httpx.AsyncClient(**_get_kwargs(self._settings))
        return self._aclient_instance

    @property
    def _auth_aclient(self) -> httpx.AsyncClient:
        if self._auth_aclient_instance is None:
            self._auth_aclient_instance = httpx.AsyncClient(**_get_auth_kwargs(self._settings))
        return self._auth_aclient_instance

    async def aclose(self) -> None:
        if self._aclient_instance:
            await self._aclient_instance.aclose()
        if self._auth_aclient_instance:
            await self._auth_aclient_instance.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def _aupdate_token(self) -> None:
        if authorization_cvar.get() is not None:
            return
        async with self._async_token_lock:
            if self._is_token_usable():
                return
            if self._settings.credentials:
                self._access_token = await auth.auth_async(
                    self._auth_aclient,
                    url=self._settings.auth_url,
                    credentials=self._settings.credentials,
                    scope=self._settings.scope,
                )
                logger.debug("Token refreshed via OAuth")
            elif self._settings.user and self._settings.password:
                self._access_token = _build_access_token(
                    await auth.token_async(
                        self._aclient,
                        user=self._settings.user,
                        password=self._settings.password,
                    )
                )
                logger.debug("Token refreshed via password auth")

    async def aget_token(self) -> Optional[AccessToken]:
        """
        Return a valid access token, refreshing if necessary.

        Returns:
            Optional[AccessToken]: The access token if authentication is configured and successful.
                Returns None if:
                1. Authentication is managed via context variable (`authorization_cvar`).
                2. No authentication credentials are provided.
        """
        await self._aupdate_token()
        return self._access_token

    @_awith_retry
    @_awith_auth
    async def atokens_count(self, input_: List[str], model: Optional[str] = None) -> List[TokensCount]:
        """Return the number of tokens in a string."""
        if not model:
            model = self._settings.model or GIGACHAT_MODEL

        return await tools.tokens_count_async(self._aclient, input_=input_, model=model, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aembeddings(self, texts: List[str], model: str = "Embeddings") -> Embeddings:
        """Return embeddings."""

        return await embeddings.embeddings_async(self._aclient, access_token=self.token, input_=texts, model=model)

    @_awith_retry
    @_awith_auth
    async def aget_models(self) -> Models:
        """Return a list of available models."""

        return await models.get_models_async(self._aclient, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aget_image(self, file_id: str) -> Image:
        """Return an image in base64 encoding."""

        return await files.get_image_async(self._aclient, file_id=file_id, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aget_model(self, model: str) -> Model:
        """Return a description of a specific model."""

        return await models.get_model_async(self._aclient, model=model, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def achat(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion:
        """Return a model response based on the provided messages."""
        chat_data = _parse_chat(payload, self._settings)

        return await chat.chat_async(self._aclient, chat=chat_data, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aupload_file(
        self,
        file: FileTypes,
        purpose: Literal["general", "assistant"] = "general",
    ) -> UploadedFile:
        """Upload a file."""

        return await files.upload_file_async(self._aclient, file=file, purpose=purpose, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aget_file(self, file: str) -> UploadedFile:
        """Return information about a file."""

        return await files.get_file_async(self._aclient, file=file, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aget_files(self) -> UploadedFiles:
        """Return a list of uploaded files."""

        return await files.get_files_async(self._aclient, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def adelete_file(
        self,
        file: str,
    ) -> DeletedFile:
        """Delete a file."""

        return await files.delete_file_async(self._aclient, file=file, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aget_balance(self) -> Balance:
        """
        Return the balance of available tokens.

        Only for prepaid clients, otherwise HTTP 403.
        """

        return await tools.get_balance_async(self._aclient, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aopenapi_function_convert(self, openapi_function: str) -> OpenApiFunctions:
        """Convert an OpenAPI function description to a GigaChat function."""

        return await tools.functions_convert_async(
            self._aclient, openapi_function=openapi_function, access_token=self.token
        )

    @_awith_retry
    @_awith_auth
    async def acheck_ai(self, text: str, model: str) -> AICheckResult:
        """Check the provided text for content generated by AI models."""

        return await tools.ai_check_async(self._aclient, input_=text, model=model, access_token=self.token)

    @_awith_retry_stream
    @_awith_auth_stream
    def astream(self, payload: Union[Chat, Dict[str, Any], str]) -> AsyncIterator[ChatCompletionChunk]:
        """Return a model response based on the provided messages (streaming)."""
        chat_data = _parse_chat(payload, self._settings)
        return chat.stream_async(self._aclient, chat=chat_data, access_token=self.token)


class GigaChat(GigaChatSyncClient, GigaChatAsyncClient):
    """
    GigaChat client.

    Args:
        base_url: Address against which requests are executed.
        auth_url: Address for requesting OAuth 2.0 access token.
        credentials: Authorization data.
        scope: API version to which access is provided.
        access_token: JWE token.
        model: Name of the model to receive a response from.
        profanity_check: Censorship parameter.
        user: User name for authorization.
        password: Password for authorization.
        timeout: Timeout for requests.
        verify_ssl_certs: Check SSL certificates.
        ca_bundle_file: Path to CA bundle file.
        cert_file: Path to certificate file.
        key_file: Path to key file.
        key_file_password: Password for key file.
        ssl_context: SSL context.
        flags: Flags for GigaChat API.
        max_connections: Maximum number of simultaneous connections to the GigaChat API.
        max_retries: Maximum number of retries for transient errors.
        retry_backoff_factor: Backoff factor for retry delays.
        retry_on_status_codes: HTTP status codes that trigger a retry.
        **kwargs: Additional keyword arguments passed to parent classes.
    """

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
        ca_bundle_file: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        flags: Optional[List[str]] = None,
        max_connections: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_backoff_factor: Optional[float] = None,
        retry_on_status_codes: Optional[Tuple[int, ...]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            base_url=base_url,
            auth_url=auth_url,
            credentials=credentials,
            scope=scope,
            access_token=access_token,
            model=model,
            profanity_check=profanity_check,
            user=user,
            password=password,
            timeout=timeout,
            verify_ssl_certs=verify_ssl_certs,
            ca_bundle_file=ca_bundle_file,
            cert_file=cert_file,
            key_file=key_file,
            key_file_password=key_file_password,
            ssl_context=ssl_context,
            flags=flags,
            max_connections=max_connections,
            max_retries=max_retries,
            retry_backoff_factor=retry_backoff_factor,
            retry_on_status_codes=retry_on_status_codes,
            **kwargs,
        )

    async def aclose(self) -> None:
        self.close()
        await super().aclose()
