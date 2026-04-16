import asyncio
import inspect
import json
import logging
import ssl
import threading
import time
import warnings
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_origin,
    overload,
)

import httpx
import pydantic
from pydantic import SecretStr
from typing_extensions import Self

from gigachat._types import FileContent, FileTypes
from gigachat.api import auth, batches, chat, chat_v2, embeddings, files, models, tools
from gigachat.assistants import AssistantsAsyncClient, AssistantsSyncClient
from gigachat.authentication import _awith_auth, _awith_auth_stream, _with_auth, _with_auth_stream
from gigachat.context import authorization_cvar
from gigachat.exceptions import (
    ContentFilterFinishReasonError,
    ContentParseError,
    ContentValidationError,
    LengthFinishReasonError,
)
from gigachat.models.auth import AccessToken, Token
from gigachat.models.batches import Batch, Batches
from gigachat.models.chat import (
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    Function,
    Messages,
    MessagesRole,
)
from gigachat.models.chat_v2 import (
    ChatCompletionV2,
    ChatCompletionV2Chunk,
    ChatV2,
    ChatV2ContentPart,
    ChatV2Message,
    ChatV2ModelOptions,
    ChatV2Storage,
)
from gigachat.models.embeddings import Embeddings
from gigachat.models.files import DeletedFile, File, UploadedFile, UploadedFiles
from gigachat.models.models import Model, Models
from gigachat.models.response_format import JsonSchemaResponseFormat
from gigachat.models.tools import (
    AICheckResult,
    Balance,
    FunctionValidationResult,
    OpenApiFunctions,
    TokensCount,
)
from gigachat.retry import _awith_retry, _awith_retry_stream, _with_retry, _with_retry_stream
from gigachat.settings import Settings
from gigachat.threads import ThreadsAsyncClient, ThreadsSyncClient

T = TypeVar("T")
_ModelT = TypeVar("_ModelT")
_AdaptedT = TypeVar("_AdaptedT")
ModelT = TypeVar("ModelT", bound=pydantic.BaseModel)

logger = logging.getLogger(__name__)

GIGACHAT_MODEL = "GigaChat"
SecretValue = Union[str, SecretStr]


