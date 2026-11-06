"""TLS configuration shared by native and optional transports."""

import ssl

import httpx2


def build_ssl_context(
    *,
    verify_ssl_certs: bool = True,
    ssl_context: ssl.SSLContext | None = None,
    ca_bundle_file: str | None = None,
    cert_file: str | None = None,
    key_file: str | None = None,
    key_file_password: str | None = None,
    trust_env: bool = True,
    for_auth: bool = False,
    auth_ssl_context: ssl.SSLContext | None = None,
) -> ssl.SSLContext | bool:
    """Build a TLS context without modifying a caller-owned context."""
    selected = auth_ssl_context if for_auth and auth_ssl_context is not None else ssl_context
    client_cert = None if for_auth else cert_file
    if not for_auth and (key_file or key_file_password) and not cert_file:
        raise ValueError("key_file and key_file_password require cert_file")
    if selected is not None:
        if ca_bundle_file or client_cert or not verify_ssl_certs:
            raise ValueError("ssl_context cannot be combined with CA, client certificate, or verify_ssl_certs=False")
        return selected
    if ca_bundle_file and not verify_ssl_certs:
        raise ValueError("ca_bundle_file cannot be combined with verify_ssl_certs=False")
    if ca_bundle_file:
        context = ssl.create_default_context(cafile=ca_bundle_file)
    else:
        context = httpx2.create_ssl_context(verify=verify_ssl_certs, trust_env=trust_env)
    if client_cert:
        context.load_cert_chain(client_cert, key_file, key_file_password)
    return context
