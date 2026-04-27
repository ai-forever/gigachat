from gigachat.proto.gigavoice import voice_pb2


def test_voice_pb2_imports_without_grpc_stub() -> None:
    assert voice_pb2.DESCRIPTOR.services_by_name["GigaVoiceService"].full_name == "GigaVoiceProtocol.GigaVoiceService"


def test_gigavoice_request_round_trip() -> None:
    giga_voice_request = vars(voice_pb2)["GigaVoiceRequest"]
    settings = vars(voice_pb2)["Settings"]
    request = giga_voice_request(settings=settings(voice_call_id="call-id"))

    payload = request.SerializeToString()
    parsed = giga_voice_request.FromString(payload)

    assert isinstance(payload, bytes)
    assert parsed.WhichOneof("request") == "settings"
    assert parsed.settings.voice_call_id == "call-id"


def test_gigavoice_response_audio_bytes_round_trip() -> None:
    giga_voice_response = vars(voice_pb2)["GigaVoiceResponse"]
    content_from_model = vars(voice_pb2)["ContentFromModel"]
    audio = vars(voice_pb2)["Audio"]
    response = giga_voice_response(output=content_from_model(audio=audio(audio_chunk=b"pcm", is_final=True)))

    parsed = giga_voice_response.FromString(response.SerializeToString())

    assert parsed.WhichOneof("response") == "output"
    assert parsed.output.WhichOneof("response") == "audio"
    assert parsed.output.audio.audio_chunk == b"pcm"
    assert parsed.output.audio.is_final is True
