"""Tests for movie validation and serialization."""

from __future__ import annotations

import unittest
from datetime import datetime

from watchlist_manager.errors import ValidationError
from watchlist_manager.models import Movie, WatchStatus


class MovieTests(unittest.TestCase):
    def test_normalizes_text_and_status(self) -> None:
        movie = Movie(
            title="  Inception  ",
            director="  Christopher Nolan ",
            genre=" Thriller ",
            status="watched",
        )

        self.assertEqual(movie.title, "Inception")
        self.assertEqual(movie.director, "Christopher Nolan")
        self.assertEqual(movie.genre, "Thriller")
        self.assertIs(movie.status, WatchStatus.WATCHED)

    def test_reads_legacy_polish_statuses(self) -> None:
        watched = Movie.from_dict({"title": "Saw", "status": "obejrzany"})
        planned = Movie.from_dict({"title": "Arrival", "status": "nieobejrzany"})

        self.assertIs(watched.status, WatchStatus.WATCHED)
        self.assertIs(planned.status, WatchStatus.PLANNED)

    def test_round_trip_preserves_supported_fields(self) -> None:
        watched_on = datetime.fromisoformat("2026-01-10T20:15:00+01:00")
        original = Movie(
            title="Interstellar",
            director="Christopher Nolan",
            year=2014,
            genre="Science Fiction",
            status=WatchStatus.WATCHED,
            rating=10,
            description="A mission through space and time.",
            watched_on=watched_on,
        )

        restored = Movie.from_dict(original.to_dict())

        self.assertEqual(restored, original)

    def test_planned_movie_cannot_keep_watched_timestamp(self) -> None:
        movie = Movie(
            title="Arrival",
            status=WatchStatus.PLANNED,
            watched_on=datetime.now(),
        )

        self.assertIsNone(movie.watched_on)

    def test_rejects_empty_title(self) -> None:
        with self.assertRaisesRegex(ValidationError, "Title"):
            Movie(title="   ")

    def test_rejects_invalid_year(self) -> None:
        for year in (1887, 2101, True, "2010"):
            with self.subTest(year=year), self.assertRaisesRegex(ValidationError, "Year"):
                Movie(title="Example", year=year)

    def test_rejects_invalid_rating(self) -> None:
        for rating in (-1, 11, True, "9"):
            with self.subTest(rating=rating), self.assertRaisesRegex(
                ValidationError, "Rating"
            ):
                Movie(title="Example", rating=rating)

    def test_rejects_unknown_status(self) -> None:
        with self.assertRaisesRegex(ValidationError, "Status"):
            Movie(title="Example", status="paused")

    def test_rejects_non_string_json_field(self) -> None:
        with self.assertRaisesRegex(ValidationError, "Text fields"):
            Movie.from_dict({"title": ["not", "text"]})


if __name__ == "__main__":
    unittest.main()
