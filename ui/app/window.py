import logging
import threading
import traceback
from pathlib import Path
from queue import Empty, Queue
from typing import Any

import customtkinter as ctk

from ui.app.components.drop_zone import DropZone
from ui.app.components.model_selector import ModelSelector
from ui.app.components.progress_bar import ProgressBar
from ui.app.components.toast import show_toast
from ui.app.components.toolbar import Toolbar
from ui.app.components.transcript_view import TranscriptView
from ui.app.core.export import export_json, export_srt, export_txt, export_vtt
from ui.app.core.ipc_client import IPCClient
from ui.app.core.transcription import TranscriptionResult, transcribe
from ui.app.utils.platform import load_config, save_config
from ui.app.utils.text import clean_transcript, remove_repetitions

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """Main application window assembling all components into the specified layout.

    Manages the transcription workflow: file selection, Go core IPC communication,
    faster-whisper inference, real-time transcript display, and export.
    """

    MIN_WIDTH = 720
    MIN_HEIGHT = 500
    DEFAULT_WIDTH = 900
    DEFAULT_HEIGHT = 620

    def __init__(self, ipc_client: IPCClient | None = None) -> None:
        super().__init__()

        self._config = load_config()
        self._ipc_client = ipc_client
        self._cancel_event = threading.Event()
        self._transcription_result: TranscriptionResult | None = None
        self._transcription_thread: threading.Thread | None = None
        self._file_path: str | None = None
        
        # Audio Streaming State
        self._chunk_queue: Queue[dict[str, Any]] = Queue()
        self._chunks_expected: int | None = None
        self._chunks_processed = 0

        self._setup_window()
        self._build_layout()
        self._bind_shortcuts()
        self._register_ipc_handlers()
        self._start_ipc_polling()

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.title("Whisper Transcriber")

        width = self._config.get("window_width", self.DEFAULT_WIDTH)
        height = self._config.get("window_height", self.DEFAULT_HEIGHT)
        self.geometry(f"{width}x{height}")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        theme = self._config.get("theme", "dark")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        """Assemble all UI components into the window layout."""
        main_pad = ctk.CTkFrame(self, fg_color="transparent")
        main_pad.pack(fill="both", expand=True, padx=25, pady=15)

        # Header row
        header = ctk.CTkFrame(main_pad, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        title = ctk.CTkLabel(
            header,
            text="Whisper Transcriber",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(side="left")

        self._theme_switch = ctk.CTkSwitch(
            header,
            text="Dark",
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light",
            cursor="hand2",
        )
        current_theme = self._config.get("theme", "dark")
        if current_theme == "dark":
            self._theme_switch.select()
        else:
            self._theme_switch.deselect()
        self._theme_switch.pack(side="right")

        # Drop zone
        self._drop_zone = DropZone(
            main_pad,
            on_file_selected=self._on_file_selected,
        )
        self._drop_zone.pack(fill="x", pady=(0, 10))

        # Model selector
        self._model_selector = ModelSelector(
            main_pad,
            on_model_changed=self._on_model_changed,
        )
        self._model_selector.pack(fill="x", pady=(0, 10))

        # Progress bar
        self._progress_bar = ProgressBar(main_pad)
        self._progress_bar.pack(fill="x", pady=(0, 10))

        # Transcript view
        self._transcript_view = TranscriptView(main_pad)
        self._transcript_view.pack(fill="both", expand=True, pady=(0, 10))

        # Toolbar
        self._toolbar = Toolbar(
            main_pad,
            on_copy=self._on_copy,
            on_save_txt=self._on_save_txt,
            on_export=self._on_export,
        )
        self._toolbar.pack(fill="x")
        self._toolbar.set_enabled(False)

    def _bind_shortcuts(self) -> None:
        """Register keyboard shortcuts."""
        self.bind("<Control-o>", lambda e: self._drop_zone._browse())
        self.bind("<Control-s>", lambda e: self._toolbar._handle_save_txt())
        self.bind("<Control-c>", lambda e: self._on_copy())
        self.bind("<Escape>", lambda e: self._on_cancel())

    def _register_ipc_handlers(self) -> None:
        """Register handlers for messages from the Go core."""
        if self._ipc_client is None:
            return

        self._ipc_client.on("hardware_info", self._handle_hardware_info)
        self._ipc_client.on("audio_extract_progress", self._handle_extract_progress)
        self._ipc_client.on("audio_chunk", self._handle_audio_chunk)
        self._ipc_client.on("audio_extraction_complete", self._handle_audio_extraction_complete)
        self._ipc_client.on("audio_ready", self._handle_audio_ready)
        self._ipc_client.on("error", self._handle_core_error)

    def _start_ipc_polling(self) -> None:
        """Poll the IPC queue for messages from the Go core."""
        if self._ipc_client is None or not self._ipc_client.connected:
            return

        # Drain the IPCClient internal queue and call registered handlers
        # safely on the main Tkinter thread.
        self._ipc_client.update()

        self.after(100, self._start_ipc_polling)

    def _handle_hardware_info(self, data: dict[str, Any]) -> None:
        """Process hardware detection results from Go core."""
        self.after(0, lambda: self._model_selector.set_hardware_info(
            device="cuda" if data.get("cuda") else "cpu",
            compute_type=data.get("recommended_compute", "int8"),
            recommended_model=data.get("recommended_model", "small"),
        ))

    def _handle_extract_progress(self, data: dict[str, Any]) -> None:
        """Update progress bar during audio extraction."""
        pct = data.get("percent", 0)
        msg = data.get("message", "Extracting audio...")
        self.after(0, lambda: self._progress_bar.set_progress(pct * 0.3, msg))

    def _handle_audio_chunk(self, data: dict[str, Any]) -> None:
        """Enqueue an extracted audio chunk for transcription."""
        self._chunk_queue.put(data)

    def _handle_audio_extraction_complete(self, data: dict[str, Any]) -> None:
        """Signal that all chunks have been extracted."""
        self._chunks_expected = data.get("total_chunks", 0)
        duration = data.get("duration_seconds", 0)
        self.after(0, lambda: self._drop_zone.set_duration(duration))

    def _handle_audio_ready(self, data: dict[str, Any]) -> None:
        """Fallback for direct monolithic transcription if chunks fail, or for direct testing."""
        audio_path = data.get("path", "")
        duration = data.get("duration_seconds", 0)
        self.after(0, lambda: self._drop_zone.set_duration(duration))
        self.after(0, lambda: self._start_transcription_direct(audio_path))

    def _handle_core_error(self, data: dict[str, Any]) -> None:
        """Display error from Go core."""
        message = data.get("message", "Unknown error")
        self.after(0, lambda: self._show_error(message))

    def _on_file_selected(self, path: str) -> None:
        """Handle file selection from drop zone."""
        self._file_path = path
        self._transcript_view.clear()
        self._toolbar.set_enabled(False)
        self._transcription_result = TranscriptionResult()

        # Reset streaming state
        self._cancel_event.clear()
        while not self._chunk_queue.empty():
            self._chunk_queue.get_nowait()
        self._chunks_expected = None
        self._chunks_processed = 0

        self._progress_bar.show_cancel(self._on_cancel)
        self._drop_zone.set_enabled(False)

        model = self._model_selector.get_model()
        device = self._model_selector.get_device()
        compute = self._model_selector.get_compute_type()

        if self._ipc_client and self._ipc_client.connected:
            self._progress_bar.set_progress(5, "Sending to core for extraction...")
            self._transcription_thread = threading.Thread(
                target=self._streaming_transcription_worker,
                args=(model, device, compute),
                daemon=True,
                name="transcription",
            )
            self._transcription_thread.start()
            self._ipc_client.send("extract_audio", {"input_path": path})
        else:
            self._start_transcription_direct(path)

    def _start_transcription_direct(self, path: str) -> None:
        """Start transcription directly without Go core (fallback mode).

        When the Go core is not available, the Python layer handles audio
        loading directly via faster-whisper, which can accept various formats.
        """
        self._cancel_event.clear()
        self._progress_bar.show_cancel(self._on_cancel)
        self._drop_zone.set_enabled(False)

        model = self._model_selector.get_model()
        device = self._model_selector.get_device()
        compute = self._model_selector.get_compute_type()

        self._transcription_thread = threading.Thread(
            target=self._transcription_worker_legacy,
            args=(path, model, device, compute),
            daemon=True,
            name="transcription",
        )
        self._transcription_thread.start()

    def _streaming_transcription_worker(
        self, model: str, device: str, compute: str
    ) -> None:
        """Background thread that pops chunks off the queue and runs whisper."""
        try:
            while not self._cancel_event.is_set():
                # Check if we are done
                if self._chunks_expected is not None and self._chunks_processed >= self._chunks_expected:
                    self.after(0, self._on_transcription_complete)
                    break

                # Wait for the next chunk
                try:
                    chunk = self._chunk_queue.get(timeout=0.1)
                except Empty:
                    continue

                if self._cancel_event.is_set():
                    break

                chunk_path = chunk.get("path")
                chunk_start_time = chunk.get("start_time", 0.0)

                def on_segment(start: float, end: float, text: str) -> None:
                    # Offset the timestamps by the chunk's start time
                    abs_start = start + chunk_start_time
                    abs_end = end + chunk_start_time
                    entry = (abs_start, abs_end, text)
                    if self._transcription_result is not None:
                        self._transcription_result.segments.append(entry)
                    self.after(0, lambda: self._transcript_view.append_text(text + "\n"))

                def on_progress(pct: int, msg: str) -> None:
                    # Extractor handles 0-30%, transcriber handles 30-100% proportionally
                    if self._chunks_expected and self._chunks_expected > 0:
                        chunk_weight = 70.0 / self._chunks_expected
                        base = 30 + (self._chunks_processed * chunk_weight)
                        overall_pct = int(base + (pct / 100.0 * chunk_weight))
                        self.after(0, lambda: self._progress_bar.set_progress(overall_pct, f"Transcribing (Chunk {self._chunks_processed + 1})..."))

                try:
                    # Note: vad_filter can be False here to avoid errors on short chunks
                    _ = transcribe(
                        chunk_path,
                        model_size=model,
                        device=device,
                        compute_type=compute,
                        cancel_event=self._cancel_event,
                        segment_callback=on_segment,
                        progress_callback=on_progress,
                        vad_filter=False,
                    )
                except Exception as exc:
                    logger.warning("Chunk %d failed transcription: %s", chunk.get("index"), exc)
                finally:
                    # Optional: clean up the WAV chunk file to save disk space
                    try:
                        os.remove(chunk_path)
                    except OSError:
                        pass
                
                self._chunks_processed += 1

            if self._cancel_event.is_set():
                self.after(0, self._on_transcription_cancelled)

        except Exception as exc:
            logger.error("Streaming transcription failed: %s\n%s", exc, traceback.format_exc())
            self.after(0, lambda: self._show_error(str(exc)))

    def _transcription_worker_legacy(
        self, audio_path: str, model: str, device: str, compute: str
    ) -> None:
        """Background thread that runs fallback faster-whisper inference."""
        try:
            def on_segment(start: float, end: float, text: str) -> None:
                self.after(0, lambda: self._transcript_view.append_text(text + "\n"))

            def on_progress(pct: int, msg: str) -> None:
                self.after(0, lambda: self._progress_bar.set_progress(pct, msg))

            result = transcribe(
                audio_path,
                model_size=model,
                device=device,
                compute_type=compute,
                cancel_event=self._cancel_event,
                segment_callback=on_segment,
                progress_callback=on_progress,
                vad_filter=False,
            )

            if not self._cancel_event.is_set():
                if self._transcription_result is None:
                    self._transcription_result = result
                else:
                    self._transcription_result.segments.extend(result.segments)
                self.after(0, self._on_transcription_complete)
            else:
                self.after(0, self._on_transcription_cancelled)

        except Exception as exc:
            logger.error("Transcription failed: %s\n%s", exc, traceback.format_exc())
            self.after(0, lambda: self._show_error(str(exc)))

    def _on_transcription_complete(self) -> None:
        """Handle successful transcription completion."""
        self._progress_bar.set_progress(100, "Transcription complete")
        self._progress_bar.hide_cancel()
        self._drop_zone.set_enabled(True)
        self._toolbar.set_enabled(True)

        if self._transcription_result and self._transcription_result.segments:
            cleaned = clean_transcript(self._transcription_result.text)
            cleaned = remove_repetitions(cleaned)
            self._transcript_view.set_text(cleaned)
            show_toast(self, "Transcription complete", style="success")
        else:
            self._transcript_view.set_text("No speech detected in this audio.")
            show_toast(self, "No speech detected in this audio.", style="warning")

    def _on_transcription_cancelled(self) -> None:
        """Handle user cancellation."""
        self._progress_bar.reset()
        self._drop_zone.set_enabled(True)
        show_toast(self, "Transcription cancelled", style="warning")

    def _on_cancel(self) -> None:
        """Request cancellation of the current transcription."""
        self._cancel_event.set()
        if self._ipc_client and self._ipc_client.connected:
            try:
                self._ipc_client.send("cancel")
            except ConnectionError:
                pass

    def _on_copy(self) -> None:
        """Copy transcript text to system clipboard."""
        text = self._transcript_view.get_text()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            show_toast(self, "Copied to clipboard", style="success")

    def _on_save_txt(self, path: str) -> None:
        """Save transcript as plain text."""
        if self._transcription_result is None:
            return
        try:
            export_txt(self._transcription_result.segments, path)
            show_toast(self, f"Saved to {Path(path).name}", style="success")
        except OSError as exc:
            self._show_error(f"Cannot save to that location: {exc}")

    def _on_export(self, path: str, fmt: str) -> None:
        """Export transcript in the specified format."""
        if self._transcription_result is None:
            return

        exporters = {
            "srt": export_srt,
            "vtt": export_vtt,
            "json": export_json,
        }
        exporter = exporters.get(fmt)
        if exporter is None:
            self._show_error(f"Unknown export format: {fmt}")
            return

        try:
            exporter(self._transcription_result.segments, path)
            show_toast(self, f"Exported to {Path(path).name}", style="success")
        except OSError as exc:
            self._show_error(f"Cannot save to that location: {exc}")

    def _on_model_changed(self, model: str) -> None:
        """Handle model selection change -- informational only."""
        logger.info("Model changed to: %s", model)

    def _toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        current = ctk.get_appearance_mode().lower()
        new_theme = "light" if current == "dark" else "dark"
        ctk.set_appearance_mode(new_theme)

        if new_theme == "dark":
            self._theme_switch.select()
        else:
            self._theme_switch.deselect()
        self._theme_switch.configure(text=new_theme.capitalize())

        self._config["theme"] = new_theme
        save_config(self._config)

    def _show_error(self, message: str) -> None:
        """Display an error to the user via toast and reset UI state."""
        logger.error("UI error: %s", message)
        self._progress_bar.reset()
        self._drop_zone.set_enabled(True)
        show_toast(self, message, style="error", duration_ms=5000)

    def _on_close(self) -> None:
        """Handle window close with confirmation if transcription is active."""
        if (
            self._transcription_thread is not None
            and self._transcription_thread.is_alive()
        ):
            dialog = ctk.CTkInputDialog(
                text="Transcription is in progress.\nStop and quit?",
                title="Confirm Exit",
            )
            # CTkInputDialog is not ideal for yes/no, use a simple toplevel instead
            self._show_quit_dialog()
            return

        self._shutdown()

    def _show_quit_dialog(self) -> None:
        """Show a confirmation dialog for quitting during transcription."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Exit")
        dialog.geometry("320x140")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        label = ctk.CTkLabel(
            dialog,
            text="Transcription is in progress.\nStop and quit?",
            font=ctk.CTkFont(size=13),
        )
        label.pack(pady=(20, 15))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack()

        stop_btn = ctk.CTkButton(
            btn_frame,
            text="Stop and Quit",
            command=lambda: self._confirm_quit(dialog),
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c"),
            cursor="hand2",
        )
        stop_btn.pack(side="left", padx=10)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Keep Running",
            command=dialog.destroy,
            fg_color=("gray70", "gray30"),
            cursor="hand2",
        )
        cancel_btn.pack(side="left", padx=10)

    def _confirm_quit(self, dialog: ctk.CTkToplevel) -> None:
        """Stop transcription and quit."""
        dialog.destroy()
        self._cancel_event.set()
        self._shutdown()

    def _shutdown(self) -> None:
        """Clean shutdown: close IPC, save config, destroy window."""
        self._config["window_width"] = self.winfo_width()
        self._config["window_height"] = self.winfo_height()
        save_config(self._config)

        if self._ipc_client and self._ipc_client.connected:
            try:
                self._ipc_client.send("shutdown")
            except ConnectionError:
                pass
            self._ipc_client.close()

        self.destroy()
