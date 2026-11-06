import builtins
import warnings
from collections.abc import AsyncIterator, Iterator
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from gigachat._core.execution import request_scope
from gigachat._core.request import RequestOptions
from gigachat.api import threads
from gigachat.models.chat import (
    Messages,
    MessagesRole,
)
from gigachat.models.threads import (
    SharedThread,
    ThreadCompletion,
    ThreadCompletionChunk,
    ThreadMessages,
    ThreadMessagesResponse,
    ThreadRunOptions,
    ThreadRunResponse,
    ThreadRunResult,
    Threads,
)

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


def _parse_message(message: Messages | str | dict[str, Any]) -> Messages:
    if isinstance(message, str):
        return Messages(role=MessagesRole.USER, content=message)
    else:
        return Messages.model_validate(message)


class ThreadsSyncClient:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @request_scope
    def get_threads(
        self,
        assistants_ids: list[str] | None = None,
        limit: int | None = None,
        before: int | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> Threads:
        """Return a list of threads."""
        return threads.get_threads_sync(
            self._base_client._client,
            assistants_ids=assistants_ids,
            limit=limit,
            before=before,
            access_token=self._base_client.token,
        )

    @request_scope
    def list(
        self,
        assistants_ids: list[str] | None = None,
        limit: int | None = None,
        before: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> Threads:
        """Alias for get_threads."""
        return self.get_threads(assistants_ids=assistants_ids, limit=limit, before=before)

    @request_scope
    def create_thread(self, *, request_options: RequestOptions | None = None) -> str:
        """Create a thread."""
        return threads.post_thread_sync(self._base_client._client, access_token=self._base_client.token).id_

    @request_scope
    def retrieve(self, threads_ids: builtins.list[str], *, request_options: RequestOptions | None = None) -> Threads:
        """Return a list of threads by their IDs."""
        return threads.retrieve_threads_sync(
            self._base_client._client, threads_ids=threads_ids, access_token=self._base_client.token
        )

    @request_scope
    def delete(self, thread_id: str, *, request_options: RequestOptions | None = None) -> bool:
        """Delete a thread."""
        return threads.delete_thread_sync(
            self._base_client._client, thread_id=thread_id, access_token=self._base_client.token
        )

    @request_scope
    def get_messages(
        self,
        thread_id: str,
        limit: int | None = None,
        before: int | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> ThreadMessages:
        """Return a list of messages in a thread."""
        return threads.get_thread_messages_sync(
            self._base_client._client,
            thread_id=thread_id,
            limit=limit,
            before=before,
            access_token=self._base_client.token,
        )

    @request_scope
    def add_message(
        self,
        thread_id: str,
        message: Messages | str | dict[str, Any],
        *,
        metadata: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> ThreadMessagesResponse:
        """Add a message to a thread."""
        message_ = _parse_message(message)
        return threads.add_thread_messages_sync(
            self._base_client._client,
            thread_id=thread_id,
            messages=[message_],
            metadata=metadata,
            access_token=self._base_client.token,
        )

    @request_scope
    def add_messages(
        self,
        thread_id: str | None = None,
        messages: builtins.list[Messages | str | dict[str, Any]] | None = None,
        *,
        metadata: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> ThreadMessagesResponse:
        """Add multiple messages to a thread."""
        if messages is None:
            messages = []
        messages_ = [_parse_message(message) for message in messages]
        return threads.add_thread_messages_sync(
            self._base_client._client,
            thread_id=thread_id,
            messages=messages_,
            metadata=metadata,
            access_token=self._base_client.token,
        )

    @request_scope
    def run(
        self,
        thread_id: str,
        assistant_id: str | None = None,
        thread_options: ThreadRunOptions | None = None,
        options: ThreadRunOptions | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> ThreadRunResponse:
        """Run a thread."""
        if options and not thread_options:
            thread_options = options
            warnings.warn("Argument 'options' is deprecated, use 'thread_options'", DeprecationWarning, stacklevel=2)

        return threads.run_thread_sync(
            self._base_client._client,
            thread_id=thread_id,
            assistant_id=assistant_id,
            thread_options=thread_options,
            access_token=self._base_client.token,
        )

    @request_scope
    def get_run(self, thread_id: str, *, request_options: RequestOptions | None = None) -> ThreadRunResult:
        """Return the status of a thread run."""
        return threads.get_thread_run_sync(
            self._base_client._client, thread_id=thread_id, access_token=self._base_client.token
        )

    @request_scope
    def run_stream(
        self,
        thread_id: str,
        assistant_id: str | None = None,
        thread_options: ThreadRunOptions | None = None,
        options: ThreadRunOptions | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Run a thread with streaming response."""
        if options and not thread_options:
            thread_options = options
            warnings.warn("Argument 'options' is deprecated, use 'thread_options'", DeprecationWarning, stacklevel=2)

        yield from threads.run_thread_stream_sync(
            self._base_client._client,
            thread_id=thread_id,
            assistant_id=assistant_id,
            thread_options=thread_options,
            access_token=self._base_client.token,
        )

    @request_scope
    def run_messages(
        self,
        messages: builtins.list[Messages | str | dict[str, Any]],
        thread_id: str | None = None,
        assistant_id: str | None = None,
        model: str | None = None,
        thread_options: ThreadRunOptions | None = None,
        *,
        metadata: dict[str, Any] | None = None,
        update_interval: float | None = None,
        request_options: RequestOptions | None = None,
    ) -> ThreadCompletion:
        """Run messages."""
        messages_ = [_parse_message(message) for message in messages]
        return threads.run_thread_messages_sync(
            self._base_client._client,
            messages=messages_,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            metadata=metadata,
            update_interval=update_interval,
            access_token=self._base_client.token,
        )

    @request_scope
    def rerun_messages(
        self,
        thread_id: str,
        thread_options: ThreadRunOptions | None = None,
        *,
        update_interval: float | None = None,
        request_options: RequestOptions | None = None,
    ) -> ThreadCompletion:
        """Regenerate messages."""
        return threads.rerun_thread_messages_sync(
            self._base_client._client,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._base_client.token,
        )

    @request_scope
    def run_messages_stream(
        self,
        messages: builtins.list[Messages | str | dict[str, Any]],
        thread_id: str | None = None,
        assistant_id: str | None = None,
        model: str | None = None,
        thread_options: ThreadRunOptions | None = None,
        update_interval: float | None = None,
        *,
        metadata: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Run messages with streaming response."""
        messages_ = [_parse_message(message) for message in messages]
        yield from threads.run_thread_messages_stream_sync(
            self._base_client._client,
            messages=messages_,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            update_interval=update_interval,
            metadata=metadata,
            access_token=self._base_client.token,
        )

    @request_scope
    def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: ThreadRunOptions | None = None,
        update_interval: float | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Regenerate messages with streaming response."""
        yield from threads.rerun_thread_messages_stream_sync(
            self._base_client._client,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._base_client.token,
        )

    @request_scope
    def share(self, thread_id: str, *, request_options: RequestOptions | None = None) -> SharedThread:
        """Create a read-only shared copy of a thread."""
        return threads.share_thread_sync(
            self._base_client._client, thread_id=thread_id, access_token=self._base_client.token
        )


class ThreadsAsyncClient:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @request_scope
    async def get_threads(
        self,
        assistants_ids: list[str] | None = None,
        limit: int | None = None,
        before: int | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> Threads:
        """Return a list of threads."""

        return await threads.get_threads_async(
            self._base_client._aclient,
            assistants_ids=assistants_ids,
            limit=limit,
            before=before,
            access_token=self._base_client.token,
        )

    @request_scope
    async def list(
        self,
        assistants_ids: list[str] | None = None,
        limit: int | None = None,
        before: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> Threads:
        """Alias for get_threads."""
        return await self.get_threads(assistants_ids=assistants_ids, limit=limit, before=before)

    @request_scope
    async def create_thread(self, *, request_options: RequestOptions | None = None) -> str:
        """Create a thread."""

        return (await threads.post_thread_async(self._base_client._aclient, access_token=self._base_client.token)).id_

    @request_scope
    async def retrieve(
        self, threads_ids: builtins.list[str], *, request_options: RequestOptions | None = None
    ) -> Threads:
        """Return a list of threads by their IDs."""

        return await threads.retrieve_threads_async(
            self._base_client._aclient, threads_ids=threads_ids, access_token=self._base_client.token
        )

    @request_scope
    async def delete(self, thread_id: str, *, request_options: RequestOptions | None = None) -> bool:
        """Delete a thread."""

        return await threads.delete_thread_async(
            self._base_client._aclient, thread_id=thread_id, access_token=self._base_client.token
        )

    @request_scope
    async def get_messages(
        self,
        thread_id: str,
        limit: int | None = None,
        before: int | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> ThreadMessages:
        """Return a list of messages in a thread."""

        return await threads.get_thread_messages_async(
            self._base_client._aclient,
            thread_id=thread_id,
            limit=limit,
            before=before,
            access_token=self._base_client.token,
        )

    @request_scope
    async def add_message(
        self,
        thread_id: str,
        message: Messages | str | dict[str, Any],
        *,
        metadata: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> ThreadMessagesResponse:
        """Add a message to a thread."""
        message_ = _parse_message(message)

        return await threads.add_thread_messages_async(
            self._base_client._aclient,
            thread_id=thread_id,
            messages=[message_],
            metadata=metadata,
            access_token=self._base_client.token,
        )

    @request_scope
    async def add_messages(
        self,
        thread_id: str | None = None,
        messages: builtins.list[Messages | str | dict[str, Any]] | None = None,
        *,
        metadata: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> ThreadMessagesResponse:
        """Add multiple messages to a thread."""
        if messages is None:
            messages = []
        messages_ = [_parse_message(message) for message in messages]

        return await threads.add_thread_messages_async(
            self._base_client._aclient,
            thread_id=thread_id,
            messages=messages_,
            metadata=metadata,
            access_token=self._base_client.token,
        )

    @request_scope
    async def run(
        self,
        thread_id: str,
        assistant_id: str | None = None,
        thread_options: ThreadRunOptions | None = None,
        options: ThreadRunOptions | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> ThreadRunResponse:
        """Run a thread."""
        if options and not thread_options:
            thread_options = options
            warnings.warn("Argument 'options' is deprecated, use 'thread_options'", DeprecationWarning, stacklevel=2)

        return await threads.run_thread_async(
            self._base_client._aclient,
            thread_id=thread_id,
            assistant_id=assistant_id,
            thread_options=thread_options,
            access_token=self._base_client.token,
        )

    @request_scope
    async def get_run(self, thread_id: str, *, request_options: RequestOptions | None = None) -> ThreadRunResult:
        """Return the status of a thread run."""

        return await threads.get_thread_run_async(
            self._base_client._aclient, thread_id=thread_id, access_token=self._base_client.token
        )

    @request_scope
    async def run_stream(
        self,
        thread_id: str,
        assistant_id: str | None = None,
        thread_options: ThreadRunOptions | None = None,
        options: ThreadRunOptions | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Run a thread with streaming response."""
        if options and not thread_options:
            thread_options = options
            warnings.warn("Argument 'options' is deprecated, use 'thread_options'", DeprecationWarning, stacklevel=2)

        iterator = threads.run_thread_stream_async(
            self._base_client._aclient,
            thread_id=thread_id,
            assistant_id=assistant_id,
            thread_options=thread_options,
            access_token=self._base_client.token,
        )
        try:
            async for chunk in iterator:
                yield chunk
        finally:
            await cast(Any, iterator).aclose()

    @request_scope
    async def run_messages(
        self,
        messages: builtins.list[Messages | str | dict[str, Any]],
        thread_id: str | None = None,
        assistant_id: str | None = None,
        model: str | None = None,
        thread_options: ThreadRunOptions | None = None,
        *,
        metadata: dict[str, Any] | None = None,
        update_interval: float | None = None,
        request_options: RequestOptions | None = None,
    ) -> ThreadCompletion:
        """Run messages."""
        messages_ = [_parse_message(message) for message in messages]

        return await threads.run_thread_messages_async(
            self._base_client._aclient,
            messages=messages_,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            metadata=metadata,
            update_interval=update_interval,
            access_token=self._base_client.token,
        )

    @request_scope
    async def rerun_messages(
        self,
        thread_id: str,
        thread_options: ThreadRunOptions | None = None,
        *,
        update_interval: float | None = None,
        request_options: RequestOptions | None = None,
    ) -> ThreadCompletion:
        """Regenerate messages."""

        return await threads.rerun_thread_messages_async(
            self._base_client._aclient,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._base_client.token,
        )

    @request_scope
    async def run_messages_stream(
        self,
        messages: builtins.list[Messages | str | dict[str, Any]],
        thread_id: str | None = None,
        assistant_id: str | None = None,
        model: str | None = None,
        thread_options: ThreadRunOptions | None = None,
        update_interval: float | None = None,
        *,
        metadata: dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Run messages with streaming response."""
        messages_ = [_parse_message(message) for message in messages]

        iterator = threads.run_thread_messages_stream_async(
            self._base_client._aclient,
            messages=messages_,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            update_interval=update_interval,
            metadata=metadata,
            access_token=self._base_client.token,
        )
        try:
            async for chunk in iterator:
                yield chunk
        finally:
            await cast(Any, iterator).aclose()

    @request_scope
    async def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: ThreadRunOptions | None = None,
        update_interval: float | None = None,
        *,
        request_options: RequestOptions | None = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Regenerate messages with streaming response."""

        iterator = threads.rerun_thread_messages_stream_async(
            self._base_client._aclient,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._base_client.token,
        )
        try:
            async for chunk in iterator:
                yield chunk
        finally:
            await cast(Any, iterator).aclose()

    @request_scope
    async def share(self, thread_id: str, *, request_options: RequestOptions | None = None) -> SharedThread:
        """Create a read-only shared copy of a thread."""
        return await threads.share_thread_async(
            self._base_client._aclient, thread_id=thread_id, access_token=self._base_client.token
        )
