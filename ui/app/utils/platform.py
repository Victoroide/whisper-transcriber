import json
import logging
import os
import platform
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "whisper_transcriber"
CONFIG_FILENAME = "config.json"


def get_app_dir() -> Path:
    """Return the application data directory at ~/.whisper_transcriber/."""
    return Path.home() / f".{APP_NAME}"


def get_config_path() -> Path:
    """Return the path to the user config file."""
    return get_app_dir() / CONFIG_FILENAME


def get_log_dir() -> Path:
    """Return the directory for application log files."""
    log_dir = get_app_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_models_dir() -> Path:
    """Return the directory for cached model files."""
    models_dir = get_app_dir() / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def get_temp_dir() -> Path:
    """Return the directory for temporary files."""
    temp_dir = get_app_dir() / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def load_config() -> dict:
    """Load user configuration from disk. Returns defaults if file is missing."""
    config_path = get_config_path()
    defaults = {
        "theme": "dark",
        "model_size": "small",
        "last_export_dir": "",
        "window_width": 900,
        "window_height": 620,
    }

    if not config_path.exists():
        return defaults

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        defaults.update(data)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load config: %s", exc)

    return defaults


def save_config(config: dict) -> None:
    """Persist user configuration to disk."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        config_path.write_text(
            json.dumps(config, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.error("Failed to save config: %s", exc)


def is_frozen() -> bool:
    """Return True if running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def get_system_info() -> dict[str, str]:
    """Return basic system information for debugging."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }


def setup_logging() -> None:
    """Configure application-wide logging to file and stderr.

    Log file is rotated when it exceeds 5MB by truncating it.
    """
    log_dir = get_log_dir()
    log_path = log_dir / "app.log"

    if log_path.exists() and log_path.stat().st_size > 5 * 1024 * 1024:
        log_path.unlink()

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
