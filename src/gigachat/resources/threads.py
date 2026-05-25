import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
)

from gigachat.api import threads
from gigachat.authentication import _awith_auth, _awith_auth_stream, _with_auth, _with_auth_stream
from gigachat.models.chat import (
    Messages,
    MessagesRole,
)
from gigachat.models.threads import (
    ThreadCompletion,
    ThreadCompletionChunk,
    ThreadMessages,
    ThreadMessagesResponse,
    ThreadRunOptions,
    ThreadRunResponse,
    ThreadRunResult,
    Threads,
)
from gigachat.retry import _awith_retry, _awith_retry_stream, _with_retry, _with_retry_stream

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


def _parse_message(message: Union[Messages, str, Dict[str, Any]]) -> Messages:
    if isinstance(message, str):
        return Messages(role=MessagesRole.USER, content=message)
    else:
        return Messages.model_validate(message)


class ThreadsSyncClient:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @_with_retry
    @_with_auth
    def get_threads(
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Return a list of threads."""
        return threads.get_threads_sync(
            self._base_client._client,
            assistants_ids=assistants_ids,
            limit=limit,
            before=before,
            access_token=self._base_client.token,
        )

    def list(
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Alias for get_threads."""
        return self.get_threads(assistants_ids=assistants_ids, limit=limit, before=before)

    @_with_retry
    @_with_auth
    def create_thread(self) -> str:
        """Create a thread."""
        return threads.post_thread_sync(self._base_client._client, access_token=self._base_client.token).id_

    @_with_retry
    @_with_auth
    def retrieve(self, threads_ids: List[str]) -> Threads:
        """Return a list of threads by their IDs."""
        return threads.retrieve_threads_sync(
            self._base_client._client, threads_ids=threads_ids, access_token=self._base_client.token
        )

    @_with_retry
    @_with_auth
    def delete(self, thread_id: str) -> bool:
        """Delete a thread."""
        return threads.delete_thread_sync(
            self._base_client._client, thread_id=thread_id, access_token=self._base_client.token
        )

    @_with_retry
    @_with_auth
    def get_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> ThreadMessages:
        """Return a list of messages in a thread."""
        return threads.get_thread_messages_sync(
            self._base_client._client,
            thread_id=thread_id,
            limit=limit,
            before=before,
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
    def add_message(self, thread_id: str, message: Union[Messages, str, Dict[str, Any]]) -> ThreadMessagesResponse:
        """Add a message to a thread."""
        message_ = _parse_message(message)
        return threads.add_thread_messages_sync(
            self._base_client._client,
            thread_id=thread_id,
            messages=[message_],
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
    def add_messages(
        self, thread_id: Optional[str] = None, messages: Optional[List[Union[Messages, str, Dict[str, Any]]]] = None
    ) -> ThreadMessagesResponse:
        """Add multiple messages to a thread."""
        if messages is None:
            messages = []
        messages_ = [_parse_message(message) for message in messages]
        return threads.add_thread_messages_sync(
            self._base_client._client,
            thread_id=thread_id,
            messages=messages_,
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
    def run(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        options: Optional[ThreadRunOptions] = None,
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

    @_with_retry
    @_with_auth
    def get_run(self, thread_id: str) -> ThreadRunResult:
        """Return the status of a thread run."""
        return threads.get_thread_run_sync(
            self._base_client._client, thread_id=thread_id, access_token=self._base_client.token
        )

    @_with_retry_stream
    @_with_auth_stream
    def run_stream(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        options: Optional[ThreadRunOptions] = None,
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

    @_with_retry
    @_with_auth
    def run_messages(
        self,
        messages: List[Union[Messages, str, Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
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
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
    def rerun_messages(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
    ) -> ThreadCompletion:
        """Regenerate messages."""
        return threads.rerun_thread_messages_sync(
            self._base_client._client,
            thread_id=thread_id,
            thread_options=thread_options,
            access_token=self._base_client.token,
        )

    @_with_retry_stream
    @_with_auth_stream
    def run_messages_stream(
        self,
        messages: List[Union[Messages, str, Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
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
            access_token=self._base_client.token,
        )

    @_with_retry_stream
    @_with_auth_stream
    def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Regenerate messages with streaming response."""
        yield from threads.rerun_thread_messages_stream_sync(
            self._base_client._client,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._base_client.token,
        )


class ThreadsAsyncClient:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @_awith_retry
    @_awith_auth
    async def get_threads(
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Return a list of threads."""

        return await threads.get_threads_async(
            self._base_client._aclient,
            assistants_ids=assistants_ids,
            limit=limit,
            before=before,
            access_token=self._base_client.token,
        )

    async def list(
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Alias for get_threads."""
        return await self.get_threads(assistants_ids=assistants_ids, limit=limit, before=before)

    @_awith_retry
    @_awith_auth
    async def create_thread(self) -> str:
        """Create a thread."""

        return (await threads.post_thread_async(self._base_client._aclient, access_token=self._base_client.token)).id_

    @_awith_retry
    @_awith_auth
    async def retrieve(self, threads_ids: List[str]) -> Threads:
        """Return a list of threads by their IDs."""

        return await threads.retrieve_threads_async(
            self._base_client._aclient, threads_ids=threads_ids, access_token=self._base_client.token
        )

    @_awith_retry
    @_awith_auth
    async def delete(self, thread_id: str) -> bool:
        """Delete a thread."""

        return await threads.delete_thread_async(
            self._base_client._aclient, thread_id=thread_id, access_token=self._base_client.token
        )

    @_awith_retry
    @_awith_auth
    async def get_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> ThreadMessages:
        """Return a list of messages in a thread."""

        return await threads.get_thread_messages_async(
            self._base_client._aclient,
            thread_id=thread_id,
            limit=limit,
            before=before,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def add_message(
        self, thread_id: str, message: Union[Messages, str, Dict[str, Any]]
    ) -> ThreadMessagesResponse:
        """Add a message to a thread."""
        message_ = _parse_message(message)

        return await threads.add_thread_messages_async(
            self._base_client._aclient,
            thread_id=thread_id,
            messages=[message_],
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def add_messages(
        self, thread_id: Optional[str] = None, messages: Optional[List[Union[Messages, str, Dict[str, Any]]]] = None
    ) -> ThreadMessagesResponse:
        """Add multiple messages to a thread."""
        if messages is None:
            messages = []
        messages_ = [_parse_message(message) for message in messages]

        return await threads.add_thread_messages_async(
            self._base_client._aclient,
            thread_id=thread_id,
            messages=messages_,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def run(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        options: Optional[ThreadRunOptions] = None,
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

    @_awith_retry
    @_awith_auth
    async def get_run(self, thread_id: str) -> ThreadRunResult:
        """Return the status of a thread run."""

        return await threads.get_thread_run_async(
            self._base_client._aclient, thread_id=thread_id, access_token=self._base_client.token
        )

    @_awith_retry_stream
    @_awith_auth_stream
    def run_stream(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        options: Optional[ThreadRunOptions] = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Run a thread with streaming response."""
        if options and not thread_options:
            thread_options = options
            warnings.warn("Argument 'options' is deprecated, use 'thread_options'", DeprecationWarning, stacklevel=2)

        return threads.run_thread_stream_async(
            self._base_client._aclient,
            thread_id=thread_id,
            assistant_id=assistant_id,
            thread_options=thread_options,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def run_messages(
        self,
        messages: List[Union[Messages, str, Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
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
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def rerun_messages(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
    ) -> ThreadCompletion:
        """Regenerate messages."""

        return await threads.rerun_thread_messages_async(
            self._base_client._aclient,
            thread_id=thread_id,
            thread_options=thread_options,
            access_token=self._base_client.token,
        )

    @_awith_retry_stream
    @_awith_auth_stream
    def run_messages_stream(
        self,
        messages: List[Union[Messages, str, Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Run messages with streaming response."""
        messages_ = [_parse_message(message) for message in messages]

        return threads.run_thread_messages_stream_async(
            self._base_client._aclient,
            messages=messages_,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._base_client.token,
        )

    @_awith_retry_stream
    @_awith_auth_stream
    def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Regenerate messages with streaming response."""

        return threads.rerun_thread_messages_stream_async(
            self._base_client._aclient,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._base_client.token,
        )
