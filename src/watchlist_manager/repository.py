"""JSON persistence for watchlist entries."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from watchlist_manager.errors import DataFormatError, ValidationError
from watchlist_manager.models import Movie


class MovieRepository(Protocol):
    """Persistence contract used by the application service."""

    def load(self) -> list[Movie]:
        """Load all movies."""

    def save(self, movies: Sequence[Movie]) -> None:
        """Persist all movies."""


class JsonMovieRepository:
    """Store a watchlist in an atomically replaced JSON file."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)

    def load(self) -> list[Movie]:
        """Load and validate every database record."""
        if not self.database_path.exists():
            return []

        try:
            raw_data = json.loads(self.database_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as error:
            raise DataFormatError(
                f"Could not read database '{self.database_path}': {error}"
            ) from error
        except json.JSONDecodeError as error:
            raise DataFormatError(
                f"Database '{self.database_path}' contains invalid JSON at "
                f"line {error.lineno}, column {error.colno}."
            ) from error

        if not isinstance(raw_data, list):
            raise DataFormatError("The database root must be a JSON array.")

        movies: list[Movie] = []
        for index, item in enumerate(raw_data):
            try:
                movies.append(Movie.from_dict(item))
            except ValidationError as error:
                message = f"Invalid movie at database index {index}: {error}"
                raise DataFormatError(message) from error
        return movies

    def save(self, movies: Sequence[Movie]) -> None:
        """Write valid JSON and replace the previous database atomically."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            [movie.to_dict() for movie in movies],
            ensure_ascii=False,
            indent=2,
        )

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self.database_path.parent,
                prefix=f".{self.database_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(payload)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            temporary_path.replace(self.database_path)
        except OSError:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise
