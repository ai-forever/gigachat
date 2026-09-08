"""Download arbitrary file content asynchronously."""

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from gigachat import GigaChatAsyncClient


async def main() -> None:
    """Download a file ID supplied on the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("file_id", help="GigaChat file identifier")
    parser.add_argument("--output", default="downloaded-file.bin", help="Destination path")
    args = parser.parse_args()
    load_dotenv()

    output = Path(args.output)
    async with GigaChatAsyncClient() as client:
        await client.adownload_file(args.file_id, output)

    print(f"Saved file to {output}")


if __name__ == "__main__":
    asyncio.run(main())
