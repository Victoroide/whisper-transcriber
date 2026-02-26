import logging
from typing import Callable

import customtkinter as ctk

logger = logging.getLogger(__name__)

MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]

MODEL_DESCRIPTIONS = {
    "tiny": "Fastest, lowest accuracy (~1GB RAM)",
    "base": "Fast, basic accuracy (~1GB RAM)",
    "small": "Balanced speed and accuracy (~2GB RAM)",
    "medium": "Good accuracy, moderate speed (~5GB RAM)",
    "large-v3": "Best accuracy, slowest (~10GB RAM)",
}


class ModelSelector(ctk.CTkFrame):
    """Model size dropdown with device info display and hardware recommendation.

    Shows the currently selected model, detected device and compute type,
    and a tooltip explaining model tradeoffs.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_model_changed: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_model_changed = on_model_changed
        self._device = "cpu"
        self._compute_type = "int8"
        self._recommended: str | None = None

        model_label = ctk.CTkLabel(self, text="Model:", font=ctk.CTkFont(size=13))
        model_label.pack(side="left", padx=(0, 8))

        self._model_var = ctk.StringVar(value="small")
        self._dropdown = ctk.CTkOptionMenu(
            self,
            variable=self._model_var,
            values=MODEL_SIZES,
            command=self._on_change,
            width=120,
            height=28,
            cursor="hand2",
        )
        self._dropdown.pack(side="left", padx=(0, 15))

        self._device_label = ctk.CTkLabel(
            self,
            text="Device: auto (CPU / INT8)",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        self._device_label.pack(side="left", padx=(0, 8))

        self._help_btn = ctk.CTkButton(
            self,
            text="?",
            width=28,
            height=28,
            corner_radius=14,
            command=self._show_help,
            cursor="hand2",
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            text_color=("gray20", "gray80"),
        )
        self._help_btn.pack(side="left", padx=(0, 10))

        self._badge_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#10b981", "#10b981"),
        )
        self._badge_label.pack(side="left")

    def set_hardware_info(
        self,
        device: str,
        compute_type: str,
        recommended_model: str,
    ) -> None:
        """Update device display based on hardware detection from Go core."""
        self._device = device
        self._compute_type = compute_type
        self._recommended = recommended_model

        device_text = device.upper() if device != "auto" else "CPU"
        self._device_label.configure(
            text=f"Device: auto ({device_text} / {compute_type.upper()})"
        )

        self._model_var.set(recommended_model)
        self._badge_label.configure(text="Recommended for your system")
        logger.info(
            "Hardware recommendation: model=%s, device=%s, compute=%s",
            recommended_model, device, compute_type,
        )

    def get_model(self) -> str:
        """Return the currently selected model size."""
        return self._model_var.get()

    def get_device(self) -> str:
        """Return the detected device."""
        return self._device

    def get_compute_type(self) -> str:
        """Return the detected compute type."""
        return self._compute_type

    def _on_change(self, value: str) -> None:
        """Handle model selection change."""
        if self._recommended and value == self._recommended:
            self._badge_label.configure(text="Recommended for your system")
        else:
            self._badge_label.configure(text="")

        if self._on_model_changed:
            self._on_model_changed(value)

    def _show_help(self) -> None:
        """Show a tooltip window explaining model sizes."""
        help_window = ctk.CTkToplevel(self)
        help_window.title("Model Guide")
        help_window.geometry("380x280")
        help_window.resizable(False, False)
        help_window.transient(self.winfo_toplevel())
        help_window.grab_set()

        title = ctk.CTkLabel(
            help_window,
            text="Whisper Model Sizes",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        title.pack(pady=(15, 10))

        for model, desc in MODEL_DESCRIPTIONS.items():
            row = ctk.CTkFrame(help_window, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)

            name_label = ctk.CTkLabel(
                row,
                text=f"{model}:",
                font=ctk.CTkFont(size=12, weight="bold"),
                width=80,
                anchor="w",
            )
            name_label.pack(side="left")

            desc_label = ctk.CTkLabel(
                row,
                text=desc,
                font=ctk.CTkFont(size=12),
                anchor="w",
            )
            desc_label.pack(side="left", fill="x", expand=True)

        close_btn = ctk.CTkButton(
            help_window,
            text="Close",
            command=help_window.destroy,
            width=80,
            cursor="hand2",
        )
        close_btn.pack(pady=15)
