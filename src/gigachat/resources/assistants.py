from typing import TYPE_CHECKING, Any, Dict, List, Optional

from gigachat.api import assistants
from gigachat.authentication import _awith_auth, _with_auth
from gigachat.models.assistants import (
    Assistant,
    AssistantDelete,
    AssistantFileDelete,
    Assistants,
    CreateAssistant,
)
from gigachat.models.chat import Function
from gigachat.retry import _awith_retry, _with_retry

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class AssistantsSyncClient:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @_with_retry
    @_with_auth
    def get(self, assistant_id: Optional[str] = None) -> Assistants:
        """Return a list of available assistants."""
        return assistants.get_assistants_sync(
            self._base_client._client,
            assistant_id=assistant_id,
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
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
        """Create an assistant."""
        return assistants.create_assistant_sync(
            self._base_client._client,
            model=model,
            name=name,
            description=description,
            instructions=instructions,
            file_ids=file_ids,
            functions=functions,
            metadata=metadata,
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
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
        """Update an assistant."""

        return assistants.modify_assistant_sync(
            self._base_client._client,
            assistant_id=assistant_id,
            name=name,
            description=description,
            instructions=instructions,
            file_ids=file_ids,
            functions=functions,
            metadata=metadata,
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
    def delete_file(self, assistant_id: str, file_id: str) -> AssistantFileDelete:
        """Delete an assistant file."""
        return assistants.delete_assistant_file_sync(
            self._base_client._client,
            assistant_id=assistant_id,
            file_id=file_id,
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
    def delete(self, assistant_id: str) -> AssistantDelete:
        """Delete an assistant."""
        return assistants.delete_assistant_sync(
            self._base_client._client,
            assistant_id=assistant_id,
            access_token=self._base_client.token,
        )


class AssistantsAsyncClient:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @_awith_retry
    @_awith_auth
    async def get(self, assistant_id: Optional[str] = None) -> Assistants:
        """Return a list of available assistants."""

        return await assistants.get_assistants_async(
            self._base_client._aclient,
            assistant_id=assistant_id,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
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
        """Create an assistant."""

        return await assistants.create_assistant_async(
            self._base_client._aclient,
            model=model,
            name=name,
            description=description,
            instructions=instructions,
            file_ids=file_ids,
            functions=functions,
            metadata=metadata,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
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
        """Update an assistant."""

        return await assistants.modify_assistant_async(
            self._base_client._aclient,
            assistant_id=assistant_id,
            name=name,
            description=description,
            instructions=instructions,
            file_ids=file_ids,
            functions=functions,
            metadata=metadata,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def delete_file(self, assistant_id: str, file_id: str) -> AssistantFileDelete:
        """Delete an assistant file."""

        return await assistants.delete_assistant_file_async(
            self._base_client._aclient,
            assistant_id=assistant_id,
            file_id=file_id,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def delete(self, assistant_id: str) -> AssistantDelete:
        """Delete an assistant."""

        return await assistants.delete_assistant_async(
            self._base_client._aclient,
            assistant_id=assistant_id,
            access_token=self._base_client.token,
        )
