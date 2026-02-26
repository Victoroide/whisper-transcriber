# Export Formats (`ui/app/core/export.py`)

The `export.py` module handles translating the internal python tuple lists (`[(start_sec, end_sec, "text")]`) representing the final transcription into an array of user-friendly standard subtitle formats.

## Output Matrix

### 1. Plain Text (`export_txt`)

- **Format Layout**: Purely concatenates the `text` string variables sequentially. Trims arbitrary leading whitespaces.
- **Ideal Use-case**: Reading the dialog like an essay.
- **Example Output**:
  ```
  Hi everybody, welcome to the presentation. My name is Alice.
  Today we will be discussing the architecture of Go.
  ```

### 2. SRT (`export_srt`)

- **Format Layout**: The SubRip Subtitle file format is the universal standard for video players.
- **Structure**:

1. A sequential index block integer.
2. The timestamp range `HH:MM:SS,mmm --> HH:MM:SS,mmm`.
3. The isolated sentence.

- **Code Implementation**: Includes a mathematically precise helper `_format_timestamp(seconds, separator)` converting the primitive float `131.5` into `00:02:11,500`.

### 3. VTT (`export_vtt`)

- **Format Layout**: Web Video Text Tracks is an HTML5 standard for providing subtitles overlaid mathematically onto `<video>` web elements.
- **Structure**: Almost biologically identical to `.srt`, with two critical exceptions handled correctly by this module:

1. It _requires_ the file header `WEBVTT` at line 1.
2. The millisecond separator is strictly a period (`HH:MM:SS.mmm`) rather than a comma.

### 4. JSON (`export_json`)

- **Format Layout**: Machine-readable format.
- **Structure**: Dumps an array of segment objects `{"start": 0.0, "end": 5.0, "text": "Hi"}` directly via the standard python `json` import, retaining maximum metadata for post-processing scripting.
