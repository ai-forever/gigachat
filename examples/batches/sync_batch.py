"""Create and inspect a batch task synchronously."""
import time
from pathlib import Path

from dotenv import load_dotenv

from gigachat import GigaChat

BATCH_JSONL = (
    b'{"id":"request-1","request":{"model":"GigaChat-2",'
    b'"messages":[{"role":"user","content":"Summarize the SDK in one sentence."}]}}\n'
)


def main() -> None:
    """Create a batch and download results if processing has completed."""
    load_dotenv()

    with GigaChat() as client:
        created = client.create_batch(BATCH_JSONL, method="chat_completions")
        batch = client.get_batches(created.id_).batches[0]
        print(f"Batch {batch.id_}: {batch.status.value}")
        time.sleep(10)
        batch = client.get_batches(created.id_).batches[0]
        if batch.output_file_id is not None:
            result = client.get_file_content(batch.output_file_id)
            output = Path("batch-results.jsonl")
            result.save(output)
            print(f"Saved {len(result.content)} bytes to {output}")


if __name__ == "__main__":
    main()
