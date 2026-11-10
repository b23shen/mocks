"""All custom errors for the theatre booking module.

Every error is a subclass of BookingError, so callers can catch all of them
with one `except BookingError`. Errors about bad input values are also
subclasses of ValueError, so code that catches ValueError keeps working.
"""


class BookingError(Exception):
    """Base class for all errors raised by the theatre module."""


class InvalidTheatreSizeError(BookingError, ValueError):
    """Raised when the number of rows or seats per row is not positive."""


class InvalidSeatError(BookingError, ValueError):
    """Raised when a row or seat number is outside the theatre."""


class InvalidBlockSizeError(BookingError, ValueError):
    """Raised when the number of seats in a block is less than 1."""


class InvalidCustomerIdError(BookingError, ValueError):
    """Raised when a customer id is empty or only whitespace."""


class SeatTakenError(BookingError):
    """Raised when someone tries to book a seat that is already booked."""


class NoFreeBlockError(BookingError):
    """Raised when no row has enough free seats next to each other."""


class SeatNotBookedError(BookingError):
    """Raised when someone tries to cancel a seat that is free."""


class NotSeatOwnerError(BookingError):
    """Raised when a customer tries to cancel a seat booked by someone else."""
