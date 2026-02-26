import json
import logging
import os
import platform
import socket
import threading
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable

logger = logging.getLogger(__name__)


class IPCClient:
    """Connects to the wt-core Go backend via TCP (Windows) or Unix socket.

    Messages are newline-delimited JSON. A background reader thread pushes
    incoming messages into a thread-safe queue for the UI to poll.
    """

    def __init__(self, address: str) -> None:
        self._address = address
        self._socket: socket.socket | None = None
        self._reader_thread: threading.Thread | None = None
        self._queue: Queue[dict[str, Any]] = Queue()
        self._running = False
        self._buffer = ""
        self._handlers: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

    def connect(self, timeout: float = 5.0) -> None:
        """Establish connection to the Go core process."""
        if platform.system() != "Windows" and self._address.startswith("/"):
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        else:
            host, port_str = self._address.rsplit(":", 1)
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._address = (host, int(port_str))

        self._socket.settimeout(timeout)
        self._socket.connect(self._address)
        self._socket.settimeout(None)

        self._running = True
        self._reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True, name="ipc-reader"
        )
        self._reader_thread.start()
        logger.info("Connected to wt-core at %s", self._address)

    def send(self, msg_type: str, data: dict[str, Any] | None = None) -> None:
        """Send a JSON message to the Go core."""
        if self._socket is None:
            raise ConnectionError("Not connected to core process")

        message = {"type": msg_type, "data": data or {}}
        payload = json.dumps(message) + "\n"
        try:
            self._socket.sendall(payload.encode("utf-8"))
        except OSError as exc:
            logger.error("Failed to send message: %s", exc)
            raise ConnectionError(f"Send failed: {exc}") from exc

    def receive(self, timeout: float = 0.1) -> dict[str, Any] | None:
        """Non-blocking receive of the next message from the queue."""
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None

    def on(self, msg_type: str, handler: Callable[[dict[str, Any]], None]) -> None:
        """Register a handler for a specific message type."""
        if msg_type not in self._handlers:
            self._handlers[msg_type] = []
        self._handlers[msg_type].append(handler)

    def close(self) -> None:
        """Shutdown the connection and reader thread."""
        self._running = False
        if self._socket is not None:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._socket.close()
            self._socket = None
        logger.info("IPC connection closed")

    @property
    def connected(self) -> bool:
        """Return True if the socket is connected."""
        return self._socket is not None and self._running

    def _reader_loop(self) -> None:
        """Background thread that reads messages from the socket."""
        while self._running and self._socket is not None:
            try:
                chunk = self._socket.recv(65536)
                if not chunk:
                    logger.warning("Core process closed the connection")
                    self._running = False
                    break

                self._buffer += chunk.decode("utf-8")
                while "\n" in self._buffer:
                    line, self._buffer = self._buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        self._queue.put(msg)
                    except json.JSONDecodeError as exc:
                        logger.warning("Invalid JSON from core: %s", exc)

            except OSError:
                if self._running:
                    logger.error("Socket read error, connection lost")
                break

    def update(self) -> None:
        """Process all pending messages in the queue.
        Must be called from the main GUI thread.
        """
        while True:
            try:
                msg = self._queue.get_nowait()
                msg_type = msg.get("type", "")
                for handler in self._handlers.get(msg_type, []):
                    try:
                        handler(msg.get("data", {}))
                    except Exception:
                        logger.exception("Handler error for message type '%s'", msg_type)
            except Empty:
                break


def find_core_binary() -> Path | None:
    """Locate the wt-core binary relative to the UI package."""
    candidates = [
        Path(__file__).parent.parent / "bin" / _binary_name(),
        Path(__file__).parent.parent.parent.parent / "core" / "bin" / _binary_name(),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _binary_name() -> str:
    """Return the platform-appropriate binary name."""
    if os.name == "nt":
        return "wt-core.exe"
    return "wt-core"
