import base64


def encode_audio(audio_chunk: bytes) -> str:
    return base64.b64encode(audio_chunk).decode("ascii")


def decode_audio(audio_chunk: str) -> bytes:
    return base64.b64decode(audio_chunk)


def pcm16_duration_seconds(audio_chunk: bytes, sample_rate: int, channels: int = 1) -> float:
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    if channels <= 0:
        raise ValueError("channels must be positive")

    return len(audio_chunk) / float(sample_rate * channels * 2)


def validate_pcm16_chunk_duration(
    audio_chunk: bytes,
    sample_rate: int,
    channels: int = 1,
    max_seconds: float = 2.0,
) -> None:
    duration_seconds = pcm16_duration_seconds(audio_chunk, sample_rate=sample_rate, channels=channels)
    if duration_seconds > max_seconds:
        raise ValueError(
            f"PCM_S16LE audio chunk duration exceeds {max_seconds:g} seconds: {duration_seconds:.3f} seconds"
        )


__all__ = (
    "decode_audio",
    "encode_audio",
    "pcm16_duration_seconds",
    "validate_pcm16_chunk_duration",
)
