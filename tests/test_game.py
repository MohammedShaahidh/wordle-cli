"""Unit tests for the CLI Wordle game."""

import json
from pathlib import Path

import pytest

from game import (
    MAX_GUESSES,
    STATUS_ABSENT,
    STATUS_CORRECT,
    STATUS_PRESENT,
    Game,
    evaluate_guess,
    load_words,
)
from history import GameHistory

SAMPLE_WORDS: list[str] = [
    "spine",
    "speed",
    "apple",
    "alley",
    "crane",
    "slate",
    "round",
    "flame",
    "sweet",
    "clean",
]


class TestEvaluateGuess:
    """Tests for the evaluate_guess function."""

    def test_fully_correct_guess(self) -> None:
        """When guess matches secret exactly, all letters are correct."""
        result = evaluate_guess("crane", "crane")
        assert result.statuses == [STATUS_CORRECT] * 5

    def test_mixed_statuses(self) -> None:
        """Test a mix of correct, present, and absent statuses."""
        # secret = "slate", guess = "stare"
        # s -> correct (idx 0)
        # t -> present (idx 1, in slate at idx 3)
        # a -> correct (idx 2)
        # r -> absent (idx 3, not in slate)
        # e -> correct (idx 4)
        result = evaluate_guess("slate", "stare")
        assert result.statuses == [
            STATUS_CORRECT,
            STATUS_PRESENT,
            STATUS_CORRECT,
            STATUS_ABSENT,
            STATUS_CORRECT,
        ]

    def test_duplicate_letters_spine_speed(self) -> None:
        """Specification test: secret='SPINE', guess='SPEED'."""
        result = evaluate_guess("SPINE", "SPEED")
        assert result.statuses == [
            STATUS_CORRECT,
            STATUS_CORRECT,
            STATUS_PRESENT,
            STATUS_ABSENT,
            STATUS_ABSENT,
        ]

    def test_duplicate_letters_apple_alley(self) -> None:
        """Specification test: secret='APPLE', guess='ALLEY'."""
        # secret: a p p l e
        # guess:  a l l e y
        # idx 0: a == a -> correct
        # idx 1: l != p -> pool has {p:2, l:1, e:1} -> l marked present
        # idx 2: l != p -> pool has l:0 -> absent
        # idx 3: e != l -> pool has e:1 -> present, pool has {p:2, l:0, e:0}
        # idx 4: y != e -> pool has y:0 -> absent
        result = evaluate_guess("APPLE", "ALLEY")
        assert result.statuses == [
            STATUS_CORRECT,
            STATUS_PRESENT,
            STATUS_ABSENT,
            STATUS_PRESENT,
            STATUS_ABSENT,
        ]

    def test_all_absent_letters(self) -> None:
        """When no letters match, all statuses are absent."""
        result = evaluate_guess("round", "fleas")
        assert result.statuses == [STATUS_ABSENT] * 5

    def test_invalid_secret_length(self) -> None:
        """Secret with length != 5 raises ValueError."""
        with pytest.raises(ValueError, match="5-letter alphabetic string"):
            evaluate_guess("four", "crane")

    def test_invalid_guess_length(self) -> None:
        """Guess with length != 5 raises ValueError."""
        with pytest.raises(ValueError, match="5-letter alphabetic string"):
            evaluate_guess("crane", "toolong")

    def test_non_alphabetic_characters(self) -> None:
        """Secret or guess with non-letters raises ValueError."""
        with pytest.raises(ValueError, match="5-letter alphabetic string"):
            evaluate_guess("cra1e", "crane")
        with pytest.raises(ValueError, match="5-letter alphabetic string"):
            evaluate_guess("crane", "cr!ne")


class TestGuessResult:
    """Tests for GuessResult formatting."""

    def test_str_formatting(self) -> None:
        """Check the formatted string with letters and symbols."""
        result = evaluate_guess("SPINE", "SPEED")
        expected_output = "S  P  E  E  D\n✓  ✓  ~  ✗  ✗"
        assert str(result) == expected_output


