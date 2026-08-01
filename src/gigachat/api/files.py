import base64
from http import HTTPStatus
from typing import Any, Dict, Literal, Optional

import httpx

from gigachat._types import FileTypes
from gigachat.api.utils import (
    _raise_for_status,
    build_headers,
    build_x_headers,
    execute_request_async,
    execute_request_sync,
)
from gigachat.models.files import DeletedFile, DownloadedFile, Image, UploadedFile, UploadedFiles


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
    client: httpx.AsyncClient,
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
    client: httpx.AsyncClient,
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
    client: httpx.AsyncClient,
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
    client: httpx.AsyncClient,
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
    accept: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    if accept is not None:
        headers["Accept"] = accept
    return {
        "method": "GET",
        "url": f"/files/{file_id}/content",
        "headers": headers,
    }


def _build_file_content_response(response: httpx.Response) -> DownloadedFile:
    if response.status_code != HTTPStatus.OK:
        _raise_for_status(response.url, response.status_code, response.content, response.headers)

    return DownloadedFile(
        x_headers=build_x_headers(response),
        content=response.content,
        content_type=response.headers.get("content-type"),
        content_disposition=response.headers.get("content-disposition"),
    )


def get_file_content_sync(
    client: httpx.Client,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> DownloadedFile:
    """Return raw file content and response metadata."""
    kwargs = _get_file_content_kwargs(access_token=access_token, file_id=file_id)
    response = client.request(**kwargs)
    return _build_file_content_response(response)


async def get_file_content_async(
    client: httpx.AsyncClient,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> DownloadedFile:
    """Return raw file content and response metadata."""
    kwargs = _get_file_content_kwargs(access_token=access_token, file_id=file_id)
    response = await client.request(**kwargs)
    return _build_file_content_response(response)


def _build_image_response(response: httpx.Response) -> Image:
    downloaded = _build_file_content_response(response)
    return Image(x_headers=downloaded.x_headers, content=base64.b64encode(downloaded.content).decode())


def get_image_sync(
    client: httpx.Client,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> Image:
    """Return an image in base64 encoding."""
    kwargs = _get_file_content_kwargs(access_token=access_token, file_id=file_id, accept="application/jpg")
    response = client.request(**kwargs)
    return _build_image_response(response)


async def get_image_async(
    client: httpx.AsyncClient,
    *,
    file_id: str,
    access_token: Optional[str] = None,
) -> Image:
    """Return an image in base64 encoding."""
    kwargs = _get_file_content_kwargs(access_token=access_token, file_id=file_id, accept="application/jpg")
    response = await client.request(**kwargs)
    return _build_image_response(response)
