import logging
import threading
from pathlib import Path
from typing import Any, Generator

from ui.app.core.model_cache import get_model

logger = logging.getLogger(__name__)

Segment = tuple[float, float, str]


class TranscriptionResult:
    """Holds the output of a transcription run."""

    def __init__(self) -> None:
        self.segments: list[Segment] = []
        self.language: str = ""
        self.language_probability: float = 0.0

    @property
    def text(self) -> str:
        """Return the full transcript as a single string."""
        return " ".join(seg[2] for seg in self.segments)

    @property
    def duration(self) -> float:
        """Return total duration covered by segments in seconds."""
        if not self.segments:
            return 0.0
        return self.segments[-1][1]


def transcribe(
    audio_path: str | Path,
    model_size: str = "small",
    device: str = "auto",
    compute_type: str = "int8",
    cancel_event: threading.Event | None = None,
    segment_callback: Any | None = None,
    progress_callback: Any | None = None,
    vad_filter: bool = True,
) -> TranscriptionResult:
    """Transcribe an audio file using faster-whisper.

    Args:
        audio_path: Path to 16kHz mono WAV file.
        model_size: Whisper model size (tiny, base, small, medium, large-v3).
        device: Device to use (auto, cpu, cuda).
        compute_type: Compute type (int8, float16, float32).
        cancel_event: Threading event to signal cancellation.
        segment_callback: Called with (start, end, text) for each segment.
        progress_callback: Called with (percent, message) for progress updates.
        vad_filter: Enable VAD filtering to skip non-speech audio segments.

    Returns:
        TranscriptionResult with all segments and metadata.
    """
    result = TranscriptionResult()
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    file_size = audio_path.stat().st_size
    if file_size < 16000:
        raise ValueError("Audio is too short to transcribe.")

    if progress_callback:
        progress_callback(10, f"Loading {model_size} model...")

    try:
        model = get_model(model_size, device, compute_type)
    except Exception as exc:
        logger.error("Failed to load model: %s", exc)
        raise RuntimeError(f"Failed to load model: {exc}") from exc

    if _is_cancelled(cancel_event):
        return result

    if progress_callback:
        progress_callback(30, "Transcribing audio...")

    try:
        segments_gen, info = model.transcribe(
            str(audio_path),
            beam_size=5,
            vad_filter=vad_filter,
        )
        result.language = info.language
        result.language_probability = info.language_probability
    except Exception as exc:
        logger.error("Transcription failed: %s", exc)
        raise RuntimeError(f"Transcription failed: {exc}") from exc

    estimated_duration = file_size / 32000.0
    for segment in segments_gen:
        if _is_cancelled(cancel_event):
            logger.info("Transcription cancelled by user")
            break

        text = segment.text.strip()
        if not text:
            continue

        entry = (segment.start, segment.end, text)
        result.segments.append(entry)

        if segment_callback:
            segment_callback(entry[0], entry[1], entry[2])

        if progress_callback and estimated_duration > 0:
            pct = min(95, int(30 + (segment.end / estimated_duration) * 65))
            progress_callback(pct, f"Transcribing... {segment.end:.1f}s processed")

    if not result.segments and not _is_cancelled(cancel_event):
        logger.warning("No speech detected in audio file: %s", audio_path)

    if progress_callback and not _is_cancelled(cancel_event):
        progress_callback(100, "Transcription complete")

    return result


def _is_cancelled(event: threading.Event | None) -> bool:
    """Check if cancellation has been requested."""
    return event is not None and event.is_set()
