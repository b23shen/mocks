"""Assign a random gift receiver to every participant.

Each person gives exactly one gift and receives exactly one gift, and nobody
gives a gift to themselves. The result is always one big circle: each person
gives to the next person, and the last person gives to the first.

Callers can also pass excluded (giver_email, receiver_email) pairs. The
circle is built one person at a time in random order, and the search goes
back a step when it gets stuck. So if any valid circle exists, it is found.
"""

import csv
import random
from collections.abc import Iterable
from dataclasses import dataclass

from errors import (
    DuplicateEmailError,
    EmptyFieldError,
    InvalidCsvError,
    NoValidAssignmentError,
    NotEnoughParticipantsError,
    UnknownParticipantError,
)

# A (giver_email, receiver_email) pair, with both emails normalized.
Pair = tuple[str, str]

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
    participants: list[Participant],
    rng: random.Random | None = None,
    exclusions: Iterable[tuple[str, str]] | None = None,
) -> dict[Participant, Participant]:
    """Give every participant one random receiver, following the exclusions.

    The search can be slow for large groups with many exclusions, because
    in the worst case it tries many circles. It is fast for groups of tens
    of people. It uses recursion, so groups must be smaller than Python's
    recursion limit (about 1000 by default).

    Args:
        participants: The people taking part. The list is not changed.
        rng: The random generator to use. Pass a seeded random.Random in
            tests to get the same result every time. If None, a new
            unseeded generator is used.
        exclusions: (giver_email, receiver_email) pairs. The giver must not
            give to the receiver. A pair blocks one direction only. Emails
            are matched ignoring case and outer spaces. None means no
            exclusions.

    Returns:
        A dict that maps each giver to their receiver. Every participant is
        a key once and a value once, no key maps to itself, and no
        (giver, receiver) is an excluded pair. All links form one circle.

    Raises:
        EmptyFieldError: If any name or email is empty.
        DuplicateEmailError: If two participants share an email.
        NotEnoughParticipantsError: If there are fewer than 2 participants.
        UnknownParticipantError: If an excluded pair uses an unknown email.
        NoValidAssignmentError: If no circle can follow all exclusions.
    """
    validate(participants)
    blocked = _normalize_pairs(exclusions or [])
    _check_known_emails(participants, blocked)
    circle = _find_circle(participants, blocked, rng or random.Random())
    if circle is None:
        raise NoValidAssignmentError("No gift circle can follow all exclusions.")
    # i gives to i+1; the modulo makes the last person give to the first.
    return {circle[i]: circle[(i + 1) % len(circle)] for i in range(len(circle))}


def _email_key(email: str) -> str:
    """Return the email in the form used to compare emails."""
    return email.strip().lower()


def _normalize_pairs(pairs: Iterable[tuple[str, str]]) -> set[Pair]:
    """Return the pairs with both emails turned into compare keys."""
    return {(_email_key(giver), _email_key(receiver)) for giver, receiver in pairs}


def _check_known_emails(participants: list[Participant], blocked: set[Pair]) -> None:
    """Raise UnknownParticipantError if a pair uses an email nobody has."""
    known = {_email_key(person.email) for person in participants}
    for giver, receiver in blocked:
        for email in (giver, receiver):
            if email not in known:
                raise UnknownParticipantError(f"Unknown email in exclusions: {email}.")


def _can_give(giver: Participant, receiver: Participant, blocked: set[Pair]) -> bool:
    """Return True if giver may give a gift to receiver."""
    if giver == receiver:
        return False
    return (_email_key(giver.email), _email_key(receiver.email)) not in blocked


def _find_circle(
    participants: list[Participant], blocked: set[Pair], rng: random.Random
) -> list[Participant] | None:
    """Return the people in circle order, or None if no valid circle exists."""
    # In a circle every person is on it, so the start person does not
    # change which circles are possible. The random order comes from
    # shuffling the choices at each step.
    path = [participants[0]]
    remaining = list(participants[1:])  # A copy, so the caller's list is safe.
    return path if _extend_circle(path, remaining, blocked, rng) else None


def _extend_circle(
    path: list[Participant],
    remaining: list[Participant],
    blocked: set[Pair],
    rng: random.Random,
) -> bool:
    """Try to add all remaining people to path; return True on success.

    Changes path and remaining in place. On success, path holds everyone
    in circle order. On failure, both lists hold the same people as before.
    """
    if not remaining:
        # The circle must also close: the last person gives to the first.
        return _can_give(path[-1], path[0], blocked)
    choices = [person for person in remaining if _can_give(path[-1], person, blocked)]
    rng.shuffle(choices)
    for person in choices:
        path.append(person)
        remaining.remove(person)
        if _extend_circle(path, remaining, blocked, rng):
            return True
        # Dead end: undo this choice and try the next one.
        path.pop()
        remaining.append(person)
    return False


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
        key = _email_key(person.email)
        if key in seen:
            raise DuplicateEmailError(f"Duplicate email: {person.email}.")
        seen.add(key)
