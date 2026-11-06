import logging
from collections.abc import AsyncIterable, AsyncIterator, Iterable, Iterator
from functools import cached_property
from typing import (
    Any,
    Literal,
    TypeVar,
    cast,
)

import httpx2 as httpx
import pydantic
from typing_extensions import Self

from gigachat import _serialization
from gigachat._base_client import _BaseClient
from gigachat._execution import request_scope
from gigachat._files import AsyncFilesMixin, SyncFilesMixin
from gigachat._http_client import DefaultAioHttpClient, DefaultAsyncHttpxClient, DefaultHttpxClient, http_client_kwargs
from gigachat._request_options import RequestOptions
from gigachat._types import FileTypes
from gigachat.api import auth, batches, chat, chat_completions, embeddings, files, models, tools
from gigachat.assistants import AssistantsAsyncClient, AssistantsSyncClient
from gigachat.context import authorization_cvar
from gigachat.models.auth import AccessToken
from gigachat.models.batches import Batch, Batches
from gigachat.models.chat import (
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
)
from gigachat.models.chat_completions import (
    ChatCompletionChunk as PrimaryChatCompletionChunk,
)
from gigachat.models.chat_completions import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from gigachat.models.embeddings import Embeddings
from gigachat.models.files import DeletedFile, Image, UploadedFile, UploadedFiles
from gigachat.models.models import Model, Models
from gigachat.models.tools import (
    AICheckResult,
    Balance,
    FunctionValidationResult,
    GeneratedContent,
    OpenApiFunctions,
    RankedFunctions,
    RerankResponse,
    TokensCount,
)
from gigachat.resources import AsyncChatNamespace, ChatNamespace
from gigachat.settings import Settings
from gigachat.threads import ThreadsAsyncClient, ThreadsSyncClient

ModelT = TypeVar("ModelT", bound=pydantic.BaseModel)

logger = logging.getLogger(__name__)


def _get_kwargs(settings: Settings) -> dict[str, Any]:
    kwargs = http_client_kwargs(settings, backend="httpx2")
    kwargs["base_url"] = settings.base_url
    if settings.session_id is not None:
        kwargs["headers"] = {"X-Session-ID": settings.session_id}
    return kwargs


def _get_auth_kwargs(settings: Settings) -> dict[str, Any]:
    return http_client_kwargs(settings, for_auth=True, backend="httpx2")


