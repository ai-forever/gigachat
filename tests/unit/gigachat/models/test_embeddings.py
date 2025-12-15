from gigachat.models.embeddings import Embedding, Embeddings


def test_embedding_creation() -> None:
    data = {
        "embedding": [0.1, 0.2],
        "usage": {"prompt_tokens": 5},
        "index": 0,
        "object": "embedding",
    }
    emb = Embedding.model_validate(data)
    assert emb.embedding == [0.1, 0.2]
    assert emb.usage.prompt_tokens == 5
    assert emb.object_ == "embedding"


def test_embeddings_creation() -> None:
    data = {
        "data": [
            {
                "embedding": [0.1],
                "usage": {"prompt_tokens": 1},
                "index": 0,
                "object": "embedding",
            }
        ],
        "model": "emb-model",
        "object": "list",
    }
    embeddings = Embeddings.model_validate(data)
    assert len(embeddings.data) == 1
    assert embeddings.model == "emb-model"
    assert embeddings.object_ == "list"
