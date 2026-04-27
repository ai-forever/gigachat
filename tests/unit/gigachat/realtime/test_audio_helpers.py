import asyncio
import builtins
import struct
import sys
from types import ModuleType
from typing import Any, List, Optional

import pytest

import gigachat.realtime.audio as audio
from gigachat.realtime.audio import (
    RealtimeMicrophone,
    RealtimeSpeaker,
    numpy_to_pcm16_bytes,
    pcm16_bytes_to_numpy,
)


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

    def reshape(self, shape: Any) -> "_FakeArray":
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


class _FakeInputStream:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.callback = kwargs["callback"]
        self.started = False
        self.stopped = False
        self.closed = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def close(self) -> None:
        self.closed = True


class _FakeOutputStream:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.started_count = 0
        self.stopped = False
        self.closed = False
        self.aborted = False
        self.writes: List[Any] = []

    def start(self) -> None:
        self.started_count += 1

    def stop(self) -> None:
        self.stopped = True

    def close(self) -> None:
        self.closed = True

    def abort(self) -> None:
        self.aborted = True

    def write(self, data: Any) -> None:
        self.writes.append(data)


class _FakeSounddevice(ModuleType):
    def __init__(self) -> None:
        super().__init__("sounddevice")
        self.input_stream: Optional[_FakeInputStream] = None
        self.output_stream: Optional[_FakeOutputStream] = None

    def InputStream(self, **kwargs: Any) -> _FakeInputStream:
        self.input_stream = _FakeInputStream(**kwargs)
        return self.input_stream

    def OutputStream(self, **kwargs: Any) -> _FakeOutputStream:
        self.output_stream = _FakeOutputStream(**kwargs)
        return self.output_stream


@pytest.fixture
def fake_numpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "numpy", _FakeNumpy("numpy"))


@pytest.fixture
def fake_sounddevice(monkeypatch: pytest.MonkeyPatch) -> _FakeSounddevice:
    module = _FakeSounddevice()
    monkeypatch.setitem(sys.modules, "sounddevice", module)
    return module


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


async def test_microphone_starts_and_closes_input_stream(fake_numpy: None, fake_sounddevice: _FakeSounddevice) -> None:
    async with RealtimeMicrophone(sample_rate=8000, channels=1, chunk_ms=20, device="input-1") as microphone:
        assert fake_sounddevice.input_stream is not None
        assert fake_sounddevice.input_stream.started is True
        assert fake_sounddevice.input_stream.kwargs["samplerate"] == 8000
        assert fake_sounddevice.input_stream.kwargs["channels"] == 1
        assert fake_sounddevice.input_stream.kwargs["blocksize"] == 160
        assert fake_sounddevice.input_stream.kwargs["device"] == "input-1"

        microphone.close()

    assert fake_sounddevice.input_stream is not None
    assert fake_sounddevice.input_stream.stopped is True
    assert fake_sounddevice.input_stream.closed is True


async def test_microphone_callback_pushes_pcm16_bytes(fake_numpy: None, fake_sounddevice: _FakeSounddevice) -> None:
    async with RealtimeMicrophone(sample_rate=16000, channels=1, chunk_ms=100) as microphone:
        assert fake_sounddevice.input_stream is not None
        fake_sounddevice.input_stream.callback(_FakeArray([1, -2, 32767]), 3, None, None)

        chunk = await asyncio.wait_for(microphone.__anext__(), timeout=1)

    assert chunk == struct.pack("<hhh", 1, -2, 32767)


async def test_speaker_starts_and_closes_output_stream(fake_numpy: None, fake_sounddevice: _FakeSounddevice) -> None:
    async with RealtimeSpeaker(sample_rate=8000, channels=2, device="output-1") as speaker:
        assert fake_sounddevice.output_stream is not None
        assert fake_sounddevice.output_stream.started_count == 1
        assert fake_sounddevice.output_stream.kwargs["samplerate"] == 8000
        assert fake_sounddevice.output_stream.kwargs["channels"] == 2
        assert fake_sounddevice.output_stream.kwargs["device"] == "output-1"

        speaker.close()

    assert fake_sounddevice.output_stream is not None
    assert fake_sounddevice.output_stream.stopped is True
    assert fake_sounddevice.output_stream.closed is True


async def test_speaker_write_converts_and_writes_pcm16_bytes(
    fake_numpy: None, fake_sounddevice: _FakeSounddevice
) -> None:
    async with RealtimeSpeaker(sample_rate=16000, channels=1) as speaker:
        assert fake_sounddevice.output_stream is not None

        await speaker.write(struct.pack("<hhh", 1, -2, 32767))

        for _ in range(10):
            if fake_sounddevice.output_stream.writes:
                break
            await asyncio.sleep(0)

        assert fake_sounddevice.output_stream.writes
        assert fake_sounddevice.output_stream.writes[0].tolist() == [1, -2, 32767]


async def test_speaker_stop_drains_queue_and_restarts_stream(
    fake_numpy: None, fake_sounddevice: _FakeSounddevice
) -> None:
    async with RealtimeSpeaker(sample_rate=16000, channels=1) as speaker:
        assert fake_sounddevice.output_stream is not None

        await speaker.write(struct.pack("<h", 1))
        speaker.stop()

        assert fake_sounddevice.output_stream.aborted is True
        assert fake_sounddevice.output_stream.started_count == 2


async def test_speaker_rejects_incomplete_channel_frame(fake_numpy: None, fake_sounddevice: _FakeSounddevice) -> None:
    async with RealtimeSpeaker(sample_rate=16000, channels=2) as speaker:
        with pytest.raises(ValueError, match="whole channel frames"):
            await speaker.write(struct.pack("<h", 1))


def test_audio_helpers_report_missing_sounddevice(monkeypatch: pytest.MonkeyPatch, fake_numpy: None) -> None:
    monkeypatch.delitem(sys.modules, "sounddevice", raising=False)
    original_import_module = audio.__dict__["import_module"]

    def fake_import_module(name: str) -> Any:
        if name == "sounddevice":
            raise ImportError("missing sounddevice")
        return original_import_module(name)

    monkeypatch.setattr(audio, "import_module", fake_import_module)

    microphone = RealtimeMicrophone()
    with pytest.raises(ImportError, match=r"gigachat\[voice_helpers\]"):
        asyncio.run(microphone.__aenter__())
