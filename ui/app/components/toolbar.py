import logging
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

logger = logging.getLogger(__name__)


class Toolbar(ctk.CTkFrame):
    """Bottom toolbar with Copy, Save, and Export buttons.

    The Export button opens a dropdown for selecting the output format
    (TXT, SRT, VTT, JSON).
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_copy: Callable[[], None],
        on_save_txt: Callable[[str], None],
        on_export: Callable[[str, str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_copy = on_copy
        self._on_save_txt = on_save_txt
        self._on_export = on_export

        self._copy_btn = ctk.CTkButton(
            self,
            text="Copy",
            width=90,
            height=32,
            cursor="hand2",
            command=self._handle_copy,
        )
        self._copy_btn.pack(side="left", padx=(0, 8))

        self._save_btn = ctk.CTkButton(
            self,
            text="Save .txt",
            width=100,
            height=32,
            cursor="hand2",
            command=self._handle_save_txt,
        )
        self._save_btn.pack(side="left", padx=(0, 8))

        self._export_menu = ctk.CTkOptionMenu(
            self,
            values=["Save as .srt", "Save as .vtt", "Save as .json"],
            command=self._handle_export,
            width=140,
            height=32,
            cursor="hand2",
        )
        self._export_menu.set("Export")
        self._export_menu.pack(side="left")

    def _handle_copy(self) -> None:
        """Copy transcript text to clipboard."""
        self._on_copy()

    def _handle_save_txt(self) -> None:
        """Open save dialog for plain text export."""
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self._on_save_txt(path)

    def _handle_export(self, choice: str) -> None:
        """Open save dialog for the selected export format."""
        format_map = {
            "Save as .srt": (".srt", [("SubRip files", "*.srt")]),
            "Save as .vtt": (".vtt", [("WebVTT files", "*.vtt")]),
            "Save as .json": (".json", [("JSON files", "*.json")]),
        }

        ext, filetypes = format_map.get(choice, (".txt", [("All files", "*.*")]))
        filetypes.append(("All files", "*.*"))

        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=filetypes,
        )
        if path:
            fmt = ext.lstrip(".")
            self._on_export(path, fmt)

        # Reset the dropdown text after selection
        self._export_menu.set("Export")

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all toolbar buttons."""
        state = "normal" if enabled else "disabled"
        self._copy_btn.configure(state=state)
        self._save_btn.configure(state=state)
        self._export_menu.configure(state=state)
