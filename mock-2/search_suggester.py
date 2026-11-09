"""Suggest past search queries that start with a typed prefix."""


class SearchSuggester:
    """Store past searches and suggest the ones that match a prefix.

    Matching is case-insensitive. All queries are stored in lowercase, and
    duplicates (including ones that differ only in case) merge their counts.
    """

    def __init__(self, searches: list[tuple[str, int]]) -> None:
        """Load past searches.

        Args:
            searches: Pairs of (query, count). count is how many times
                the query was searched.

        Raises:
            ValueError: If a query is an empty string or a count is negative.
        """
        # Keep counts now, even though suggest() does not use them yet;
        # ranking by popularity will need them.
        self._counts: dict[str, int] = {}
        for query, count in searches:
            self._add(query, count)

    def _add(self, query: str, count: int) -> None:
        """Validate one search and add its count to the stored total.

        Args:
            query: The search text.
            count: How many times the query was searched.

        Raises:
            ValueError: If query is empty or count is negative.
        """
        if not query:
            raise ValueError("query must not be empty")
        if count < 0:
            raise ValueError(f"count must not be negative, got {count}")
        key = query.lower()
        self._counts[key] = self._counts.get(key, 0) + count

    def record_search(self, query: str) -> None:
        """Record that a user searched for query once.

        A new query is added with count 1 so it can be suggested from now on.

        Args:
            query: The search text. Case is ignored.

        Raises:
            ValueError: If query is empty.
        """
        self._add(query, 1)

    def suggest(self, prefix: str) -> list[str]:
        """Return stored queries that start with prefix, ignoring case.

        Args:
            prefix: The text the user has typed so far.

        Returns:
            Matching queries in lowercase, in no particular order.
            An empty list if prefix is empty or nothing matches.
        """
        # We start suggesting from the first letter, so "" gives nothing.
        if not prefix:
            return []
        needle = prefix.lower()
        return [query for query in self._counts if query.startswith(needle)]
