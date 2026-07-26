"""Application services for managing and analyzing a watchlist."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from statistics import mean
from typing import Any

from watchlist_manager.errors import MovieNotFoundError, ValidationError
from watchlist_manager.models import Movie, WatchStatus
from watchlist_manager.repository import MovieRepository


@dataclass(frozen=True, slots=True)
class CatalogStatistics:
    """Summary metrics calculated from the current watchlist."""

    total: int
    watched: int
    planned: int
    rated: int
    average_rating: float | None
    highest_rated: Movie | None
    genre_counts: Mapping[str, int]


class WatchlistService:
    """Coordinate validation, persistence, search, and statistics."""

    SORT_FIELDS: Mapping[str, Callable[[Movie], Any]] = {
        "title": lambda movie: movie.title.casefold(),
        "year": lambda movie: movie.year if movie.year is not None else -1,
        "genre": lambda movie: movie.genre.casefold(),
        "rating": lambda movie: movie.rating if movie.rating is not None else -1,
        "status": lambda movie: movie.status.value,
    }

    def __init__(self, repository: MovieRepository) -> None:
        self._repository = repository
        self._movies = repository.load()

    @property
    def movies(self) -> tuple[Movie, ...]:
        """Return an immutable view of the current collection."""
        return tuple(self._movies)

    def add(self, movie: Movie) -> Movie:
        """Add and persist one movie."""
        normalized = self._apply_status_timestamp(movie)
        self._persist([*self._movies, normalized])
        return normalized

    def get(self, index: int) -> Movie:
        """Return a movie by its displayed index."""
        if isinstance(index, bool) or not 0 <= index < len(self._movies):
            raise MovieNotFoundError(f"Movie index {index} does not exist.")
        return self._movies[index]

    def update(self, index: int, **changes: Any) -> Movie:
        """Validate and persist selected changes to a movie."""
        current = self.get(index)
        allowed_fields = {
            "title",
            "director",
            "year",
            "genre",
            "status",
            "rating",
            "description",
        }
        unknown_fields = set(changes) - allowed_fields
        if unknown_fields:
            unknown = ", ".join(sorted(unknown_fields))
            raise ValidationError(f"Unsupported update fields: {unknown}.")

        if "status" in changes:
            changes["status"] = WatchStatus.parse(changes["status"])

        updated = self._apply_status_timestamp(replace(current, **changes), previous=current)
        movies = self._movies.copy()
        movies[index] = updated
        self._persist(movies)
        return updated

    def delete(self, index: int) -> Movie:
        """Delete and return a movie by index."""
        movie = self.get(index)
        movies = self._movies.copy()
        del movies[index]
        self._persist(movies)
        return movie

    def search(self, query: str) -> list[Movie]:
        """Find movies by case-insensitive text in common fields."""
        normalized = query.strip().casefold()
        if not normalized:
            return list(self._movies)

        return [
            movie
            for movie in self._movies
            if any(
                normalized in value.casefold()
                for value in (movie.title, movie.director, movie.genre)
            )
        ]

    def sorted_movies(self, field: str, *, reverse: bool = False) -> list[Movie]:
        """Return a sorted copy without changing persisted order."""
        try:
            key = self.SORT_FIELDS[field]
        except KeyError as error:
            allowed = ", ".join(self.SORT_FIELDS)
            raise ValidationError(f"Sort field must be one of: {allowed}.") from error
        return sorted(self._movies, key=key, reverse=reverse)

    def statistics(self) -> CatalogStatistics:
        """Calculate aggregate watchlist metrics."""
        ratings = [movie.rating for movie in self._movies if movie.rating is not None]
        watched = sum(movie.status is WatchStatus.WATCHED for movie in self._movies)
        genre_counts = Counter(movie.genre or "Unspecified" for movie in self._movies)
        highest_rated = max(
            (movie for movie in self._movies if movie.rating is not None),
            key=lambda movie: movie.rating,
            default=None,
        )

        return CatalogStatistics(
            total=len(self._movies),
            watched=watched,
            planned=len(self._movies) - watched,
            rated=len(ratings),
            average_rating=mean(ratings) if ratings else None,
            highest_rated=highest_rated,
            genre_counts=dict(sorted(genre_counts.items())),
        )

    def _persist(self, movies: Iterable[Movie]) -> None:
        updated = list(movies)
        self._repository.save(updated)
        self._movies = updated

    @staticmethod
    def _apply_status_timestamp(movie: Movie, previous: Movie | None = None) -> Movie:
        if movie.status is WatchStatus.PLANNED:
            return replace(movie, watched_on=None)
        if movie.watched_on is not None:
            return movie
        if previous is not None and previous.watched_on is not None:
            return replace(movie, watched_on=previous.watched_on)
        return replace(movie, watched_on=datetime.now().astimezone())
