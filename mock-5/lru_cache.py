"""A fixed-size key-value cache that removes the least recently used item.

Both get() and add() count as a "use" of a key. When the cache is full and
a new key is added, the key that was used least recently is removed first.
"""

from collections import OrderedDict
from typing import Generic, Hashable, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """A key-value cache with a fixed capacity and LRU eviction.

    The items are kept in an OrderedDict in usage order: the first item is
    the least recently used, and the last item is the most recently used.
    get() and add() both run in O(1) time.
    """

    def __init__(self, capacity: int) -> None:
        """Create an empty cache.

        Args:
            capacity: The maximum number of items the cache can hold.

        Raises:
            ValueError: If capacity is less than 1.
        """
        if capacity < 1:
            raise ValueError(f"capacity must be at least 1, got {capacity}")
        self._capacity = capacity
        self._items: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K) -> V:
        """Return the value for a key and mark the key as most recently used.

        Args:
            key: The key to look up.

        Returns:
            The value stored for the key.

        Raises:
            KeyError: If the key is not in the cache.
        """
        # Raise instead of returning None, because None can be a real value.
        value = self._items[key]
        self._items.move_to_end(key)
        return value

    def add(self, key: K, value: V) -> None:
        """Add or update a key and mark it as most recently used.

        If the key is new and the cache is full, the least recently used
        key is removed first.

        Args:
            key: The key to add or update.
            value: The value to store for the key.
        """
        if key in self._items:
            # An update never changes the size, so nothing is evicted.
            self._items.move_to_end(key)
        elif len(self._items) >= self._capacity:
            self._items.popitem(last=False)
        self._items[key] = value

    def __len__(self) -> int:
        """Return the number of items in the cache.

        Returns:
            The current number of items.
        """
        return len(self._items)
