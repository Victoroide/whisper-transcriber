"""Tests for ui.app.core.export -- TXT, SRT, VTT, JSON exporters."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ui.app.core.export import export_json, export_srt, export_txt, export_vtt

# Sample segments for testing: (start_seconds, end_seconds, text)
SAMPLE_SEGMENTS = [
    (0.0, 2.5, "Hello and welcome."),
    (2.5, 5.8, "This is a test transcript."),
    (6.0, 10.2, "It contains multiple segments."),
]


class TestExportTxt:
    """Verify plain text export."""

    def test_produces_plain_text(self, tmp_path: Path) -> None:
        output = tmp_path / "out.txt"
        export_txt(SAMPLE_SEGMENTS, output)
        content = output.read_text(encoding="utf-8")
        assert "Hello and welcome." in content
        assert "This is a test transcript." in content
        assert "-->" not in content

    def test_empty_segments(self, tmp_path: Path) -> None:
        output = tmp_path / "empty.txt"
        export_txt([], output)
        content = output.read_text(encoding="utf-8")
        assert content.strip() == ""


class TestExportSrt:
    """Verify SubRip format output."""

    def test_has_sequential_numbers(self, tmp_path: Path) -> None:
        output = tmp_path / "out.srt"
        export_srt(SAMPLE_SEGMENTS, output)
        content = output.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert lines[0] == "1"

    def test_has_correct_timestamp_format(self, tmp_path: Path) -> None:
        output = tmp_path / "out.srt"
        export_srt(SAMPLE_SEGMENTS, output)
        content = output.read_text(encoding="utf-8")
        # SRT uses comma for milliseconds: HH:MM:SS,mmm --> HH:MM:SS,mmm
        assert "00:00:00,000 --> 00:00:02,500" in content

    def test_has_blank_line_separation(self, tmp_path: Path) -> None:
        output = tmp_path / "out.srt"
        export_srt(SAMPLE_SEGMENTS, output)
        content = output.read_text(encoding="utf-8")
        blocks = content.strip().split("\n\n")
        assert len(blocks) == len(SAMPLE_SEGMENTS)

    def test_segment_text_present(self, tmp_path: Path) -> None:
        output = tmp_path / "out.srt"
        export_srt(SAMPLE_SEGMENTS, output)
        content = output.read_text(encoding="utf-8")
        for _, _, text in SAMPLE_SEGMENTS:
            assert text in content


class TestExportVtt:
    """Verify WebVTT format output."""

    def test_starts_with_webvtt_header(self, tmp_path: Path) -> None:
        output = tmp_path / "out.vtt"
        export_vtt(SAMPLE_SEGMENTS, output)
        content = output.read_text(encoding="utf-8")
        assert content.startswith("WEBVTT")

    def test_uses_dot_for_milliseconds(self, tmp_path: Path) -> None:
        output = tmp_path / "out.vtt"
        export_vtt(SAMPLE_SEGMENTS, output)
        content = output.read_text(encoding="utf-8")
        # VTT uses dot for milliseconds: HH:MM:SS.mmm
        assert "00:00:00.000 --> 00:00:02.500" in content

    def test_contains_all_segments(self, tmp_path: Path) -> None:
        output = tmp_path / "out.vtt"
        export_vtt(SAMPLE_SEGMENTS, output)
        content = output.read_text(encoding="utf-8")
        for _, _, text in SAMPLE_SEGMENTS:
            assert text in content


class TestExportJson:
    """Verify JSON export format."""

    def test_valid_json(self, tmp_path: Path) -> None:
        output = tmp_path / "out.json"
        export_json(SAMPLE_SEGMENTS, output)
        content = output.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_has_segments_array(self, tmp_path: Path) -> None:
        output = tmp_path / "out.json"
        export_json(SAMPLE_SEGMENTS, output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert "segments" in data
        assert len(data["segments"]) == len(SAMPLE_SEGMENTS)

    def test_segment_schema(self, tmp_path: Path) -> None:
        output = tmp_path / "out.json"
        export_json(SAMPLE_SEGMENTS, output)
        data = json.loads(output.read_text(encoding="utf-8"))
        seg = data["segments"][0]
        assert "start" in seg
        assert "end" in seg
        assert "text" in seg
        assert seg["text"] == "Hello and welcome."

    def test_has_full_text(self, tmp_path: Path) -> None:
        output = tmp_path / "out.json"
        export_json(SAMPLE_SEGMENTS, output)
        data = json.loads(output.read_text(encoding="utf-8"))
        assert "text" in data
        assert "Hello and welcome." in data["text"]
