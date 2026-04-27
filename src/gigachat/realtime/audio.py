import asyncio
from contextlib import suppress
from importlib import import_module
from types import TracebackType
from typing import Any, Optional, Type, Union


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


def _require_sounddevice() -> Any:
    try:
        return import_module("sounddevice")
    except ImportError as exc:
        raise ImportError(
            "Install `gigachat[voice_helpers]` or `gigachat[realtime_voice]` to use audio helpers"
        ) from exc


def _validate_positive_int(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0")


class RealtimeMicrophone:
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_ms: int = 100,
        dtype: str = "int16",
        device: Optional[Union[int, str]] = None,
    ) -> None:
        _validate_positive_int("sample_rate", sample_rate)
        _validate_positive_int("channels", channels)
        _validate_positive_int("chunk_ms", chunk_ms)
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_ms = chunk_ms
        self.dtype = dtype
        self.device = device
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue = None  # type: Optional[asyncio.Queue[Optional[bytes]]]
        self._stream: Optional[Any] = None
        self._closed = False

    async def __aenter__(self) -> "RealtimeMicrophone":
        self._closed = False
        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue()
        sd = _require_sounddevice()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            device=self.device,
            blocksize=self._frames_per_chunk(),
            callback=self._on_audio,
        )
        self._stream.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()

    def __aiter__(self) -> "RealtimeMicrophone":
        return self

    async def __anext__(self) -> bytes:
        if self._queue is None:
            raise RuntimeError("RealtimeMicrophone must be used as an async context manager")

        chunk = await self._queue.get()
        if chunk is None:
            raise StopAsyncIteration
        return chunk

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        stream = self._stream
        self._stream = None
        if stream is not None:
            stream.stop()
            stream.close()

        self._put_close_marker()

    def _frames_per_chunk(self) -> int:
        return max(1, int(self.sample_rate * self.chunk_ms / 1000))

    def _on_audio(self, indata: Any, frames: int, time: Any, status: Any) -> None:
        del frames, time, status
        if self._closed or self._loop is None or self._queue is None:
            return

        audio_chunk = numpy_to_pcm16_bytes(indata)
        self._loop.call_soon_threadsafe(self._queue.put_nowait, audio_chunk)

    def _put_close_marker(self) -> None:
        if self._queue is None:
            return
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._queue.put_nowait, None)
        else:
            self._queue.put_nowait(None)


class RealtimeSpeaker:
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = "int16",
        device: Optional[Union[int, str]] = None,
    ) -> None:
        _validate_positive_int("sample_rate", sample_rate)
        _validate_positive_int("channels", channels)
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.device = device
        self._queue = None  # type: Optional[asyncio.Queue[Optional[Any]]]
        self._stream: Optional[Any] = None
        self._writer_task: Optional[Any] = None
        self._closed = False

    async def __aenter__(self) -> "RealtimeSpeaker":
        self._closed = False
        self._queue = asyncio.Queue()
        sd = _require_sounddevice()
        self._stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            device=self.device,
        )
        self._stream.start()
        self._writer_task = asyncio.create_task(self._write_loop())
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()
        if self._writer_task is not None:
            with suppress(asyncio.CancelledError):
                await self._writer_task

    async def write(self, audio_chunk: bytes) -> None:
        if self._closed or self._queue is None:
            raise RuntimeError("RealtimeSpeaker must be used as an async context manager")
        await self._queue.put(self._audio_chunk_to_array(audio_chunk))

    def stop(self) -> None:
        self._drain_queue()

        stream = self._stream
        if stream is None:
            return

        abort = getattr(stream, "abort", None)
        if callable(abort):
            abort()
        else:
            stream.stop()
        if not self._closed:
            stream.start()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._drain_queue()

        if self._queue is not None:
            self._queue.put_nowait(None)

        stream = self._stream
        self._stream = None
        if stream is not None:
            stream.stop()
            stream.close()

    async def _write_loop(self) -> None:
        if self._queue is None:
            return

        while True:
            item = await self._queue.get()
            if item is None:
                return

            stream = self._stream
            if stream is not None:
                stream.write(item)

    def _audio_chunk_to_array(self, audio_chunk: bytes) -> Any:
        frame_size = self.channels * 2
        if len(audio_chunk) % frame_size:
            raise ValueError("PCM_S16LE audio chunk length must contain whole channel frames")

        array = pcm16_bytes_to_numpy(audio_chunk)
        if self.channels > 1:
            array = array.reshape((-1, self.channels))
        return array

    def _drain_queue(self) -> None:
        if self._queue is None:
            return

        while not self._queue.empty():
            self._queue.get_nowait()


__all__ = (
    "RealtimeMicrophone",
    "RealtimeSpeaker",
    "numpy_to_pcm16_bytes",
    "pcm16_bytes_to_numpy",
)
