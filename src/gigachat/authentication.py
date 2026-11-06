"""Retain public authentication protocol names for compatibility."""

from typing import Protocol, runtime_checkable

__all__ = ["AuthClientProtocol", "AsyncAuthClientProtocol"]


@runtime_checkable
class AuthClientProtocol(Protocol):
    """Protocol for synchronous authentication client."""

    @property
    def _use_auth(self) -> bool: ...

    def _is_token_usable(self) -> bool: ...

    def _reset_token(self) -> None: ...

    def _update_token(self) -> None: ...


@runtime_checkable
class AsyncAuthClientProtocol(Protocol):
    """Protocol for asynchronous authentication client."""

    @property
    def _use_auth(self) -> bool: ...

    def _is_token_usable(self) -> bool: ...

    def _reset_token(self) -> None: ...

    async def _aupdate_token(self) -> None: ...
