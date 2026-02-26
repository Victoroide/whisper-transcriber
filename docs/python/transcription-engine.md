# Transcription Engine (`ui/app/core/transcription.py`)

The transcription engine is the Python interface to the `faster-whisper` CTranslate2 models. It is responsible for initializing the GPU tensors, decoding the raw `.wav` chunks incoming from the Go core, and translating spoken audio into localized segments.

## Primary Method: `transcribe()`

```python
def transcribe(
    audio_path: str,
    model_size: str = "small",
    device: str = "cpu",
    compute_type: str = "int8",
    cancel_event: threading.Event | None = None,
    segment_callback: Callable[[float, float, str], None] | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
    vad_filter: bool = True
) -> TranscriptionResult
```

### Parameters

- `audio_path`: The absolute path to the `.wav` chunk extracted by the Go worker pool.
- `model_size`: The specific Hugging Face repository tag (`tiny`, `small`, `base`, `medium`, `large-v3`).
- `device`: The hardware target (`cuda` or `cpu`). Derived from the `_handle_hardware_info` event.
- `compute_type`: Tensor precision (`float16` for GPUs, `int8` for CPUs).
- `cancel_event`: A `threading.Event` monitored continuously during the transcribing generator loop. If triggered, execution aborts immediately to save compute time.
- `segment_callback`: Executes _as soon as_ a phrase is transcribed. This is key to the application's real-time streaming feel.
- `vad_filter`: Voice Activity Detection. If true, the model skips periods of silence robustly. (Passed as `False` for synthetic benchmark pieces).

### Execution Flow

1.  **Instantiation**: Leverages the `ModelCache` to fetch the cached `faster_whisper.WhisperModel` object. This avoids devastating reload times.
2.  **Inference**: Invokes `model.transcribe()`.
3.  **Yielding Loop**: The `faster-whisper` library natively yields segments sequentially. The engine iterates over this generator, calculating mathematical percentages of completion and executing the caller's `segment_callback` to instantly update the Tkinter UI without waiting for the entire audio file to process natively.

## Data Structures

### `TranscriptionResult`

A simple dataclass encapsulating the aggregated metrics once the generator exhausts completely.

```python
@dataclass
class TranscriptionResult:
    text: str = ""
    segments: list[tuple[float, float, str]] = field(default_factory=list)
    language: str | None = None
```

This immutable artifact is stored in the UI's state variables and serves as the sole input to the `export.py` formatters.
