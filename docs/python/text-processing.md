# Text Processing (`ui/app/utils/text.py`)

A critical challenge with Whisper (specifically smaller quantization variants like `.en.tiny`) is that they are prone to occasional "hallucinations" – situations where background noise or absolute silence triggers the model into endlessly predicting conversational filler loops or repeatedly predicting the same punctuation mark.

This repository introduces a post-inference text sanitation pipeline executed on the finalized document before it reaches the end user or is exported.

## Core Operations

### `clean_transcript(text: str) -> str`

This regex-based scrubber targets severe punctuation loops and hallucinatory artifacts before they corrupt the subtitle files.

- **Punctuation Condensation**: It utilizes `re.sub(r'([.?!,])\1+', r'\1', text)` to compress endless trails of punctuation (e.g., `"Hellooooooooo......,,,,," -> "Hellooooo."`).
- **Whitespace Normalization**: Collapses repeated spaces and newlines strictly down to a single space.
- **Case Fixing**: Applies `.capitalize()` specifically to the absolute first character of the document.

### `remove_repetitions(text: str) -> str`

This is a sophisticated NLP operation protecting against the infamous Whisper fallback loop error (e.g., `"Thank you. Thank you. Thank you. Thank you. Thank you."`).

- **Tokenization**: Splits the entire blob strictly into words.
- **Look-ahead Dictionary**: Passes over the words analyzing the next 4 tokens simultaneously.
- **Sliding Window Detection**: If a sequence exactly matches an immediately prior sequence (and this sequence has already happened 3 times), consecutive repeats are dynamically excluded. This allows natural conversational repeats `"You, you are crazy"` but aggressively filters out `"You are crazy. You are crazy. You are crazy."` loops.
- **Single-letter bypass**: Explicitly ignores English grammar singles (`"I"`, `"a"`) so it doesn't accidentally destroy sentences like `"I think that I am a dog"`.
