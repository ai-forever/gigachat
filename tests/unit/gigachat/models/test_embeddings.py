from gigachat.models.embeddings import Embedding, Embeddings


def test_embeddings_use_documented_object_defaults() -> None:
    response = Embeddings.model_validate(
        {
            "data": [
                {
                    "embedding": [0.1, 0.2],
                    "usage": {"prompt_tokens": 2},
                    "index": 0,
                }
            ]
        }
    )

    assert response.object_ == "list"
    assert isinstance(response.data[0], Embedding)
    assert response.data[0].object_ == "embedding"
    assert response.model_dump(by_alias=True)["object"] == "list"
    assert response.model_dump(by_alias=True)["data"][0]["object"] == "embedding"
