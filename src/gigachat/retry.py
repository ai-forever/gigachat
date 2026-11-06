"""Classify failures for the shared executor retry policy."""

import ssl

import httpx2

from gigachat.exceptions import ResponseError


def _certificate_failure(exception: BaseException) -> bool:
    seen: set[int] = set()
    pending = [exception]
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(current):
            return True
        pending.extend(error for error in (current.__cause__, current.__context__) if error is not None)
    return False


def _should_retry(exception: Exception, retry_codes: tuple[int, ...]) -> bool:
    """Retry explicit statuses and transient network failures before response delivery."""
    if isinstance(exception, ResponseError):
        return exception.status_code in retry_codes
    if _certificate_failure(exception):
        return False
    return isinstance(
        exception,
        (
            httpx2.ConnectError,
            httpx2.ReadError,
            httpx2.WriteError,
            httpx2.CloseError,
            httpx2.ConnectTimeout,
            httpx2.ReadTimeout,
            httpx2.WriteTimeout,
            httpx2.RemoteProtocolError,
        ),
    )
