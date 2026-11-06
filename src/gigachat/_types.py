from collections.abc import Mapping
from typing import IO

FileContent = IO[bytes] | bytes | str
FileTypes = (
    FileContent
    | tuple[str | None, FileContent]
    | tuple[str | None, FileContent, str | None]
    | tuple[str | None, FileContent, str | None, Mapping[str, str]]
)
