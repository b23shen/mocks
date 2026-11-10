"""Tests for the LRUCache class in lru_cache.py."""

import pytest

from lru_cache import LRUCache


def test_get_returns_added_value() -> None:
    """get() returns the value that add() stored for the key."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.add("a", 1)
    assert cache.get("a") == 1
    assert len(cache) == 1


def test_get_missing_key_raises_key_error() -> None:
    """get() raises KeyError for a key that was never added."""
    cache: LRUCache[str, int] = LRUCache(2)
    with pytest.raises(KeyError):
        cache.get("missing")


def test_add_existing_key_updates_value() -> None:
    """add() with an existing key replaces the value, not the size."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.add("a", 1)
    cache.add("a", 100)
    assert cache.get("a") == 100
    assert len(cache) == 1


def test_add_existing_key_when_full_does_not_evict() -> None:
    """Updating a key in a full cache keeps every key."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.add("a", 1)
    cache.add("b", 2)
    cache.add("a", 10)
    assert len(cache) == 2
    assert cache.get("a") == 10
    assert cache.get("b") == 2


def test_add_new_key_when_full_evicts_least_recently_used() -> None:
    """A new key in a full cache removes the oldest used key."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.add("a", 1)
    cache.add("b", 2)
    cache.add("c", 3)
    assert len(cache) == 2
    with pytest.raises(KeyError):
        cache.get("a")
    assert cache.get("b") == 2
    assert cache.get("c") == 3

    # Edge case: with capacity 1, every new key replaces the old one.
    tiny: LRUCache[str, int] = LRUCache(1)
    tiny.add("x", 1)
    tiny.add("y", 2)
    assert len(tiny) == 1
    with pytest.raises(KeyError):
        tiny.get("x")
    assert tiny.get("y") == 2


def test_get_marks_key_as_recently_used() -> None:
    """After get("a"), "b" becomes the least recently used and is evicted."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.add("a", 1)
    cache.add("b", 2)
    cache.get("a")
    cache.add("c", 3)
    with pytest.raises(KeyError):
        cache.get("b")
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_add_update_marks_key_as_recently_used() -> None:
    """After updating "a", "b" becomes the least recently used and is evicted."""
    cache: LRUCache[str, int] = LRUCache(2)
    cache.add("a", 1)
    cache.add("b", 2)
    cache.add("a", 10)
    cache.add("c", 3)
    with pytest.raises(KeyError):
        cache.get("b")
    assert cache.get("a") == 10
    assert cache.get("c") == 3


@pytest.mark.parametrize("capacity", [0, -1])
def test_capacity_below_one_raises_value_error(capacity: int) -> None:
    """A cache must hold at least one item."""
    with pytest.raises(ValueError):
        LRUCache(capacity)
