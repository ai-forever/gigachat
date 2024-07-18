from typing import TYPE_CHECKING, Any, Dict, List, Optional

from gigachat.api.assistants import (
    get_assistants,
    post_assistant_delete,
    post_assistant_files_delete,
    post_assistant_modify,
    post_assistants,
)
from gigachat.models import Function
from gigachat.models.assistants import (
    Assistant,
    AssistantDelete,
    AssistantFileDelete,
    Assistants,
    CreateAssistant,
)

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class AssistantsSyncClient:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self.base_client = base_client

    def get(self, assistant_id: Optional[str] = None) -> Assistants:
        """Возвращает список доступных ассистентов"""
        return self.base_client._decorator(
            lambda: get_assistants.sync(
                self.base_client._client,
                assistant_id=assistant_id,
                access_token=self.base_client.token,
            )
        )

    def create(
        self,
        model: str,
        name: str,
        instructions: Optional[str] = None,
        description: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        functions: Optional[List[Function]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CreateAssistant:
        """Создает ассистента"""
        return self.base_client._decorator(
            lambda: post_assistants.sync(
                self.base_client._client,
                model=model,
                name=name,
                description=description,
                instructions=instructions,
                file_ids=file_ids,
                functions=functions,
                metadata=metadata,
                access_token=self.base_client.token,
            )
        )

    def update(
        self,
        assistant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        functions: Optional[List[Function]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Assistant:
        """Обновляет ассистента"""

        return self.base_client._decorator(
            lambda: post_assistant_modify.sync(
                self.base_client._client,
                assistant_id=assistant_id,
                name=name,
                description=description,
                instructions=instructions,
                file_ids=file_ids,
                functions=functions,
                metadata=metadata,
                access_token=self.base_client.token,
            )
        )

    def delete_file(self, assistant_id: str, file_id: str) -> AssistantFileDelete:
        """Удаляет файл ассистента"""
        return self.base_client._decorator(
            lambda: post_assistant_files_delete.sync(
                self.base_client._client,
                assistant_id=assistant_id,
                file_id=file_id,
                access_token=self.base_client.token,
            )
        )

    def delete(self, assistant_id: str) -> AssistantDelete:
        """Удаляет ассистента"""
        return self.base_client._decorator(
            lambda: post_assistant_delete.sync(
                self.base_client._client,
                assistant_id=assistant_id,
                access_token=self.base_client.token,
            )
        )


class AssistantsAsyncClient:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self.base_client = base_client

    async def get(self, assistant_id: Optional[str] = None) -> Assistants:
        """Возвращает список доступных ассистентов"""

        async def _acall() -> Assistants:
            return await get_assistants.asyncio(
                self.base_client._aclient,
                assistant_id=assistant_id,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def create(
        self,
        model: str,
        name: str,
        instructions: Optional[str] = None,
        description: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        functions: Optional[List[Function]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CreateAssistant:
        """Создает ассистента"""

        async def _acall() -> CreateAssistant:
            return await post_assistants.asyncio(
                self.base_client._aclient,
                model=model,
                name=name,
                description=description,
                instructions=instructions,
                file_ids=file_ids,
                functions=functions,
                metadata=metadata,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def update(
        self,
        assistant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        functions: Optional[List[Function]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Assistant:
        """Обновляет ассистента"""

        async def _acall() -> Assistant:
            return await post_assistant_modify.asyncio(
                self.base_client._aclient,
                assistant_id=assistant_id,
                name=name,
                description=description,
                instructions=instructions,
                file_ids=file_ids,
                functions=functions,
                metadata=metadata,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def delete_file(self, assistant_id: str, file_id: str) -> AssistantFileDelete:
        """Удаляет файл ассистента"""

        async def _acall() -> AssistantFileDelete:
            return await post_assistant_files_delete.asyncio(
                self.base_client._aclient,
                assistant_id=assistant_id,
                file_id=file_id,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)

    async def delete(self, assistant_id: str) -> AssistantDelete:
        """Удаляет ассистента"""

        async def _acall() -> AssistantDelete:
            return await post_assistant_delete.asyncio(
                self.base_client._aclient,
                assistant_id=assistant_id,
                access_token=self.base_client.token,
            )

        return await self.base_client._adecorator(_acall)
