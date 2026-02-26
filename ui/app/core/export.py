import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

Segment = tuple[float, float, str]


def export_txt(segments: list[Segment], output_path: str | Path) -> None:
    """Export transcript as plain text without timestamps."""
    output_path = Path(output_path)
    text = " ".join(seg[2] for seg in segments)
    output_path.write_text(text, encoding="utf-8")
    logger.info("Exported TXT to %s", output_path)


def export_srt(segments: list[Segment], output_path: str | Path) -> None:
    """Export transcript in SubRip (.srt) format."""
    output_path = Path(output_path)
    lines: list[str] = []

    for i, (start, end, text) in enumerate(segments, 1):
        start_ts = _format_srt_timestamp(start)
        end_ts = _format_srt_timestamp(end)
        lines.append(str(i))
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Exported SRT to %s", output_path)


def export_vtt(segments: list[Segment], output_path: str | Path) -> None:
    """Export transcript in WebVTT (.vtt) format."""
    output_path = Path(output_path)
    lines: list[str] = ["WEBVTT", ""]

    for start, end, text in segments:
        start_ts = _format_vtt_timestamp(start)
        end_ts = _format_vtt_timestamp(end)
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(text)
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Exported VTT to %s", output_path)


def export_json(segments: list[Segment], output_path: str | Path) -> None:
    """Export transcript as structured JSON."""
    output_path = Path(output_path)
    data = {
        "segments": [
            {"start": start, "end": end, "text": text}
            for start, end, text in segments
        ],
        "text": " ".join(seg[2] for seg in segments),
    }
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Exported JSON to %s", output_path)


def _format_srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_vtt_timestamp(seconds: float) -> str:
    """Convert seconds to WebVTT timestamp format: HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
