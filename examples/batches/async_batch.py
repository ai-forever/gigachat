"""Create and inspect a batch task asynchronously."""

import asyncio
import time
from pathlib import Path

from dotenv import load_dotenv

from gigachat import GigaChatAsyncClient

BATCH_JSONL = (
    b'{"id":"request-1","request":{"model":"GigaChat-2",'
    b'"messages":[{"role":"user","content":"Summarize the SDK in one sentence."}]}}\n'
)


async def main() -> None:
    """Create a batch and download results if processing has completed."""
    load_dotenv()

    async with GigaChatAsyncClient() as client:
        created = await client.acreate_batch(BATCH_JSONL, method="chat_completions")
        batch = (await client.aget_batches(created.id_)).batches[0]
        print(f"Batch {batch.id_}: {batch.status.value}")
        time.sleep(10)
        batch = (await client.aget_batches(created.id_)).batches[0]
        if batch.output_file_id is not None:
            result = await client.aget_file_content(batch.output_file_id)
            output = Path("batch-results.jsonl")
            result.save(output)
            print(f"Saved {len(result.content)} bytes to {output}")


if __name__ == "__main__":
    asyncio.run(main())
