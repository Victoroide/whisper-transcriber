# Running Python Tests (`tests/python/`)

The Python frontend uses the standard `pytest` framework to validate all utilities and UI-agnostic core logic. The test suite avoids launching CustomTkinter directly (since graphical testing requires complex OS-level mocks), focusing instead on module correctness.

## Test Categories

### Data Exporting (`test_export.py`)

Validates that the `ui/app/core/export.py` module generates standard files perfectly.

- **Assertions**: Checks for correct WebVTT headers (`WEBVTT`), SRT sequential item blocks, explicit formatting differences (e.g., `,` vs `.` in timestamps), and valid JSON arrays.

### Text Processor (`test_text_utils.py`)

Ensures the Whisper hallucination safeguards are effective.

- **Assertions**: Passes strings mimicking Whisper failure states such as repetitive commas `,,,,` and duplicate phrases `Hello Hello Hello` to guarantee the `remove_repetitions` regex correctly intervenes without corrupting legitimate grammar.

### Mock Transcription (`test_transcription.py`)

This is the most critical test block. Because testing requires an audio file, it programmatically relies on the binary stored at `tests/python/fixtures/jfk.wav`.

- **Assertions**: It initializes a real `faster-whisper` thread against the `tiny` model predicting CPU hardware. It asserts that the text payload genuinely contains the speech string `"ask not what your country can do for you"`.

## Running the Suite

Ensure you are located at the repository root with your `.venv` activated.

```bash
python -m pytest tests/python/ -v
```

You should see 25+ checks resolve green.
