import customtkinter as ctk


class ProgressBar(ctk.CTkFrame):
    """Progress bar with an integrated status text label.

    Shows a percentage-based progress bar and a descriptive message
    about the current operation.
    """

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
            anchor="w",
        )
        self._status_label.pack(fill="x", pady=(0, 4))

        self._progress = ctk.CTkProgressBar(self, height=8)
        self._progress.pack(fill="x")
        self._progress.set(0)

        self._cancel_btn = ctk.CTkButton(
            self,
            text="Cancel",
            width=80,
            height=28,
            cursor="hand2",
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("gray10", "gray90"),
        )
        self._cancel_callback = None

    def set_progress(self, value: float, message: str = "") -> None:
        """Update progress bar value (0-100) and status message."""
        self._progress.set(value / 100.0)
        if message:
            self._status_label.configure(text=message)

    def set_status(self, message: str) -> None:
        """Update only the status message without changing the progress bar."""
        self._status_label.configure(text=message)

    def reset(self) -> None:
        """Reset progress bar to zero and status to Ready."""
        self._progress.set(0)
        self._status_label.configure(text="Ready")
        self.hide_cancel()

    def show_cancel(self, callback) -> None:
        """Show the cancel button with the given callback."""
        self._cancel_callback = callback
        self._cancel_btn.configure(command=callback)
        self._cancel_btn.pack(pady=(6, 0), anchor="w")

    def hide_cancel(self) -> None:
        """Hide the cancel button."""
        self._cancel_btn.pack_forget()
        self._cancel_callback = None
