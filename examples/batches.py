"""List batches or submit an existing JSONL file without buffering it."""

import argparse
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from gigachat import GigaChat


def submit(client: GigaChat, path: Path, method: Literal["chat_completions", "embedder"]) -> None:
    with path.open("rb") as source:
        batch = client.create_batch(iter(lambda: source.read(65536), b""), method=method)
    print(batch.id_, batch.status)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submit", type=Path, help="Submit this existing JSONL file as a new batch")
    parser.add_argument("--method", choices=("chat_completions", "embedder"), default="chat_completions")
    parser.add_argument("--batch-id", help="Select a batch when listing")
    args = parser.parse_args()
    load_dotenv()
    with GigaChat() as client:
        if args.submit is not None:
            submit(client, args.submit, args.method)
        else:
            for batch in client.get_batches(args.batch_id).batches:
                print(batch.id_, batch.status, batch.output_file_id)


if __name__ == "__main__":
    main()
