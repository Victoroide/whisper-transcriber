import customtkinter as ctk


class TranscriptView(ctk.CTkFrame):
    """Scrollable text area for displaying transcription results in real-time.

    Text auto-scrolls to follow new content. The textbox is read-only
    during transcription and editable afterwards for user corrections.
    """

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=13),
            wrap="word",
            corner_radius=8,
            border_width=1,
            border_color=("gray70", "gray30"),
        )
        self._textbox.pack(fill="both", expand=True)

    def append_text(self, text: str) -> None:
        """Append text to the transcript and scroll to the bottom."""
        self._textbox.insert("end", text)
        self._textbox.see("end")

    def set_text(self, text: str) -> None:
        """Replace all text in the transcript view."""
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", text)

    def get_text(self) -> str:
        """Return all text from the transcript view."""
        return self._textbox.get("1.0", "end").strip()

    def clear(self) -> None:
        """Remove all text from the transcript view."""
        self._textbox.delete("1.0", "end")

    def set_read_only(self, read_only: bool) -> None:
        """Toggle read-only mode for the textbox."""
        state = "disabled" if read_only else "normal"
        self._textbox.configure(state=state)
