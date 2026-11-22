# Wordle --- Python CLI Game

A command-line Wordle implementation built with Python.

## Rules

- Guess the hidden five-letter word.
- You have six valid attempts.
- `✓` means the letter is correct and in the right position.
- `~` means the letter is in the word but in the wrong position.
- `✗` means the letter is not available at that position after accounting for duplicate letters.
- Invalid guesses do not consume an attempt.
- Completed games are saved to `history.json`.

## Project structure

```text
wordle/
├── words.txt
├── game.py
├── history.py
├── wordle.py
├── history.json
├── requirements.txt
├── pyproject.toml
├── README.md
└── tests/
    └── test_game.py
```

## Setup

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

- Windows PowerShell:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- Windows Command Prompt:
  ```bat
  .venv\Scripts\activate.bat
  ```
- macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```

Install development tools:

```bash
python -m pip install -r requirements.txt
```

## Run the game

From the `wordle` directory:

```bash
python wordle.py
```

## Run tests

```bash
pytest -v
```

## Run Ruff

```bash
ruff check .
```

## Key implementation ideas

### Duplicate-letter handling

Guess evaluation uses two passes:
1. **Pass 1:** Identify exact-position matches (`correct`) and count only the secret letters that remain unmatched in a frequency pool.
2. **Pass 2:** Check the remaining non-matching guess letters against the unmatched frequency pool. If the letter is in the pool and has a count greater than 0, mark it `present` and decrement its count. Otherwise, mark it `absent`.

This ensures that repeated letters in a guess do not receive more `correct` or `present` marks than exist in the secret word.

### Current streak

The current streak is calculated by scanning game records backward from the most recent game. It counts each consecutive win and stops immediately when the first loss is encountered. If no games exist or the latest game was a loss, it returns 0.

## Instructor walkthrough

Be ready to explain:

- Why guess evaluation, game state, and history persistence are separated across modules (`evaluate_guess`, `Game`, `GameHistory`).
- How invalid input is validated and rejected without consuming attempts.
- How the two-pass duplicate-letter algorithm prevents double-counting.
- How history records are stored in JSON using standard library modules.
- How current and best streaks are calculated from recorded game history.
- How the test suite uses deterministic words and `tmp_path` fixtures to avoid modifying real game data or depending on random state.
