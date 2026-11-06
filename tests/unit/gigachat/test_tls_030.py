import ssl
from pathlib import Path
from typing import TypedDict
from unittest.mock import Mock

import pytest

from gigachat._tls import build_ssl_context


def test_explicit_context_is_returned_unchanged() -> None:
    context = ssl.create_default_context()
    assert build_ssl_context(ssl_context=context) is context
    with pytest.raises(ValueError, match="ssl_context"):
        build_ssl_context(ssl_context=context, cert_file="cert.pem")


def test_auth_does_not_load_api_client_certificate(monkeypatch: pytest.MonkeyPatch) -> None:
    context = Mock()
    monkeypatch.setattr("gigachat._tls.httpx2.create_ssl_context", lambda **kwargs: context)
    assert build_ssl_context(cert_file="cert.pem", key_file="key.pem", for_auth=True) is context
    context.load_cert_chain.assert_not_called()
    build_ssl_context(cert_file="cert.pem", key_file="key.pem", key_file_password="password")
    context.load_cert_chain.assert_called_once_with("cert.pem", "key.pem", "password")


def test_invalid_ca_does_not_disable_verification() -> None:
    with pytest.raises((OSError, ssl.SSLError)):
        build_ssl_context(ca_bundle_file="/nonexistent/gigachat-ca.pem")


@pytest.fixture(scope="module")
def certificate_files(tmp_path_factory: pytest.TempPathFactory) -> Path:
    import subprocess

    root = tmp_path_factory.mktemp("tls-wire")

    def openssl(*args: str) -> None:
        subprocess.run(["openssl", *args], cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603, S607

    config = root / "openssl.cnf"
    config.write_text(
        "[req]\ndistinguished_name=dn\nx509_extensions=ext\nprompt=no\n"
        "[dn]\nCN=localhost\n[ext]\nbasicConstraints=critical,CA:TRUE\n"
        "subjectAltName=DNS:localhost,IP:127.0.0.1\n"
    )
    openssl(
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-days",
        "1",
        "-keyout",
        "ca.key",
        "-out",
        "ca.pem",
        "-config",
        str(config),
    )
    openssl(
        "req",
        "-newkey",
        "rsa:2048",
        "-passout",
        "pass:wire-password",
        "-keyout",
        "client.key",
        "-out",
        "client.csr",
        "-subj",
        "/CN=client",
    )
    openssl(
        "x509",
        "-req",
        "-in",
        "client.csr",
        "-CA",
        "ca.pem",
        "-CAkey",
        "ca.key",
        "-CAcreateserial",
        "-days",
        "1",
        "-out",
        "client.pem",
    )
    return root


@pytest.mark.parametrize("backend", ["httpx2", "aiohttp"])
async def test_tls_wire_custom_ca_environment_explicit_context_and_mtls(
    backend: str, certificate_files: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    import httpx2

    from gigachat._http_client import DefaultAioHttpClient, DefaultAsyncHttpxClient

    if backend == "aiohttp":
        pytest.importorskip("aiohttp")
    cls = DefaultAioHttpClient if backend == "aiohttp" else DefaultAsyncHttpxClient
    root = certificate_files
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(str(root / "ca.pem"), str(root / "ca.key"))
    server_context.load_verify_locations(cafile=str(root / "ca.pem"))
    server_context.verify_mode = ssl.CERT_REQUIRED

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readuntil(b"\r\n\r\n")
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle, "127.0.0.1", 0, ssl=server_context)
    url = f"https://127.0.0.1:{server.sockets[0].getsockname()[1]}/"
    try:
        monkeypatch.setenv("SSL_CERT_FILE", str(root / "ca.pem"))

        class CertificateParams(TypedDict):
            cert_file: str
            key_file: str
            key_file_password: str

        common: CertificateParams = {
            "cert_file": str(root / "client.pem"),
            "key_file": str(root / "client.key"),
            "key_file_password": "wire-password",
        }
        contexts = [
            build_ssl_context(ca_bundle_file=str(root / "ca.pem"), trust_env=False, **common),
            build_ssl_context(trust_env=True, **common),
        ]
        explicit = ssl.create_default_context(cafile=str(root / "ca.pem"))
        explicit.load_cert_chain(common["cert_file"], common["key_file"], common["key_file_password"])
        contexts.append(build_ssl_context(ssl_context=explicit, trust_env=False))
        assert contexts[-1] is explicit
        for context in contexts:
            async with cls(verify=context, trust_env=False) as client:
                response = await client.get(url)
                assert response.text == "ok"
        # A client without the certificate must not pass the server's mTLS policy.
        context = build_ssl_context(ca_bundle_file=str(root / "ca.pem"), trust_env=False)
        async with cls(verify=context, trust_env=False) as client:
            with pytest.raises(httpx2.TransportError):
                await client.get(url)
        # A CA supplied only via environment is ignored with trust_env=False.
        context = build_ssl_context(trust_env=False, **common)
        async with cls(verify=context, trust_env=False) as client:
            with pytest.raises(httpx2.TransportError):
                await client.get(url)
    finally:
        server.close()
        await server.wait_closed()
