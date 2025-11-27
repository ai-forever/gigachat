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
from gigachat.exceptions import AuthenticationError
from gigachat.models import (
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
        self.base_client = base_client

    def list(  # noqa: A003
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Получение перечня тредов"""
        return self.base_client._decorator(
            lambda: threads.get_threads_sync(
                self.base_client._client,
                assistants_ids=assistants_ids,
                limit=limit,
                before=before,
                access_token=self.base_client.token,
            )
        )

    def retrieve(
        self,
        threads_ids: List[str],
    ) -> Threads:
        """Получение перечня тредов по идентификаторам"""
        return self.base_client._decorator(
            lambda: threads.retrieve_threads_sync(
                self.base_client._client,
                threads_ids=threads_ids,
                access_token=self.base_client.token,
            )
        )

    def delete(self, thread_id: str) -> bool:
        """Удаляет тред"""

        return self.base_client._decorator(
            lambda: threads.delete_thread_sync(
                self.base_client._client,
                thread_id=thread_id,
                access_token=self.base_client.token,
            )
        )

    def get_run(self, thread_id: str) -> ThreadRunResult:
        """Получить результат run треда"""
        warnings.warn("get_run is deprecated. Use get_messages instead", stacklevel=2)

        return self.base_client._decorator(
            lambda: threads.get_thread_run_sync(
                self.base_client._client,
                thread_id=thread_id,
                access_token=self.base_client.token,
            )
        )

    def get_messages(self, thread_id: str, limit: Optional[int] = None, before: Optional[int] = None) -> ThreadMessages:
        """Получение сообщений треда"""

        return self.base_client._decorator(
            lambda: threads.get_thread_messages_sync(
                self.base_client._client,
                thread_id=thread_id,
                limit=limit,
                before=before,
                access_token=self.base_client.token,
            )
        )

    def run(
        self,
        thread_id: str,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
    ) -> ThreadRunResponse:
        """Запуск генерации ответа на контекст треда"""
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)
        return self.base_client._decorator(
            lambda: threads.run_thread_sync(
                self.base_client._client,
                thread_id=thread_id,
                thread_options=thread_options,
                access_token=self.base_client.token,
            )
        )

    def add_messages(
        self,
        messages: Union[List[Messages], List[str], List[Dict[str, Any]]],
        model: Optional[str] = None,
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
    ) -> ThreadMessagesResponse:
        """Добавление сообщений к треду без запуска"""
        parsed_messages = [_parse_message(message) for message in messages]
        return self.base_client._decorator(
            lambda: threads.add_thread_messages_sync(
                self.base_client._client,
                messages=parsed_messages,
                model=model,
                thread_id=thread_id,
                assistant_id=assistant_id,
                access_token=self.base_client.token,
            )
        )

    def run_messages(
        self,
        messages: Union[List[Messages], List[str], List[Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
    ) -> ThreadCompletion:
        """Добавление сообщений к треду с запуском"""
        warnings.warn("run_messages is deprecated. Use GigaChat.chat instead", stacklevel=2)
        parsed_messages = [_parse_message(message) for message in messages]
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        return self.base_client._decorator(
            lambda: threads.run_thread_messages_sync(
                self.base_client._client,
                messages=parsed_messages,
                thread_id=thread_id,
                assistant_id=assistant_id,
                model=model,
                thread_options=thread_options,
                access_token=self.base_client.token,
            )
        )

    def rerun_messages(
        self,
        thread_id: str,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
    ) -> ThreadCompletion:
        """Перегенерация ответа модели"""
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        return self.base_client._decorator(
            lambda: threads.rerun_thread_messages_sync(
                self.base_client._client,
                thread_id=thread_id,
                thread_options=thread_options,
                access_token=self.base_client.token,
            )
        )

    def run_messages_stream(
        self,
        messages: Union[List[Messages], List[str], List[Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
        update_interval: Optional[int] = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Добавление сообщений к треду с запуском"""
        warnings.warn("run_messages is deprecated. Use GigaChat.chat instead", stacklevel=2)
        parsed_messages = [_parse_message(message) for message in messages]
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        if self.base_client._use_auth:
            if self.base_client._check_validity_token():
                try:
                    for chunk in threads.run_thread_messages_stream_sync(
                        self.base_client._client,
                        messages=parsed_messages,
                        thread_id=thread_id,
                        assistant_id=assistant_id,
                        model=model,
                        thread_options=thread_options,
                        update_interval=update_interval,
                        access_token=self.base_client.token,
                    ):
                        yield chunk
                    return
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    self.base_client._reset_token()
            self.base_client._update_token()

        for chunk in threads.run_thread_messages_stream_sync(
            self.base_client._client,
            messages=parsed_messages,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self.base_client.token,
        ):
            yield chunk

    def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
        update_interval: Optional[int] = None,
    ) -> Iterator[ThreadCompletionChunk]:
        """Перегенерация ответа модели"""
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        if self.base_client._use_auth:
            if self.base_client._check_validity_token():
                try:
                    for chunk in threads.rerun_thread_messages_stream_sync(
                        self.base_client._client,
                        thread_id=thread_id,
                        thread_options=thread_options,
                        update_interval=update_interval,
                        access_token=self.base_client.token,
                    ):
                        yield chunk
                    return
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    self.base_client._reset_token()
            self.base_client._update_token()

        for chunk in threads.rerun_thread_messages_stream_sync(
            self.base_client._client,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self.base_client.token,
        ):
            yield chunk


class ThreadsAsyncClient:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self.base_client = base_client

    async def list(  # noqa: A003
        self,
        assistants_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        before: Optional[int] = None,
    ) -> Threads:
        """Получение перечня тредов"""

        async def _acall() -> Threads:
            return await threads.get_threads_async(
                self.base_client._aclient,
                assistants_ids=assistants_ids,
                limit=limit,
                before=before,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def retrieve(
        self,
        threads_ids: List[str],
    ) -> Threads:
        """Получение перечня тредов по идентификаторам"""

        async def _acall() -> Threads:
            return await threads.retrieve_threads_async(
                self.base_client._aclient,
                threads_ids=threads_ids,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def delete(self, thread_id: str) -> bool:
        """Удаляет тред"""

        async def _acall() -> bool:
            return await threads.delete_thread_async(
                self.base_client._aclient,
                thread_id=thread_id,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def get_run(self, thread_id: str) -> ThreadRunResult:
        """Получить результат run треда"""
        warnings.warn("get_run is deprecated. Use get_messages instead", stacklevel=2)

        async def _acall() -> ThreadRunResult:
            return await threads.get_thread_run_async(
                self.base_client._aclient,
                thread_id=thread_id,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def get_messages(
        self, thread_id: str, limit: Optional[int] = None, before: Optional[int] = None
    ) -> ThreadMessages:
        """Получение сообщений треда"""

        async def _acall() -> ThreadMessages:
            return await threads.get_thread_messages_async(
                self.base_client._aclient,
                thread_id=thread_id,
                limit=limit,
                before=before,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def run(
        self,
        thread_id: str,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
    ) -> ThreadRunResponse:
        """Запуск генерации ответа на контекст треда"""
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        async def _acall() -> ThreadRunResponse:
            return await threads.run_thread_async(
                self.base_client._aclient,
                thread_id=thread_id,
                thread_options=thread_options,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def add_messages(
        self,
        messages: Union[List[Messages], List[str], List[Dict[str, Any]]],
        model: Optional[str] = None,
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
    ) -> ThreadMessagesResponse:
        """Добавление сообщений к треду без запуска"""
        parsed_messages = [_parse_message(message) for message in messages]

        async def _acall() -> ThreadMessagesResponse:
            return await threads.add_thread_messages_async(
                self.base_client._aclient,
                messages=parsed_messages,
                model=model,
                thread_id=thread_id,
                assistant_id=assistant_id,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def run_messages(
        self,
        messages: Union[List[Messages], List[str], List[Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
    ) -> ThreadCompletion:
        """Добавление сообщений к треду с запуском"""
        warnings.warn("run_messages is deprecated. Use GigaChat.chat instead", stacklevel=2)
        parsed_messages = [_parse_message(message) for message in messages]
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        async def _acall() -> ThreadCompletion:
            return await threads.run_thread_messages_async(
                self.base_client._aclient,
                messages=parsed_messages,
                thread_id=thread_id,
                assistant_id=assistant_id,
                model=model,
                thread_options=thread_options,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def rerun_messages(
        self,
        thread_id: str,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
    ) -> ThreadCompletion:
        """Перегенерация ответа модели"""
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        async def _acall() -> ThreadCompletion:
            return await threads.rerun_thread_messages_async(
                self.base_client._aclient,
                thread_id=thread_id,
                thread_options=thread_options,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def run_messages_stream(
        self,
        messages: Union[List[Messages], List[str], List[Dict[str, Any]]],
        thread_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        model: Optional[str] = None,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
        update_interval: Optional[int] = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Добавление сообщений к треду с запуском"""
        warnings.warn("run_messages is deprecated. Use GigaChat.chat instead", stacklevel=2)
        parsed_messages = [_parse_message(message) for message in messages]
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        if self.base_client._use_auth:
            if self.base_client._check_validity_token():
                try:
                    async for chunk in threads.run_thread_messages_stream_async(
                        self.base_client._aclient,
                        messages=parsed_messages,
                        thread_id=thread_id,
                        assistant_id=assistant_id,
                        model=model,
                        thread_options=thread_options,
                        update_interval=update_interval,
                        access_token=self.base_client.token,
                    ):
                        yield chunk
                    return
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    self.base_client._reset_token()
            await self.base_client._aupdate_token()

        async for chunk in threads.run_thread_messages_stream_async(
            self.base_client._aclient,
            messages=parsed_messages,
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self.base_client.token,
        ):
            yield chunk

    async def rerun_messages_stream(
        self,
        thread_id: str,
        thread_options: Optional[Union[ThreadRunOptions, Dict[str, Any]]] = None,
        update_interval: Optional[int] = None,
    ) -> AsyncIterator[ThreadCompletionChunk]:
        """Перегенерация ответа модели"""
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        if self.base_client._use_auth:
            if self.base_client._check_validity_token():
                try:
                    async for chunk in threads.rerun_thread_messages_stream_async(
                        self.base_client._aclient,
                        thread_id=thread_id,
                        thread_options=thread_options,
                        update_interval=update_interval,
                        access_token=self.base_client.token,
                    ):
                        yield chunk
                    return
                except AuthenticationError:
                    _logger.debug("AUTHENTICATION ERROR")
                    self.base_client._reset_token()
            await self.base_client._aupdate_token()

        async for chunk in threads.rerun_thread_messages_stream_async(
            self.base_client._aclient,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self.base_client.token,
        ):
            yield chunk
