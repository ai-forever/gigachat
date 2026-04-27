import warnings
from typing import Any, Dict, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from tests.constants import BASE_URL, FILE

ResourceCase = Tuple[str, str, str, str, Tuple[Any, ...], Dict[str, Any], str]

SYNC_RESOURCE_CASES: Tuple[ResourceCase, ...] = (
    (
        "get_models",
        "models",
        "list",
        "gigachat.resources.models.models.get_models_sync",
        (),
        {},
        r"client\.models\.list\(\)",
    ),
    (
        "get_model",
        "models",
        "retrieve",
        "gigachat.resources.models.models.get_model_sync",
        ("model",),
        {},
        r"client\.models\.retrieve\(\.\.\.\)",
    ),
    (
        "embeddings",
        "embeddings",
        "create",
        "gigachat.resources.embeddings.embeddings.embeddings_sync",
        (["text"],),
        {"model": "model"},
        r"client\.embeddings\.create\(\.\.\.\)",
    ),
    (
        "upload_file",
        "files",
        "upload",
        "gigachat.resources.files.files.upload_file_sync",
        (),
        {"file": FILE},
        r"client\.files\.upload\(\.\.\.\)",
    ),
    (
        "get_file",
        "files",
        "retrieve",
        "gigachat.resources.files.files.get_file_sync",
        ("1",),
        {},
        r"client\.files\.retrieve\(\.\.\.\)",
    ),
    (
        "get_files",
        "files",
        "list",
        "gigachat.resources.files.files.get_files_sync",
        (),
        {},
        r"client\.files\.list\(\)",
    ),
    (
        "delete_file",
        "files",
        "delete",
        "gigachat.resources.files.files.delete_file_sync",
        ("1",),
        {},
        r"client\.files\.delete\(\.\.\.\)",
    ),
    (
        "get_image",
        "files",
        "retrieve_image",
        "gigachat.resources.files.files.get_image_sync",
        ("img_file",),
        {},
        r"client\.files\.retrieve_image\(\.\.\.\)",
    ),
    (
        "tokens_count",
        "tokens",
        "count",
        "gigachat.resources.tokens.tools.tokens_count_sync",
        (["text"],),
        {"model": "model"},
        r"client\.tokens\.count\(\.\.\.\)",
    ),
    (
        "get_balance",
        "balance",
        "get",
        "gigachat.resources.balance.tools.get_balance_sync",
        (),
        {},
        r"client\.balance\.get\(\)",
    ),
    (
        "openapi_function_convert",
        "functions",
        "convert_openapi",
        "gigachat.resources.functions.tools.functions_convert_sync",
        ("openapi",),
        {},
        r"client\.functions\.convert_openapi\(\.\.\.\)",
    ),
    (
        "check_ai",
        "ai_check",
        "check",
        "gigachat.resources.ai_check.tools.ai_check_sync",
        ("text", "model"),
        {},
        r"client\.ai_check\.check\(\.\.\.\)",
    ),
)

ASYNC_RESOURCE_CASES: Tuple[ResourceCase, ...] = (
    (
        "aget_models",
        "a_models",
        "list",
        "gigachat.resources.models.models.get_models_async",
        (),
        {},
        r"client\.a_models\.list\(\)",
    ),
    (
        "aget_model",
        "a_models",
        "retrieve",
        "gigachat.resources.models.models.get_model_async",
        ("model",),
        {},
        r"client\.a_models\.retrieve\(\.\.\.\)",
    ),
    (
        "aembeddings",
        "a_embeddings",
        "create",
        "gigachat.resources.embeddings.embeddings.embeddings_async",
        (["text"],),
        {"model": "model"},
        r"client\.a_embeddings\.create\(\.\.\.\)",
    ),
    (
        "aupload_file",
        "a_files",
        "upload",
        "gigachat.resources.files.files.upload_file_async",
        (),
        {"file": FILE},
        r"client\.a_files\.upload\(\.\.\.\)",
    ),
    (
        "aget_file",
        "a_files",
        "retrieve",
        "gigachat.resources.files.files.get_file_async",
        ("1",),
        {},
        r"client\.a_files\.retrieve\(\.\.\.\)",
    ),
    (
        "aget_files",
        "a_files",
        "list",
        "gigachat.resources.files.files.get_files_async",
        (),
        {},
        r"client\.a_files\.list\(\)",
    ),
    (
        "adelete_file",
        "a_files",
        "delete",
        "gigachat.resources.files.files.delete_file_async",
        ("1",),
        {},
        r"client\.a_files\.delete\(\.\.\.\)",
    ),
    (
        "aget_image",
        "a_files",
        "retrieve_image",
        "gigachat.resources.files.files.get_image_async",
        ("img_file",),
        {},
        r"client\.a_files\.retrieve_image\(\.\.\.\)",
    ),
    (
        "atokens_count",
        "a_tokens",
        "count",
        "gigachat.resources.tokens.tools.tokens_count_async",
        (["text"],),
        {"model": "model"},
        r"client\.a_tokens\.count\(\.\.\.\)",
    ),
    (
        "aget_balance",
        "a_balance",
        "get",
        "gigachat.resources.balance.tools.get_balance_async",
        (),
        {},
        r"client\.a_balance\.get\(\)",
    ),
    (
        "aopenapi_function_convert",
        "a_functions",
        "convert_openapi",
        "gigachat.resources.functions.tools.functions_convert_async",
        ("openapi",),
        {},
        r"client\.a_functions\.convert_openapi\(\.\.\.\)",
    ),
    (
        "acheck_ai",
        "a_ai_check",
        "check",
        "gigachat.resources.ai_check.tools.ai_check_async",
        ("text", "model"),
        {},
        r"client\.a_ai_check\.check\(\.\.\.\)",
    ),
)


