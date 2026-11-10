"""All custom errors for the gift exchange module.

Every error is a subclass of GiftExchangeError, so callers can catch all of
them with one `except GiftExchangeError`. Errors about bad input values are
also subclasses of ValueError, so code that catches ValueError keeps working.
"""


class GiftExchangeError(Exception):
    """Base class for all errors raised by the gift exchange module."""


class InvalidCsvError(GiftExchangeError, ValueError):
    """Raised when the CSV file does not have the 'name' and 'email' columns."""


class EmptyFieldError(GiftExchangeError, ValueError):
    """Raised when a name or email is empty or only whitespace."""


class DuplicateEmailError(GiftExchangeError, ValueError):
    """Raised when two participants have the same email."""


class NotEnoughParticipantsError(GiftExchangeError, ValueError):
    """Raised when there are fewer than 2 participants."""
