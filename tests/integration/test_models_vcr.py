"""Integration tests for /models endpoint using VCR cassettes."""

import pytest

from gigachat import GigaChat, Model, Models, NotFoundError


@pytest.mark.integration
@pytest.mark.vcr
def test_models_list(gigachat_client: GigaChat) -> None:
    """Test listing all available models."""
    result = gigachat_client.models.list()

    assert isinstance(result, Models)
    assert result.data is not None
    assert len(result.data) > 0


@pytest.mark.integration
@pytest.mark.vcr
def test_models_retrieve(gigachat_client: GigaChat) -> None:
    """Test getting a specific model by name."""
    result = gigachat_client.models.retrieve("GigaChat")

    assert isinstance(result, Model)
    assert result.id_ == "GigaChat"


@pytest.mark.integration
@pytest.mark.vcr
def test_models_retrieve_not_found(gigachat_client: GigaChat) -> None:
    """Test that getting a non-existent model raises NotFoundError."""
    with pytest.raises(NotFoundError) as exc_info:
        gigachat_client.models.retrieve("NonExistentModel")

    assert exc_info.value.status_code == 404


@pytest.mark.integration
@pytest.mark.vcr
async def test_a_models_list(gigachat_async_client: GigaChat) -> None:
    """Test listing all available models asynchronously."""
    result = await gigachat_async_client.a_models.list()

    assert isinstance(result, Models)
    assert result.data is not None
    assert len(result.data) > 0


@pytest.mark.integration
@pytest.mark.vcr
async def test_a_models_retrieve(gigachat_async_client: GigaChat) -> None:
    """Test getting a specific model by name asynchronously."""
    result = await gigachat_async_client.a_models.retrieve("GigaChat")

    assert isinstance(result, Model)
    assert result.id_ == "GigaChat"


@pytest.mark.integration
@pytest.mark.vcr
async def test_a_models_retrieve_not_found(gigachat_async_client: GigaChat) -> None:
    """Test that getting a non-existent model asynchronously raises NotFoundError."""
    with pytest.raises(NotFoundError) as exc_info:
        await gigachat_async_client.a_models.retrieve("NonExistentModel")

    assert exc_info.value.status_code == 404
