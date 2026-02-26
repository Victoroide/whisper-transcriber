"""Tests for ui.app.utils.text -- clean_transcript and remove_repetitions."""
import sys
from pathlib import Path

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ui.app.utils.text import clean_transcript, remove_repetitions


class TestCleanTranscript:
    """Verify that clean_transcript preserves legitimate content."""

    def test_preserves_single_letter_a(self) -> None:
        result = clean_transcript("This is a test")
        assert "a" in result.split()

    def test_preserves_single_letter_i(self) -> None:
        result = clean_transcript("I went to the store")
        assert result.startswith("I ")

    def test_preserves_spanish_single_letters(self) -> None:
        result = clean_transcript("Ella y yo fuimos o no")
        assert " y " in result
        assert " o " in result

    def test_removes_angle_brackets(self) -> None:
        result = clean_transcript("Hello <unk> world")
        assert "<" not in result
        assert ">" not in result
        assert "Hello" in result
        assert "world" in result

    def test_removes_pipe_characters(self) -> None:
        result = clean_transcript("text | more text")
        assert "|" not in result

    def test_removes_curly_braces(self) -> None:
        result = clean_transcript("text {artifact} here")
        assert "{" not in result
        assert "}" not in result

    def test_collapses_whitespace(self) -> None:
        result = clean_transcript("too    many   spaces")
        assert "  " not in result

    def test_strips_leading_trailing(self) -> None:
        result = clean_transcript("  hello world  ")
        assert result == "hello world"

    def test_empty_string(self) -> None:
        result = clean_transcript("")
        assert result == ""

    def test_preserves_normal_sentence(self) -> None:
        text = "The quick brown fox jumps over a lazy dog"
        result = clean_transcript(text)
        assert result == text


class TestRemoveRepetitions:
    """Verify repetition removal with edge cases."""

    def test_empty_string(self) -> None:
        assert remove_repetitions("") == ""

    def test_single_word(self) -> None:
        assert remove_repetitions("hello") == "hello"

    def test_no_repetitions(self) -> None:
        text = "The weather is nice today"
        assert remove_repetitions(text) == text

    def test_removes_repeated_word_four_times(self) -> None:
        result = remove_repetitions("the the the the cat")
        assert "the the the the" not in result
        assert "cat" in result

    def test_keeps_word_repeated_twice(self) -> None:
        result = remove_repetitions("the the cat")
        assert result == "the the cat"

    def test_removes_repeated_phrase(self) -> None:
        result = remove_repetitions("good morning good morning everyone")
        # Should collapse "good morning good morning" to "good morning"
        assert result.count("good morning") == 1
        assert "everyone" in result

    def test_multiple_repetition_groups(self) -> None:
        text = "hello hello hello hello world world world world"
        result = remove_repetitions(text)
        assert result.count("hello") == 1
        assert result.count("world") == 1

    def test_preserves_naturally_repeated_words(self) -> None:
        text = "she said that that was fine"
        result = remove_repetitions(text)
        assert "that that" in result
