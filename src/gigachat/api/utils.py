from typing import Dict, Optional

from gigachat.context import (
    authorization_cvar,
    client_id_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
)

USER_AGENT = "GigaChat-python-lib"


def build_headers(access_token: Optional[str] = None) -> Dict[str, str]:
    headers = {}

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    headers["User-Agent"] = USER_AGENT

    authorization = authorization_cvar.get()
    session_id = session_id_cvar.get()
    request_id = request_id_cvar.get()
    service_id = service_id_cvar.get()
    operation_id = operation_id_cvar.get()
    client_id = client_id_cvar.get()

    if authorization:
        headers["Authorization"] = authorization
    if session_id:
        headers["X-Session-ID"] = session_id
    if request_id:
        headers["X-Request-ID"] = request_id
    if service_id:
        headers["X-Service-ID"] = service_id
    if operation_id:
        headers["X-Operation-ID"] = operation_id
    if client_id:
        headers["X-Client-ID"] = client_id
    return headers
