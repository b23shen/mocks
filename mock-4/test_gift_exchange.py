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