class GigaChatSyncClient(SyncFilesMixin, _BaseClient):
    """Synchronous GigaChat client."""

    @cached_property
    def chat(self) -> ChatNamespace:
        """Return the chat namespace with primary chat methods."""
        return ChatNamespace(self)

    @cached_property
    def assistants(self) -> AssistantsSyncClient:
        """Return the assistants resource."""
        return AssistantsSyncClient(self)

    @cached_property
    def threads(self) -> ThreadsSyncClient:
        """Return the threads resource."""
        return ThreadsSyncClient(self)

    @property
    def _client(self) -> httpx.Client:
        self._ensure_open("sync")
        if self._owner is not self:
            return cast(GigaChatSyncClient, self._owner)._client
        if self._client_instance is None:
            with self._lifecycle_lock:
                self._ensure_open("sync")
                if self._client_instance is None:
                    self._client_instance = DefaultHttpxClient(**_get_kwargs(self._settings))
        return self._client_instance

    @property
    def _auth_client(self) -> httpx.Client:
        self._ensure_open("sync")
        if self._owner is not self:
            return cast(GigaChatSyncClient, self._owner)._auth_client
        if self._auth_client_instance is None:
            with self._lifecycle_lock:
                self._ensure_open("sync")
                if self._auth_client_instance is None:
                    self._auth_client_instance = DefaultHttpxClient(**_get_auth_kwargs(self._settings))
        return self._auth_client_instance

    def close(self) -> None:
        if self._owner is not self:
            self._view_closed = True
            return
        with self._lifecycle_lock:
            self._sync_closed = True
            self._closed = self._closed or not hasattr(type(self), "_aclient")
            if self._client_instance and self._injected_http is None:
                self._client_instance.close()
            if self._auth_client_instance and self._injected_auth_http is None:
                self._auth_client_instance.close()

    def __enter__(self) -> Self:
        self._ensure_open("sync")
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _update_token(self) -> None:
        self._ensure_open("sync")
        if self._owner is not self:
            return cast(GigaChatSyncClient, self._owner)._update_token()
        if authorization_cvar.get() is not None:
            return

        with self._sync_token_lock:
            if self._is_token_usable():
                return

            if self._settings.credentials:
                self._set_token(
                    auth.auth_sync(
                        self._auth_client,
                        url=self._settings.auth_url,
                        credentials=self._settings.credentials,
                        scope=self._settings.scope,
                    )
                )
                logger.debug("Token refreshed via OAuth")
            elif self._settings.user and self._settings.password:
                self._set_token(
                    _serialization._build_access_token(
                        auth.token_sync(
                            self._client,
                            url=self._settings.base_url.rstrip("/") + "/token",
                            user=self._settings.user,
                            password=self._settings.password,
                        )
                    )
                )
                logger.debug("Token refreshed via password auth")

    def get_token(self) -> AccessToken | None:
        """
        Return a valid access token, refreshing if necessary.

        Returns:
            Optional[AccessToken]: The access token if authentication is configured and successful.
                Returns None if:
                1. Authentication is managed via context variable (`authorization_cvar`).
                2. No authentication credentials are provided.
        """
        self._update_token()
        return self._owner._access_token

    @request_scope
    def tokens_count(
        self, input_: str | list[str], model: str | None = None, *, request_options: RequestOptions | None = None
    ) -> list[TokensCount]:
        """Return the number of tokens in a string."""
        model = _serialization._resolve_model(model, self._settings)
        return tools.tokens_count_sync(self._client, input_=input_, model=model, access_token=self.token)

    @request_scope
    def embeddings(
        self,
        texts: str | list[str],
        model: str = "Embeddings",
        *,
        encoding_format: str | None = None,
        truncate: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Embeddings:
        """Return embeddings."""
        return embeddings.embeddings_sync(
            self._client,
            access_token=self.token,
            input_=texts,
            model=model,
            encoding_format=encoding_format,
            truncate=truncate,
        )

    @request_scope
    def get_models(self, *, request_options: RequestOptions | None = None) -> Models:
        """Return a list of available models."""
        return models.get_models_sync(self._client, access_token=self.token)

    @request_scope
    def get_model(self, model: str, *, request_options: RequestOptions | None = None) -> Model:
        """Return a description of a specific model."""
        return models.get_model_sync(self._client, model=model, access_token=self.token)

    @request_scope
    def get_image(self, file_id: str, *, request_options: RequestOptions | None = None) -> Image:
        """Return an image in base64 encoding."""
        return files.get_image_sync(self._client, file_id=file_id, access_token=self.token)

    @request_scope
    def upload_file(
        self,
        file: FileTypes,
        purpose: Literal["general", "assistant"] = "general",
        *,
        request_options: RequestOptions | None = None,
    ) -> UploadedFile:
        """Upload a file."""
        return files.upload_file_sync(self._client, file=file, purpose=purpose, access_token=self.token)

    @request_scope
    def get_file(self, file: str, *, request_options: RequestOptions | None = None) -> UploadedFile:
        """Return information about a file."""
        return files.get_file_sync(self._client, file=file, access_token=self.token)

    @request_scope
    def get_files(self, *, request_options: RequestOptions | None = None) -> UploadedFiles:
        """Return a list of uploaded files."""
        return files.get_files_sync(self._client, access_token=self.token)

    @request_scope
    def delete_file(self, file: str, *, request_options: RequestOptions | None = None) -> DeletedFile:
        """Delete a file."""
        return files.delete_file_sync(self._client, file=file, access_token=self.token)

    @request_scope
    def _chat_create(
        self, payload: ChatCompletionRequest | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> ChatCompletionResponse:
        """Return a primary chat completion based on the provided messages."""
        chat_data = _serialization._parse_chat_completion(payload, self._settings)
        return chat_completions.chat_sync(self._client, chat=chat_data, access_token=self.token)

    @request_scope
    def _chat_stream(
        self, payload: ChatCompletionRequest | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> Iterator[PrimaryChatCompletionChunk]:
        """Return a primary streaming chat completion based on the provided messages."""
        chat_data = _serialization._parse_chat_completion(payload, self._settings)
        yield from chat_completions.stream_sync(self._client, chat=chat_data, access_token=self.token)

    @request_scope
    def _chat_parse(
        self,
        payload: ChatCompletionRequest | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletionResponse, ModelT]:
        """Send a primary chat request and parse the response into a structured object."""
        chat_data = _serialization._prepare_chat_completion_for_parse(payload, self._settings, response_format, strict)
        completion = self._chat_create(chat_data)
        parsed = _serialization._parse_primary_completion(completion, response_format)
        return completion, parsed

    @request_scope
    def _chat(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> ChatCompletion:
        """Return a root chat completion based on the provided messages."""
        _serialization._validate_response_format(payload)
        chat_data = _serialization._parse_chat(payload, self._settings)
        return chat.chat_sync(self._client, chat=chat_data, access_token=self.token)

    @request_scope
    def _stream(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> Iterator[ChatCompletionChunk]:
        """Return a root streaming chat completion based on the provided messages."""
        chat_data = _serialization._parse_chat(payload, self._settings)

        yield from chat.stream_sync(self._client, chat=chat_data, access_token=self.token)

    @request_scope
    def _chat_parse_root(
        self,
        payload: Chat | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletion, ModelT]:
        """Send a root chat request and parse the response into a structured object."""
        chat_data = _serialization._prepare_chat_for_parse(payload, self._settings, response_format, strict)
        completion = self._chat(chat_data)
        parsed = _serialization._parse_completion(completion, response_format)
        return completion, parsed

    @request_scope
    def chat_parse(
        self,
        payload: Chat | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletion, ModelT]:
        """Parse via the root chat compatibility shim.

        .. note:: **Beta.** This feature may not work correctly with all model versions.

        *response_format* accepts a Pydantic ``BaseModel`` subclass.
        The method derives a JSON Schema from it, sends the request via the root
        chat contract, then parses and validates ``message.content``.

        Raise :class:`~gigachat.exceptions.LengthFinishReasonError` if
        ``finish_reason`` is ``"length"`` (truncated response).
        """
        return self._chat_parse_root(payload, response_format=response_format, strict=strict)

    @request_scope
    def get_balance(self, *, request_options: RequestOptions | None = None) -> Balance:
        """
        Return the balance of available tokens.

        Only for prepaid clients, otherwise HTTP 403.
        """
        return tools.get_balance_sync(self._client, access_token=self.token)

    @request_scope
    def openapi_function_convert(
        self, openapi_function: str, *, request_options: RequestOptions | None = None
    ) -> OpenApiFunctions:
        """Convert an OpenAPI function description to a GigaChat function."""
        return tools.functions_convert_sync(self._client, openapi_function=openapi_function, access_token=self.token)

    @request_scope
    def check_ai(self, text: str, model: str, *, request_options: RequestOptions | None = None) -> AICheckResult:
        """Check the provided text for content generated by AI models."""
        return tools.ai_check_sync(self._client, input_=text, model=model, access_token=self.token)

    @request_scope
    def stream(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> Iterator[ChatCompletionChunk]:
        """Stream via the root chat compatibility shim."""
        yield from self._stream(payload)

    @request_scope
    def rerank(
        self,
        model: str,
        input_: list[dict[str, Any]],
        *,
        options: dict[str, Any] | None = None,
        include_documents: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> RerankResponse:
        """Rank documents for each query."""
        return tools.rerank_sync(
            self._client,
            model=model,
            input_=input_,
            options=options,
            include_documents=include_documents,
            access_token=self.token,
        )

    @request_scope
    def update_file_access(
        self,
        file_ids: list[str],
        access_policy: Literal["public", "private"],
        *,
        request_options: RequestOptions | None = None,
    ) -> UploadedFiles:
        """Update file access policies."""
        return files.update_file_access_sync(
            self._client, file_ids=file_ids, access_policy=access_policy, access_token=self.token
        )

    @request_scope
    def functions_validate(
        self, function: dict[str, Any] | str | bytes, *, request_options: RequestOptions | None = None
    ) -> FunctionValidationResult:
        """Validate a JSON function object or raw OpenAPI YAML."""
        return tools.functions_validate_sync(self._client, function=function, access_token=self.token)

    @request_scope
    def functions_generate(
        self, input_: str, model: str | None = None, *, request_options: RequestOptions | None = None
    ) -> GeneratedContent:
        """Generate a function definition as text."""
        return tools.functions_generate_sync(
            self._client,
            input_=input_,
            model=_serialization._resolve_model(model, self._settings),
            access_token=self.token,
        )

    @request_scope
    def instructions_generate(
        self, input_: str, model: str | None = None, *, request_options: RequestOptions | None = None
    ) -> GeneratedContent:
        """Generate instructions as text."""
        return tools.instructions_generate_sync(
            self._client,
            input_=input_,
            model=_serialization._resolve_model(model, self._settings),
            access_token=self.token,
        )

    @request_scope
    def functions_rank(
        self,
        messages: list[dict[str, Any]],
        functions: list[dict[str, Any]],
        *,
        options: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> RankedFunctions:
        """Rank functions using the embedder."""
        return tools.functions_rank_sync(
            self._client, messages=messages, functions=functions, options=options, access_token=self.token
        )

    @request_scope
    def create_batch(
        self,
        data: bytes | Iterable[bytes],
        *,
        method: Literal["chat_completions", "embedder"],
        request_options: RequestOptions | None = None,
    ) -> Batch:
        """Submit raw JSONL without polling or replaying ambiguous failures."""
        return batches.create_batch_sync(self._client, data=data, method=method, access_token=self.token)

    @request_scope
    def get_batches(self, batch_id: str | None = None, *, request_options: RequestOptions | None = None) -> Batches:
        """Query batches using an optional batch identifier."""
        return batches.get_batches_sync(self._client, batch_id=batch_id, access_token=self.token)


class GigaChatAsyncClient(AsyncFilesMixin, _BaseClient):
    """Asynchronous GigaChat client."""

    @cached_property
    def achat(self) -> AsyncChatNamespace:
        """Return the async chat namespace with primary chat methods."""
        return AsyncChatNamespace(self)

    @cached_property
    def a_assistants(self) -> AssistantsAsyncClient:
        """Return the async assistants resource."""
        return AssistantsAsyncClient(self)

    @cached_property
    def a_threads(self) -> ThreadsAsyncClient:
        """Return the async threads resource."""
        return ThreadsAsyncClient(self)

    @property
    def _aclient(self) -> httpx.AsyncClient:
        self._ensure_open("async")
        if self._owner is not self:
            return cast(GigaChatAsyncClient, self._owner)._aclient
        if self._aclient_instance is None:
            factory = DefaultAioHttpClient if self._settings.async_backend == "aiohttp" else DefaultAsyncHttpxClient
            self._aclient_instance = factory(base_url=self._settings.base_url, **http_client_kwargs(self._settings))
        return self._aclient_instance

    @property
    def _auth_aclient(self) -> httpx.AsyncClient:
        self._ensure_open("async")
        if self._owner is not self:
            return cast(GigaChatAsyncClient, self._owner)._auth_aclient
        if self._auth_aclient_instance is None:
            factory = DefaultAioHttpClient if self._settings.async_backend == "aiohttp" else DefaultAsyncHttpxClient
            self._auth_aclient_instance = factory(**http_client_kwargs(self._settings, for_auth=True))
        return self._auth_aclient_instance

    async def aclose(self) -> None:
        if self._owner is not self:
            self._view_closed = True
            return
        with self._lifecycle_lock:
            self._async_closed = True
            self._closed = True
        if self._aclient_instance and self._injected_async_http is None:
            await self._aclient_instance.aclose()
        if self._auth_aclient_instance and self._injected_auth_async_http is None:
            await self._auth_aclient_instance.aclose()

    async def __aenter__(self) -> Self:
        self._ensure_async_loop()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def _aupdate_token(self) -> None:
        self._ensure_async_loop()
        if self._owner is not self:
            return await cast(GigaChatAsyncClient, self._owner)._aupdate_token()
        if authorization_cvar.get() is not None:
            return
        async with self._async_token_lock:
            if self._is_token_usable():
                return
            if self._settings.credentials:
                self._set_token(
                    await auth.auth_async(
                        self._auth_aclient,
                        url=self._settings.auth_url,
                        credentials=self._settings.credentials,
                        scope=self._settings.scope,
                    )
                )
                logger.debug("Token refreshed via OAuth")
            elif self._settings.user and self._settings.password:
                self._set_token(
                    _serialization._build_access_token(
                        await auth.token_async(
                            self._aclient,
                            url=self._settings.base_url.rstrip("/") + "/token",
                            user=self._settings.user,
                            password=self._settings.password,
                        )
                    )
                )
                logger.debug("Token refreshed via password auth")

    async def aget_token(self) -> AccessToken | None:
        """
        Return a valid access token, refreshing if necessary.

        Returns:
            Optional[AccessToken]: The access token if authentication is configured and successful.
                Returns None if:
                1. Authentication is managed via context variable (`authorization_cvar`).
                2. No authentication credentials are provided.
        """
        await self._aupdate_token()
        return self._owner._access_token

    @request_scope
    async def atokens_count(
        self, input_: str | list[str], model: str | None = None, *, request_options: RequestOptions | None = None
    ) -> list[TokensCount]:
        """Return the number of tokens in a string."""
        model = _serialization._resolve_model(model, self._settings)

        return await tools.tokens_count_async(self._aclient, input_=input_, model=model, access_token=self.token)

    @request_scope
    async def aembeddings(
        self,
        texts: str | list[str],
        model: str = "Embeddings",
        *,
        encoding_format: str | None = None,
        truncate: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Embeddings:
        """Return embeddings."""

        return await embeddings.embeddings_async(
            self._aclient,
            access_token=self.token,
            input_=texts,
            model=model,
            encoding_format=encoding_format,
            truncate=truncate,
        )

    @request_scope
    async def aget_models(self, *, request_options: RequestOptions | None = None) -> Models:
        """Return a list of available models."""

        return await models.get_models_async(self._aclient, access_token=self.token)

    @request_scope
    async def aget_image(self, file_id: str, *, request_options: RequestOptions | None = None) -> Image:
        """Return an image in base64 encoding."""

        return await files.get_image_async(self._aclient, file_id=file_id, access_token=self.token)

    @request_scope
    async def aget_model(self, model: str, *, request_options: RequestOptions | None = None) -> Model:
        """Return a description of a specific model."""

        return await models.get_model_async(self._aclient, model=model, access_token=self.token)

    @request_scope
    async def _achat(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> ChatCompletion:
        """Return a root chat completion based on the provided messages."""
        _serialization._validate_response_format(payload)
        chat_data = _serialization._parse_chat(payload, self._settings)

        return await chat.chat_async(self._aclient, chat=chat_data, access_token=self.token)

    @request_scope
    async def _achat_create(
        self, payload: ChatCompletionRequest | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> ChatCompletionResponse:
        """Return a primary chat completion based on the provided messages."""
        chat_data = _serialization._parse_chat_completion(payload, self._settings)
        return await chat_completions.chat_async(self._aclient, chat=chat_data, access_token=self.token)

    @request_scope
    async def _achat_stream(
        self, payload: ChatCompletionRequest | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> AsyncIterator[PrimaryChatCompletionChunk]:
        """Return a primary streaming chat completion based on the provided messages."""
        chat_data = _serialization._parse_chat_completion(payload, self._settings)
        iterator = chat_completions.stream_async(self._aclient, chat=chat_data, access_token=self.token)
        try:
            async for chunk in iterator:
                yield chunk
        finally:
            await cast(Any, iterator).aclose()

    @request_scope
    async def _astream(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Return a root streaming chat completion based on the provided messages."""
        chat_data = _serialization._parse_chat(payload, self._settings)
        iterator = chat.stream_async(self._aclient, chat=chat_data, access_token=self.token)
        try:
            async for chunk in iterator:
                yield chunk
        finally:
            await cast(Any, iterator).aclose()

    @request_scope
    async def _achat_parse(
        self,
        payload: ChatCompletionRequest | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletionResponse, ModelT]:
        """Send a primary chat request and parse the response into a structured object."""
        chat_data = _serialization._prepare_chat_completion_for_parse(payload, self._settings, response_format, strict)
        completion = await self._achat_create(chat_data)
        parsed = _serialization._parse_primary_completion(completion, response_format)
        return completion, parsed

    @request_scope
    async def _achat_parse_root(
        self,
        payload: Chat | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletion, ModelT]:
        """Send a root chat request and parse the response into *response_format*."""
        chat_data = _serialization._prepare_chat_for_parse(payload, self._settings, response_format, strict)
        completion = await self._achat(chat_data)
        parsed = _serialization._parse_completion(completion, response_format)
        return completion, parsed

    @request_scope
    async def achat_parse(
        self,
        payload: Chat | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletion, ModelT]:
        """Parse via the root async chat compatibility shim.

        .. note:: **Beta.** This feature may not work correctly with all model versions.

        Async version of :meth:`GigaChatSyncClient.chat_parse`.

        Raise :class:`~gigachat.exceptions.LengthFinishReasonError` if
        ``finish_reason`` is ``"length"`` (truncated response).
        """
        return await self._achat_parse_root(payload, response_format=response_format, strict=strict)

    @request_scope
    async def aupload_file(
        self,
        file: FileTypes,
        purpose: Literal["general", "assistant"] = "general",
        *,
        request_options: RequestOptions | None = None,
    ) -> UploadedFile:
        """Upload a file."""

        return await files.upload_file_async(self._aclient, file=file, purpose=purpose, access_token=self.token)

    @request_scope
    async def aget_file(self, file: str, *, request_options: RequestOptions | None = None) -> UploadedFile:
        """Return information about a file."""

        return await files.get_file_async(self._aclient, file=file, access_token=self.token)

    @request_scope
    async def aget_files(self, *, request_options: RequestOptions | None = None) -> UploadedFiles:
        """Return a list of uploaded files."""

        return await files.get_files_async(self._aclient, access_token=self.token)

    @request_scope
    async def adelete_file(self, file: str, *, request_options: RequestOptions | None = None) -> DeletedFile:
        """Delete a file."""

        return await files.delete_file_async(self._aclient, file=file, access_token=self.token)

    @request_scope
    async def aget_balance(self, *, request_options: RequestOptions | None = None) -> Balance:
        """
        Return the balance of available tokens.

        Only for prepaid clients, otherwise HTTP 403.
        """

        return await tools.get_balance_async(self._aclient, access_token=self.token)

    @request_scope
    async def aopenapi_function_convert(
        self, openapi_function: str, *, request_options: RequestOptions | None = None
    ) -> OpenApiFunctions:
        """Convert an OpenAPI function description to a GigaChat function."""

        return await tools.functions_convert_async(
            self._aclient, openapi_function=openapi_function, access_token=self.token
        )

    @request_scope
    async def acheck_ai(self, text: str, model: str, *, request_options: RequestOptions | None = None) -> AICheckResult:
        """Check the provided text for content generated by AI models."""

        return await tools.ai_check_async(self._aclient, input_=text, model=model, access_token=self.token)

    @request_scope
    async def astream(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Stream via the root async chat compatibility shim."""
        iterator = self._astream(payload)
        try:
            async for chunk in iterator:
                yield chunk
        finally:
            await cast(Any, iterator).aclose()

    @request_scope
    async def arerank(
        self,
        model: str,
        input_: list[dict[str, Any]],
        *,
        options: dict[str, Any] | None = None,
        include_documents: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> RerankResponse:
        """Rank documents for each query."""
        return await tools.rerank_async(
            self._aclient,
            model=model,
            input_=input_,
            options=options,
            include_documents=include_documents,
            access_token=self.token,
        )

    @request_scope
    async def aupdate_file_access(
        self,
        file_ids: list[str],
        access_policy: Literal["public", "private"],
        *,
        request_options: RequestOptions | None = None,
    ) -> UploadedFiles:
        """Update file access policies."""
        return await files.update_file_access_async(
            self._aclient, file_ids=file_ids, access_policy=access_policy, access_token=self.token
        )

    @request_scope
    async def afunctions_validate(
        self, function: dict[str, Any] | str | bytes, *, request_options: RequestOptions | None = None
    ) -> FunctionValidationResult:
        """Validate a JSON function object or raw OpenAPI YAML."""
        return await tools.functions_validate_async(self._aclient, function=function, access_token=self.token)

    @request_scope
    async def afunctions_generate(
        self, input_: str, model: str | None = None, *, request_options: RequestOptions | None = None
    ) -> GeneratedContent:
        """Generate a function definition as text."""
        return await tools.functions_generate_async(
            self._aclient,
            input_=input_,
            model=_serialization._resolve_model(model, self._settings),
            access_token=self.token,
        )

    @request_scope
    async def ainstructions_generate(
        self, input_: str, model: str | None = None, *, request_options: RequestOptions | None = None
    ) -> GeneratedContent:
        """Generate instructions as text."""
        return await tools.instructions_generate_async(
            self._aclient,
            input_=input_,
            model=_serialization._resolve_model(model, self._settings),
            access_token=self.token,
        )

    @request_scope
    async def afunctions_rank(
        self,
        messages: list[dict[str, Any]],
        functions: list[dict[str, Any]],
        *,
        options: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> RankedFunctions:
        """Rank functions using the embedder."""
        return await tools.functions_rank_async(
            self._aclient, messages=messages, functions=functions, options=options, access_token=self.token
        )

    @request_scope
    async def acreate_batch(
        self,
        data: bytes | AsyncIterable[bytes],
        *,
        method: Literal["chat_completions", "embedder"],
        request_options: RequestOptions | None = None,
    ) -> Batch:
        """Submit raw JSONL without polling or replaying ambiguous failures."""
        return await batches.create_batch_async(self._aclient, data=data, method=method, access_token=self.token)

    @request_scope
    async def aget_batches(
        self, batch_id: str | None = None, *, request_options: RequestOptions | None = None
    ) -> Batches:
        """Query batches using an optional batch identifier."""
        return await batches.get_batches_async(self._aclient, batch_id=batch_id, access_token=self.token)


class GigaChat(GigaChatSyncClient, GigaChatAsyncClient):
    """GigaChat client."""

    async def aclose(self) -> None:
        self.close()
        await super().aclose()
