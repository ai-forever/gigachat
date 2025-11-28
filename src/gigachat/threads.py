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

    def get_threads(
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Получение списка тредов"""
        return self._client._decorator(
            lambda: threads.get_threads_sync(
                self._client._client,
                assistants_ids=assistants_ids,
                limit=limit,
                before=before,
                access_token=self._client.token,
            )
        )

    def list(  # noqa: A003
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Alias for get_threads"""
        return self.get_threads(assistants_ids=assistants_ids, limit=limit, before=before)

    def create_thread(self) -> str:
        """Создание треда"""
        return self._client._decorator(
            lambda: threads.post_thread_sync(self._client._client, access_token=self._client.token)
        ).id_

    def retrieve(self, threads_ids: List[str]) -> Threads:
        """Получение списка тредов по идентификаторам"""
        return self._client._decorator(
            lambda: threads.retrieve_threads_sync(
                self._client._client, threads_ids=threads_ids, access_token=self._client.token
            )
        )

    def delete(self, thread_id: str) -> bool:
        """Удаление треда"""
        return self._client._decorator(
            lambda: threads.delete_thread_sync(
                self._client._client, thread_id=thread_id, access_token=self._client.token
            )
        )

    def get_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> ThreadMessages:
        """Получение списка сообщений треда"""
        return self._client._decorator(
            lambda: threads.get_thread_messages_sync(
                self._client._client,
                thread_id=thread_id,
                limit=limit,
                before=before,
                access_token=self._client.token,
            )
        )

    def add_message(self, thread_id: str, message: Union[Messages, str, Dict[str, Any]]) -> ThreadMessagesResponse:
        """Добавление сообщения в тред"""
        message_ = _parse_message(message)
        return self._client._decorator(
            lambda: threads.add_thread_messages_sync(
                self._client._client,
                thread_id=thread_id,
                messages=[message_],
                access_token=self._client.token,
            )
        )

    def add_messages(
        self, thread_id: Optional[str] = None, messages: Optional[List[Union[Messages, str, Dict[str, Any]]]] = None
    ) -> ThreadMessagesResponse:
        """Добавление сообщений в тред"""
        if messages is None:
            messages = []
        messages_ = [_parse_message(message) for message in messages]
        return self._client._decorator(
            lambda: threads.add_thread_messages_sync(
                self._client._client,
                thread_id=thread_id,
                messages=messages_,
                access_token=self._client.token,
            )
        )

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

        return self._client._decorator(
            lambda: threads.run_thread_sync(
                self._client._client,
                thread_id=thread_id,
                assistant_id=assistant_id,
                thread_options=thread_options,
                access_token=self._client.token,
            )
        )

    def get_run(self, thread_id: str) -> ThreadRunResult:
        """Получение статуса запуска треда"""
        return self._client._decorator(
            lambda: threads.get_thread_run_sync(
                self._client._client, thread_id=thread_id, access_token=self._client.token
            )
        )

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

        return self._client._stream_decorator(
            lambda: threads.run_thread_stream_sync(
                self._client._client,
                thread_id=thread_id,
                assistant_id=assistant_id,
                thread_options=thread_options,
                access_token=self._client.token,
            )
        )

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
        return self._client._decorator(
            lambda: threads.run_thread_messages_sync(
                self._client._client,
                messages=messages_,
                thread_id=thread_id,
                assistant_id=assistant_id,
                model=model,
                thread_options=thread_options,
                access_token=self._client.token,
            )
        )

    def rerun_messages(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
    ) -> ThreadCompletion:
        """Перегенерация сообщений"""
        return self._client._decorator(
            lambda: threads.rerun_thread_messages_sync(
                self._client._client,
                thread_id=thread_id,
                thread_options=thread_options,
                access_token=self._client.token,
            )
        )

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
        return self._client._stream_decorator(
            lambda: threads.run_thread_messages_stream_sync(
                self._client._client,
                messages=messages_,
                thread_id=thread_id,
                assistant_id=assistant_id,
                model=model,
                thread_options=thread_options,
                update_interval=update_interval,
                access_token=self._client.token,
            )
        )

    def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Перегенерация сообщений в стриме"""
        return self._client._stream_decorator(
            lambda: threads.rerun_thread_messages_stream_sync(
                self._client._client,
                thread_id=thread_id,
                thread_options=thread_options,
                update_interval=update_interval,
                access_token=self._client.token,
            )
        )


class ThreadsAsyncClient:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._client = base_client

    async def get_threads(
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Получение списка тредов"""

        async def _acall() -> Threads:
            return await threads.get_threads_async(
                self._client._aclient,
                assistants_ids=assistants_ids,
                limit=limit,
                before=before,
                access_token=self._client.token,
            )

        return await self._client._adecorator(_acall)

    async def list(  # noqa: A003
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Alias for get_threads"""
        return await self.get_threads(assistants_ids=assistants_ids, limit=limit, before=before)

    async def create_thread(self) -> str:
        """Создание треда"""

        async def _acall() -> str:
            return (await threads.post_thread_async(self._client._aclient, access_token=self._client.token)).id_

        return await self._client._adecorator(_acall)

    async def retrieve(self, threads_ids: List[str]) -> Threads:
        """Получение списка тредов по идентификаторам"""

        async def _acall() -> Threads:
            return await threads.retrieve_threads_async(
                self._client._aclient, threads_ids=threads_ids, access_token=self._client.token
            )

        return await self._client._adecorator(_acall)

    async def delete(self, thread_id: str) -> bool:
        """Удаление треда"""

        async def _acall() -> bool:
            return await threads.delete_thread_async(
                self._client._aclient, thread_id=thread_id, access_token=self._client.token
            )

        return await self._client._adecorator(_acall)

    async def get_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> ThreadMessages:
        """Получение списка сообщений треда"""

        async def _acall() -> ThreadMessages:
            return await threads.get_thread_messages_async(
                self._client._aclient,
                thread_id=thread_id,
                limit=limit,
                before=before,
                access_token=self._client.token,
            )

        return await self._client._adecorator(_acall)

    async def add_message(
        self, thread_id: str, message: Union[Messages, str, Dict[str, Any]]
    ) -> ThreadMessagesResponse:
        """Добавление сообщения в тред"""
        message_ = _parse_message(message)

        async def _acall() -> ThreadMessagesResponse:
            return await threads.add_thread_messages_async(
                self._client._aclient,
                thread_id=thread_id,
                messages=[message_],
                access_token=self._client.token,
            )

        return await self._client._adecorator(_acall)

    async def add_messages(
        self, thread_id: Optional[str] = None, messages: Optional[List[Union[Messages, str, Dict[str, Any]]]] = None
    ) -> ThreadMessagesResponse:
        """Добавление сообщений в тред"""
        if messages is None:
            messages = []
        messages_ = [_parse_message(message) for message in messages]

        async def _acall() -> ThreadMessagesResponse:
            return await threads.add_thread_messages_async(
                self._client._aclient,
                thread_id=thread_id,
                messages=messages_,
                access_token=self._client.token,
            )

        return await self._client._adecorator(_acall)

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

        async def _acall() -> ThreadRunResponse:
            return await threads.run_thread_async(
                self._client._aclient,
                thread_id=thread_id,
                assistant_id=assistant_id,
                thread_options=thread_options,
                access_token=self._client.token,
            )

        return await self._client._adecorator(_acall)

    async def get_run(self, thread_id: str) -> ThreadRunResult:
        """Получение статуса запуска треда"""

        async def _acall() -> ThreadRunResult:
            return await threads.get_thread_run_async(
                self._client._aclient, thread_id=thread_id, access_token=self._client.token
            )

        return await self._client._adecorator(_acall)

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

        async def _acall() -> AsyncIterator[ThreadCompletionChunk]:
            async for chunk in threads.run_thread_stream_async(
                self._client._aclient,
                thread_id=thread_id,
                assistant_id=assistant_id,
                thread_options=thread_options,
                access_token=self._client.token,
            ):
                yield chunk

        return self._client._astream_decorator(_acall)

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

        async def _acall() -> ThreadCompletion:
            return await threads.run_thread_messages_async(
                self._client._aclient,
                messages=messages_,
                thread_id=thread_id,
                assistant_id=assistant_id,
                model=model,
                thread_options=thread_options,
                access_token=self._client.token,
            )

        return await self._client._adecorator(_acall)

    async def rerun_messages(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
    ) -> ThreadCompletion:
        """Перегенерация сообщений"""

        async def _acall() -> ThreadCompletion:
            return await threads.rerun_thread_messages_async(
                self._client._aclient,
                thread_id=thread_id,
                thread_options=thread_options,
                access_token=self._client.token,
            )

        return await self._client._adecorator(_acall)

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

        async def _acall() -> AsyncIterator[ThreadCompletionChunk]:
            async for chunk in threads.run_thread_messages_stream_async(
                self._client._aclient,
                messages=messages_,
                thread_id=thread_id,
                assistant_id=assistant_id,
                model=model,
                thread_options=thread_options,
                update_interval=update_interval,
                access_token=self._client.token,
            ):
                yield chunk

        return self._client._astream_decorator(_acall)

    def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: Optional[ThreadRunOptions] = None,
        update_interval: Optional[int] = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Перегенерация сообщений в стриме"""

        async def _acall() -> AsyncIterator[ThreadCompletionChunk]:
            async for chunk in threads.rerun_thread_messages_stream_async(
                self._client._aclient,
                thread_id=thread_id,
                thread_options=thread_options,
                update_interval=update_interval,
                access_token=self._client.token,
            ):
                yield chunk

        return self._client._astream_decorator(_acall)
