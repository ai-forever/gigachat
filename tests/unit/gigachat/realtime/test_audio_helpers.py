import builtins
import struct
import sys
from types import ModuleType
from typing import Any, List

import pytest

from gigachat.realtime.audio import numpy_to_pcm16_bytes, pcm16_bytes_to_numpy


class _FakeDType:
    def __init__(self, kind: str) -> None:
        self.kind = kind


class _FakeArray:
    def __init__(self, values: List[float], dtype_kind: str = "i") -> None:
        self.values = values
        self.dtype = _FakeDType(dtype_kind)

    def __mul__(self, factor: int) -> "_FakeArray":
        return _FakeArray([value * factor for value in self.values], self.dtype.kind)

    def astype(self, _dtype: str, copy: bool = True) -> "_FakeArray":
        return _FakeArray([int(value) for value in self.values], "i")

    def copy(self) -> "_FakeArray":
        return _FakeArray(list(self.values), self.dtype.kind)

    def tobytes(self) -> bytes:
        return struct.pack("<" + "h" * len(self.values), *[int(value) for value in self.values])

    def tolist(self) -> List[int]:
        return [int(value) for value in self.values]


class _FakeNumpy(ModuleType):
    def asarray(self, array: Any) -> _FakeArray:
        if isinstance(array, _FakeArray):
            return array

        values = list(array)
        dtype_kind = "f" if any(isinstance(value, float) for value in values) else "i"
        return _FakeArray(values, dtype_kind)

    def clip(self, array: _FakeArray, min_value: float, max_value: float) -> _FakeArray:
        return _FakeArray([min(max(value, min_value), max_value) for value in array.values], array.dtype.kind)

    def ascontiguousarray(self, array: _FakeArray) -> _FakeArray:
        return array

    def frombuffer(self, audio_chunk: bytes, dtype: str) -> _FakeArray:
        assert dtype == "<i2"
        values = list(struct.unpack("<" + "h" * (len(audio_chunk) // 2), audio_chunk))
        return _FakeArray([float(value) for value in values], "i")


@pytest.fixture
def fake_numpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "numpy", _FakeNumpy("numpy"))


def test_numpy_to_pcm16_bytes_converts_integer_array(fake_numpy: None) -> None:
    assert numpy_to_pcm16_bytes([1, -2, 32767]) == struct.pack("<hhh", 1, -2, 32767)


def test_numpy_to_pcm16_bytes_clips_and_scales_float_array(fake_numpy: None) -> None:
    assert numpy_to_pcm16_bytes([-1.5, 0.5, 2.0]) == struct.pack("<hhh", -32767, 16383, 32767)


def test_pcm16_bytes_to_numpy_returns_int16_array(fake_numpy: None) -> None:
    array = pcm16_bytes_to_numpy(struct.pack("<hhh", 1, -2, 32767))

    assert array.tolist() == [1, -2, 32767]


def test_pcm16_conversion_roundtrip(fake_numpy: None) -> None:
    audio_chunk = numpy_to_pcm16_bytes([0, 16000, -16000])

    assert pcm16_bytes_to_numpy(audio_chunk).tolist() == [0, 16000, -16000]


def test_pcm16_bytes_to_numpy_rejects_odd_length(fake_numpy: None) -> None:
    with pytest.raises(ValueError, match="divisible by 2"):
        pcm16_bytes_to_numpy(b"\x00")


def test_audio_helpers_report_missing_numpy(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__
    monkeypatch.delitem(sys.modules, "numpy", raising=False)

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "numpy":
            raise ImportError("missing numpy")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ImportError, match=r"gigachat\[voice_helpers\]"):
        numpy_to_pcm16_bytes([0])
