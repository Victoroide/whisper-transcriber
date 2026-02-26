import customtkinter as ctk


class Toast(ctk.CTkToplevel):
    """Non-blocking toast notification that appears in the bottom-right
    corner of the parent window.

    Supports three styles: success (green), error (red), and warning (yellow).
    Auto-dismisses after the specified duration.
    """

    COLORS = {
        "success": ("#10b981", "#059669"),
        "error": ("#ef4444", "#dc2626"),
        "warning": ("#f59e0b", "#d97706"),
    }

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        message: str,
        style: str = "success",
        duration_ms: int = 3000,
    ) -> None:
        super().__init__(master)

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        bg_color = self.COLORS.get(style, self.COLORS["success"])

        self._frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=bg_color,
            width=320,
            height=50,
        )
        self._frame.pack(fill="both", expand=True, padx=2, pady=2)
        self._frame.pack_propagate(False)

        label = ctk.CTkLabel(
            self._frame,
            text=message,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white",
        )
        label.pack(expand=True, padx=15)

        # Position the toast at the bottom-right of the parent window
        self.update_idletasks()
        parent = master.winfo_toplevel()
        x = parent.winfo_x() + parent.winfo_width() - 340
        y = parent.winfo_y() + parent.winfo_height() - 70
        self.geometry(f"320x50+{x}+{y}")

        self.after(duration_ms, self._fade_out)

    def _fade_out(self) -> None:
        """Destroy the toast window."""
        try:
            self.destroy()
        except Exception:
            pass


def show_toast(
    master: ctk.CTkBaseClass,
    message: str,
    style: str = "success",
    duration_ms: int = 3000,
) -> Toast:
    """Convenience function to create and show a toast notification."""
    return Toast(master, message, style=style, duration_ms=duration_ms)
