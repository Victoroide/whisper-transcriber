import re


def clean_transcript(text: str) -> str:
    """Clean transcript text by removing unwanted characters while preserving
    all legitimate single-letter words such as 'a', 'I', 'y', and 'o'.

    Unlike the original implementation, this does NOT use a regex that
    strips single-character words. Instead, it only removes specific
    special characters that appear as artifacts from the model output.
    """
    text = re.sub(r"[<|>{}\\~]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def remove_repetitions(text: str) -> str:
    """Remove repeated words and phrases from transcript text.

    Handles three cases:
    - Empty or single-word input (returned as-is)
    - Single word repeated 4+ times consecutively (collapsed to one)
    - Multi-word phrases repeated 2+ times consecutively (collapsed to one)
    """
    if not text or " " not in text:
        return text

    # Remove single words repeated 4 or more times in a row
    text = re.sub(r"\b(\w+)(?:\s+\1){3,}\b", r"\1", text)

    # Remove repeated multi-word phrases (2-9 words, repeated 2+ times)
    for phrase_len in range(2, 10):
        word_group = r"(?:\S+)"
        phrase = word_group + (r"\s+" + word_group) * (phrase_len - 1)
        pattern = r"(" + phrase + r")(?:\s+\1){1,}"
        text = re.sub(pattern, r"\1", text)

    return text
