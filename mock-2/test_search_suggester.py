"""Tests for SearchSuggester."""

import pytest

from search_suggester import MAX_SUGGESTIONS, SearchSuggester

SEARCHES = [("red shoes", 50), ("red dress", 30), ("blue jeans", 20)]


def test_suggest_returns_queries_with_matching_prefix() -> None:
    suggester = SearchSuggester(SEARCHES)
    # Higher count first: red shoes (50) before red dress (30).
    assert suggester.suggest("red") == ["red shoes", "red dress"]
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
    assert suggester.count("red shoes") == 16


def test_init_ignores_empty_and_whitespace_only_queries() -> None:
    suggester = SearchSuggester([("red shoes", 1), ("", 3), ("   ", 4), ("\t\n", 2)])
    assert suggester.count("red shoes") == 1
    assert suggester.count("") == 0
    assert suggester.count("   ") == 0
    # Only the real query is stored, so nothing else can be suggested.
    assert suggester.suggest("r") == ["red shoes"]


def test_init_raises_on_negative_count() -> None:
    with pytest.raises(ValueError, match="negative"):
        SearchSuggester([("red shoes", -1)])


def test_record_search_new_query_becomes_suggestable() -> None:
    suggester = SearchSuggester(SEARCHES)
    assert suggester.suggest("green") == []
    suggester.record_search("green hat")
    assert suggester.suggest("green") == ["green hat"]
    assert suggester.count("green hat") == 1


def test_record_search_existing_query_increments_count() -> None:
    suggester = SearchSuggester(SEARCHES)
    suggester.record_search("red shoes")
    suggester.record_search("red shoes")
    assert suggester.count("red shoes") == 52


def test_record_search_is_case_insensitive() -> None:
    suggester = SearchSuggester(SEARCHES)
    suggester.record_search("RED Shoes")
    assert suggester.count("red shoes") == 51
    # No separate entry is created for the uppercase spelling.
    assert set(suggester.suggest("red")) == {"red shoes", "red dress"}


def test_record_search_ignores_empty_and_whitespace_only_query() -> None:
    suggester = SearchSuggester(SEARCHES)
    # A blank search is valid: no error, and nothing is stored.
    suggester.record_search("")
    suggester.record_search("   ")
    assert suggester.count("") == 0
    assert suggester.count("   ") == 0
    assert suggester.count("red shoes") == 50


def test_queries_are_trimmed_and_merged() -> None:
    suggester = SearchSuggester([("red shoes", 10), ("  Red Shoes ", 5)])
    suggester.record_search(" red shoes  ")
    assert suggester.count("red shoes") == 16
    assert suggester.suggest("red") == ["red shoes"]


def test_suggest_ignores_leading_spaces_in_prefix() -> None:
    suggester = SearchSuggester(SEARCHES)
    assert set(suggester.suggest(" red")) == {"red shoes", "red dress"}
    assert suggester.suggest("   BLUE") == ["blue jeans"]


def test_suggest_keeps_trailing_space_in_prefix() -> None:
    suggester = SearchSuggester([("red shoes", 5), ("reddit", 3)])
    assert suggester.suggest("red ") == ["red shoes"]
    assert set(suggester.suggest("red")) == {"red shoes", "reddit"}


def test_suggest_returns_empty_list_for_whitespace_only_prefix() -> None:
    suggester = SearchSuggester(SEARCHES)
    assert suggester.suggest(" ") == []
    assert suggester.suggest("   ") == []


def test_return_3_items() -> None:
    suggester = SearchSuggester(
        [("red shoes", 10), ("Red Pants", 5), ("red hat", 1), ("red dress", 1)]
    )
    assert suggester.suggest("red") == ["red shoes", "red pants", "red dress"]


def test_count_returns_zero_for_unknown_query() -> None:
    suggester = SearchSuggester(SEARCHES)
    assert suggester.count("green hat") == 0
    # Longer than any stored query: the trie path runs out.
    assert suggester.count("red shoes and socks") == 0


def test_count_returns_zero_for_prefix_of_stored_query() -> None:
    suggester = SearchSuggester(SEARCHES)
    # The "red" node exists, but no query ends there.
    assert suggester.count("red") == 0


def test_count_ignores_case_and_outer_spaces() -> None:
    suggester = SearchSuggester([("red shoes", 50), ("Red Shoes", 5)])
    assert suggester.count("  RED SHOES ") == 55


def test_suggest_includes_query_that_equals_prefix() -> None:
    # "red" is both a stored query and the parent of "red shoes".
    suggester = SearchSuggester([("red", 2), ("red shoes", 5)])
    assert suggester.suggest("red") == ["red shoes", "red"]


def test_suggest_breaks_ties_alphabetically() -> None:
    suggester = SearchSuggester([("red shoes", 5), ("red dress", 5), ("red hat", 5)])
    assert suggester.suggest("red") == ["red dress", "red hat", "red shoes"]


def test_suggest_returns_at_most_max_suggestions() -> None:
    searches = [(f"red item {i}", i + 1) for i in range(MAX_SUGGESTIONS + 2)]
    suggester = SearchSuggester(searches)
    result = suggester.suggest("red")
    assert len(result) == MAX_SUGGESTIONS
    # The highest counts win.
    expected = [f"red item {i}" for i in range(MAX_SUGGESTIONS + 1, 1, -1)]
    assert result == expected
