from gigachat.models.batches import Batch, Batches, BatchMethod, BatchStatus


def test_batch_models_documented_response() -> None:
    response = Batches.model_validate(
        {
            "batches": [
                {
                    "id": "batch-1",
                    "method": "chat_completions",
                    "request_counts": {"total": 3, "completed": 2, "failed": 1},
                    "status": "completed",
                    "output_file_id": "file-1",
                    "created_at": 1726478395,
                    "updated_at": 1726478474,
                }
            ]
        }
    )

    batch = response.batches[0]
    assert isinstance(batch, Batch)
    assert batch.id_ == "batch-1"
    assert batch.method is BatchMethod.CHAT_COMPLETIONS
    assert batch.status is BatchStatus.COMPLETED
    assert batch.request_counts.completed == 2


def test_batch_create_response_allows_pending_counts() -> None:
    batch = Batch.model_validate(
        {
            "id": "batch-1",
            "method": "embedder",
            "request_counts": {"total": 0},
            "status": "created",
            "created_at": 1726478395,
            "updated_at": 1726478395,
        }
    )

    assert batch.method is BatchMethod.EMBEDDER
    assert batch.request_counts.completed is None
    assert batch.output_file_id is None
