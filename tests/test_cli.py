"""Smoke tests for the interactive interface."""

from __future__ import annotations

import unittest
from collections.abc import Sequence

from watchlist_manager.cli import InteractiveCLI
from watchlist_manager.models import Movie
from watchlist_manager.service import WatchlistService


class InMemoryRepository:
    def load(self) -> list[Movie]:
        return []

    def save(self, movies: Sequence[Movie]) -> None:
        self.movies = list(movies)


class InteractiveCLITests(unittest.TestCase):
    def test_user_can_exit_cleanly(self) -> None:
        answers = iter(["0"])
        output: list[str] = []
        cli = InteractiveCLI(
            WatchlistService(InMemoryRepository()),
            input_function=lambda _: next(answers),
            output_function=output.append,
        )

        result = cli.run()

        self.assertEqual(result, 0)
        self.assertIn("Goodbye.", output)

    def test_invalid_option_returns_to_menu(self) -> None:
        answers = iter(["unknown", "0"])
        output: list[str] = []
        cli = InteractiveCLI(
            WatchlistService(InMemoryRepository()),
            input_function=lambda _: next(answers),
            output_function=output.append,
        )

        cli.run()

        self.assertIn("[ERROR] Invalid menu option.", output)

    def test_end_of_input_during_action_exits_cleanly(self) -> None:
        answers = iter(["1"])
        output: list[str] = []

        def input_function(_: str) -> str:
            try:
                return next(answers)
            except StopIteration as error:
                raise EOFError from error

        cli = InteractiveCLI(
            WatchlistService(InMemoryRepository()),
            input_function=input_function,
            output_function=output.append,
        )

        result = cli.run()

        self.assertEqual(result, 0)
        self.assertIn("\nGoodbye.", output)


if __name__ == "__main__":
    unittest.main()
