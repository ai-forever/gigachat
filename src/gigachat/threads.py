import logging
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

from gigachat.api.threads import (
    get_threads,
    get_threads_messages,
    get_threads_run,
    post_thread_messages_rerun,
    post_thread_messages_rerun_stream,
    post_thread_messages_run,
    post_thread_messages_run_stream,
    post_threads_delete,
    post_threads_messages,
    post_threads_retrieve,
    post_threads_run,
)
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
            lambda: get_threads.sync(
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
            lambda: post_threads_retrieve.sync(
                self.base_client._client,
                threads_ids=threads_ids,
                access_token=self.base_client.token,
            )
        )

    def delete(self, thread_id: str) -> bool:
        """Удаляет тред"""

        return self.base_client._decorator(
            lambda: post_threads_delete.sync(
                self.base_client._client,
                thread_id=thread_id,
                access_token=self.base_client.token,
            )
        )

    def get_run(self, thread_id: str) -> ThreadRunResult:
        """Получить результат run треда"""

        return self.base_client._decorator(
            lambda: get_threads_run.sync(
                self.base_client._client,
                thread_id=thread_id,
                access_token=self.base_client.token,
            )
        )

    def get_messages(self, thread_id: str, limit: Optional[int] = None, before: Optional[int] = None) -> ThreadMessages:
        """Получение сообщений треда"""

        return self.base_client._decorator(
            lambda: get_threads_messages.sync(
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
            lambda: post_threads_run.sync(
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
            lambda: post_threads_messages.sync(
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
        parsed_messages = [_parse_message(message) for message in messages]
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        return self.base_client._decorator(
            lambda: post_thread_messages_run.sync(
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
            lambda: post_thread_messages_rerun.sync(
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
        parsed_messages = [_parse_message(message) for message in messages]
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        if self.base_client._use_auth:
            if self.base_client._check_validity_token():
                try:
                    for chunk in post_thread_messages_run_stream.sync(
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

        for chunk in post_thread_messages_run_stream.sync(
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
                    for chunk in post_thread_messages_rerun_stream.sync(
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

        for chunk in post_thread_messages_rerun_stream.sync(
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
            return await get_threads.asyncio(
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
            return await post_threads_retrieve.asyncio(
                self.base_client._aclient,
                threads_ids=threads_ids,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def delete(self, thread_id: str) -> bool:
        """Удаляет тред"""

        async def _acall() -> bool:
            return await post_threads_delete.asyncio(
                self.base_client._aclient,
                thread_id=thread_id,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def get_run(self, thread_id: str) -> ThreadRunResult:
        """Получить результат run треда"""

        async def _acall() -> ThreadRunResult:
            return await get_threads_run.asyncio(
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
            return await get_threads_messages.asyncio(
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
            return await post_threads_run.asyncio(
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
            return await post_threads_messages.asyncio(
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
        parsed_messages = [_parse_message(message) for message in messages]
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        async def _acall() -> ThreadCompletion:
            return await post_thread_messages_run.asyncio(
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
            return await post_thread_messages_rerun.asyncio(
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
        parsed_messages = [_parse_message(message) for message in messages]
        if thread_options is not None:
            thread_options = ThreadRunOptions.parse_obj(thread_options)

        if self.base_client._use_auth:
            if self.base_client._check_validity_token():
                try:
                    async for chunk in post_thread_messages_run_stream.asyncio(
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

        async for chunk in post_thread_messages_run_stream.asyncio(
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
                    async for chunk in post_thread_messages_rerun_stream.asyncio(
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

        async for chunk in post_thread_messages_rerun_stream.asyncio(
            self.base_client._aclient,
            thread_id=thread_id,
            thread_options=thread_options,
            update_interval=update_interval,
            access_token=self.base_client.token,
        ):
            yield chunk
