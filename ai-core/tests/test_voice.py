import pytest
from voice.stt_whisper import WhisperSTT, VoiceActivityDetector
from voice.tts_piper import PiperTTS


# --- STT ---

def test_whisper_uses_mock_when_not_installed():
    stt = WhisperSTT()
    assert not stt.is_loaded()


def test_whisper_mock_transcription_shape():
    stt = WhisperSTT()
    result = stt.transcribe_audio("nonexistent.wav")
    assert "text" in result
    assert "language" in result
    assert "confidence" in result
    assert result.get("is_mock") is True


def test_whisper_detect_language_fallback():
    stt = WhisperSTT()
    assert stt.detect_language("nonexistent.wav") == "en"


def test_voice_activity_detector_short_buffer():
    vad = VoiceActivityDetector()
    assert not vad.is_speech(b"short")


def test_voice_activity_detector_long_buffer():
    vad = VoiceActivityDetector()
    assert vad.is_speech(b"x" * 2000)


# --- TTS ---

def test_piper_uses_mock_when_binary_not_found():
    tts = PiperTTS()
    assert not tts.is_loaded()


def test_piper_mock_returns_valid_wav():
    tts = PiperTTS()
    audio = tts.synthesize("Hello world")
    assert len(audio) > 0
    assert audio[:4] == b"RIFF", "mock audio should be a valid WAV file"


def test_piper_available_voices_nonexistent_path():
    tts = PiperTTS(model_path="/nonexistent/model/path")
    voices = tts.get_available_voices()
    assert isinstance(voices, list)
    assert voices == []
