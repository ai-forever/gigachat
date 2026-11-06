from typing import TYPE_CHECKING, Any

from gigachat._core.execution import request_scope
from gigachat._core.request import RequestOptions
from gigachat.api import assistants
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
        self._base_client = base_client

    @request_scope
    def get(self, assistant_id: str | None = None, *, request_options: RequestOptions | None = None) -> Assistants:
        """Return a list of available assistants."""
        return assistants.get_assistants_sync(
            self._base_client._client,
            assistant_id=assistant_id,
            access_token=self._base_client.token,
        )

    @request_scope
    def create(
        self,
        model: str,
        name: str,
        instructions: str | None = None,
        description: str | None = None,
        file_ids: list[str] | None = None,
        functions: list[Function] | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        request_options: RequestOptions | None = None,
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

    @request_scope
    def update(
        self,
        assistant_id: str,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        file_ids: list[str] | None = None,
        functions: list[Function] | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        request_options: RequestOptions | None = None,
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

    @request_scope
    def delete_file(
        self, assistant_id: str, file_id: str, *, request_options: RequestOptions | None = None
    ) -> AssistantFileDelete:
        """Delete an assistant file."""
        return assistants.delete_assistant_file_sync(
            self._base_client._client,
            assistant_id=assistant_id,
            file_id=file_id,
            access_token=self._base_client.token,
        )

    @request_scope
    def delete(self, assistant_id: str, *, request_options: RequestOptions | None = None) -> AssistantDelete:
        """Delete an assistant."""
        return assistants.delete_assistant_sync(
            self._base_client._client,
            assistant_id=assistant_id,
            access_token=self._base_client.token,
        )


class AssistantsAsyncClient:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @request_scope
    async def get(
        self, assistant_id: str | None = None, *, request_options: RequestOptions | None = None
    ) -> Assistants:
        """Return a list of available assistants."""

        return await assistants.get_assistants_async(
            self._base_client._aclient,
            assistant_id=assistant_id,
            access_token=self._base_client.token,
        )

    @request_scope
    async def create(
        self,
        model: str,
        name: str,
        instructions: str | None = None,
        description: str | None = None,
        file_ids: list[str] | None = None,
        functions: list[Function] | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        request_options: RequestOptions | None = None,
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

    @request_scope
    async def update(
        self,
        assistant_id: str,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        file_ids: list[str] | None = None,
        functions: list[Function] | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        request_options: RequestOptions | None = None,
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

    @request_scope
    async def delete_file(
        self, assistant_id: str, file_id: str, *, request_options: RequestOptions | None = None
    ) -> AssistantFileDelete:
        """Delete an assistant file."""

        return await assistants.delete_assistant_file_async(
            self._base_client._aclient,
            assistant_id=assistant_id,
            file_id=file_id,
            access_token=self._base_client.token,
        )

    @request_scope
    async def delete(self, assistant_id: str, *, request_options: RequestOptions | None = None) -> AssistantDelete:
        """Delete an assistant."""

        return await assistants.delete_assistant_async(
            self._base_client._aclient,
            assistant_id=assistant_id,
            access_token=self._base_client.token,
        )