def _unwrap_secret(value: Optional[SecretValue]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    return value


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
            _unwrap_secret(settings.key_file_password),
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


def _validate_response_format(payload: Union[Chat, Dict[str, Any], str]) -> None:
    """Reject bare Pydantic models in ``chat(response_format=...)``.

    ``chat_parse()`` is the source-of-truth helper for deriving JSON Schema from a
    Pydantic model in v1 chat requests.
    """
    if isinstance(payload, dict):
        response_format = payload.get("response_format")
    elif isinstance(payload, Chat):
        response_format = payload.response_format
    else:
        return

    if (
        response_format is not None
        and inspect.isclass(response_format)
        and issubclass(response_format, pydantic.BaseModel)
    ):
        raise TypeError(
            "You tried to pass a Pydantic model to `chat(response_format=...)`; "
            "use `client.chat_parse(payload, response_format=...)` instead"
        )


def _validate_response_format_v2(payload: Union[ChatV2, Dict[str, Any], str]) -> None:
    """Reject schema shorthands in direct v2 requests.

    v2 keeps the same response_format structure as v1, but nested under
    ``model_options.response_format``.
    """
    if isinstance(payload, dict):
        model_options = payload.get("model_options")
        response_format = model_options.get("response_format") if isinstance(model_options, dict) else None
    elif isinstance(payload, ChatV2):
        response_format = payload.model_options.response_format if payload.model_options is not None else None
    else:
        return

    if (
        response_format is not None
        and (
            (inspect.isclass(response_format) and issubclass(response_format, pydantic.BaseModel))
            or isinstance(response_format, pydantic.TypeAdapter)
            or get_origin(response_format) is not None
        )
    ):
        raise TypeError(
            "You tried to pass a model to `chat_v2(model_options.response_format=...)`; "
            "use `client.chat_parse_v2(payload, response_format=...)` instead"
        )


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


def _prepare_chat_for_parse(
    payload: Union[Chat, Dict[str, Any], str],
    settings: Settings,
    response_format: Type[pydantic.BaseModel],
    strict: bool,
) -> Chat:
    """Prepare a Chat object with response_format derived from *response_format*."""
    chat_data = _parse_chat(payload, settings)
    chat_data.response_format = JsonSchemaResponseFormat(schema=response_format, strict=strict)
    return chat_data


def _prepare_chat_v2_for_parse(
    payload: Union[ChatV2, Dict[str, Any], str],
    settings: Settings,
    response_format: Type[pydantic.BaseModel],
    strict: bool,
) -> ChatV2:
    """Prepare a ChatV2 object with response_format derived from *response_format*."""
    chat_data = _parse_chat_v2(payload, settings)
    if chat_data.model_options is None:
        chat_data.model_options = ChatV2ModelOptions()
    chat_data.model_options.response_format = JsonSchemaResponseFormat(schema=response_format, strict=strict)
    return chat_data


def _parse_chat_v2(payload: Union[ChatV2, Dict[str, Any], str], settings: Settings) -> ChatV2:
    if isinstance(payload, str):
        chat_data = ChatV2(messages=[ChatV2Message(role="user", content=[ChatV2ContentPart(text=payload)])])
    else:
        chat_data = ChatV2.model_validate(payload)

    storage_thread_id = chat_data.storage.thread_id if isinstance(chat_data.storage, ChatV2Storage) else None
    using_assistant = chat_data.assistant_id is not None or storage_thread_id is not None
    if not using_assistant and chat_data.model is None:
        chat_data.model = settings.model or GIGACHAT_MODEL
    if chat_data.flags is None:
        chat_data.flags = settings.flags
    return chat_data


def _get_response_model_adapter(response_model: Any) -> Optional[pydantic.TypeAdapter[Any]]:
    """Return a TypeAdapter for supported typing annotations and adapters."""
    if isinstance(response_model, pydantic.TypeAdapter):
        return response_model

    if inspect.isclass(response_model) and issubclass(response_model, pydantic.BaseModel):
        return None

    if get_origin(response_model) is not None:
        return pydantic.TypeAdapter(response_model)

    return None


def _parse_response_content(
    content: Any,
    completion: Union[ChatCompletion, ChatCompletionV2],
    response_model: Any,
) -> Any:
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ContentParseError(content, completion) from exc

    try:
        adapter = _get_response_model_adapter(response_model)
        if adapter is not None:
            return adapter.validate_python(data)
        return response_model.model_validate(data)
    except pydantic.ValidationError as exc:
        raise ContentValidationError(content, completion, exc) from exc


def _parse_completion(
    completion: ChatCompletion,
    response_format: Type[ModelT],
) -> ModelT:
    """Parse and validate message content from *completion* into *response_format*."""
    if not completion.choices:
        raise ValueError("Response has no choices")

    choice = completion.choices[0]

    if choice.finish_reason == "length":
        raise LengthFinishReasonError(completion)

    data = json.loads(choice.message.content)
    return response_format.model_validate(data)


@overload
def _parse_completion_v2(completion: ChatCompletionV2, response_model: Type[_ModelT]) -> _ModelT: ...


@overload
def _parse_completion_v2(
    completion: ChatCompletionV2,
    response_model: pydantic.TypeAdapter[_AdaptedT],
) -> _AdaptedT: ...


@overload
def _parse_completion_v2(
    completion: ChatCompletionV2,
    response_model: Any,
) -> Any: ...


def _parse_completion_v2(
    completion: ChatCompletionV2,
    response_model: Any,
) -> Any:
    """Parse and validate text content from a v2 completion into *response_model*."""
    if not completion.messages:
        raise ContentParseError("", completion)

    if completion.finish_reason == "length":
        raise LengthFinishReasonError(completion)
    if completion.finish_reason == "content_filter":
        raise ContentFilterFinishReasonError(completion)

    content = ""
    for message in completion.messages:
        text_parts = [part.text for part in message.content if part.text is not None]
        if text_parts:
            content = "".join(text_parts)
            break

    return _parse_response_content(content, completion, response_model)


def _build_access_token(token: Token) -> AccessToken:
    return AccessToken(access_token=token.tok, expires_at=token.exp, x_headers=token.x_headers)


class _BaseClient:
    _access_token: Optional[AccessToken] = None

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        auth_url: Optional[str] = None,
        credentials: Optional[SecretValue] = None,
        scope: Optional[str] = None,
        access_token: Optional[SecretValue] = None,
        model: Optional[str] = None,
        profanity_check: Optional[bool] = None,
        user: Optional[str] = None,
        password: Optional[SecretValue] = None,
        timeout: Optional[float] = None,
        verify_ssl_certs: Optional[bool] = None,
        ca_bundle_file: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[SecretValue] = None,
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
            self._access_token = AccessToken(
                access_token=self._settings.access_token,
                expires_at=0,
            )

    @property
    def token(self) -> Optional[str]:
        if self._access_token:
            return self._access_token.access_token.get_secret_value()
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
        credentials: Optional[SecretValue] = None,
        scope: Optional[str] = None,
        access_token: Optional[SecretValue] = None,
        model: Optional[str] = None,
        profanity_check: Optional[bool] = None,
        user: Optional[str] = None,
        password: Optional[SecretValue] = None,
        timeout: Optional[float] = None,
        verify_ssl_certs: Optional[bool] = None,
        ca_bundle_file: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[SecretValue] = None,
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
                credentials = self._settings.credentials.get_secret_value()
                self._access_token = auth.auth_sync(
                    self._auth_client,
                    url=self._settings.auth_url,
                    credentials=credentials,
                    scope=self._settings.scope,
                )
                logger.debug("Token refreshed via OAuth")
            elif self._settings.user and self._settings.password:
                password = self._settings.password.get_secret_value()
                self._access_token = _build_access_token(
                    auth.token_sync(
                        self._client,
                        user=self._settings.user,
                        password=password,
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
    def create_batch(self, file: FileContent, method: Literal["chat_completions", "embedder"]) -> Batch:
        """Create a batch task for asynchronous processing."""
        return batches.create_batch_sync(self._client, file=file, method=method, access_token=self.token)

    @_with_retry
    @_with_auth
    def get_batches(self, batch_id: Optional[str] = None) -> Batches:
        """Return batch tasks or a specific batch task."""
        return batches.get_batches_sync(self._client, batch_id=batch_id, access_token=self.token)

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
    def get_file_content(self, file_id: str) -> File:
        """Return file content in base64 encoding."""
        return files.get_file_content_sync(self._client, file_id=file_id, access_token=self.token)

    @_with_retry
    @_with_auth
    def get_image(self, file_id: str) -> File:
        """Use `get_file_content`; this alias is deprecated."""
        warnings.warn(
            "Method 'get_image' is deprecated, use 'get_file_content'",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_file_content(file_id=file_id)

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
        _validate_response_format(payload)
        chat_data = _parse_chat(payload, self._settings)
        return chat.chat_sync(self._client, chat=chat_data, access_token=self.token)

    @_with_retry
    @_with_auth
    def chat_v2(self, payload: Union[ChatV2, Dict[str, Any], str]) -> ChatCompletionV2:
        """Return a v2 model response based on the provided messages."""
        _validate_response_format_v2(payload)
        chat_data = _parse_chat_v2(payload, self._settings)
        return chat_v2.chat_v2_sync(
            self._client,
            chat=chat_data,
            base_url=self._settings.base_url,
            access_token=self.token,
        )

    def chat_parse(
        self,
        payload: Union[Chat, Dict[str, Any], str],
        *,
        response_format: Type[ModelT],
        strict: bool = True,
    ) -> Tuple[ChatCompletion, ModelT]:
        """Send a chat request and parse the response into *response_format*.

        .. note:: **Beta.** This feature may not work correctly with all model versions.
        """
        chat_data = _prepare_chat_for_parse(payload, self._settings, response_format, strict)
        completion = self.chat(chat_data)
        parsed = _parse_completion(completion, response_format)
        return completion, parsed

    @overload
    def chat_parse_v2(
        self,
        payload: Union[ChatV2, Dict[str, Any], str],
        *,
        response_format: Type[ModelT],
        strict: bool = True,
    ) -> Tuple[ChatCompletionV2, ModelT]: ...

    def chat_parse_v2(
        self,
        payload: Union[ChatV2, Dict[str, Any], str],
        *,
        response_format: Optional[Type[ModelT]] = None,
        response_model: Optional[Type[ModelT]] = None,
        strict: bool = True,
    ) -> Tuple[ChatCompletionV2, Any]:
        """Send a v2 chat request and parse the first text response into *response_format*."""
        if (response_format is None) == (response_model is None):
            raise TypeError("Provide exactly one of `response_format` or `response_model`")

        parse_model = response_format if response_format is not None else response_model
        assert parse_model is not None

        chat_data = _prepare_chat_v2_for_parse(payload, self._settings, parse_model, strict)
        completion = self.chat_v2(chat_data)
        parsed: Any = _parse_completion_v2(completion, parse_model)
        return completion, parsed

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
    def validate_function(self, function: Union[Function, Dict[str, Any]]) -> FunctionValidationResult:
        """Validate a GigaChat function definition."""
        return tools.function_validate_sync(self._client, function=function, access_token=self.token)

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

    @_with_retry_stream
    @_with_auth_stream
    def stream_v2(self, payload: Union[ChatV2, Dict[str, Any], str]) -> Iterator[ChatCompletionV2Chunk]:
        """Return a v2 model response based on the provided messages (streaming)."""
        chat_data = _parse_chat_v2(payload, self._settings)

        yield from chat_v2.stream_v2_sync(
            self._client,
            chat=chat_data,
            base_url=self._settings.base_url,
            access_token=self.token,
        )


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
        credentials: Optional[SecretValue] = None,
        scope: Optional[str] = None,
        access_token: Optional[SecretValue] = None,
        model: Optional[str] = None,
        profanity_check: Optional[bool] = None,
        user: Optional[str] = None,
        password: Optional[SecretValue] = None,
        timeout: Optional[float] = None,
        verify_ssl_certs: Optional[bool] = None,
        ca_bundle_file: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[SecretValue] = None,
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
                credentials = self._settings.credentials.get_secret_value()
                self._access_token = await auth.auth_async(
                    self._auth_aclient,
                    url=self._settings.auth_url,
                    credentials=credentials,
                    scope=self._settings.scope,
                )
                logger.debug("Token refreshed via OAuth")
            elif self._settings.user and self._settings.password:
                password = self._settings.password.get_secret_value()
                self._access_token = _build_access_token(
                    await auth.token_async(
                        self._aclient,
                        user=self._settings.user,
                        password=password,
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
    async def acreate_batch(self, file: FileContent, method: Literal["chat_completions", "embedder"]) -> Batch:
        """Create a batch task for asynchronous processing."""
        return await batches.create_batch_async(self._aclient, file=file, method=method, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aget_batches(self, batch_id: Optional[str] = None) -> Batches:
        """Return batch tasks or a specific batch task."""
        return await batches.get_batches_async(self._aclient, batch_id=batch_id, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aget_models(self) -> Models:
        """Return a list of available models."""

        return await models.get_models_async(self._aclient, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aget_file_content(self, file_id: str) -> File:
        """Return file content in base64 encoding."""
        return await files.get_file_content_async(self._aclient, file_id=file_id, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def aget_image(self, file_id: str) -> File:
        """Use `aget_file_content`; this alias is deprecated."""
        warnings.warn(
            "Method 'aget_image' is deprecated, use 'aget_file_content'",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.aget_file_content(file_id=file_id)

    @_awith_retry
    @_awith_auth
    async def aget_model(self, model: str) -> Model:
        """Return a description of a specific model."""

        return await models.get_model_async(self._aclient, model=model, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def achat(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion:
        """Return a model response based on the provided messages."""
        _validate_response_format(payload)
        chat_data = _parse_chat(payload, self._settings)

        return await chat.chat_async(self._aclient, chat=chat_data, access_token=self.token)

    @_awith_retry
    @_awith_auth
    async def achat_v2(self, payload: Union[ChatV2, Dict[str, Any], str]) -> ChatCompletionV2:
        """Return an async v2 model response based on the provided messages."""
        _validate_response_format_v2(payload)
        chat_data = _parse_chat_v2(payload, self._settings)

        return await chat_v2.chat_v2_async(
            self._aclient,
            chat=chat_data,
            base_url=self._settings.base_url,
            access_token=self.token,
        )

    async def achat_parse(
        self,
        payload: Union[Chat, Dict[str, Any], str],
        *,
        response_format: Type[ModelT],
        strict: bool = True,
    ) -> Tuple[ChatCompletion, ModelT]:
        """Send a chat request and parse the response into *response_format*.

        Async version of :meth:`GigaChatSyncClient.chat_parse`.
        """
        chat_data = _prepare_chat_for_parse(payload, self._settings, response_format, strict)
        completion = await self.achat(chat_data)
        parsed = _parse_completion(completion, response_format)
        return completion, parsed

    @overload
    async def achat_parse_v2(
        self,
        payload: Union[ChatV2, Dict[str, Any], str],
        *,
        response_format: Type[ModelT],
        strict: bool = True,
    ) -> Tuple[ChatCompletionV2, ModelT]: ...

    async def achat_parse_v2(
        self,
        payload: Union[ChatV2, Dict[str, Any], str],
        *,
        response_format: Optional[Type[ModelT]] = None,
        response_model: Optional[Type[ModelT]] = None,
        strict: bool = True,
    ) -> Tuple[ChatCompletionV2, Any]:
        """Send an async v2 chat request and parse the first text response into *response_format*."""
        if (response_format is None) == (response_model is None):
            raise TypeError("Provide exactly one of `response_format` or `response_model`")

        parse_model = response_format if response_format is not None else response_model
        assert parse_model is not None

        chat_data = _prepare_chat_v2_for_parse(payload, self._settings, parse_model, strict)
        completion = await self.achat_v2(chat_data)
        parsed: Any = _parse_completion_v2(completion, parse_model)
        return completion, parsed

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
    async def avalidate_function(self, function: Union[Function, Dict[str, Any]]) -> FunctionValidationResult:
        """Validate a GigaChat function definition."""
        return await tools.function_validate_async(self._aclient, function=function, access_token=self.token)

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

    @_awith_retry_stream
    @_awith_auth_stream
    def astream_v2(self, payload: Union[ChatV2, Dict[str, Any], str]) -> AsyncIterator[ChatCompletionV2Chunk]:
        """Return a v2 model response based on the provided messages (streaming)."""
        chat_data = _parse_chat_v2(payload, self._settings)
        return chat_v2.stream_v2_async(
            self._aclient,
            chat=chat_data,
            base_url=self._settings.base_url,
            access_token=self.token,
        )


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
        credentials: Optional[SecretValue] = None,
        scope: Optional[str] = None,
        access_token: Optional[SecretValue] = None,
        model: Optional[str] = None,
        profanity_check: Optional[bool] = None,
        user: Optional[str] = None,
        password: Optional[SecretValue] = None,
        timeout: Optional[float] = None,
        verify_ssl_certs: Optional[bool] = None,
        ca_bundle_file: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        key_file_password: Optional[SecretValue] = None,
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
