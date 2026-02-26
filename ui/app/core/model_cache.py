import logging
from typing import Any

logger = logging.getLogger(__name__)

_cache: dict[str, Any] = {}


def get_model(size: str, device: str = "auto", compute_type: str = "int8") -> Any:
    """Return a cached WhisperModel instance, creating one if needed.

    This singleton cache prevents reloading the same model on every
    transcription, which saves both time and memory.
    """
    key = f"{size}_{device}_{compute_type}"
    if key in _cache:
        logger.info("Using cached model: %s", key)
        return _cache[key]

    logger.info("Loading model: size=%s, device=%s, compute=%s", size, device, compute_type)

    from faster_whisper import WhisperModel

    model = WhisperModel(size, device=device, compute_type=compute_type)
    _cache[key] = model
    logger.info("Model loaded and cached: %s", key)
    return model


def clear_cache() -> None:
    """Remove all cached models to free memory."""
    _cache.clear()
    logger.info("Model cache cleared")


def is_loaded(size: str, device: str = "auto", compute_type: str = "int8") -> bool:
    """Check if a specific model configuration is already cached."""
    key = f"{size}_{device}_{compute_type}"
    return key in _cache
