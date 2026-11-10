"""Suggest past search queries that start with a typed prefix."""

from __future__ import annotations

# How many suggestions the search box shows at most.
MAX_SUGGESTIONS = 3


class _TrieNode:
    """One node in the prefix tree: one character of one or more queries."""

    def __init__(self) -> None:
        """Create an empty node with no children and count 0."""
        self.children: dict[str, _TrieNode] = {}
        # 0 means no stored query ends here. Blank queries are never stored
        # and counts never go negative, so 0 is a safe "not a query" marker.
        self.count: int = 0


class SearchSuggester:
    """Store past searches in a trie and suggest the ones that match a prefix.

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
        self._root = _TrieNode()
        for query, count in searches:
            self._add(query, count)

    @staticmethod
    def _normalize(query: str) -> str:
        """Return query trimmed at both ends and in lowercase.

        Args:
            query: The raw search text.

        Returns:
            The key used to store and look up the query.
        """
        return query.strip().lower()

    def _find_node(self, text: str) -> _TrieNode | None:
        """Return the node reached by following text from the root.

        Args:
            text: Already-normalized characters to follow.

        Returns:
            The node for the last character, or None if the path does not exist.
        """
        node = self._root
        for char in text:
            next_node = node.children.get(char)
            if next_node is None:
                return None
            node = next_node
        return node

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
        key = self._normalize(query)
        # A blank search is valid, but there is nothing useful to suggest.
        if not key:
            return
        node = self._root
        for char in key:
            node = node.children.setdefault(char, _TrieNode())
        node.count += count

    def record_search(self, query: str) -> None:
        """Record that a user searched for query once.

        A new query is added with count 1 so it can be suggested from now on.
        Empty or whitespace-only queries are accepted but not stored.

        Args:
            query: The search text. Case and outer spaces are ignored.
        """
        self._add(query, 1)

    def count(self, query: str) -> int:
        """Return how many times query has been searched.

        Args:
            query: The search text. Case and outer spaces are ignored.

        Returns:
            The stored count, or 0 if query is blank, unknown, or only a
            prefix of a stored query.
        """
        key = self._normalize(query)
        if not key:
            return 0
        node = self._find_node(key)
        return node.count if node is not None else 0

    def suggest(self, prefix: str) -> list[str]:
        """Return the most searched queries that start with prefix.

        Matching ignores case. Leading spaces in prefix are ignored;
        trailing spaces are kept.

        Args:
            prefix: The text the user has typed so far.

        Returns:
            Up to MAX_SUGGESTIONS queries in lowercase, sorted by count from
            high to low, with ties in alphabetical order. An empty list if
            prefix is empty, only spaces, or nothing matches.
        """
        # Stored queries never start with a space, so leading spaces can never
        # match. A trailing space is kept: "red " should not match "reddit".
        needle = prefix.lstrip().lower()
        # We start suggesting from the first letter, so "" gives nothing.
        if not needle:
            return []
        start = self._find_node(needle)
        if start is None:
            return []
        matched = self._collect(start, needle)
        ranked = sorted(matched, key=lambda pair: (-pair[1], pair[0]))
        return [query for query, _ in ranked[:MAX_SUGGESTIONS]]

    @staticmethod
    def _collect(start: _TrieNode, prefix: str) -> list[tuple[str, int]]:
        """Return every stored (query, count) in the subtree under start.

        Args:
            start: The node to search from.
            prefix: The text that leads from the root to start.

        Returns:
            All (query, count) pairs whose query ends at start or below it,
            in no particular order.
        """
        found: list[tuple[str, int]] = []
        # Iterative DFS, so very long queries cannot hit the recursion limit.
        stack: list[tuple[_TrieNode, str]] = [(start, prefix)]
        while stack:
            node, text = stack.pop()
            if node.count > 0:
                found.append((text, node.count))
            for char, child in node.children.items():
                stack.append((child, text + char))
        return found
