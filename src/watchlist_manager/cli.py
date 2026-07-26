"""Interactive command-line interface for Watchlist Data Manager."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from watchlist_manager import __version__
from watchlist_manager.errors import WatchlistError
from watchlist_manager.export import export_tsv
from watchlist_manager.models import Movie, WatchStatus
from watchlist_manager.repository import JsonMovieRepository
from watchlist_manager.service import CatalogStatistics, WatchlistService

InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


class InteractiveCLI:
    """Menu-based interface with injectable input and output functions."""

    def __init__(
        self,
        service: WatchlistService,
        *,
        input_function: InputFunction = input,
        output_function: OutputFunction = print,
    ) -> None:
        self.service = service
        self._input = input_function
        self._output = output_function
        self._actions: dict[str, tuple[str, Callable[[], None] | None]] = {
            "1": ("Add a movie", self.add_movie),
            "2": ("List the collection", self.list_collection),
            "3": ("Search", self.search),
            "4": ("Edit a movie", self.edit_movie),
            "5": ("Delete a movie", self.delete_movie),
            "6": ("Sort and display", self.sort_collection),
            "7": ("Export to TSV", self.export_collection),
            "8": ("Show statistics", self.show_statistics),
            "9": ("Filter the collection", self.filter_collection),
            "10": ("Recommend a planned movie", self.recommend_movie),
            "0": ("Exit", None),
        }

    def run(self) -> int:
        """Run the menu until the user exits."""
        while True:
            self._output("\n===== WATCHLIST DATA MANAGER =====")
            for key, (description, _) in self._actions.items():
                self._output(f"{key}. {description}")

            try:
                choice = self._input("Choose an option: ").strip()
            except (EOFError, KeyboardInterrupt):
                self._output("\nGoodbye.")
                return 0

            if choice == "0":
                self._output("Goodbye.")
                return 0

            action = self._actions.get(choice, ("", None))[1]
            if action is None:
                self._output("[ERROR] Invalid menu option.")
                continue

            try:
                action()
            except (EOFError, KeyboardInterrupt):
                self._output("\nGoodbye.")
                return 0
            except (WatchlistError, OSError) as error:
                self._output(f"[ERROR] {error}")

    def add_movie(self) -> None:
        """Collect, validate, and persist a new movie."""
        title = self._read_text("Title: ")
        director = self._read_text("Director (optional): ", allow_empty=True)
        year = self._read_integer("Release year (optional): ", allow_empty=True)
        genre = self._read_text("Genre (optional): ", allow_empty=True)
        status_text = self._read_text(
            "Status [planned/watched] (default: planned): ",
            allow_empty=True,
        )
        movie = Movie(
            title=title,
            director=director,
            year=year,
            genre=genre,
            status=WatchStatus.parse(status_text or WatchStatus.PLANNED),
            rating=self._read_integer(
                "Rating 0-10 (optional): ",
                allow_empty=True,
                minimum=0,
                maximum=10,
            ),
            description=self._read_text("Description (optional): ", allow_empty=True),
        )
        added = self.service.add(movie)
        self._output(f"[OK] Added '{added.title}'.")

    def list_collection(self) -> None:
        """Display all movies in persisted order."""
        self._display_movies(self.service.movies)

    def search(self) -> None:
        """Search common text fields."""
        query = self._read_text("Search title, director, or genre: ")
        results = self.service.search(query)
        self._display_movies(results)
        self._output(f"Found: {len(results)}")

    def edit_movie(self) -> None:
        """Update selected fields while preserving blank answers."""
        self.list_collection()
        index = self._read_integer("Movie index to edit: ", minimum=0)
        assert index is not None
        movie = self.service.get(index)
        self._output("Press Enter to keep the current value.")

        changes: dict[str, object] = {}
        text_fields = (
            ("title", "Title"),
            ("director", "Director"),
            ("genre", "Genre"),
            ("description", "Description"),
        )
        for field, label in text_fields:
            current_value = getattr(movie, field)
            value = self._read_text(f"{label} [{current_value}]: ", allow_empty=True)
            if value:
                changes[field] = value

        year = self._read_integer(
            f"Release year [{movie.year if movie.year is not None else '-'}]: ",
            allow_empty=True,
        )
        if year is not None:
            changes["year"] = year

        status = self._read_text(
            f"Status [{movie.status.value}] (planned/watched): ",
            allow_empty=True,
        )
        if status:
            changes["status"] = WatchStatus.parse(status)

        rating = self._read_integer(
            f"Rating [{movie.rating if movie.rating is not None else '-'}]: ",
            allow_empty=True,
            minimum=0,
            maximum=10,
        )
        if rating is not None:
            changes["rating"] = rating

        updated = self.service.update(index, **changes)
        self._output(f"[OK] Updated '{updated.title}'.")

    def delete_movie(self) -> None:
        """Delete a selected movie after confirmation."""
        self.list_collection()
        index = self._read_integer("Movie index to delete: ", minimum=0)
        assert index is not None
        movie = self.service.get(index)
        confirmation = self._read_text(
            f"Delete '{movie.title}'? [y/N]: ",
            allow_empty=True,
        )
        if confirmation.casefold() not in {"y", "yes"}:
            self._output("Deletion cancelled.")
            return

        deleted = self.service.delete(index)
        self._output(f"[OK] Deleted '{deleted.title}'.")

    def sort_collection(self) -> None:
        """Display a sorted copy of the collection."""
        field = self._read_text(
            "Sort by [title/year/genre/rating/status]: "
        ).casefold()
        descending = self._read_text(
            "Descending order? [y/N]: ",
            allow_empty=True,
        ).casefold() in {"y", "yes"}
        self._display_movies(self.service.sorted_movies(field, reverse=descending))

    def export_collection(self) -> None:
        """Export the current watchlist to a TSV file."""
        destination = self._read_text(
            "Destination (default: exports/watchlist.tsv): ",
            allow_empty=True,
        )
        output_path = export_tsv(
            self.service.movies,
            Path(destination or "exports/watchlist.tsv"),
        )
        self._output(f"[OK] Exported {len(self.service.movies)} movies to '{output_path}'.")

    def show_statistics(self) -> None:
        """Display aggregate metrics and optionally render charts."""
        statistics = self.service.statistics()
        self._display_statistics(statistics)

        if statistics.total == 0:
            return
        show_charts = self._read_text(
            "Open Matplotlib charts? [y/N]: ",
            allow_empty=True,
        )
        if show_charts.casefold() in {"y", "yes"}:
            self._show_charts(statistics)

    def filter_collection(self) -> None:
        """Display movies matching optional filters."""
        status = self._read_text(
            "Status [planned/watched] (optional): ",
            allow_empty=True,
        )
        genre = self._read_text("Genre (optional): ", allow_empty=True)
        minimum_rating = self._read_integer(
            "Minimum rating 0-10 (optional): ",
            allow_empty=True,
            minimum=0,
            maximum=10,
        )
        results = self.service.filter_movies(
            status=status or None,
            genre=genre or None,
            minimum_rating=minimum_rating,
        )
        self._display_movies(results)
        self._output(f"Found: {len(results)}")

    def recommend_movie(self) -> None:
        """Recommend one unwatched movie, optionally from a selected genre."""
        genre = self._read_text(
            "Preferred genre (optional): ",
            allow_empty=True,
        )
        recommendation = self.service.recommend(genre=genre or None)
        year = f" ({recommendation.year})" if recommendation.year else ""
        genre_label = recommendation.genre or "Unspecified genre"
        self._output(
            f"Recommendation: {recommendation.title}{year} - {genre_label}"
        )

    def _display_movies(self, movies: Sequence[Movie]) -> None:
        if not movies:
            self._output("The collection is empty.")
            return

        self._output(" # | Title (year) | Rating | Genre | Status")
        self._output("-" * 72)
        for index, movie in enumerate(movies):
            year = movie.year if movie.year is not None else "-"
            rating = movie.rating if movie.rating is not None else "-"
            genre = movie.genre or "-"
            self._output(
                f"{index:2d} | {movie.title} ({year}) | {rating!s:^6} | "
                f"{genre} | {movie.status.value}"
            )

    def _display_statistics(self, statistics: CatalogStatistics) -> None:
        average = (
            f"{statistics.average_rating:.2f}"
            if statistics.average_rating is not None
            else "not available"
        )
        self._output("\n--- Statistics ---")
        self._output(f"Total movies: {statistics.total}")
        self._output(f"Watched: {statistics.watched}")
        self._output(f"Planned: {statistics.planned}")
        self._output(f"Rated: {statistics.rated}")
        self._output(f"Average rating: {average}")
        if statistics.highest_rated:
            self._output(
                f"Highest rated: {statistics.highest_rated.title} "
                f"({statistics.highest_rated.rating}/10)"
            )
        self._output("Movies by genre:")
        for genre, count in statistics.genre_counts.items():
            self._output(f"  {genre}: {count}")

    def _show_charts(self, statistics: CatalogStatistics) -> None:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            self._output(
                "[ERROR] Matplotlib is not installed. "
                "Run 'pip install -e .[charts]' to enable charts."
            )
            return

        ratings = [
            movie.rating for movie in self.service.movies if movie.rating is not None
        ]
        figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        axes[0].bar(
            statistics.genre_counts.keys(),
            statistics.genre_counts.values(),
        )
        axes[0].set_title("Movies by genre")
        axes[0].tick_params(axis="x", rotation=35)

        axes[1].hist(ratings, bins=range(0, 12), edgecolor="black", align="left")
        axes[1].set_title("Rating distribution")
        axes[1].set_xticks(range(0, 11))
        figure.tight_layout()
        plt.show()

    def _read_text(self, message: str, *, allow_empty: bool = False) -> str:
        while True:
            value = self._input(message).strip()
            if value or allow_empty:
                return value
            self._output("[ERROR] This field cannot be empty.")

    def _read_integer(
        self,
        message: str,
        *,
        allow_empty: bool = False,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> int | None:
        while True:
            value = self._input(message).strip()
            if not value and allow_empty:
                return None
            try:
                parsed = int(value)
            except ValueError:
                self._output("[ERROR] Enter a whole number.")
                continue

            if minimum is not None and parsed < minimum:
                self._output(f"[ERROR] Value must be at least {minimum}.")
                continue
            if maximum is not None and parsed > maximum:
                self._output(f"[ERROR] Value must be at most {maximum}.")
                continue
            return parsed


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser."""
    parser = argparse.ArgumentParser(
        description="Manage a local movie watchlist from an interactive terminal."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("watchlist.json"),
        help="JSON database path (default: ./watchlist.json)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    """Application entry point."""
    options = build_parser().parse_args(arguments)
    try:
        service = WatchlistService(JsonMovieRepository(options.database))
    except (WatchlistError, OSError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    return InteractiveCLI(service).run()
