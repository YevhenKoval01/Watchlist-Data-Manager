"""Watchlist Data Manager package."""

from watchlist_manager.models import Movie, WatchStatus
from watchlist_manager.repository import JsonMovieRepository
from watchlist_manager.service import CatalogStatistics, WatchlistService

__all__ = [
    "CatalogStatistics",
    "JsonMovieRepository",
    "Movie",
    "WatchStatus",
    "WatchlistService",
]

__version__ = "1.1.0"
