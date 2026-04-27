import base64

import pytest

from gigachat.realtime._base64 import (
    decode_audio,
    encode_audio,
    pcm16_duration_seconds,
    validate_pcm16_chunk_duration,
)


def test_encode_audio_returns_base64_ascii_string() -> None:
    assert encode_audio(b"pcm") == base64.b64encode(b"pcm").decode("ascii")


def test_decode_audio_returns_bytes() -> None:
    assert decode_audio(base64.b64encode(b"pcm").decode("ascii")) == b"pcm"


def test_pcm16_duration_seconds() -> None:
    assert pcm16_duration_seconds(b"\x00" * 32000, sample_rate=16000) == 1.0


def test_pcm16_duration_validates_sample_rate() -> None:
    with pytest.raises(ValueError, match="sample_rate must be positive"):
        pcm16_duration_seconds(b"", sample_rate=0)


def test_validate_pcm16_chunk_duration_rejects_long_chunk() -> None:
    with pytest.raises(ValueError, match="exceeds 2 seconds"):
        validate_pcm16_chunk_duration(b"\x00" * 64002, sample_rate=16000)
