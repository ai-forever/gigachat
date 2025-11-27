from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import Model, Models


def _get_models_kwargs(
    *,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": "/models",
        "headers": headers,
    }


def get_models_sync(
    client: httpx.Client,
    *,
    access_token: Optional[str] = None,
) -> Models:
    """Возвращает массив объектов с данными доступных моделей"""
    kwargs = _get_models_kwargs(access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Models)


async def get_models_async(
    client: httpx.AsyncClient,
    *,
    access_token: Optional[str] = None,
) -> Models:
    """Возвращает массив объектов с данными доступных моделей"""
    kwargs = _get_models_kwargs(access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Models)


def _get_model_kwargs(
    *,
    model: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": f"/models/{model}",
        "headers": headers,
    }


def get_model_sync(
    client: httpx.Client,
    *,
    model: str,
    access_token: Optional[str] = None,
) -> Model:
    """Возвращает объект с описанием указанной модели"""
    kwargs = _get_model_kwargs(model=model, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, Model)


async def get_model_async(
    client: httpx.AsyncClient,
    *,
    model: str,
    access_token: Optional[str] = None,
) -> Model:
    """Возвращает объект с описанием указанной модели"""
    kwargs = _get_model_kwargs(model=model, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, Model)

