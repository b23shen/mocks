"""Assign a random gift receiver to every participant.

Each person gives exactly one gift and receives exactly one gift, and nobody
gives a gift to themselves. The assignment works like this: shuffle the
participants, then each person gives to the next person in the shuffled list,
and the last person gives to the first. This always makes one big circle.
"""

import csv
import random
from dataclasses import dataclass

from errors import (
    DuplicateEmailError,
    EmptyFieldError,
    InvalidCsvError,
    NotEnoughParticipantsError,
)

REQUIRED_COLUMNS = ("name", "email")


@dataclass(frozen=True)
class Participant:
    """One person in the gift exchange.

    Frozen so a Participant can be used as a dict key.

    Attributes:
        name: The person's display name.
        email: The person's email. It is unique for each participant.
    """

    name: str
    email: str


def load_participants(path: str) -> list[Participant]:
    """Read participants from a CSV file with 'name' and 'email' columns.

    Leading and trailing spaces are removed from every value. The file is
    not validated here; call validate() for that.

    Args:
        path: The path to the CSV file. The first line must be the header.

    Returns:
        The participants in the same order as the rows in the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        InvalidCsvError: If the header is missing 'name' or 'email'.
    """
    with open(path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        _check_header(reader.fieldnames)
        return [_row_to_participant(row) for row in reader]


def validate(participants: list[Participant]) -> None:
    """Check that the participants can be used for a gift exchange.

    Args:
        participants: The people taking part.

    Returns:
        None. The function only raises when something is wrong.

    Raises:
        EmptyFieldError: If any name or email is empty.
        DuplicateEmailError: If two participants share an email.
        NotEnoughParticipantsError: If there are fewer than 2 participants.
    """
    _check_no_empty_fields(participants)
    _check_unique_emails(participants)
    if len(participants) < 2:
        raise NotEnoughParticipantsError(
            f"Need at least 2 participants, got {len(participants)}."
        )


def assign(
    participants: list[Participant], rng: random.Random | None = None
) -> dict[Participant, Participant]:
    """Give every participant one random receiver.

    Args:
        participants: The people taking part. The list is not changed.
        rng: The random generator to use. Pass a seeded random.Random in
            tests to get the same result every time. If None, a new
            unseeded generator is used.

    Returns:
        A dict that maps each giver to their receiver. Every participant is
        a key once and a value once, and no key maps to itself.

    Raises:
        EmptyFieldError: If any name or email is empty.
        DuplicateEmailError: If two participants share an email.
        NotEnoughParticipantsError: If there are fewer than 2 participants.
    """
    validate(participants)
    rng = rng or random.Random()
    # Shuffle a copy so the caller's list keeps its order.
    order = list(participants)
    rng.shuffle(order)
    # i gives to i+1; the modulo makes the last person give to the first.
    return {order[i]: order[(i + 1) % len(order)] for i in range(len(order))}


def _check_header(fieldnames: list[str] | None) -> None:
    """Raise InvalidCsvError if a required column is missing."""
    columns = [name.strip().lower() for name in fieldnames or []]
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
    if missing:
        raise InvalidCsvError(f"CSV is missing columns: {', '.join(missing)}.")


def _row_to_participant(row: dict[str, str | None]) -> Participant:
    """Build a Participant from one CSV row, ignoring case and spaces in keys."""
    # A short row gives None for missing cells; treat that as empty.
    clean = {
        (key or "").strip().lower(): (value or "").strip()
        for key, value in row.items()
    }
    return Participant(name=clean["name"], email=clean["email"])


def _check_no_empty_fields(participants: list[Participant]) -> None:
    """Raise EmptyFieldError if any participant has an empty name or email."""
    for index, person in enumerate(participants):
        if not person.name.strip() or not person.email.strip():
            raise EmptyFieldError(f"Participant {index} has an empty name or email.")


def _check_unique_emails(participants: list[Participant]) -> None:
    """Raise DuplicateEmailError if two participants share an email."""
    seen: set[str] = set()
    for person in participants:
        # Emails are case-insensitive in practice, so compare in lower case.
        key = person.email.strip().lower()
        if key in seen:
            raise DuplicateEmailError(f"Duplicate email: {person.email}.")
        seen.add(key)
