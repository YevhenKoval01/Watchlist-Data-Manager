"""Tests for watchlist application services."""

from __future__ import annotations

import unittest
from collections.abc import Sequence

from watchlist_manager.errors import MovieNotFoundError, ValidationError
from watchlist_manager.models import Movie, WatchStatus
from watchlist_manager.service import WatchlistService


class InMemoryRepository:
    def __init__(self, movies: Sequence[Movie] = ()) -> None:
        self.movies = list(movies)
        self.save_calls = 0

    def load(self) -> list[Movie]:
        return self.movies.copy()

    def save(self, movies: Sequence[Movie]) -> None:
        self.movies = list(movies)
        self.save_calls += 1


class WatchlistServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryRepository(
            [
                Movie(
                    title="Inception",
                    director="Christopher Nolan",
                    year=2010,
                    genre="Science Fiction",
                    status=WatchStatus.WATCHED,
                    rating=9,
                ),
                Movie(
                    title="Arrival",
                    director="Denis Villeneuve",
                    year=2016,
                    genre="Science Fiction",
                ),
                Movie(
                    title="Saw",
                    director="James Wan",
                    year=2004,
                    genre="Horror",
                    status=WatchStatus.WATCHED,
                    rating=8,
                ),
            ]
        )
        self.service = WatchlistService(self.repository)

    def test_add_persists_movie_and_sets_watched_timestamp(self) -> None:
        added = self.service.add(Movie(title="Heat", status=WatchStatus.WATCHED))

        self.assertIsNotNone(added.watched_on)
        self.assertEqual(self.service.movies[-1], added)
        self.assertEqual(self.repository.save_calls, 1)

    def test_update_validates_and_persists_changes(self) -> None:
        updated = self.service.update(1, rating=10, status="watched")

        self.assertEqual(updated.rating, 10)
        self.assertIs(updated.status, WatchStatus.WATCHED)
        self.assertIsNotNone(updated.watched_on)
        self.assertEqual(self.repository.save_calls, 1)

    def test_switching_to_planned_removes_timestamp(self) -> None:
        watched = self.service.update(1, status="watched")

        planned = self.service.update(1, status="planned")

        self.assertIsNotNone(watched.watched_on)
        self.assertIsNone(planned.watched_on)

    def test_delete_returns_removed_movie(self) -> None:
        deleted = self.service.delete(2)

        self.assertEqual(deleted.title, "Saw")
        self.assertEqual(len(self.service.movies), 2)
        self.assertEqual(self.repository.save_calls, 1)

    def test_rejects_missing_index(self) -> None:
        for index in (-1, 3, True):
            with self.subTest(index=index), self.assertRaises(MovieNotFoundError):
                self.service.get(index)

    def test_rejects_unknown_update_fields(self) -> None:
        with self.assertRaisesRegex(ValidationError, "Unsupported"):
            self.service.update(0, unknown="value")

    def test_searches_title_director_and_genre_case_insensitively(self) -> None:
        self.assertEqual(
            [movie.title for movie in self.service.search("nolan")],
            ["Inception"],
        )
        self.assertEqual(
            [movie.title for movie in self.service.search("SCIENCE")],
            ["Inception", "Arrival"],
        )
        self.assertEqual(
            [movie.title for movie in self.service.search("saw")],
            ["Saw"],
        )

    def test_empty_search_returns_all_movies(self) -> None:
        self.assertEqual(self.service.search("  "), list(self.service.movies))

    def test_sort_does_not_change_persisted_order(self) -> None:
        sorted_titles = [
            movie.title for movie in self.service.sorted_movies("year", reverse=True)
        ]

        self.assertEqual(sorted_titles, ["Arrival", "Inception", "Saw"])
        self.assertEqual(
            [movie.title for movie in self.service.movies],
            ["Inception", "Arrival", "Saw"],
        )

    def test_rejects_unknown_sort_field(self) -> None:
        with self.assertRaisesRegex(ValidationError, "Sort field"):
            self.service.sorted_movies("director")

    def test_calculates_statistics(self) -> None:
        statistics = self.service.statistics()

        self.assertEqual(statistics.total, 3)
        self.assertEqual(statistics.watched, 2)
        self.assertEqual(statistics.planned, 1)
        self.assertEqual(statistics.rated, 2)
        self.assertEqual(statistics.average_rating, 8.5)
        self.assertEqual(statistics.highest_rated.title, "Inception")
        self.assertEqual(statistics.genre_counts, {"Horror": 1, "Science Fiction": 2})


if __name__ == "__main__":
    unittest.main()
