"""Integration tests for /embeddings endpoint using VCR cassettes."""

import pytest

from gigachat import GigaChat
from gigachat.models import Embedding, Embeddings


@pytest.mark.integration
@pytest.mark.vcr
def test_embeddings_single(gigachat_client: GigaChat) -> None:
    """Test generating embeddings for a single text."""
    result = gigachat_client.embeddings(texts=["Hello, world!"])

    assert isinstance(result, Embeddings)
    assert result.object_ == "list"
    assert len(result.data) == 1

    embedding = result.data[0]
    assert isinstance(embedding, Embedding)
    assert embedding.object_ == "embedding"
    assert embedding.index == 0
    assert len(embedding.embedding) > 0
    assert embedding.usage.prompt_tokens > 0


@pytest.mark.integration
@pytest.mark.vcr
def test_embeddings_multiple(gigachat_client: GigaChat) -> None:
    """Test generating embeddings for multiple texts."""
    result = gigachat_client.embeddings(texts=["First text", "Second text"])

    assert isinstance(result, Embeddings)
    assert result.object_ == "list"
    assert len(result.data) == 2

    for i, embedding in enumerate(result.data):
        assert isinstance(embedding, Embedding)
        assert embedding.object_ == "embedding"
        assert embedding.index == i
        assert len(embedding.embedding) > 0
        assert embedding.usage.prompt_tokens > 0


@pytest.mark.integration
@pytest.mark.vcr
async def test_aembeddings_single(gigachat_async_client: GigaChat) -> None:
    """Test generating embeddings for a single text asynchronously."""
    result = await gigachat_async_client.aembeddings(texts=["Hello, world!"])

    assert isinstance(result, Embeddings)
    assert result.object_ == "list"
    assert len(result.data) == 1

    embedding = result.data[0]
    assert isinstance(embedding, Embedding)
    assert embedding.object_ == "embedding"
    assert embedding.index == 0
    assert len(embedding.embedding) > 0
    assert embedding.usage.prompt_tokens > 0


@pytest.mark.integration
@pytest.mark.vcr
async def test_aembeddings_multiple(gigachat_async_client: GigaChat) -> None:
    """Test generating embeddings for multiple texts asynchronously."""
    result = await gigachat_async_client.aembeddings(texts=["First text", "Second text"])

    assert isinstance(result, Embeddings)
    assert result.object_ == "list"
    assert len(result.data) == 2

    for i, embedding in enumerate(result.data):
        assert isinstance(embedding, Embedding)
        assert embedding.object_ == "embedding"
        assert embedding.index == i
        assert len(embedding.embedding) > 0
        assert embedding.usage.prompt_tokens > 0
