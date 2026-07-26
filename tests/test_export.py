"""Tests for tab-separated exports."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from watchlist_manager.export import EXPORT_FIELDS, export_tsv
from watchlist_manager.models import Movie


class ExportTests(unittest.TestCase):
    def test_exports_header_and_movie_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "nested" / "movies.tsv"

            result = export_tsv(
                [Movie(title="Arrival", year=2016, genre="Science Fiction")],
                destination,
            )

            with result.open(encoding="utf-8", newline="") as exported_file:
                rows = list(csv.DictReader(exported_file, delimiter="\t"))

        self.assertEqual(result, destination)
        self.assertEqual(tuple(rows[0]), EXPORT_FIELDS)
        self.assertEqual(rows[0]["title"], "Arrival")
        self.assertEqual(rows[0]["year"], "2016")


if __name__ == "__main__":
    unittest.main()
