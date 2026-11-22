"""History tracking and statistics persistence for the CLI Wordle game."""

import json
from pathlib import Path
from typing import Any

from game import MAX_GUESSES, WORD_LENGTH


class GameHistory:
    """Manages persistent Wordle game records and player statistics."""

    def __init__(self, file_path: Path | str | None = None) -> None:
        """Initialize the history manager with a target JSON file path.

        Args:
            file_path: Optional path to the history file. Defaults to 'history.json'
                in the same directory as this module.
        """
        if file_path is None:
            self.file_path: Path = Path(__file__).parent / "history.json"
        else:
            self.file_path = Path(file_path)

        self.records: list[dict[str, Any]] = []
        self._load_or_create()

    def _load_or_create(self) -> None:
        """Load records from the JSON file, or create it if missing."""
        if not self.file_path.exists():
            self.records = []
            self._save()
            return

        try:
            content = self.file_path.read_text(encoding="utf-8")
            data = json.loads(content)
        except json.JSONDecodeError as err:
            raise ValueError(
                f"Invalid JSON in history file: {self.file_path}"
            ) from err

        if not isinstance(data, list):
            raise ValueError(
                f"History file root must be a JSON list: {self.file_path}"
            )

        for idx, entry in enumerate(data):
            if not isinstance(entry, dict):
                raise ValueError(f"Record at index {idx} must be a dictionary.")
            if "won" not in entry or not isinstance(entry["won"], bool):
                raise ValueError(
                    f"Record at index {idx} has invalid or missing 'won' boolean."
                )
            if (
                "attempts" not in entry
                or not isinstance(entry["attempts"], int)
                or entry["attempts"] < 1
                or entry["attempts"] > MAX_GUESSES
            ):
                raise ValueError(
                    f"Record at index {idx} has invalid 'attempts' "
                    f"(must be integer between 1 and {MAX_GUESSES})."
                )
            if (
                "word" not in entry
                or not isinstance(entry["word"], str)
                or len(entry["word"].strip()) != WORD_LENGTH
            ):
                raise ValueError(
                    f"Record at index {idx} has invalid 'word' "
                    f"(must be a {WORD_LENGTH}-character string)."
                )

        self.records = data

    def _save(self) -> None:
        """Save current records to the JSON file formatted with indent."""
        content = json.dumps(self.records, indent=2)
        self.file_path.write_text(content, encoding="utf-8")

    def record_game(self, won: bool, attempts: int, word: str) -> None:
        """Validate, append, and persist a completed game record.

        Args:
            won: True if the player won, False otherwise.
            attempts: The number of valid guesses made (1 to MAX_GUESSES).
            word: The secret word of the completed game.

        Raises:
            ValueError: If any parameter fails validation.
        """
        if not isinstance(won, bool):
            raise ValueError("The 'won' argument must be a boolean.")

        if not isinstance(attempts, int) or attempts < 1 or attempts > MAX_GUESSES:
            raise ValueError(
                f"The 'attempts' argument must be an integer "
                f"between 1 and {MAX_GUESSES}."
            )

        cleaned_word = word.strip().lower()
        if (
            not isinstance(word, str)
            or len(cleaned_word) != WORD_LENGTH
            or not cleaned_word.isalpha()
        ):
            raise ValueError(
                f"The 'word' argument must be a {WORD_LENGTH}-letter alphabetic word."
            )

        record: dict[str, Any] = {
            "won": won,
            "attempts": attempts,
            "word": cleaned_word,
        }
        self.records.append(record)
        self._save()

    @property
    def total_games(self) -> int:
        """Return the total number of completed games."""
        return len(self.records)

    @property
    def total_wins(self) -> int:
        """Return the total number of won games."""
        return sum(1 for record in self.records if record["won"])

    @property
    def win_percentage(self) -> float:
        """Return the percentage of games won (0.0 to 100.0)."""
        if not self.records:
            return 0.0
        return (self.total_wins / self.total_games) * 100.0

    @property
    def current_streak(self) -> int:
        """Return the number of consecutive wins ending with the most recent game."""
        streak = 0
        for record in reversed(self.records):
            if record["won"]:
                streak += 1
            else:
                break
        return streak

    @property
    def best_streak(self) -> int:
        """Return the longest consecutive winning streak in the history."""
        best = 0
        current = 0
        for record in self.records:
            if record["won"]:
                current += 1
                if current > best:
                    best = current
            else:
                current = 0
        return best
