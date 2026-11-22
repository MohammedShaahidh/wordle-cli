"""CLI entry point for playing the Python Wordle game."""

import random
from pathlib import Path

from game import MAX_GUESSES, Game, load_words
from history import GameHistory


def display_welcome() -> None:
    """Print the welcome banner and rules explanation to the console."""
    print("=" * 44)
    print("             CLI WORDLE GAME")
    print("=" * 44)
    print("Guess the secret 5-letter word in 6 attempts!")
    print("\nSymbols:")
    print("  ✓ : Letter is correct and in the right position")
    print("  ~ : Letter is in the word, but in a different position")
    print("  ✗ : Letter is not in the word (or already matched)")
    print("=" * 44)


def display_stats(history: GameHistory) -> None:
    """Print player career statistics to the console.

    Args:
        history: The GameHistory instance containing recorded games.
    """
    print("\n" + "=" * 16 + " CAREER STATS " + "=" * 16)
    print(f"Total games played : {history.total_games}")
    print(f"Total wins         : {history.total_wins}")
    print(f"Win percentage     : {history.win_percentage:.1f}%")
    print(f"Current streak     : {history.current_streak}")
    print(f"Best streak        : {history.best_streak}")
    print("=" * 46)


def main() -> None:
    """Coordinate the Wordle game session from startup to completion."""
    words_file = Path(__file__).parent / "words.txt"
    try:
        words = load_words(words_file)
    except (FileNotFoundError, ValueError) as err:
        print(f"Error loading word list: {err}")
        return

    secret_word = random.choice(words)
    game = Game(secret_word=secret_word, word_list=words)
    history = GameHistory()

    display_welcome()

    try:
        while not game.is_over:
            print("\n" + str(game))
            user_input = input("\nEnter your guess: ")
            try:
                game.make_guess(user_input)
            except ValueError as err:
                print(f"Invalid guess: {err}")
    except (KeyboardInterrupt, EOFError):
        print("\n\nGame aborted. Progress was not saved.")
        return

    # Game is now over (either won or max guesses reached)
    print("\n" + str(game))
    if game.is_won:
        print(f"\nYou got it in {len(game.guesses)}/{MAX_GUESSES}!")
    else:
        print(f"\nThe word was {game.secret_word.upper()}.")

    # Record the completed game exactly once
    history.record_game(
        won=game.is_won,
        attempts=len(game.guesses),
        word=game.secret_word,
    )
    print("\nGame recorded in history.")
    display_stats(history)


if __name__ == "__main__":
    main()