class TestGame:
    """Tests for Game class logic."""

    def test_initialization_valid(self) -> None:
        """Game initializes correctly with valid secret and word list."""
        game = Game("crane", SAMPLE_WORDS)
        assert game.secret_word == "crane"
        assert len(game.guesses) == 0
        assert not game.is_won
        assert not game.is_over
        assert game.remaining_attempts == MAX_GUESSES

    def test_initialization_secret_not_in_list(self) -> None:
        """Secret not in word list raises ValueError."""
        with pytest.raises(ValueError, match="not in the provided word list"):
            Game("zebra", SAMPLE_WORDS)

    def test_initialization_invalid_secret_length(self) -> None:
        """Secret word with wrong length raises ValueError."""
        with pytest.raises(ValueError, match="5-letter alphabetic string"):
            Game("toolong", SAMPLE_WORDS)

    def test_make_guess_valid(self) -> None:
        """Making a valid guess appends guess and returns result."""
        game = Game("crane", SAMPLE_WORDS)
        result = game.make_guess("slate")
        assert len(game.guesses) == 1
        assert game.guesses[0] == "slate"
        assert result.statuses[0] == STATUS_ABSENT  # s not in crane
        assert game.remaining_attempts == 5

    def test_make_guess_not_in_word_list(self) -> None:
        """Guess not in allowed word list raises ValueError."""
        game = Game("crane", SAMPLE_WORDS)
        with pytest.raises(ValueError, match="not in the word list"):
            game.make_guess("zebra")
        # Attempt must not be consumed
        assert len(game.guesses) == 0
        assert game.remaining_attempts == MAX_GUESSES

    def test_make_guess_invalid_length(self) -> None:
        """Guess with invalid length raises ValueError and consumes no attempt."""
        game = Game("crane", SAMPLE_WORDS)
        with pytest.raises(ValueError, match="exactly 5 alphabetic letters"):
            game.make_guess("cat")
        assert len(game.guesses) == 0
        assert game.remaining_attempts == MAX_GUESSES

    def test_is_won_after_correct_guess(self) -> None:
        """Game is won and is over when secret word is guessed."""
        game = Game("crane", SAMPLE_WORDS)
        result = game.make_guess("crane")
        assert result.statuses == [STATUS_CORRECT] * 5
        assert game.is_won is True
        assert game.is_over is True

    def test_is_over_after_max_guesses(self) -> None:
        """Game is over and not won after 6 failed guesses."""
        game = Game("crane", SAMPLE_WORDS)
        for _ in range(MAX_GUESSES):
            game.make_guess("slate")
        assert game.is_won is False
        assert game.is_over is True
        assert game.remaining_attempts == 0

    def test_make_guess_after_game_over(self) -> None:
        """Attempting to guess after game ends raises ValueError."""
        game = Game("crane", SAMPLE_WORDS)
        game.make_guess("crane")
        assert game.is_over is True
        with pytest.raises(ValueError, match="already over"):
            game.make_guess("slate")

    def test_board_display_empty(self) -> None:
        """Empty board display shows remaining attempts message."""
        game = Game("crane", SAMPLE_WORDS)
        assert "No guesses yet. 6 attempts remaining." in str(game)

    def test_board_display_does_not_reveal_secret(self) -> None:
        """Board display contains guessed rows and remaining attempts, not secret."""
        game = Game("crane", SAMPLE_WORDS)
        game.make_guess("slate")
        board = str(game)
        assert "S  L  A  T  E" in board
        assert "Attempts remaining: 5" in board
        assert "crane" not in board.lower() or "c  r  a  n  e" in board


