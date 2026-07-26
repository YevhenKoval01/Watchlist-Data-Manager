"""Application-specific exceptions."""


class WatchlistError(Exception):
    """Base exception for errors that can be shown safely to a user."""


class DataFormatError(WatchlistError):
    """Raised when the JSON database does not match the expected schema."""


class MovieNotFoundError(WatchlistError, LookupError):
    """Raised when a movie index does not exist."""


class ValidationError(WatchlistError, ValueError):
    """Raised when movie data fails domain validation."""