def _assert_no_deprecation(caught: Any) -> None:
    deprecated = [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]
    assert deprecated == []


def _call_sync_resource(
    client: GigaChatSyncClient,
    resource_name: str,
    method_name: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Any:
    resource = getattr(client, resource_name)
    return getattr(resource, method_name)(*args, **kwargs)


def _call_sync_shim(
    client: GigaChatSyncClient,
    shim_name: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Any:
    shim = getattr(client, shim_name)
    return shim(*args, **kwargs)


async def _call_async_resource(
    client: GigaChatAsyncClient,
    resource_name: str,
    method_name: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Any:
    resource = getattr(client, resource_name)
    return await getattr(resource, method_name)(*args, **kwargs)


async def _call_async_shim(
    client: GigaChatAsyncClient,
    shim_name: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Any:
    shim = getattr(client, shim_name)
    return await shim(*args, **kwargs)


@pytest.mark.parametrize(
    ("shim_name", "resource_name", "method_name", "patch_target", "args", "kwargs", "warning_match"),
    SYNC_RESOURCE_CASES,
)
def test_sync_resource_paths_do_not_warn_and_use_low_level_api(
    shim_name: str,
    resource_name: str,
    method_name: str,
    patch_target: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    warning_match: str,
) -> None:
    del shim_name, warning_match
    response = object()

    with patch(patch_target, MagicMock(return_value=response)) as api_mock:
        with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", DeprecationWarning)
                result = _call_sync_resource(client, resource_name, method_name, args, kwargs)

    assert result is response
    api_mock.assert_called_once()
    _assert_no_deprecation(caught)


@pytest.mark.parametrize(
    ("shim_name", "resource_name", "method_name", "patch_target", "args", "kwargs", "warning_match"),
    SYNC_RESOURCE_CASES,
)
def test_sync_deprecated_root_shims_warn_and_use_same_low_level_api(
    shim_name: str,
    resource_name: str,
    method_name: str,
    patch_target: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    warning_match: str,
) -> None:
    del resource_name, method_name
    response = object()

    with patch(patch_target, MagicMock(return_value=response)) as api_mock:
        with GigaChatSyncClient(base_url=BASE_URL, model="model") as client:
            with pytest.warns(DeprecationWarning, match=warning_match):
                result = _call_sync_shim(client, shim_name, args, kwargs)

    assert result is response
    api_mock.assert_called_once()


@pytest.mark.parametrize(
    ("shim_name", "resource_name", "method_name", "patch_target", "args", "kwargs", "warning_match"),
    ASYNC_RESOURCE_CASES,
)
async def test_async_resource_paths_do_not_warn_and_use_low_level_api(
    shim_name: str,
    resource_name: str,
    method_name: str,
    patch_target: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    warning_match: str,
) -> None:
    del shim_name, warning_match
    response = object()

    with patch(patch_target, AsyncMock(return_value=response)) as api_mock:
        async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", DeprecationWarning)
                result = await _call_async_resource(client, resource_name, method_name, args, kwargs)

    assert result is response
    api_mock.assert_awaited_once()
    _assert_no_deprecation(caught)


@pytest.mark.parametrize(
    ("shim_name", "resource_name", "method_name", "patch_target", "args", "kwargs", "warning_match"),
    ASYNC_RESOURCE_CASES,
)
async def test_async_deprecated_root_shims_warn_and_use_same_low_level_api(
    shim_name: str,
    resource_name: str,
    method_name: str,
    patch_target: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    warning_match: str,
) -> None:
    del resource_name, method_name
    response = object()

    with patch(patch_target, AsyncMock(return_value=response)) as api_mock:
        async with GigaChatAsyncClient(base_url=BASE_URL, model="model") as client:
            with pytest.warns(DeprecationWarning, match=warning_match):
                result = await _call_async_shim(client, shim_name, args, kwargs)

    assert result is response
    api_mock.assert_awaited_once()
