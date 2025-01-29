from typing import Any, Dict, List, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import Function
from gigachat.models.assistants import CreateAssistant


def _get_kwargs(
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
        data["functions"] = [function.dict(exclude_none=True, by_alias=True) for function in functions]

    return {
        "method": "POST",
        "url": "/assistants",
        "json": data,
        "headers": headers,
    }


def sync(
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
    """Создание ассистента"""
    kwargs = _get_kwargs(
        model=model,
        name=name,
        description=description,
        instructions=instructions,
        file_ids=file_ids,
        functions=functions,
        metadata=metadata,
        access_token=access_token,
    )
    response = client.request(**kwargs)
    return build_response(response, CreateAssistant)


async def asyncio(
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
    """Создание ассистента"""
    kwargs = _get_kwargs(
        model=model,
        name=name,
        description=description,
        instructions=instructions,
        file_ids=file_ids,
        functions=functions,
        metadata=metadata,
        access_token=access_token,
    )
    response = await client.request(**kwargs)
    return build_response(response, CreateAssistant)
