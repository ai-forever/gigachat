import base64
import warnings
from http import HTTPStatus
from typing import Any, Dict, Literal, Optional

import httpx

from gigachat._types import FileTypes
from gigachat.api.utils import build_headers, build_x_headers, execute_request_async, execute_request_sync
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.http_client import AsyncHttpClient
from gigachat.models.files import DeletedFile, File, UploadedFile, UploadedFiles


def _get_file_kwargs(
    *,
    file: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    access_token: Optional[str] = None,
) -> UploadedFile:
    """Return information about a file."""
    kwargs = _get_file_kwargs(file=file, access_token=access_token)
    return execute_request_sync(client, kwargs, UploadedFile)


async def get_file_async(
    client: AsyncHttpClient,
    *,
    file: str,
    access_token: Optional[str] = None,
) -> UploadedFile:
    """Return information about a file."""
    kwargs = _get_file_kwargs(file=file, access_token=access_token)
    return await execute_request_async(client, kwargs, UploadedFile)


def _get_files_kwargs(
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    return {
        "method": "GET",
        "url": "/files",
        "headers": headers,
    }


def get_files_sync(
    client: httpx.Client,
    *,
    access_token: Optional[str] = None,
) -> UploadedFiles:
    """Return a list of uploaded files."""
    kwargs = _get_files_kwargs(access_token=access_token)
    return execute_request_sync(client, kwargs, UploadedFiles)


async def get_files_async(
    client: AsyncHttpClient,
    *,
    access_token: Optional[str] = None,
) -> UploadedFiles:
    """Return a list of uploaded files."""
    kwargs = _get_files_kwargs(access_token=access_token)
    return await execute_request_async(client, kwargs, UploadedFiles)


def _upload_file_kwargs(
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    access_token: Optional[str] = None,
) -> UploadedFile:
    """Upload a file."""
    kwargs = _upload_file_kwargs(file=file, purpose=purpose, access_token=access_token)
    return execute_request_sync(client, kwargs, UploadedFile)


async def upload_file_async(
    client: AsyncHttpClient,
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: Optional[str] = None,
) -> UploadedFile:
    """Upload a file."""
    kwargs = _upload_file_kwargs(file=file, purpose=purpose, access_token=access_token)
    return await execute_request_async(client, kwargs, UploadedFile)


def _delete_file_kwargs(
    *,
    file: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
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
    access_token: Optional[str] = None,
) -> DeletedFile:
    """Delete a file."""
    kwargs = _delete_file_kwargs(file=file, access_token=access_token)
    return execute_request_sync(client, kwargs, DeletedFile)


async def delete_file_async(
    client: AsyncHttpClient,
    *,
    file: str,
    access_token: Optional[str] = None,
) -> DeletedFile:
    """Delete a file."""
    kwargs = _delete_file_kwargs(file=file, access_token=access_token)
    return await execute_request_async(client, kwargs, DeletedFile)


def _get_file_content_kwargs(
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Accept"] = "application/jpg"
    return {
        "method": "GET",
        "url": f"/files/{file_id}/content",
        "headers": headers,
    }


def _build_file_content_response(response: httpx.Response) -> File:
    if response.status_code == HTTPStatus.OK:
        x_headers = build_x_headers(response)
        return File(x_headers=x_headers, content=base64.b64encode(response.content).decode())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def get_file_content_sync(
    client: httpx.Client,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> File:
    """Return file content in base64 encoding."""
    kwargs = _get_file_content_kwargs(access_token=access_token, file_id=file_id)
    response = client.request(**kwargs)
    return _build_file_content_response(response)


async def get_file_content_async(
    client: AsyncHttpClient,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> File:
    """Return file content in base64 encoding."""
    kwargs = _get_file_content_kwargs(access_token=access_token, file_id=file_id)
    response = await client.request(**kwargs)
    return _build_file_content_response(response)


def get_image_sync(
    client: httpx.Client,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> File:
    """Use `get_file_content_sync`; this alias is deprecated."""
    warnings.warn(
        "Function 'get_image_sync' is deprecated, use 'get_file_content_sync'",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_file_content_sync(client, file_id=file_id, access_token=access_token)


async def get_image_async(
    client: AsyncHttpClient,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> File:
    """Use `get_file_content_async`; this alias is deprecated."""
    warnings.warn(
        "Function 'get_image_async' is deprecated, use 'get_file_content_async'",
        DeprecationWarning,
        stacklevel=2,
    )
    return await get_file_content_async(client, file_id=file_id, access_token=access_token)
