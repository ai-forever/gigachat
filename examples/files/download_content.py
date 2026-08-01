"""Download arbitrary file content synchronously."""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from gigachat import GigaChat


def main() -> None:
    """Download a file ID supplied on the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("file_id", help="GigaChat file identifier")
    parser.add_argument("--output", default="downloaded-file.bin", help="Destination path")
    args = parser.parse_args()
    load_dotenv()

    output = Path(args.output)
    with GigaChat() as client:
        client.download_file(args.file_id, output)

    print(f"Saved file to {output}")


if __name__ == "__main__":
    main()
