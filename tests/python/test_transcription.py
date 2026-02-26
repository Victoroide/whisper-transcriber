"""Tests for ui.app.core.transcription -- requires faster-whisper and a model.

These tests download the 'tiny' model on first run and transcribe a short
audio fixture. They are marked to skip if faster-whisper is not installed.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

FIXTURES_DIR = Path(__file__).parent / "fixtures"

try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    HAS_FASTER_WHISPER = False


@pytest.mark.skipif(not HAS_FASTER_WHISPER, reason="faster-whisper not installed")
class TestTranscription:
    """Integration tests that run actual model inference."""

    def test_transcribe_loads_model_and_processes_audio(self) -> None:
        """Verify the transcription pipeline loads the model, processes audio,
        and returns a valid TranscriptionResult object. With synthetic audio
        the model may or may not produce segments, but it must not crash."""
        from ui.app.core.transcription import transcribe

        sample = FIXTURES_DIR / "sample_audio.wav"
        if not sample.exists():
            pytest.skip("sample_audio.wav fixture not found")

        result = transcribe(
            str(sample),
            model_size="tiny",
            device="cpu",
            compute_type="int8",
            vad_filter=False,
        )

        # TranscriptionResult must be returned with valid structure
        assert result is not None
        assert isinstance(result.segments, list)
        assert isinstance(result.text, str)
        assert isinstance(result.language, str)
        assert len(result.language) > 0, "Expected a detected language"
        assert 0.0 <= result.language_probability <= 1.0

    def test_transcribe_returns_non_empty_with_speech(self) -> None:
        """If segments are produced, verify they contain non-empty text."""
        from ui.app.core.transcription import transcribe

        sample = FIXTURES_DIR / "sample_audio.wav"
        if not sample.exists():
            pytest.skip("sample_audio.wav fixture not found")

        result = transcribe(
            str(sample),
            model_size="tiny",
            device="cpu",
            compute_type="int8",
            vad_filter=False,
        )

        # If the model produced segments, they must all have text
        for start, end, text in result.segments:
            assert len(text.strip()) > 0, f"Empty text in segment [{start}-{end}]"

    def test_no_duplicate_sentences(self) -> None:
        from ui.app.core.transcription import transcribe

        sample = FIXTURES_DIR / "sample_audio.wav"
        if not sample.exists():
            pytest.skip("sample_audio.wav fixture not found")

        result = transcribe(
            str(sample),
            model_size="tiny",
            device="cpu",
            compute_type="int8",
            vad_filter=False,
        )

        # Check that no identical sentence appears more than once
        texts = [seg[2] for seg in result.segments]
        for text in texts:
            count = texts.count(text)
            if count > 1:
                pytest.fail(
                    f"Duplicate segment detected ({count} times): '{text}'"
                )

    def test_segments_have_valid_timestamps(self) -> None:
        from ui.app.core.transcription import transcribe

        sample = FIXTURES_DIR / "sample_audio.wav"
        if not sample.exists():
            pytest.skip("sample_audio.wav fixture not found")

        result = transcribe(
            str(sample),
            model_size="tiny",
            device="cpu",
            compute_type="int8",
            vad_filter=False,
        )

        for start, end, text in result.segments:
            assert start >= 0, f"Negative start time: {start}"
            assert end > start, f"End ({end}) not after start ({start})"
            assert len(text) > 0, "Empty segment text"

    def test_missing_file_raises_error(self) -> None:
        """Verify that transcribe raises FileNotFoundError for missing files."""
        from ui.app.core.transcription import transcribe

        with pytest.raises(FileNotFoundError):
            transcribe(
                "/nonexistent/path/audio.wav",
                model_size="tiny",
                device="cpu",
                compute_type="int8",
            )

    def test_cancellation_stops_transcription(self) -> None:
        """Verify that setting the cancel event stops transcription."""
        import threading
        from ui.app.core.transcription import transcribe

        sample = FIXTURES_DIR / "sample_audio.wav"
        if not sample.exists():
            pytest.skip("sample_audio.wav fixture not found")

        cancel = threading.Event()
        cancel.set()  # Pre-cancel

        result = transcribe(
            str(sample),
            model_size="tiny",
            device="cpu",
            compute_type="int8",
            cancel_event=cancel,
            vad_filter=False,
        )

        # Should return early with no segments
        assert result.segments == []
