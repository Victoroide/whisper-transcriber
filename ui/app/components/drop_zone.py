import logging
from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm",
    ".mp3", ".wav", ".m4a", ".ogg", ".flac",
}

FILETYPES = [
    ("Media files", " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))),
    ("All files", "*.*"),
]


class DropZone(ctk.CTkFrame):
    """Drag-and-drop area for selecting audio/video files.

    Falls back to a file browser dialog when clicked. Displays the
    selected file name and duration after selection.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_file_selected: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_file_selected = on_file_selected
        self._file_path: str | None = None

        self.configure(
            corner_radius=12,
            border_width=2,
            border_color=("gray70", "gray30"),
            fg_color=("gray95", "gray17"),
            height=100,
        )

        self._label = ctk.CTkLabel(
            self,
            text="Drop video or audio file here\nor click to browse",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),
        )
        self._label.pack(expand=True, fill="both", padx=20, pady=10)

        self._browse_btn = ctk.CTkButton(
            self,
            text="Select File",
            command=self._browse,
            width=120,
            height=32,
            cursor="hand2",
        )
        self._browse_btn.pack(pady=(0, 15))

        # Bind click on the label/frame to trigger browse
        self._label.bind("<Button-1>", lambda e: self._browse())
        self.bind("<Button-1>", lambda e: self._browse())

        self._setup_drag_and_drop()

    def _setup_drag_and_drop(self) -> None:
        """Configure tkinterdnd2 drag-and-drop if available."""
        try:
            self.drop_target_register("DND_Files")
            self.dnd_bind("<<Drop>>", self._on_drop)
            self.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            self.dnd_bind("<<DragLeave>>", self._on_drag_leave)
        except (AttributeError, Exception) as exc:
            logger.debug("Drag-and-drop not available: %s", exc)

    def _on_drop(self, event) -> None:
        """Handle file drop event."""
        path = event.data.strip()
        if path.startswith("{") and path.endswith("}"):
            path = path[1:-1]

        file_path = Path(path)
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            self._select_file(str(file_path))
        else:
            logger.warning("Unsupported file format: %s", file_path.suffix)

        self.configure(border_color=("gray70", "gray30"))

    def _on_drag_enter(self, event) -> None:
        """Visual feedback when a file is dragged over."""
        self.configure(border_color=("#4b6bfb", "#4b6bfb"))

    def _on_drag_leave(self, event) -> None:
        """Reset visual feedback."""
        self.configure(border_color=("gray70", "gray30"))

    def _browse(self) -> None:
        """Open a file browser dialog."""
        path = filedialog.askopenfilename(
            title="Select an audio or video file",
            filetypes=FILETYPES,
        )
        if path:
            self._select_file(path)

    def _select_file(self, path: str) -> None:
        """Process a selected file path."""
        self._file_path = path
        name = Path(path).name
        self._label.configure(text=name, text_color=("gray10", "gray90"))
        self._on_file_selected(path)

    def set_duration(self, seconds: float) -> None:
        """Update the label to show file name and duration."""
        if self._file_path:
            name = Path(self._file_path).name
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            self._label.configure(text=f"{name}  ({minutes}:{secs:02d})")

    def reset(self) -> None:
        """Reset the drop zone to its initial state."""
        self._file_path = None
        self._label.configure(
            text="Drop video or audio file here\nor click to browse",
            text_color=("gray40", "gray60"),
        )

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the browse button."""
        state = "normal" if enabled else "disabled"
        self._browse_btn.configure(state=state)
