"""Export helpers for watchlist data."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from watchlist_manager.models import Movie

EXPORT_FIELDS = (
    "title",
    "director",
    "year",
    "genre",
    "status",
    "rating",
    "description",
    "watched_on",
)


def export_tsv(movies: Iterable[Movie], destination: Path | str) -> Path:
    """Export movies as a tab-separated UTF-8 file."""
    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=EXPORT_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerows(movie.to_dict() for movie in movies)

    return output_path
