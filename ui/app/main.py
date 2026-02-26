import logging
import subprocess
import sys
import time
from pathlib import Path

from ui.app.core.ipc_client import IPCClient, find_core_binary
from ui.app.utils.platform import setup_logging
from ui.app.window import MainWindow

logger = logging.getLogger(__name__)

CORE_STARTUP_TIMEOUT = 5.0


def main() -> None:
    """Application entry point.

    Sequence:
    1. Setup logging
    2. Locate and launch the Go core binary
    3. Establish IPC connection
    4. Create and run the main window
    5. Graceful shutdown on exit
    """
    setup_logging()
    logger.info("Starting Whisper Transcriber")

    core_process = None
    ipc_client = None

    core_binary = find_core_binary()
    if core_binary is not None:
        core_process, ipc_client = _start_core(core_binary)
    else:
        logger.warning(
            "wt-core binary not found. Running in standalone mode "
            "(audio extraction and hardware detection unavailable)."
        )

    try:
        app = MainWindow(ipc_client=ipc_client)
        app.mainloop()
    except Exception:
        logger.exception("Unhandled exception in main loop")
    finally:
        _cleanup(core_process, ipc_client)


def _start_core(binary_path: Path) -> tuple[subprocess.Popen | None, IPCClient | None]:
    """Launch the Go core process and establish IPC."""
    logger.info("Launching wt-core from: %s", binary_path)

    try:
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            [str(binary_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creation_flags,
        )
    except OSError as exc:
        logger.error("Failed to launch wt-core: %s", exc)
        return None, None

    # Read the IPC address from the first line of stdout
    address = _read_address(process)
    if address is None:
        logger.error("wt-core did not output an IPC address within %ss", CORE_STARTUP_TIMEOUT)
        process.terminate()
        return None, None

    logger.info("wt-core listening on: %s", address)

    client = IPCClient(address)
    try:
        client.connect(timeout=CORE_STARTUP_TIMEOUT)
    except (ConnectionError, OSError) as exc:
        logger.error("Failed to connect to wt-core: %s", exc)
        process.terminate()
        return process, None

    return process, client


def _read_address(process: subprocess.Popen) -> str | None:
    """Read the IPC address from the core process stdout with a timeout."""
    deadline = time.monotonic() + CORE_STARTUP_TIMEOUT

    while time.monotonic() < deadline:
        if process.poll() is not None:
            stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            logger.error("wt-core exited early (code %d): %s", process.returncode, stderr)
            return None

        if process.stdout is None:
            return None

        line = process.stdout.readline()
        if line:
            return line.decode("utf-8").strip()

        time.sleep(0.05)

    return None


def _cleanup(
    process: subprocess.Popen | None,
    client: IPCClient | None,
) -> None:
    """Shut down the IPC client and core process."""
    if client is not None:
        try:
            client.send("shutdown")
        except (ConnectionError, OSError):
            pass
        client.close()

    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            logger.warning("wt-core did not exit gracefully, force killing")
            process.kill()

    logger.info("Whisper Transcriber shut down")


if __name__ == "__main__":
    main()
