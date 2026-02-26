# Component Lifecycle (`ui/app/window.py`)

A graphical interface handling long-running background Machine Learning tasks must strictly manage the enabled/disabled state of its child widgets to prevent the user from triggering conflicting events (e.g., clicking "Export" before the transcription is actually finished, or dragging a new video into the DropZone while the current video is actively being decoded).

## Lifecycle States

### 1. The IDLE State

This is the application's default resting state immediately upon launch (`if __name__ == "__main__":`).

- **Active Features**:
  1. The `DropZone` border is highlighted and actively listening for OS-level Drag-and-Drop file events.
  2. Theme and Settings toggles in the `Toolbar` respond freely.
  3. The `ModelSelector` comboboxes are unlocked, allowing the user to select dictionary sizes (e.g., `tiny`, `small`, `large-v3`).
- **Disabled Features**:
  1. The `ProgressBar` frame is `.pack_forget()`, rendering it completely invisible.
  2. The Export buttons are entirely disabled since `self._current_segments` array is empty.

### 2. The ACTIVE (PROCESSING) State

This lifecycle occurs exactly when the user drops a valid media file, or selects one via `filedialog`. The `_on_file_selected(file_path)` method is invoked globally.

- **Destructive Actions**:
  1. Flushes the `TranscriptView` textbox entirely if it contained a previous output.
  2. The `ModelSelector` inputs are hard-disabled (`state="disabled"`).
  3. The `DropZone` is deactivated and overlaid with an "Adding file is disabled while processing..." translucent tint.
- **Constructive Actions**:
  1. Summons the `ProgressBar` frame visibly using `.pack()`.
  2. Modifies the primary UI string to "Connecting to Core..."
  3. Spawns the IPC connection to the Go process.

### 3. The FINISHED State

Triggered exclusively when the background transcriber mathematical loop generator encounters an exhausting `StopIteration`.

- **Actions**:
  1. Returns the `DropZone` back to receptive mode (IDLE).
  2. Restores the `ModelSelector`.
  3. Unlocks the generic Toolbar Export buttons (TXT, SRT, VTT, JSON), enabling the user to save the results.
  4. Automatically invokes `_reset_progress_bar()` to collapse the visual loading component securely.
