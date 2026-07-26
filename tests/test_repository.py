"""Tests for JSON persistence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from watchlist_manager.errors import DataFormatError
from watchlist_manager.models import Movie, WatchStatus
from watchlist_manager.repository import JsonMovieRepository


class JsonMovieRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "data" / "watchlist.json"
        self.repository = JsonMovieRepository(self.database_path)

    def test_missing_database_returns_empty_collection(self) -> None:
        self.assertEqual(self.repository.load(), [])

    def test_round_trip_creates_parent_directory(self) -> None:
        movies = [
            Movie(
                title="Inception",
                year=2010,
                status=WatchStatus.WATCHED,
                rating=9,
            )
        ]

        self.repository.save(movies)

        self.assertEqual(self.repository.load(), movies)
        self.assertTrue(self.database_path.exists())

    def test_saved_json_is_utf8_and_human_readable(self) -> None:
        self.repository.save([Movie(title="Amelie", description="Cafe in Paris")])

        content = self.database_path.read_text(encoding="utf-8")

        self.assertIn("\n  {", content)
        self.assertTrue(content.endswith("\n"))

    def test_atomic_save_leaves_no_temporary_files(self) -> None:
        self.repository.save([Movie(title="Arrival")])

        temporary_files = list(self.database_path.parent.glob("*.tmp"))

        self.assertEqual(temporary_files, [])

    def test_invalid_json_has_actionable_error(self) -> None:
        self.database_path.parent.mkdir(parents=True)
        self.database_path.write_text("[invalid", encoding="utf-8")

        with self.assertRaisesRegex(DataFormatError, "line 1, column 2"):
            self.repository.load()

    def test_rejects_non_array_database_root(self) -> None:
        self.database_path.parent.mkdir(parents=True)
        self.database_path.write_text('{"title": "Inception"}', encoding="utf-8")

        with self.assertRaisesRegex(DataFormatError, "JSON array"):
            self.repository.load()

    def test_reports_invalid_entry_index(self) -> None:
        self.database_path.parent.mkdir(parents=True)
        self.database_path.write_text(
            json.dumps([{"title": "Valid"}, {"title": ""}]),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(DataFormatError, "index 1"):
            self.repository.load()


if __name__ == "__main__":
    unittest.main()