class TestGameHistory:
    """Tests for GameHistory persistence and streak logic."""

    def test_empty_history(self, tmp_path: Path) -> None:
        """Empty history returns zero for all statistics."""
        history_file = tmp_path / "test_history.json"
        history = GameHistory(history_file)
        assert history.total_games == 0
        assert history.total_wins == 0
        assert history.win_percentage == 0.0
        assert history.current_streak == 0
        assert history.best_streak == 0
        assert history_file.exists()

    def test_record_and_persistence(self, tmp_path: Path) -> None:
        """Recorded games are saved to JSON and reloaded by a new instance."""
        history_file = tmp_path / "test_history.json"
        history = GameHistory(history_file)
        history.record_game(won=True, attempts=3, word="crane")
        history.record_game(won=False, attempts=6, word="slate")

        # Reload from the same file in a new instance
        reloaded = GameHistory(history_file)
        assert reloaded.total_games == 2
        assert reloaded.total_wins == 1
        assert reloaded.win_percentage == 50.0

    def test_streaks_calculation(self, tmp_path: Path) -> None:
        """Verify streak behavior: Win, Win, Loss, Win, Win, Win."""
        history_file = tmp_path / "test_history.json"
        history = GameHistory(history_file)

        # Sequence: Win, Win, Loss, Win, Win, Win
        history.record_game(won=True, attempts=1, word="crane")
        history.record_game(won=True, attempts=2, word="slate")
        history.record_game(won=False, attempts=6, word="round")
        history.record_game(won=True, attempts=3, word="apple")
        history.record_game(won=True, attempts=4, word="alley")
        history.record_game(won=True, attempts=5, word="spine")

        assert history.total_games == 6
        assert history.total_wins == 5
        assert history.current_streak == 3
        assert history.best_streak == 3

        # Next game is a Loss: current_streak resets to 0, best_streak stays 3
        history.record_game(won=False, attempts=6, word="flame")
        assert history.current_streak == 0
        assert history.best_streak == 3

        # Next game is a Win: current_streak becomes 1, best_streak stays 3
        history.record_game(won=True, attempts=2, word="clean")
        assert history.current_streak == 1
        assert history.best_streak == 3

    def test_invalid_json_handling(self, tmp_path: Path) -> None:
        """Malformed JSON raises ValueError."""
        history_file = tmp_path / "corrupt.json"
        history_file.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            GameHistory(history_file)

    def test_non_list_root_json(self, tmp_path: Path) -> None:
        """JSON file with object root instead of list raises ValueError."""
        history_file = tmp_path / "not_a_list.json"
        history_file.write_text(json.dumps({"total": 1}), encoding="utf-8")
        with pytest.raises(ValueError, match="must be a JSON list"):
            GameHistory(history_file)

    def test_record_validation(self, tmp_path: Path) -> None:
        """Invalid arguments to record_game raise ValueError."""
        history_file = tmp_path / "test_history.json"
        history = GameHistory(history_file)
        with pytest.raises(ValueError, match="integer between 1 and 6"):
            history.record_game(won=True, attempts=7, word="crane")
        with pytest.raises(ValueError, match="5-letter alphabetic word"):
            history.record_game(won=True, attempts=3, word="bad")


class TestLoadWords:
    """Tests for load_words function."""

    def test_load_valid_words(self, tmp_path: Path) -> None:
        """Valid words file loads successfully and ignores blank lines."""
        word_file = tmp_path / "test_words.txt"
        word_file.write_text("crane\n\n  slate  \nround\n", encoding="utf-8")
        words = load_words(word_file)
        assert words == ["crane", "slate", "round"]

    def test_load_missing_file(self, tmp_path: Path) -> None:
        """Missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_words(tmp_path / "does_not_exist.txt")

    def test_load_invalid_word_length(self, tmp_path: Path) -> None:
        """Word with length != 5 raises ValueError with line number."""
        word_file = tmp_path / "test_words.txt"
        word_file.write_text("crane\nfour\nslate\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid word 'four' at line 2"):
            load_words(word_file)

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """Empty file raises ValueError."""
        word_file = tmp_path / "empty_words.txt"
        word_file.write_text("\n   \n", encoding="utf-8")
        with pytest.raises(ValueError, match="is empty"):
            load_words(word_file)
