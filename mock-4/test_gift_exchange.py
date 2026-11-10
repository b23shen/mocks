"""Tests for the gift exchange module in gift_exchange.py."""

import random
from pathlib import Path

import pytest

from errors import (
    DuplicateEmailError,
    EmptyFieldError,
    GiftExchangeError,
    InvalidCsvError,
    NotEnoughParticipantsError,
    NoValidAssignmentError,
    UnknownParticipantError,
)
from gift_exchange import Participant, assign, load_participants, validate


def make_people(count: int) -> list[Participant]:
    """Return `count` participants with unique names and emails."""
    return [Participant(f"p{i}", f"p{i}@example.com") for i in range(count)]


# Several sizes, so small and larger groups are both covered.
SIZES = [2, 3, 10, 50]


@pytest.mark.parametrize("size", SIZES)
def test_assign_every_person_gives_and_receives_once(size: int) -> None:
    people = make_people(size)
    result = assign(people, random.Random(0))
    assert set(result.keys()) == set(people)
    # Same set and same length means no receiver appears twice.
    assert set(result.values()) == set(people)
    assert len(result) == size


@pytest.mark.parametrize("seed", range(20))
def test_assign_nobody_gives_to_self(seed: int) -> None:
    result = assign(make_people(5), random.Random(seed))
    assert all(giver != receiver for giver, receiver in result.items())


@pytest.mark.parametrize("size", SIZES)
def test_assign_forms_one_single_cycle(size: int) -> None:
    people = make_people(size)
    result = assign(people, random.Random(1))
    # Follow the chain from one person; it must visit everyone and return.
    start = people[0]
    current = result[start]
    steps = 1
    while current != start:
        current = result[current]
        steps += 1
    assert steps == size


def test_assign_same_seed_gives_same_result() -> None:
    people = make_people(10)
    first = assign(people, random.Random(42))
    second = assign(people, random.Random(42))
    assert first == second
    # The caller's list must not be shuffled in place.
    assert people == make_people(10)


def test_assign_two_people_swap_gifts() -> None:
    a, b = make_people(2)
    result = assign([a, b], random.Random(7))
    assert result == {a: b, b: a}


@pytest.mark.parametrize("size", [0, 1])
def test_validate_raises_for_fewer_than_two(size: int) -> None:
    with pytest.raises(NotEnoughParticipantsError):
        validate(make_people(size))
    with pytest.raises(GiftExchangeError):
        assign(make_people(size))


@pytest.mark.parametrize(
    "people, error",
    [
        (
            [Participant("A", "same@x.com"), Participant("B", "SAME@x.com")],
            DuplicateEmailError,
        ),
        ([Participant("A", "a@x.com"), Participant("B", "  ")], EmptyFieldError),
        ([Participant("", "a@x.com"), Participant("B", "b@x.com")], EmptyFieldError),
    ],
)
def test_validate_raises_for_duplicate_or_empty_email(
    people: list[Participant], error: type[Exception]
) -> None:
    with pytest.raises(error):
        validate(people)


def test_load_participants_reads_csv_and_rejects_bad_header(tmp_path: Path) -> None:
    good = tmp_path / "good.csv"
    good.write_text(" Name , Email \n Ann , ann@x.com \nBob,bob@x.com\n")
    assert load_participants(str(good)) == [
        Participant("Ann", "ann@x.com"),
        Participant("Bob", "bob@x.com"),
    ]

    bad = tmp_path / "bad.csv"
    bad.write_text("name,phone\nAnn,123\n")
    with pytest.raises(InvalidCsvError):
        load_participants(str(bad))

    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.raises(InvalidCsvError):
        load_participants(str(empty))


# ---------- Exclusions ----------


def by_name(result: dict[Participant, Participant]) -> dict[str, str]:
    """Return the assignment as {giver_name: receiver_name}, easy to compare."""
    return {giver.name: receiver.name for giver, receiver in result.items()}


