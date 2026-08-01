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

    async with GigaChatAsyncClient() as client:
        downloaded = await client.aget_file_content(args.file_id)

    output = Path(args.output)
    output.write_bytes(downloaded.content)
    print(f"Saved {len(downloaded.content)} bytes ({downloaded.content_type}) to {output}")


if __name__ == "__main__":
    asyncio.run(main())
