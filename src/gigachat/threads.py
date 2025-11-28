import logging
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
from gigachat.authentication import awith_auth, awith_auth_stream, with_auth, with_auth_stream
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

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


def _parse_message(message: Union[Messages, str, Dict[str, Any]]) -> Messages:
    if isinstance(message, str):
        return Messages(role=MessagesRole.USER, content=message)
    else:
        return Messages.parse_obj(message)


_logger = logging.getLogger(__name__)


class ThreadsSyncClient:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._client = base_client

    @with_auth
    def get_threads(
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Получение списка тредов"""
        return threads.get_threads_sync(
            self._client._client,
            assistants_ids=assistants_ids,
            limit=limit,
            before=before,
            access_token=self._client.token,
        )

    def list(  # noqa: A003
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Alias for get_threads"""
        return self.get_threads(assistants_ids=assistants_ids, limit=limit, before=before)

    @with_auth
    def create_thread(self) -> str:
        """Создание треда"""
        return threads.post_thread_sync(self._client._client, access_token=self._client.token).id_

    @with_auth
    def retrieve(self, threads_ids: List[str]) -> Threads:
        """Получение списка тредов по идентификаторам"""
        return threads.retrieve_threads_sync(
            self._client._client, threads_ids=threads_ids, access_token=self._client.token
        )

    @with_auth
    def delete(self, thread_id: str) -> bool:
        """Удаление треда"""
        return threads.delete_thread_sync(self._client._client, thread_id=thread_id, access_token=self._client.token)

    @with_auth
    def get_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> ThreadMessages:
        """Получение списка сообщений треда"""
        return threads.get_thread_messages_sync(
            self._client._client,
            thread_id=thread_id,
            limit=limit,
            before=before,
            access_token=self._client.token,
        )

    @with_auth
    def add_message(self, thread_id: str, message: Union[Messages, str, Dict[str, Any]]) -> ThreadMessagesResponse:
        """Добавление сообщения в тред"""
        message_ = _parse_message(message)
        return threads.add_thread_messages_sync(
            self._client._client,
            thread_id=thread_id,
            messages=[message_],
            access_token=self._client.token,
        )

    @with_auth
    def add_messages(
        self, thread_id: Optional[str] = None, messages: Optional[List[Union[Messages, str, Dict[str, Any]]]] = None
    ) -> ThreadMessagesResponse:
        """Добавление сообщений в тред"""
        if messages is None:
            messages = []
        messages_ = [_parse_message(message) for message in messages]
        return threads.add_thread_messages_sync(
            self._client._client,
            thread_id=thread_id,
            messages=messages_,
            access_token=self._client.token,
        )

    @with_auth
    def run(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        # Backwards compatibility args (if needed by user code, though run signature in test uses named args)
        options: Optional[ThreadRunOptions] = None,
    ) -> ThreadRunResponse:
        """Запуск треда"""
        if options and not thread_options:
            thread_options = options
            warnings.warn("Argument 'options' is deprecated, use 'thread_options'", DeprecationWarning, stacklevel=2)

        return threads.run_thread_sync(
            self._client._client,
            thread_id=thread_id,
            assistant_id=assistant_id,
            thread_options=thread_options,
            access_token=self._client.token,
        )

    @with_auth
    def get_run(self, thread_id: str) -> ThreadRunResult:
        """Получение статуса запуска треда"""
        return threads.get_thread_run_sync(self._client._client, thread_id=thread_id, access_token=self._client.token)

    @with_auth_stream
    def run_stream(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        # Backwards compatibility
        options: Optional[ThreadRunOptions] = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Запуск треда с возвратом потока"""
        if options and not thread_options:
            thread_options = options
            warnings.warn("Argument 'options' is deprecated, use 'thread_options'", DeprecationWarning, stacklevel=2)

        yield from threads.run_thread_stream_sync(
            self._client._client,
            thread_id=thread_id,
            assistant_id=assistant_id,
            thread_options=thread_options,
            access_token=self._client.token,
        )

    @with_auth
    def run_messages(
        self,
        messages: List[Union[Messages, str, Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
    ) -> ThreadCompletion:
        """Запуск сообщений"""
        messages_ = [_parse_message(message) for message in messages]
        return threads.run_thread_messages_sync(
            self._client._client,
            messages=messages_,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            access_token=self._client.token,
        )

    @with_auth
    def rerun_messages(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
    ) -> ThreadCompletion:
        """Перегенерация сообщений"""
        return threads.rerun_thread_messages_sync(
            self._client._client,
            thread_id=thread_id,
            thread_options=thread_options,
            access_token=self._client.token,
        )

    @with_auth_stream
    def run_messages_stream(
        self,
        messages: List[Union[Messages, str, Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Запуск сообщений в стриме"""
        messages_ = [_parse_message(message) for message in messages]
        yield from threads.run_thread_messages_stream_sync(
            self._client._client,
            messages=messages_,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._client.token,
        )

    @with_auth_stream
    def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Перегенерация сообщений в стриме"""
        yield from threads.rerun_thread_messages_stream_sync(
            self._client._client,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._client.token,
        )


class ThreadsAsyncClient:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._client = base_client

    @awith_auth
    async def get_threads(
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Получение списка тредов"""

        return await threads.get_threads_async(
            self._client._aclient,
            assistants_ids=assistants_ids,
            limit=limit,
            before=before,
            access_token=self._client.token,
        )

    async def list(  # noqa: A003
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Alias for get_threads"""
        return await self.get_threads(assistants_ids=assistants_ids, limit=limit, before=before)

    @awith_auth
    async def create_thread(self) -> str:
        """Создание треда"""

        return (await threads.post_thread_async(self._client._aclient, access_token=self._client.token)).id_

    @awith_auth
    async def retrieve(self, threads_ids: List[str]) -> Threads:
        """Получение списка тредов по идентификаторам"""

        return await threads.retrieve_threads_async(
            self._client._aclient, threads_ids=threads_ids, access_token=self._client.token
        )

    @awith_auth
    async def delete(self, thread_id: str) -> bool:
        """Удаление треда"""

        return await threads.delete_thread_async(
            self._client._aclient, thread_id=thread_id, access_token=self._client.token
        )

    @awith_auth
    async def get_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> ThreadMessages:
        """Получение списка сообщений треда"""

        return await threads.get_thread_messages_async(
            self._client._aclient,
            thread_id=thread_id,
            limit=limit,
            before=before,
            access_token=self._client.token,
        )

    @awith_auth
    async def add_message(
        self, thread_id: str, message: Union[Messages, str, Dict[str, Any]]
    ) -> ThreadMessagesResponse:
        """Добавление сообщения в тред"""
        message_ = _parse_message(message)

        return await threads.add_thread_messages_async(
            self._client._aclient,
            thread_id=thread_id,
            messages=[message_],
            access_token=self._client.token,
        )

    @awith_auth
    async def add_messages(
        self, thread_id: Optional[str] = None, messages: Optional[List[Union[Messages, str, Dict[str, Any]]]] = None
    ) -> ThreadMessagesResponse:
        """Добавление сообщений в тред"""
        if messages is None:
            messages = []
        messages_ = [_parse_message(message) for message in messages]

        return await threads.add_thread_messages_async(
            self._client._aclient,
            thread_id=thread_id,
            messages=messages_,
            access_token=self._client.token,
        )

    @awith_auth
    async def run(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        # Backwards compatibility
        options: Optional[ThreadRunOptions] = None,
    ) -> ThreadRunResponse:
        """Запуск треда"""
        if options and not thread_options:
            thread_options = options
            warnings.warn("Argument 'options' is deprecated, use 'thread_options'", DeprecationWarning, stacklevel=2)

        return await threads.run_thread_async(
            self._client._aclient,
            thread_id=thread_id,
            assistant_id=assistant_id,
            thread_options=thread_options,
            access_token=self._client.token,
        )

    @awith_auth
    async def get_run(self, thread_id: str) -> ThreadRunResult:
        """Получение статуса запуска треда"""

        return await threads.get_thread_run_async(
            self._client._aclient, thread_id=thread_id, access_token=self._client.token
        )

    @awith_auth_stream
    def run_stream(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        # Backwards compatibility
        options: Optional[ThreadRunOptions] = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Запуск треда с возвратом потока"""
        if options and not thread_options:
            thread_options = options
            warnings.warn("Argument 'options' is deprecated, use 'thread_options'", DeprecationWarning, stacklevel=2)

        return threads.run_thread_stream_async(
            self._client._aclient,
            thread_id=thread_id,
            assistant_id=assistant_id,
            thread_options=thread_options,
            access_token=self._client.token,
        )

    @awith_auth
    async def run_messages(
        self,
        messages: List[Union[Messages, str, Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
    ) -> ThreadCompletion:
        """Запуск сообщений"""
        messages_ = [_parse_message(message) for message in messages]

        return await threads.run_thread_messages_async(
            self._client._aclient,
            messages=messages_,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            access_token=self._client.token,
        )

    @awith_auth
    async def rerun_messages(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
    ) -> ThreadCompletion:
        """Перегенерация сообщений"""

        return await threads.rerun_thread_messages_async(
            self._client._aclient,
            thread_id=thread_id,
            thread_options=thread_options,
            access_token=self._client.token,
        )

    @awith_auth_stream
    def run_messages_stream(
        self,
        messages: List[Union[Messages, str, Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Запуск сообщений в стриме"""
        messages_ = [_parse_message(message) for message in messages]

        return threads.run_thread_messages_stream_async(
            self._client._aclient,
            messages=messages_,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._client.token,
        )

    @awith_auth_stream
    def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Перегенерация сообщений в стриме"""

        return threads.rerun_thread_messages_stream_async(
            self._client._aclient,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self._client.token,
        )
