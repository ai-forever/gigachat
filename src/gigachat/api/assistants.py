from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers, execute_request_async, execute_request_sync
from gigachat.models.assistants import (
    Assistant,
    AssistantDelete,
    AssistantFileDelete,
    Assistants,
    CreateAssistant,
)
from gigachat.models.chat import Function


def _get_assistants_kwargs(
    *,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    params = {
        "method": "GET",
        "url": "/assistants",
        "headers": headers,
    }
    if assistant_id:
        params["params"] = {"assistant_id": assistant_id}
    return params


def get_assistants_sync(
    client: httpx.Client,
    *,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Assistants:
    """Get list of assistants."""
    kwargs = _get_assistants_kwargs(assistant_id=assistant_id, access_token=access_token)
    return execute_request_sync(client, kwargs, Assistants)


async def get_assistants_async(
    client: httpx.AsyncClient,
    *,
    assistant_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> Assistants:
    """Get list of assistants."""
    kwargs = _get_assistants_kwargs(assistant_id=assistant_id, access_token=access_token)
    return await execute_request_async(client, kwargs, Assistants)


def _create_assistant_kwargs(
    *,
    model: str,
    name: str,
    description: Optional[str] = None,
    instructions: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    functions: Optional[List[Function]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    data: Dict[str, Any] = {
        "model": model,
        "name": name,
        "description": description,
        "instructions": instructions,
        "file_ids": file_ids,
        "metadata": metadata,
    }
    if functions is not None:
        data["functions"] = [function.model_dump(exclude_none=True, by_alias=True) for function in functions]

    return {
        "method": "POST",
        "url": "/assistants",
        "json": data,
        "headers": headers,
    }


def create_assistant_sync(
    client: httpx.Client,
    *,
    model: str,
    name: str,
    description: Optional[str] = None,
    instructions: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    functions: Optional[List[Function]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    access_token: Optional[str] = None,
) -> CreateAssistant:
    """Create assistant."""
    kwargs = _create_assistant_kwargs(
        model=model,
        name=name,
        description=description,
        instructions=instructions,
        file_ids=file_ids,
        functions=functions,
        metadata=metadata,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, CreateAssistant)


async def create_assistant_async(
    client: httpx.AsyncClient,
    *,
    model: str,
    name: str,
    description: Optional[str] = None,
    instructions: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    functions: Optional[List[Function]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    access_token: Optional[str] = None,
) -> CreateAssistant:
    """Create assistant."""
    kwargs = _create_assistant_kwargs(
        model=model,
        name=name,
        description=description,
        instructions=instructions,
        file_ids=file_ids,
        functions=functions,
        metadata=metadata,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, CreateAssistant)


def _modify_assistant_kwargs(
    *,
    assistant_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    instructions: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    functions: Optional[List[Function]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    data: Dict[str, Any] = {
        "assistant_id": assistant_id,
        "name": name,
        "description": description,
        "instructions": instructions,
        "file_ids": file_ids,
        "metadata": metadata,
    }
    if functions is not None:
        data["functions"] = [function.model_dump(exclude_none=True, by_alias=True) for function in functions]

    return {
        "method": "POST",
        "url": "/assistants/modify",
        "json": data,
        "headers": headers,
    }


def modify_assistant_sync(
    client: httpx.Client,
    *,
    assistant_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    instructions: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    functions: Optional[List[Function]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    access_token: Optional[str] = None,
) -> Assistant:
    """Modify assistant."""
    kwargs = _modify_assistant_kwargs(
        assistant_id=assistant_id,
        name=name,
        description=description,
        instructions=instructions,
        file_ids=file_ids,
        functions=functions,
        metadata=metadata,
        access_token=access_token,
    )
    return execute_request_sync(client, kwargs, Assistant)


async def modify_assistant_async(
    client: httpx.AsyncClient,
    *,
    assistant_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    instructions: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    functions: Optional[List[Function]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    access_token: Optional[str] = None,
) -> Assistant:
    """Modify assistant."""
    kwargs = _modify_assistant_kwargs(
        assistant_id=assistant_id,
        name=name,
        description=description,
        instructions=instructions,
        file_ids=file_ids,
        functions=functions,
        metadata=metadata,
        access_token=access_token,
    )
    return await execute_request_async(client, kwargs, Assistant)


def _delete_assistant_kwargs(
    *,
    assistant_id: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/assistants/delete",
        "json": {
            "assistant_id": assistant_id,
        },
        "headers": headers,
    }


def delete_assistant_sync(
    client: httpx.Client,
    *,
    assistant_id: str,
    access_token: Optional[str] = None,
) -> AssistantDelete:
    """Delete assistant."""
    kwargs = _delete_assistant_kwargs(assistant_id=assistant_id, access_token=access_token)
    return execute_request_sync(client, kwargs, AssistantDelete)


async def delete_assistant_async(
    client: httpx.AsyncClient,
    *,
    assistant_id: str,
    access_token: Optional[str] = None,
) -> AssistantDelete:
    """Delete assistant."""
    kwargs = _delete_assistant_kwargs(assistant_id=assistant_id, access_token=access_token)
    return await execute_request_async(client, kwargs, AssistantDelete)


def _delete_assistant_file_kwargs(
    *,
    assistant_id: str,
    file_id: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/assistants/files/delete",
        "json": {
            "assistant_id": assistant_id,
            "file_id": file_id,
        },
        "headers": headers,
    }


def delete_assistant_file_sync(
    client: httpx.Client,
    *,
    assistant_id: str,
    file_id: str,
    access_token: Optional[str] = None,
) -> AssistantFileDelete:
    """Delete assistant file."""
    kwargs = _delete_assistant_file_kwargs(assistant_id=assistant_id, file_id=file_id, access_token=access_token)
    return execute_request_sync(client, kwargs, AssistantFileDelete)


async def delete_assistant_file_async(
    client: httpx.AsyncClient,
    *,
    assistant_id: str,
    file_id: str,
    access_token: Optional[str] = None,
) -> AssistantFileDelete:
    """Delete assistant file."""
    kwargs = _delete_assistant_file_kwargs(assistant_id=assistant_id, file_id=file_id, access_token=access_token)
    return await execute_request_async(client, kwargs, AssistantFileDelete)
