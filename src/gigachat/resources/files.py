from typing import TYPE_CHECKING, Literal

from gigachat._types import FileTypes
from gigachat.api import files
from gigachat.authentication import _awith_auth, _with_auth
from gigachat.models.files import DeletedFile, File, UploadedFile, UploadedFiles
from gigachat.retry import _awith_retry, _with_retry

from ._utils import warn_deprecated_resource_api

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class FilesSyncResource:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @_with_retry
    @_with_auth
    def upload(
        self,
        file: FileTypes,
        purpose: Literal["general", "assistant"] = "general",
    ) -> UploadedFile:
        """Upload a file."""
        return files.upload_file_sync(
            self._base_client._client,
            file=file,
            purpose=purpose,
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
    def retrieve(self, file: str) -> UploadedFile:
        """Return information about a file."""
        return files.get_file_sync(self._base_client._client, file=file, access_token=self._base_client.token)

    @_with_retry
    @_with_auth
    def list(self) -> UploadedFiles:
        """Return a list of uploaded files."""
        return files.get_files_sync(self._base_client._client, access_token=self._base_client.token)

    @_with_retry
    @_with_auth
    def delete(self, file: str) -> DeletedFile:
        """Delete a file."""
        return files.delete_file_sync(self._base_client._client, file=file, access_token=self._base_client.token)

    @_with_retry
    @_with_auth
    def retrieve_content(self, file_id: str) -> File:
        """Return file content in base64 encoding."""
        return files.get_file_content_sync(
            self._base_client._client,
            file_id=file_id,
            access_token=self._base_client.token,
        )

    def retrieve_image(self, file_id: str) -> File:
        """Return file content via deprecated image compatibility alias."""
        warn_deprecated_resource_api("client.files.retrieve_image(...)", "client.files.retrieve_content(...)")
        return self.retrieve_content(file_id)


class FilesAsyncResource:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @_awith_retry
    @_awith_auth
    async def upload(
        self,
        file: FileTypes,
        purpose: Literal["general", "assistant"] = "general",
    ) -> UploadedFile:
        """Upload a file."""
        return await files.upload_file_async(
            self._base_client._aclient,
            file=file,
            purpose=purpose,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def retrieve(self, file: str) -> UploadedFile:
        """Return information about a file."""
        return await files.get_file_async(self._base_client._aclient, file=file, access_token=self._base_client.token)

    @_awith_retry
    @_awith_auth
    async def list(self) -> UploadedFiles:
        """Return a list of uploaded files."""
        return await files.get_files_async(self._base_client._aclient, access_token=self._base_client.token)

    @_awith_retry
    @_awith_auth
    async def delete(self, file: str) -> DeletedFile:
        """Delete a file."""
        return await files.delete_file_async(
            self._base_client._aclient,
            file=file,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def retrieve_content(self, file_id: str) -> File:
        """Return file content in base64 encoding."""
        return await files.get_file_content_async(
            self._base_client._aclient,
            file_id=file_id,
            access_token=self._base_client.token,
        )

    async def retrieve_image(self, file_id: str) -> File:
        """Return file content via deprecated image compatibility alias."""
        warn_deprecated_resource_api("client.a_files.retrieve_image(...)", "client.a_files.retrieve_content(...)")
        return await self.retrieve_content(file_id)
