"""Tests for the Theatre class in theatre.py. Rows and seats start at 0."""

import pytest

from errors import (
    BookingError,
    InvalidBlockSizeError,
    InvalidCustomerIdError,
    InvalidSeatError,
    InvalidTheatreSizeError,
    NoFreeBlockError,
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


# --- Block booking -----------------------------------------------------------


@pytest.fixture
def wide_theatre() -> Theatre:
    """Return an empty theatre with 2 rows of 5 seats."""
    return Theatre(2, 5)


def test_book_block_books_all_seats_in_range(wide_theatre: Theatre) -> None:
    """A block books exactly its seats, all for the same customer."""
    wide_theatre.book_block(0, 1, 3, "alice")
    assert wide_theatre.available_seats() == [
        (0, 0), (0, 4),
        (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
    ]
    # Each seat belongs to alice, so she can cancel them one by one.
    for seat in (1, 2, 3):
        wide_theatre.cancel(0, seat, "alice")


def test_cancel_block_cancels_all_seats_in_range(wide_theatre: Theatre) -> None:
    """A block books exactly its seats, all for the same customer."""
    wide_theatre.book_block(0, 1, 3, "alice")
    assert wide_theatre.available_seats() == [
        (0, 0), (0, 4),
        (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
    ]
    wide_theatre.cancel_block(0, 1, 2, "alice")
    assert wide_theatre.available_seats() == [
            (0, 0), (0, 1), (0, 2), (0, 4),
            (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
        ]


def test_book_block_with_one_taken_seat_books_nothing(wide_theatre: Theatre) -> None:
    """If one seat in the block is taken, no seat of the block is booked."""
    wide_theatre.book(0, 3, "bob")
    with pytest.raises(SeatTakenError):
        wide_theatre.book_block(0, 1, 3, "alice")
    # Only bob's seat is gone; seats 1 and 2 were not booked for alice.
    assert len(wide_theatre.available_seats()) == 9
    assert (0, 1) in wide_theatre.available_seats()
    assert (0, 2) in wide_theatre.available_seats()


def test_book_block_past_end_of_row_raises(wide_theatre: Theatre) -> None:
    """A block that would go past the last seat is rejected, not wrapped."""
    with pytest.raises(InvalidSeatError):
        wide_theatre.book_block(0, 3, 3, "alice")
    assert len(wide_theatre.available_seats()) == 10
    # A block that ends exactly on the last seat is fine.
    wide_theatre.book_block(0, 3, 2, "alice")
    assert len(wide_theatre.available_seats()) == 8


@pytest.mark.parametrize(
    ("count", "error"),
    [
        (0, InvalidBlockSizeError),
        (-2, InvalidBlockSizeError),
        (True, TypeError),
        (2.0, TypeError),
    ],
)
def test_invalid_block_count_raises(
    wide_theatre: Theatre, count: object, error: type[Exception]
) -> None:
    """Counts that are not ints >= 1 are rejected by all block methods."""
    with pytest.raises(error):
        wide_theatre.book_block(0, 0, count, "alice")  # type: ignore[arg-type]
    with pytest.raises(error):
        wide_theatre.find_free_block(count)  # type: ignore[arg-type]
    with pytest.raises(error):
        wide_theatre.book_any_block(count, "alice")  # type: ignore[arg-type]
    assert len(wide_theatre.available_seats()) == 10


def test_find_free_block_returns_first_fit(wide_theatre: Theatre) -> None:
    """The search picks the lowest row, then the lowest first seat."""
    assert wide_theatre.find_free_block(3) == (0, 0)
    wide_theatre.book(0, 0, "bob")
    assert wide_theatre.find_free_block(3) == (0, 1)
    # Finding a block does not book it.
    assert len(wide_theatre.available_seats()) == 9


def test_find_free_block_skips_gaps_too_small(wide_theatre: Theatre) -> None:
    """Gaps shorter than count are skipped; blocks never cross rows."""
    # Row 0 free seats: 0, 1, 3 -> no 3 free seats together.
    wide_theatre.book(0, 2, "bob")
    wide_theatre.book(0, 4, "bob")
    # Row 1 free seats: 0, 1 -> joined with row 0's end, it would look
    # like a block of 3 if the search crossed rows.
    for seat in (2, 3, 4):
        wide_theatre.book(1, seat, "bob")
    assert wide_theatre.find_free_block(3) is None
    assert wide_theatre.find_free_block(2) == (0, 0)


def test_find_free_block_returns_none_when_no_block_fits(wide_theatre: Theatre) -> None:
    """A count bigger than a row, or a full theatre, gives None."""
    assert wide_theatre.find_free_block(6) is None
    for row in range(2):
        wide_theatre.book_block(row, 0, 5, "bob")
    assert wide_theatre.find_free_block(1) is None


def test_book_any_block_books_and_returns_position(wide_theatre: Theatre) -> None:
    """It books the first free block and says where; with no block, nothing changes."""
    wide_theatre.book(0, 1, "bob")
    assert wide_theatre.book_any_block(3, "alice") == (0, 2)
    assert wide_theatre.available_seats() == [
        (0, 0),
        (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
    ]
    # Row 1 is the only place for 5 seats, then nothing is left for 2.
    assert wide_theatre.book_any_block(5, "carol") == (1, 0)
    with pytest.raises(NoFreeBlockError):
        wide_theatre.book_any_block(2, "dave")
    assert wide_theatre.available_seats() == [(0, 0)]
