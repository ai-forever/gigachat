"""Integration tests for /models endpoint using VCR cassettes."""

import pytest

from gigachat import GigaChat, Model, Models, NotFoundError


@pytest.mark.integration
@pytest.mark.vcr
def test_get_models(gigachat_client: GigaChat) -> None:
    """Test listing all available models."""
    result = gigachat_client.get_models()

    assert isinstance(result, Models)
    assert result.data is not None
    assert len(result.data) > 0


@pytest.mark.integration
@pytest.mark.vcr
def test_get_model(gigachat_client: GigaChat) -> None:
    """Test getting a specific model by name."""
    result = gigachat_client.get_model("GigaChat")

    assert isinstance(result, Model)
    assert result.id_ == "GigaChat"


@pytest.mark.integration
@pytest.mark.vcr
def test_get_model_not_found(gigachat_client: GigaChat) -> None:
    """Test that getting a non-existent model raises NotFoundError."""
    with pytest.raises(NotFoundError) as exc_info:
        gigachat_client.get_model("NonExistentModel")

    assert exc_info.value.status_code == 404


@pytest.mark.integration
@pytest.mark.vcr
async def test_aget_models(gigachat_async_client: GigaChat) -> None:
    """Test listing all available models asynchronously."""
    result = await gigachat_async_client.aget_models()

    assert isinstance(result, Models)
    assert result.data is not None
    assert len(result.data) > 0


@pytest.mark.integration
@pytest.mark.vcr
async def test_aget_model(gigachat_async_client: GigaChat) -> None:
    """Test getting a specific model by name asynchronously."""
    result = await gigachat_async_client.aget_model("GigaChat")

    assert isinstance(result, Model)
    assert result.id_ == "GigaChat"


@pytest.mark.integration
@pytest.mark.vcr
async def test_aget_model_not_found(gigachat_async_client: GigaChat) -> None:
    """Test that getting a non-existent model asynchronously raises NotFoundError."""
    with pytest.raises(NotFoundError) as exc_info:
        await gigachat_async_client.aget_model("NonExistentModel")

    assert exc_info.value.status_code == 404
