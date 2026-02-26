# Window Layout (`ui/app/window.py`)

The application leverages the `customtkinter` (CTk) library to present a dark-mode, hardware-accelerated user interface. The `MainWindow` class orchestrates the instantiation, placement, and event binding of all specialized custom child widgets.

## Hierarchy Structure

The UI utilizes a vertically stacked `.pack()` layout system inside a master `main_pad` transparent frame, offering responsive elasticity.

1.  **Toolbar (`ui/app/components/toolbar.py`)**
    - **Position**: Pinned precisely to the top row using `.pack(fill="x")`.
    - **Functionality**: Hosts the application's logo banner and utility action buttons (Copy to Clipboard, Export, Settings, Theme Toggle).
2.  **Model Selector (`ui/app/components/model_selector.py`)**
    - **Position**: Sub-frame directly beneath the toolbar.
    - **Functionality**: Provides three discrete dropdown combo-boxes mapping directly to `faster-whisper` parameters (Model Size, Computing Hardware [CPU/CUDA], and Quantization precision).
3.  **Drop Zone (`ui/app/components/drop_zone.py`)**
    - **Position**: Mid-section container featuring a prominent dashed border.
    - **Functionality**: Registers OS-level Drag-and-Drop file path events via `tkinterdnd2` natively supporting both Windows Path resolutions and Unix URI interpretations. Allows manual file picking via `ctk.filedialog`.
4.  **Progress Bar (`ui/app/components/progress_bar.py`)**
    - **Position**: Renders explicitly _only_ when the system establishes an IPC transport connection and begins processing.
    - **Functionality**: Features a determinant integer-mapping percentage bar, a status text label (e.g., "Extracting Chunks..."), and a highly conspicuous Red Cancellation trigger bounding to the Go Core interrupt sequences.
5.  **Transcript View (`ui/app/components/transcript_view.py`)**
    - **Position**: The dominant bottom-half expanding text box taking up remaining vertical space via `expand=True`.
    - **Functionality**: Read-only `CTkTextbox` populated continuously as the `_streaming_transcription_worker` yields mathematical text segments.

## Theme Engine

The window initializes explicitly utilizing the `#1a1a1a` Dark theme by default but saves persistent modifications into the system's local configuration JSON payload utilizing `utils/platform.py` for subsequent restarts.
