"""A booking system for one small movie theatre.

Seats are stored in a nested list: seats[row][seat] holds the id of the
customer who booked it, or None when the seat is free. Row and seat numbers
start at 0.
"""

from errors import (
    InvalidCustomerIdError,
    InvalidSeatError,
    InvalidTheatreSizeError,
    NotSeatOwnerError,
    SeatNotBookedError,
    SeatTakenError,
)


class Theatre:
    """A theatre with a fixed grid of seats that customers can book and cancel."""

    def __init__(self, rows: int, seats_per_row: int) -> None:
        """Create a theatre where every seat is free.

        Args:
            rows: The number of rows. Must be an int > 0.
            seats_per_row: The number of seats in each row. Must be an int > 0.

        Raises:
            TypeError: If rows or seats_per_row is not an int.
            InvalidTheatreSizeError: If rows or seats_per_row is <= 0.
        """
        _check_size(rows, "rows")
        _check_size(seats_per_row, "seats_per_row")
        self._rows = rows
        self._seats_per_row = seats_per_row
        # Build each row on its own; [[None] * n] * m would share one list.
        self._seats: list[list[str | None]] = [
            [None] * seats_per_row for _ in range(rows)
        ]

    def available_seats(self) -> list[tuple[int, int]]:
        """List every free seat.

        Returns:
            A list of (row, seat) pairs, in row order and then seat order.
        """
        return [
            (row, seat)
            for row, row_seats in enumerate(self._seats)
            for seat, owner in enumerate(row_seats)
            if owner is None
        ]

    def book(self, row: int, seat: int, customer_id: str) -> None:
        """Book a free seat for a customer.

        Args:
            row: The row number, from 0 to rows - 1.
            seat: The seat number in the row, from 0 to seats_per_row - 1.
            customer_id: The id of the customer. Must be a non-empty string.

        Raises:
            TypeError: If row or seat is not an int, or customer_id is not a str.
            InvalidSeatError: If row or seat is outside the theatre.
            InvalidCustomerIdError: If customer_id is empty or only whitespace.
            SeatTakenError: If the seat is already booked, even by the same
                customer.
        """
        self._check_seat(row, seat)
        _check_customer_id(customer_id)
        # Never overwrite a booking: this is what stops two people
        # from getting the same seat.
        if self._seats[row][seat] is not None:
            raise SeatTakenError(f"seat ({row}, {seat}) is already booked")
        self._seats[row][seat] = customer_id

    def cancel(self, row: int, seat: int, customer_id: str) -> None:
        """Cancel a customer's booking so the seat becomes free.

        Args:
            row: The row number, from 0 to rows - 1.
            seat: The seat number in the row, from 0 to seats_per_row - 1.
            customer_id: The id of the customer who booked the seat.

        Raises:
            TypeError: If row or seat is not an int, or customer_id is not a str.
            InvalidSeatError: If row or seat is outside the theatre.
            InvalidCustomerIdError: If customer_id is empty or only whitespace.
            SeatNotBookedError: If the seat is free.
            NotSeatOwnerError: If the seat was booked by another customer.
        """
        self._check_seat(row, seat)
        _check_customer_id(customer_id)
        owner = self._seats[row][seat]
        if owner is None:
            raise SeatNotBookedError(f"seat ({row}, {seat}) is not booked")
        if owner != customer_id:
            raise NotSeatOwnerError(
                f"seat ({row}, {seat}) was booked by another customer"
            )
        self._seats[row][seat] = None

    def _check_seat(self, row: int, seat: int) -> None:
        """Check that (row, seat) is a real seat in this theatre.

        Args:
            row: The row number to check.
            seat: The seat number to check.

        Raises:
            TypeError: If row or seat is not an int.
            InvalidSeatError: If row or seat is outside the theatre.
        """
        _check_int(row, "row")
        _check_int(seat, "seat")
        # Check bounds by hand: Python would accept a negative index
        # and quietly use a seat from the end of the row.
        if not 0 <= row < self._rows:
            raise InvalidSeatError(f"row must be from 0 to {self._rows - 1}, got {row}")
        if not 0 <= seat < self._seats_per_row:
            raise InvalidSeatError(
                f"seat must be from 0 to {self._seats_per_row - 1}, got {seat}"
            )


def _check_int(value: int, name: str) -> None:
    """Check that value is an int and not a bool.

    Args:
        value: The value to check.
        name: The argument name, used in the error message.

    Raises:
        TypeError: If value is not an int, or is a bool.
    """
    # bool is a subclass of int, but True/False are never a valid number here.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")


def _check_size(value: int, name: str) -> None:
    """Check that a theatre size is a positive int.

    Args:
        value: The size to check.
        name: The argument name, used in the error message.

    Raises:
        TypeError: If value is not an int.
        InvalidTheatreSizeError: If value is <= 0.
    """
    _check_int(value, name)
    if value <= 0:
        raise InvalidTheatreSizeError(f"{name} must be > 0, got {value}")


def _check_customer_id(customer_id: str) -> None:
    """Check that a customer id is a non-empty string.

    Args:
        customer_id: The id to check.

    Raises:
        TypeError: If customer_id is not a str.
        InvalidCustomerIdError: If customer_id is empty or only whitespace.
    """
    if not isinstance(customer_id, str):
        raise TypeError(f"customer_id must be a str, got {type(customer_id).__name__}")
    if not customer_id.strip():
        raise InvalidCustomerIdError("customer_id must not be empty")
