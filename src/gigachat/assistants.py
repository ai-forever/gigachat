from typing import TYPE_CHECKING, Any, Dict, List, Optional

from gigachat.api import assistants
from gigachat.authentication import awith_auth, with_auth
from gigachat.models.assistants import (
    Assistant,
    AssistantDelete,
    AssistantFileDelete,
    Assistants,
    CreateAssistant,
)
from gigachat.models.chat import Function

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class AssistantsSyncClient:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self.base_client = base_client

    @with_auth
    def get(self, assistant_id: Optional[str] = None) -> Assistants:
        """Возвращает список доступных ассистентов"""
        return assistants.get_assistants_sync(
            self.base_client._client,
            assistant_id=assistant_id,
            access_token=self.base_client.token,
        )

    @with_auth
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
        return assistants.create_assistant_sync(
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

    @with_auth
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

        return assistants.modify_assistant_sync(
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

    @with_auth
    def delete_file(self, assistant_id: str, file_id: str) -> AssistantFileDelete:
        """Удаляет файл ассистента"""
        return assistants.delete_assistant_file_sync(
            self.base_client._client,
            assistant_id=assistant_id,
            file_id=file_id,
            access_token=self.base_client.token,
        )

    @with_auth
    def delete(self, assistant_id: str) -> AssistantDelete:
        """Удаляет ассистента"""
        return assistants.delete_assistant_sync(
            self.base_client._client,
            assistant_id=assistant_id,
            access_token=self.base_client.token,
        )


class AssistantsAsyncClient:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self.base_client = base_client

    @awith_auth
    async def get(self, assistant_id: Optional[str] = None) -> Assistants:
        """Возвращает список доступных ассистентов"""

        return await assistants.get_assistants_async(
            self.base_client._aclient,
            assistant_id=assistant_id,
            access_token=self.base_client.token,
        )

    @awith_auth
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

        return await assistants.create_assistant_async(
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

    @awith_auth
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

        return await assistants.modify_assistant_async(
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

    @awith_auth
    async def delete_file(self, assistant_id: str, file_id: str) -> AssistantFileDelete:
        """Удаляет файл ассистента"""

        return await assistants.delete_assistant_file_async(
            self.base_client._aclient,
            assistant_id=assistant_id,
            file_id=file_id,
            access_token=self.base_client.token,
        )

    @awith_auth
    async def delete(self, assistant_id: str) -> AssistantDelete:
        """Удаляет ассистента"""

        return await assistants.delete_assistant_async(
            self.base_client._aclient,
            assistant_id=assistant_id,
            access_token=self.base_client.token,
        )
