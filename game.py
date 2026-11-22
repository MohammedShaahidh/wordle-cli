"""Game logic and evaluation for the CLI Wordle game."""

from pathlib import Path

WORD_LENGTH: int = 5
MAX_GUESSES: int = 6

STATUS_CORRECT: str = "correct"
STATUS_PRESENT: str = "present"
STATUS_ABSENT: str = "absent"

SYMBOL_MAP: dict[str, str] = {
    STATUS_CORRECT: "✓",
    STATUS_PRESENT: "~",
    STATUS_ABSENT: "✗",
}


class GuessResult:
    """Represents the evaluation of a single player guess against the secret word."""

    def __init__(self, word: str, statuses: list[str]) -> None:
        """Initialize a GuessResult with the guessed word and character statuses."""
        self.word: str = word
        self.statuses: list[str] = statuses

    def __str__(self) -> str:
        """Return a formatted two-line representation with letters and symbols."""
        letters = "  ".join(self.word.upper())
        symbols = "  ".join(SYMBOL_MAP.get(status, "?") for status in self.statuses)
        return f"{letters}\n{symbols}"

    def __repr__(self) -> str:
        """Return a debug string representation of the GuessResult."""
        return f"GuessResult(word={self.word!r}, statuses={self.statuses!r})"


def evaluate_guess(secret: str, guess: str) -> GuessResult:
    """Evaluate a 5-letter guess against the secret word using a two-pass algorithm.

    Pass 1:
        Identify exact letter matches (same letter at the same index).
        These are marked as 'correct'. We count the remaining unmatched letters
        in the secret word so that duplicate letters are not double-counted.

    Pass 2:
        For positions that were not exact matches, check if the guessed letter
        exists in the unmatched secret pool. If it does, mark it as 'present'
        and decrement that letter's remaining pool count. If it does not,
        mark it as 'absent'.

    Args:
        secret: The hidden target word.
        guess: The player's guessed word.

    Returns:
        GuessResult containing the guessed word and an ordered list of 5 statuses.

    Raises:
        ValueError: If secret or guess is not a 5-letter alphabetic string.
    """
    if (
        not isinstance(secret, str)
        or len(secret) != WORD_LENGTH
        or not secret.isalpha()
    ):
        raise ValueError(
            f"Secret word must be a {WORD_LENGTH}-letter alphabetic string."
        )

    if not isinstance(guess, str) or len(guess) != WORD_LENGTH or not guess.isalpha():
        raise ValueError(f"Guess must be a {WORD_LENGTH}-letter alphabetic string.")

    secret_lower = secret.lower()
    guess_lower = guess.lower()

    statuses: list[str] = [STATUS_ABSENT] * WORD_LENGTH
    remaining_secret_counts: dict[str, int] = {}

    # Pass 1: Mark exact matches ('correct')
    for i in range(WORD_LENGTH):
        if guess_lower[i] == secret_lower[i]:
            statuses[i] = STATUS_CORRECT
        else:
            char = secret_lower[i]
            remaining_secret_counts[char] = remaining_secret_counts.get(char, 0) + 1

    # Pass 2: Mark remaining letters as 'present' or 'absent'
    for i in range(WORD_LENGTH):
        if statuses[i] != STATUS_CORRECT:
            char = guess_lower[i]
            if remaining_secret_counts.get(char, 0) > 0:
                statuses[i] = STATUS_PRESENT
                remaining_secret_counts[char] -= 1
            else:
                statuses[i] = STATUS_ABSENT

    return GuessResult(word=guess_lower, statuses=statuses)


def load_words(file_path: Path | str | None = None) -> list[str]:
    """Load and validate the word list from a file.

    Args:
        file_path: Optional path to the word file. Defaults to 'words.txt' in
            the same directory as this module.

    Returns:
        A list of valid lowercase words.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or contains an invalid nonblank entry.
    """
    if file_path is None:
        path = Path(__file__).parent / "words.txt"
    else:
        path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Word list file not found: {path}")

    words: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if (
                len(stripped) != WORD_LENGTH
                or not stripped.isalpha()
                or not stripped.islower()
            ):
                raise ValueError(
                    f"Invalid word '{stripped}' at line {line_num}: "
                    f"must be exactly {WORD_LENGTH} lowercase alphabetic letters."
                )
            words.append(stripped)

    if not words:
        raise ValueError(f"Word list file '{path}' is empty.")

    return words


class Game:
    """Coordinates the state and rules of a single Wordle match."""

    def __init__(self, secret_word: str, word_list: list[str]) -> None:
        """Initialize the game with a secret word and an allowed word list.

        Args:
            secret_word: The hidden target word to be guessed.
            word_list: List of valid allowed words.

        Raises:
            ValueError: If the secret word is invalid or not in the word list.
        """
        normalized_secret = secret_word.strip().lower()
        if (
            len(normalized_secret) != WORD_LENGTH
            or not normalized_secret.isalpha()
        ):
            raise ValueError(
                f"Secret word must be a {WORD_LENGTH}-letter alphabetic string."
            )

        self.word_list: list[str] = [w.strip().lower() for w in word_list]
        self._word_set: set[str] = set(self.word_list)

        if normalized_secret not in self._word_set:
            raise ValueError(
                f"Secret word '{secret_word}' is not in the provided word list."
            )

        self.secret_word: str = normalized_secret
        self.guesses: list[str] = []
        self.results: list[GuessResult] = []

    def make_guess(self, word: str) -> GuessResult:
        """Accept and validate a player guess, returning the evaluation result.

        Args:
            word: The player's guessed word.

        Returns:
            The GuessResult evaluation for this guess.

        Raises:
            ValueError: If the game is already over, the guess length is wrong,
                the guess contains non-alphabetic characters, or the guess is
                not in the allowed word list.
        """
        if self.is_over:
            raise ValueError("The game is already over.")

        normalized_guess = word.strip().lower()
        if (
            len(normalized_guess) != WORD_LENGTH
            or not normalized_guess.isalpha()
        ):
            raise ValueError(
                f"Guess must be exactly {WORD_LENGTH} alphabetic letters."
            )

        if normalized_guess not in self._word_set:
            raise ValueError(f"'{word.strip()}' is not in the word list.")

        result = evaluate_guess(self.secret_word, normalized_guess)
        self.guesses.append(normalized_guess)
        self.results.append(result)
        return result

    @property
    def is_won(self) -> bool:
        """Return True if any accepted guess exactly matched the secret word."""
        return bool(self.guesses and self.guesses[-1] == self.secret_word)

    @property
    def is_over(self) -> bool:
        """Return True if the game has been won or maximum attempts were reached."""
        return self.is_won or len(self.guesses) >= MAX_GUESSES

    @property
    def remaining_attempts(self) -> int:
        """Return the number of remaining valid attempts."""
        return MAX_GUESSES - len(self.guesses)

    def __str__(self) -> str:
        """Render the complete current board display."""
        if not self.results:
            return f"No guesses yet. {MAX_GUESSES} attempts remaining."

        rows: list[str] = [str(result) for result in self.results]
        remaining = self.remaining_attempts
        return "\n\n".join(rows) + f"\n\nAttempts remaining: {remaining}"
