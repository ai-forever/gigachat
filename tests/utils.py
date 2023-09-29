import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent / "data"


def get_json(path: str) -> Any:
    with open(DATA_PATH / path, encoding="utf-8") as fp:
        return json.load(fp)


def get_bytes(path: str) -> bytes:
    with open(DATA_PATH / path, mode="rb") as fp:
        return fp.read()
