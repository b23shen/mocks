"""Suggest past search queries that start with a typed prefix."""


class SearchSuggester:
    """Store past searches and suggest the ones that match a prefix.

    Matching is case-insensitive. Queries are trimmed and stored in lowercase,
    and duplicates (including ones that differ only in case or outer spaces)
    merge their counts. Empty or whitespace-only queries are never stored.
    """

    def __init__(self, searches: list[tuple[str, int]]) -> None:
        """Load past searches.

        Empty or whitespace-only queries are skipped.

        Args:
            searches: Pairs of (query, count). count is how many times
                the query was searched.

        Raises:
            ValueError: If a count is negative.
        """
        # Keep counts now, even though suggest() does not use them yet;
        # ranking by popularity will need them.
        self._counts: dict[str, int] = {}
        for query, count in searches:
            self._add(query, count)

    def _add(self, query: str, count: int) -> None:
        """Add count to the stored total for query.

        Empty or whitespace-only queries are skipped.

        Args:
            query: The search text.
            count: How many times the query was searched.

        Raises:
            ValueError: If count is negative.
        """
        # Check count first so bad data fails even when the query is skipped.
        if count < 0:
            raise ValueError(f"count must not be negative, got {count}")
        key = query.strip().lower()
        # A blank search is valid, but there is nothing useful to suggest.
        if not key:
            return
        self._counts[key] = self._counts.get(key, 0) + count

    def record_search(self, query: str) -> None:
        """Record that a user searched for query once.

        A new query is added with count 1 so it can be suggested from now on.
        Empty or whitespace-only queries are accepted but not stored.

        Args:
            query: The search text. Case and outer spaces are ignored.
        """
        self._add(query, 1)

    def suggest(self, prefix: str) -> list[str]:
        """Return stored queries that start with prefix, ignoring case.

        Leading spaces in prefix are ignored. Trailing spaces are kept.

        Args:
            prefix: The text the user has typed so far.

        Returns:
            Matching queries in lowercase, in no particular order.
            An empty list if prefix is empty, only spaces, or nothing matches.
        """
        # Stored queries never start with a space, so leading spaces can never
        # match. A trailing space is kept: "red " should not match "reddit".
        needle = prefix.lstrip().lower()
        # We start suggesting from the first letter, so "" gives nothing.
        if not needle:
            return []
        matched = [(query, count) for query, count in self._counts.items() if query.startswith(needle)]
        return [pair[0] for pair in sorted(matched, key=lambda pair: (-pair[1], pair[0]))][:3]
