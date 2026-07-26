"""Smoke tests for the interactive interface."""

from __future__ import annotations

import unittest
from collections.abc import Sequence

from watchlist_manager.cli import InteractiveCLI
from watchlist_manager.models import Movie
from watchlist_manager.service import WatchlistService


class InMemoryRepository:
    def __init__(self, movies: Sequence[Movie] = ()) -> None:
        self.movies = list(movies)

    def load(self) -> list[Movie]:
        return self.movies.copy()

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

    def test_add_movie_collects_and_persists_values(self) -> None:
        answers = iter(
            [
                "Blade Runner",
                "Ridley Scott",
                "1982",
                "Science Fiction",
                "watched",
                "9",
                "A replicant hunter questions his identity.",
            ]
        )
        output: list[str] = []
        repository = InMemoryRepository()
        cli = InteractiveCLI(
            WatchlistService(repository),
            input_function=lambda _: next(answers),
            output_function=output.append,
        )

        cli.add_movie()

        self.assertEqual(repository.movies[0].title, "Blade Runner")
        self.assertEqual(repository.movies[0].rating, 9)
        self.assertIn("[OK] Added 'Blade Runner'.", output)

    def test_filter_collection_displays_only_matching_movies(self) -> None:
        answers = iter(["planned", "Science Fiction", ""])
        output: list[str] = []
        repository = InMemoryRepository(
            [
                Movie(title="Arrival", genre="Science Fiction"),
                Movie(title="Saw", genre="Horror"),
            ]
        )
        cli = InteractiveCLI(
            WatchlistService(repository),
            input_function=lambda _: next(answers),
            output_function=output.append,
        )

        cli.filter_collection()

        rendered = "\n".join(output)
        self.assertIn("Arrival", rendered)
        self.assertNotIn("Saw", rendered)
        self.assertIn("Found: 1", output)

    def test_recommendation_displays_planned_movie(self) -> None:
        answers = iter(["Science Fiction"])
        output: list[str] = []
        repository = InMemoryRepository(
            [Movie(title="Arrival", year=2016, genre="Science Fiction")]
        )
        cli = InteractiveCLI(
            WatchlistService(repository),
            input_function=lambda _: next(answers),
            output_function=output.append,
        )

        cli.recommend_movie()

        self.assertIn(
            "Recommendation: Arrival (2016) - Science Fiction",
            output,
        )

    def test_statistics_handles_empty_collection(self) -> None:
        output: list[str] = []
        cli = InteractiveCLI(
            WatchlistService(InMemoryRepository()),
            input_function=lambda _: self.fail("No prompt expected"),
            output_function=output.append,
        )

        cli.show_statistics()

        self.assertIn("Total movies: 0", output)
        self.assertIn("Average rating: not available", output)


if __name__ == "__main__":
    unittest.main()
