import base64
from http import HTTPStatus
from typing import Any, Literal
from urllib.parse import quote

import httpx2 as httpx

from gigachat._core.execution import request_async, request_sync, send_async, send_sync
from gigachat._core.request import FileTypes
from gigachat._core.response import AsyncStreamingResponse, StreamingResponse, _raise_for_status
from gigachat.api.utils import build_headers, build_x_headers, execute_request_async, execute_request_sync
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models.files import DeletedFile, Image, UploadedFile, UploadedFiles


def _get_file_kwargs(
    *,
    file: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    return {
        "method": "GET",
        "url": f"/files/{file}",
        "headers": headers,
    }


def get_file_sync(
    client: httpx.Client,
    *,
    file: str,
    access_token: str | None = None,
) -> UploadedFile:
    """Return information about a file."""
    kwargs = _get_file_kwargs(file=file, access_token=access_token)
    return execute_request_sync(client, kwargs, UploadedFile)


async def get_file_async(
    client: httpx.AsyncClient,
    *,
    file: str,
    access_token: str | None = None,
) -> UploadedFile:
    """Return information about a file."""
    kwargs = _get_file_kwargs(file=file, access_token=access_token)
    return await execute_request_async(client, kwargs, UploadedFile)


def _get_files_kwargs(
    *,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    return {
        "method": "GET",
        "url": "/files",
        "headers": headers,
    }


def get_files_sync(
    client: httpx.Client,
    *,
    access_token: str | None = None,
) -> UploadedFiles:
    """Return a list of uploaded files."""
    kwargs = _get_files_kwargs(access_token=access_token)
    return execute_request_sync(client, kwargs, UploadedFiles)


async def get_files_async(
    client: httpx.AsyncClient,
    *,
    access_token: str | None = None,
) -> UploadedFiles:
    """Return a list of uploaded files."""
    kwargs = _get_files_kwargs(access_token=access_token)
    return await execute_request_async(client, kwargs, UploadedFiles)


def _upload_file_kwargs(
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    return {
        "method": "POST",
        "url": "/files",
        "files": {"file": file},
        "data": {"purpose": purpose},
        "headers": headers,
    }


def upload_file_sync(
    client: httpx.Client,
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: str | None = None,
) -> UploadedFile:
    """Upload a file."""
    kwargs = _upload_file_kwargs(file=file, purpose=purpose, access_token=access_token)
    return execute_request_sync(client, kwargs, UploadedFile)


async def upload_file_async(
    client: httpx.AsyncClient,
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: str | None = None,
) -> UploadedFile:
    """Upload a file."""
    kwargs = _upload_file_kwargs(file=file, purpose=purpose, access_token=access_token)
    return await execute_request_async(client, kwargs, UploadedFile)


def _delete_file_kwargs(
    *,
    file: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    return {
        "method": "POST",
        "url": f"/files/{file}/delete",
        "files": {"file": file},
        "data": {},
        "headers": build_headers(access_token),
    }


def delete_file_sync(
    client: httpx.Client,
    *,
    file: str,
    access_token: str | None = None,
) -> DeletedFile:
    """Delete a file."""
    kwargs = _delete_file_kwargs(file=file, access_token=access_token)
    return execute_request_sync(client, kwargs, DeletedFile)


async def delete_file_async(
    client: httpx.AsyncClient,
    *,
    file: str,
    access_token: str | None = None,
) -> DeletedFile:
    """Delete a file."""
    kwargs = _delete_file_kwargs(file=file, access_token=access_token)
    return await execute_request_async(client, kwargs, DeletedFile)


def _get_image_kwargs(
    *,
    file_id: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    headers = build_headers(access_token)
    headers["Accept"] = "application/jpg"
    return {
        "method": "GET",
        "url": f"/files/{file_id}/content",
        "headers": headers,
    }


def _build_image_response(response: httpx.Response) -> Image:
    if response.status_code == HTTPStatus.OK:
        x_headers = build_x_headers(response)
        return Image(x_headers=x_headers, content=base64.b64encode(response.content).decode())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def get_image_sync(
    client: httpx.Client,
    *,
    file_id: str,
    access_token: str | None = None,
) -> Image:
    """Return an image in base64 encoding."""
    kwargs = _get_image_kwargs(access_token=access_token, file_id=file_id)
    response = request_sync(client, **kwargs)
    return _build_image_response(response)


async def get_image_async(
    client: httpx.AsyncClient,
    *,
    file_id: str,
    access_token: str | None = None,
) -> Image:
    """Return an image in base64 encoding."""
    kwargs = _get_image_kwargs(access_token=access_token, file_id=file_id)
    response = await request_async(client, **kwargs)
    return _build_image_response(response)


def update_file_access_sync(
    client: httpx.Client, *, file_ids: list[str], access_policy: str, access_token: str | None = None
) -> UploadedFiles:
    """Update the access policy of uploaded files."""
    kwargs = _get_update_file_access_kwargs(file_ids=file_ids, access_policy=access_policy, access_token=access_token)
    return execute_request_sync(client, kwargs, UploadedFiles)


async def update_file_access_async(
    client: httpx.AsyncClient, *, file_ids: list[str], access_policy: str, access_token: str | None = None
) -> UploadedFiles:
    """Update the access policy of uploaded files."""
    kwargs = _get_update_file_access_kwargs(file_ids=file_ids, access_policy=access_policy, access_token=access_token)
    return await execute_request_async(client, kwargs, UploadedFiles)


def _get_file_content_kwargs(*, file_id: str, access_token: str | None = None) -> dict[str, Any]:
    return {
        "method": "GET",
        "url": f"/files/{quote(file_id, safe='')}/content",
        "headers": {**build_headers(access_token), "Accept": "application/octet-stream"},
    }


def stream_file_content_sync(
    client: httpx.Client, *, file_id: str, access_token: str | None = None
) -> StreamingResponse[bytes]:
    """Open and validate a binary file response."""
    response = send_sync(client, stream=True, **_get_file_content_kwargs(file_id=file_id, access_token=access_token))
    wrapped = StreamingResponse(response, lambda result: result.content)
    if response.status_code != 200:
        _raise_for_status(response.url, response.status_code, wrapped.read(), response.headers)
    return wrapped


async def stream_file_content_async(
    client: httpx.AsyncClient, *, file_id: str, access_token: str | None = None
) -> AsyncStreamingResponse[bytes]:
    """Open and validate a binary file response."""
    response = await send_async(
        client, stream=True, **_get_file_content_kwargs(file_id=file_id, access_token=access_token)
    )
    wrapped = AsyncStreamingResponse(response, lambda result: result.content)
    if response.status_code != 200:
        _raise_for_status(response.url, response.status_code, await wrapped.read(), response.headers)
    return wrapped


def _get_update_file_access_kwargs(
    *, file_ids: list[str], access_policy: str, access_token: str | None
) -> dict[str, Any]:
    return {
        "method": "POST",
        "url": "/files/access",
        "headers": build_headers(access_token),
        "json": {"file_ids": file_ids, "access_policy": access_policy},
    }
