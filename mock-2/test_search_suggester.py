"""Tests for SearchSuggester."""

import pytest

from search_suggester import SearchSuggester

SEARCHES = [("red shoes", 50), ("red dress", 30), ("blue jeans", 20)]


def test_suggest_returns_queries_with_matching_prefix() -> None:
    suggester = SearchSuggester(SEARCHES)
    # Order is not defined yet, so compare as sets.
    assert set(suggester.suggest("red")) == {"red shoes", "red dress"}
    assert suggester.suggest("b") == ["blue jeans"]


def test_suggest_returns_empty_list_for_empty_prefix() -> None:
    suggester = SearchSuggester(SEARCHES)
    assert suggester.suggest("") == []


def test_suggest_returns_empty_list_when_no_match() -> None:
    suggester = SearchSuggester(SEARCHES)
    assert suggester.suggest("green") == []
    # A prefix longer than any query must not match.
    assert suggester.suggest("red shoes and socks") == []


def test_suggest_full_query_as_prefix_matches_itself() -> None:
    suggester = SearchSuggester(SEARCHES)
    assert suggester.suggest("red shoes") == ["red shoes"]


def test_suggest_is_case_insensitive() -> None:
    suggester = SearchSuggester([("Red Shoes", 5), ("blue jeans", 2)])
    assert suggester.suggest("RED") == ["red shoes"]
    assert suggester.suggest("Blue") == ["blue jeans"]


def test_duplicate_queries_merge_counts_across_case() -> None:
    suggester = SearchSuggester([("red shoes", 10), ("Red Shoes", 5), ("red shoes", 1)])
    assert suggester.suggest("red") == ["red shoes"]
    assert suggester._counts == {"red shoes": 16}


def test_init_raises_on_empty_query() -> None:
    with pytest.raises(ValueError, match="empty"):
        SearchSuggester([("red shoes", 1), ("", 3)])


def test_init_raises_on_negative_count() -> None:
    with pytest.raises(ValueError, match="negative"):
        SearchSuggester([("red shoes", -1)])
