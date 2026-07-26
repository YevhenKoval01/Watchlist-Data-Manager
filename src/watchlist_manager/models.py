"""Domain models and validation rules for watchlist entries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from watchlist_manager.errors import ValidationError


class WatchStatus(str, Enum):
    """Supported watch states."""

    PLANNED = "planned"
    WATCHED = "watched"

    @classmethod
    def parse(cls, value: WatchStatus | str) -> WatchStatus:
        """Normalize current and legacy status names."""
        if isinstance(value, cls):
            return value

        normalized = str(value).strip().casefold()
        aliases = {
            "planned": cls.PLANNED,
            "unwatched": cls.PLANNED,
            "nieobejrzany": cls.PLANNED,
            "watched": cls.WATCHED,
            "obejrzany": cls.WATCHED,
        }
        try:
            return aliases[normalized]
        except KeyError as error:
            allowed = ", ".join(status.value for status in cls)
            raise ValidationError(f"Status must be one of: {allowed}.") from error


@dataclass(frozen=True, slots=True)
class Movie:
    """A validated movie stored in the watchlist."""

    title: str
    director: str = ""
    year: int | None = None
    genre: str = ""
    status: WatchStatus = WatchStatus.PLANNED
    rating: int | None = None
    description: str = ""
    watched_on: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "director", self.director.strip())
        object.__setattr__(self, "genre", self.genre.strip())
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "status", WatchStatus.parse(self.status))

        if not self.title:
            raise ValidationError("Title cannot be empty.")
        if self.year is not None and (
            isinstance(self.year, bool)
            or not isinstance(self.year, int)
            or not 1888 <= self.year <= 2100
        ):
            raise ValidationError("Year must be between 1888 and 2100.")
        if self.rating is not None and (
            isinstance(self.rating, bool)
            or not isinstance(self.rating, int)
            or not 0 <= self.rating <= 10
        ):
            raise ValidationError("Rating must be between 0 and 10.")
        if self.status is WatchStatus.PLANNED and self.watched_on is not None:
            object.__setattr__(self, "watched_on", None)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Movie:
        """Build a movie from a JSON-compatible mapping."""
        if not isinstance(data, Mapping):
            raise ValidationError("Each database entry must be a JSON object.")

        watched_on = data.get("watched_on")
        if watched_on:
            try:
                watched_on = datetime.fromisoformat(str(watched_on))
            except ValueError as error:
                raise ValidationError("'watched_on' must use ISO 8601 format.") from error
        else:
            watched_on = None

        return cls(
            title=_string_value(data.get("title")),
            director=_string_value(data.get("director")),
            year=_optional_integer(data.get("year"), "year"),
            genre=_string_value(data.get("genre")),
            status=WatchStatus.parse(data.get("status", WatchStatus.PLANNED)),
            rating=_optional_integer(data.get("rating"), "rating"),
            description=_string_value(data.get("description")),
            watched_on=watched_on,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "title": self.title,
            "director": self.director,
            "year": self.year,
            "genre": self.genre,
            "status": self.status.value,
            "rating": self.rating,
            "description": self.description,
            "watched_on": self.watched_on.isoformat() if self.watched_on else None,
        }


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError("Text fields must contain strings.")
    return value


def _optional_integer(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"'{field_name}' must be an integer or null.")
    return value