@pytest.mark.parametrize("seed", range(20))
def test_assign_never_uses_excluded_pair(seed: int) -> None:
    people = make_people(6)
    exclusions = [
        ("p0@example.com", "p1@example.com"),
        ("p1@example.com", "p2@example.com"),
        ("p2@example.com", "p0@example.com"),
        ("p3@example.com", "p4@example.com"),
    ]
    result = assign(people, random.Random(seed), exclusions)
    used = {(giver.email, receiver.email) for giver, receiver in result.items()}
    assert used.isdisjoint(exclusions)
    assert set(result.values()) == set(people)


def test_exclusion_blocks_one_direction_only() -> None:
    # With 3 people there are 2 circles: a->b->c->a and a->c->b->a.
    # Blocking a->b leaves only the second one, where b DOES give to a.
    people = make_people(3)
    result = assign(people, random.Random(0), [("p0@example.com", "p1@example.com")])
    assert by_name(result) == {"p0": "p2", "p2": "p1", "p1": "p0"}


def test_exclusion_emails_ignore_case_and_spaces() -> None:
    people = make_people(3)
    result = assign(people, random.Random(0), [(" P0@Example.COM ", "p1@EXAMPLE.com")])
    assert by_name(result)["p0"] == "p2"


@pytest.mark.parametrize("seed", range(10))
def test_assign_finds_the_only_valid_circle(seed: int) -> None:
    # Block every link except p0->p1->p2->p3->p4->p0, so only one circle is left.
    people = make_people(5)
    allowed = {(i, (i + 1) % 5) for i in range(5)}
    exclusions = [
        (f"p{g}@example.com", f"p{r}@example.com")
        for g in range(5)
        for r in range(5)
        if g != r and (g, r) not in allowed
    ]
    result = assign(people, random.Random(seed), exclusions)
    assert by_name(result) == {"p0": "p1", "p1": "p2", "p2": "p3", "p3": "p4", "p4": "p0"}


@pytest.mark.parametrize(
    "size, exclusions",
    [
        # 2 people must give to each other, so one block makes it impossible.
        (2, [("p0@example.com", "p1@example.com")]),
        # p0 is blocked from giving to everyone else.
        (3, [("p0@example.com", "p1@example.com"), ("p0@example.com", "p2@example.com")]),
        # Nobody may give to p2.
        (3, [("p0@example.com", "p2@example.com"), ("p1@example.com", "p2@example.com")]),
    ],
)
def test_assign_raises_when_no_valid_circle(
    size: int, exclusions: list[tuple[str, str]]
) -> None:
    with pytest.raises(NoValidAssignmentError):
        assign(make_people(size), random.Random(0), exclusions)


@pytest.mark.parametrize(
    "pair",
    [
        ("nobody@example.com", "p1@example.com"),  # Unknown giver.
        ("p0@example.com", "nobody@example.com"),  # Unknown receiver.
    ],
)
def test_assign_raises_for_unknown_email_in_exclusions(pair: tuple[str, str]) -> None:
    with pytest.raises(UnknownParticipantError):
        assign(make_people(3), random.Random(0), [pair])


def test_assign_with_exclusions_same_seed_gives_same_result() -> None:
    people = make_people(10)
    exclusions = [("p0@example.com", "p1@example.com"), ("p5@example.com", "p6@example.com")]
    first = assign(people, random.Random(42), exclusions)
    second = assign(people, random.Random(42), exclusions)
    assert first == second


def test_assign_with_exclusions_does_not_change_input_list() -> None:
    # These exclusions force the search to undo choices, which changes its
    # own working lists; the caller's list must stay the same.
    people = make_people(5)
    exclusions = [
        ("p0@example.com", "p1@example.com"),
        ("p0@example.com", "p2@example.com"),
        ("p0@example.com", "p3@example.com"),
    ]
    assign(people, random.Random(0), exclusions)
    assert people == make_people(5)
    with pytest.raises(NoValidAssignmentError):
        assign(people, random.Random(0), exclusions + [("p0@example.com", "p4@example.com")])
    assert people == make_people(5)
