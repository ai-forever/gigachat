from importlib import import_module
from typing import Any


def _require_numpy() -> Any:
    try:
        return import_module("numpy")
    except ImportError as exc:
        raise ImportError(
            "Install `gigachat[voice_helpers]` or `gigachat[realtime_voice]` to use audio helpers"
        ) from exc


def numpy_to_pcm16_bytes(array: Any) -> bytes:
    np = _require_numpy()
    values = np.asarray(array)

    if getattr(values.dtype, "kind", None) == "f":
        values = np.clip(values, -1.0, 1.0)
        values = (values * 32767).astype("<i2")
    else:
        values = values.astype("<i2", copy=False)

    return bytes(np.ascontiguousarray(values).tobytes())


def pcm16_bytes_to_numpy(audio_chunk: bytes) -> Any:
    if len(audio_chunk) % 2:
        raise ValueError("PCM_S16LE audio chunk length must be divisible by 2")

    np = _require_numpy()
    return np.frombuffer(audio_chunk, dtype="<i2").copy()


__all__ = (
    "numpy_to_pcm16_bytes",
    "pcm16_bytes_to_numpy",
)
