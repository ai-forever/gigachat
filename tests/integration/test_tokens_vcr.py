"""Integration tests for /tokens/count endpoint using VCR cassettes."""

import pytest

from gigachat import GigaChat
from gigachat.models import TokensCount


@pytest.mark.integration
@pytest.mark.vcr
def test_tokens_resource_count_single(gigachat_client: GigaChat) -> None:
    """Test counting tokens in a single text."""
    result = gigachat_client.tokens.count(input_=["Hello, world!"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TokensCount)
    assert result[0].tokens > 0
    assert result[0].characters > 0
    assert result[0].object_ == "tokens"


@pytest.mark.integration
@pytest.mark.vcr
def test_tokens_resource_count_multiple(gigachat_client: GigaChat) -> None:
    """Test counting tokens in multiple texts."""
    result = gigachat_client.tokens.count(input_=["First text", "Second text"])

    assert isinstance(result, list)
    assert len(result) == 2
    for item in result:
        assert isinstance(item, TokensCount)
        assert item.tokens > 0
        assert item.characters > 0
        assert item.object_ == "tokens"


@pytest.mark.integration
@pytest.mark.vcr
async def test_a_tokens_resource_count_single(gigachat_async_client: GigaChat) -> None:
    """Test counting tokens in a single text asynchronously."""
    result = await gigachat_async_client.a_tokens.count(input_=["Hello, world!"])

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TokensCount)
    assert result[0].tokens > 0
    assert result[0].characters > 0
    assert result[0].object_ == "tokens"


@pytest.mark.integration
@pytest.mark.vcr
async def test_a_tokens_resource_count_multiple(gigachat_async_client: GigaChat) -> None:
    """Test counting tokens in multiple texts asynchronously."""
    result = await gigachat_async_client.a_tokens.count(input_=["First text", "Second text"])

    assert isinstance(result, list)
    assert len(result) == 2
    for item in result:
        assert isinstance(item, TokensCount)
        assert item.tokens > 0
        assert item.characters > 0
        assert item.object_ == "tokens"
