"""Tests for the Theatre class in theatre.py. Rows and seats start at 0."""

import pytest

from errors import (
    BookingError,
    InvalidCustomerIdError,
    InvalidSeatError,
    InvalidTheatreSizeError,
    NotSeatOwnerError,
    SeatNotBookedError,
    SeatTakenError,
)
from theatre import Theatre


@pytest.fixture
def theatre() -> Theatre:
    """Return an empty theatre with 2 rows of 3 seats."""
    return Theatre(2, 3)


def test_new_theatre_has_all_seats_available(theatre: Theatre) -> None:
    """A new theatre lists every seat as free, in row then seat order."""
    assert theatre.available_seats() == [
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 1), (1, 2),
    ]


@pytest.mark.parametrize(
    ("rows", "seats_per_row", "error"),
    [
        (0, 3, InvalidTheatreSizeError),
        (2, 0, InvalidTheatreSizeError),
        (-1, 3, InvalidTheatreSizeError),
        (2.0, 3, TypeError),
        (True, 3, TypeError),
        (2, "3", TypeError),
    ],
)
def test_invalid_theatre_size_raises(
    rows: object, seats_per_row: object, error: type[Exception]
) -> None:
    """Sizes that are not positive ints are rejected."""
    with pytest.raises(error):
        Theatre(rows, seats_per_row)  # type: ignore[arg-type]


def test_book_free_seat_removes_it_from_available(theatre: Theatre) -> None:
    """Booking a seat removes only that seat from the free list."""
    theatre.book(1, 2, "alice")
    available = theatre.available_seats()
    assert (1, 2) not in available
    assert len(available) == 5


def test_book_taken_seat_raises_and_keeps_first_owner(theatre: Theatre) -> None:
    """A second booking of the same seat fails and does not change the owner."""
    theatre.book(0, 1, "alice")
    with pytest.raises(SeatTakenError):
        theatre.book(0, 1, "bob")
    # The same customer cannot book the seat twice either.
    with pytest.raises(SeatTakenError):
        theatre.book(0, 1, "alice")
    # bob is not the owner, so alice must still be.
    with pytest.raises(NotSeatOwnerError):
        theatre.cancel(0, 1, "bob")
    theatre.cancel(0, 1, "alice")


@pytest.mark.parametrize(
    ("row", "seat", "error"),
    [
        (-1, 0, InvalidSeatError),
        (0, -1, InvalidSeatError),
        (2, 0, InvalidSeatError),
        (0, 3, InvalidSeatError),
        (0.0, 0, TypeError),
        (0, False, TypeError),
    ],
)
def test_out_of_range_or_negative_seat_raises(
    theatre: Theatre, row: object, seat: object, error: type[Exception]
) -> None:
    """Seats outside the theatre are rejected for both book and cancel."""
    with pytest.raises(error):
        theatre.book(row, seat, "alice")  # type: ignore[arg-type]
    with pytest.raises(error):
        theatre.cancel(row, seat, "alice")  # type: ignore[arg-type]
    # A rejected call must not book any seat.
    assert len(theatre.available_seats()) == 6


@pytest.mark.parametrize(
    ("customer_id", "error"),
    [("", InvalidCustomerIdError), ("   ", InvalidCustomerIdError), (None, TypeError)],
)
def test_invalid_customer_id_raises(
    theatre: Theatre, customer_id: object, error: type[Exception]
) -> None:
    """Empty, blank, or non-str customer ids are rejected."""
    with pytest.raises(error):
        theatre.book(0, 0, customer_id)  # type: ignore[arg-type]
    assert (0, 0) in theatre.available_seats()


def test_cancel_by_owner_frees_seat(theatre: Theatre) -> None:
    """The owner can cancel, and then another customer can book the seat."""
    theatre.book(0, 0, "alice")
    theatre.cancel(0, 0, "alice")
    assert (0, 0) in theatre.available_seats()
    theatre.book(0, 0, "bob")
    assert (0, 0) not in theatre.available_seats()


def test_cancel_free_seat_or_by_other_customer_raises(theatre: Theatre) -> None:
    """Cancel fails on a free seat, and on a seat owned by someone else."""
    with pytest.raises(SeatNotBookedError):
        theatre.cancel(0, 0, "alice")
    theatre.book(0, 0, "alice")
    with pytest.raises(NotSeatOwnerError):
        theatre.cancel(0, 0, "bob")
    assert (0, 0) not in theatre.available_seats()
    # All booking errors share one base class.
    assert issubclass(NotSeatOwnerError, BookingError)
