"""A SkipList Python implementation

A SkipList stores an ordered sequence of items.
It offers efficient item lookup and support finding closest value or values within a range

This implementation uses an interface similar to Java ConcurrentSkipListSet
https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentSkipListSet.html
"""

import operator as _operator
from collections.abc import Sequence as _Sequence
from random import random as _random
from math import log2 as _log2
from itertools import islice as _islice

_sentinel_value = object()

def _link2(a, b):
    a.link(b)

def _link3(a, b, c):
    a.link(b)
    b.link(c)

def _random_height():
    """returns a non-negative integer"""
    return int(-_log2(1 - _random()))


class BaseLinkedListNode:

    __slots__ = ('next', 'value')

    def __init__(self, value):
        self.value = value


class LinkedListNode(BaseLinkedListNode):

    __slots__ = ('prev', )

    def link(self, other):
        self.next = other
        other.prev = self


class SkipListNode(BaseLinkedListNode):

    __slots__ = ('below', )

    def __init__(self, value, below):
        super().__init__(value)
        self.below = below

    def link(self, other):
        self.next = other


class SkipList(_Sequence):
    """An ordered sequence data structure that provides efficient search."""

    def __init__(self, iterable=tuple(), comparator=None, random_height=None):
        """accepts an iterable to populate initial content if provided,
        comparator should implement the operator module if provided, or the items should be comparable,
        random_height function should return a non-negative integer when called.
        """
        self.__comparator = _operator if comparator == None else comparator
        self.__random_height = _random_height if random_height == None else random_height
        self.__sentinels = [LinkedListNode(_sentinel_value)]
        _link2(self.__sentinels[0], self.__sentinels[0])
        self.add = self.insert
        self.__size = 0
        self.extends(iterable)

    def __trace(self, value):
        le = self.__comparator.le
        node = self.__sentinels[-1]
        path = []
        while True:
            next_node = node.next
            next_value = next_node.value
            while next_value is not _sentinel_value and le(next_value, value):
                node = next_node
                next_node = node.next
                next_value = next_node.value
            path.append(node)
            if hasattr(node, 'below'):
                node = node.below
            else:
                break
        return path

    def __ceiling(self, key, inclusive):
        node = self.__trace(key)[-1]
        if self.__comparator.eq(node.value, key) and inclusive:
            return node
        return node.next

    def __floor(self, key, inclusive):
        node = self.__trace(key)[-1]
        if self.__comparator.eq(node.value, key) and not inclusive:
            return node.prev
        return node

    def __range(self, current, end):
        while current.value is not _sentinel_value and current != end:
            yield current.value
            current = current.next

    def __iloc(self, index):
        if index < 0:
            index = index + self.__size
        if index < 0 or index >= self.__size:
            raise IndexError('list index out of range')
        node = self.__sentinels[0].next
        for i in range(index):
            node = node.next
        return node

    def insert(self, value, replacing=True):
        """Adds the value into the list,
        If an equal value already exists, replacing the original value when replacing flag is True."""
        *intermediates, node = self.__trace(value)
        if node.value is not _sentinel_value and self.__comparator.eq(node.value, value):
            if replacing:
                node.value = value
        else: # create new node
            # generate new layers if needed
            height = min(self.__random_height(), 8 + int(_log2(self.__size + 1)))
            for i in range(len(self.__sentinels) - 1, height):
                new_sentinel = SkipListNode(_sentinel_value, self.__sentinels[-1])
                _link2(new_sentinel, new_sentinel)
                self.__sentinels.append(new_sentinel)
                intermediates.insert(0, new_sentinel)
            # insert the linkedlist node
            new_node = LinkedListNode(value)
            _link3(node, new_node, node.next)
            # insert skiplist nodes
            for n in intermediates[:-height - 1:-1]:
                new_node = SkipListNode(value, new_node)
                _link3(n, new_node, n.next)
            self.__size += 1

    def extends(self, iterable, replacing=True):
        """Extends the sequence from the iterable. This is equivlent to insert every item from the iterable to this list."""
        for i in iterable:
            self.insert(i, replacing)

    def remove(self, value):
        """Removes and returns the specified value from this list if it is present, otherwise raises KeyError."""
        nodes = self.__trace(value)
        if self.__comparator.ne(nodes[-1].value, value):
            raise KeyError(value)
        if nodes[-1].prev.value is _sentinel_value:
            previous = self.__sentinels
        else:
            previous = reversed(self.__trace(nodes[-1].prev.value))
        for p, n in zip(previous, reversed(nodes)):
            if p.next is n:
                _link2(p, n.next)
            else:
                break
        self.__size -= 1
        return nodes[-1].value

    def clear(self):
        """Removes all of the elements from this list."""
        self.__sentinels = [LinkedListNode(_sentinel_value)]
        _link2(self.__sentinels[0], self.__sentinels[0])
        self.__size = 0

    def first(self, default=_sentinel_value):
        """Returns the first (smallest) value in this list."""
        if self.__size == 0:
            if default != _sentinel_value:
                return default
            raise LookupError('List is empty.')
        else:
            return self.__sentinels[0].next.value

    def last(self, default=_sentinel_value):
        """Returns the last (greatest) value currently in this list."""
        if self.__size == 0:
            if default != _sentinel_value:
                return default
            raise LookupError('List is empty.')
        else:
            return self.__sentinels[0].prev.value

    def shift(self):
        """Retrieves and removes the first (smallest) value,
        raises IndexError if this set is empty."""
        if self.__size == 0:
            raise IndexError('shift from empty list')
        value = self.first()
        self.remove(value)
        return value

    def pop(self, value=_sentinel_value):
        """Retrieves and removes the last (greatest) value,
        raises IndexError if this set is empty."""
        if self.__size == 0:
            raise IndexError('pop from empty list')
        if value is _sentinel_value:
            value = self.last()
        return self.remove(value)

    def ceiling(self, value, inclusive=True, default=_sentinel_value):
        """Returns the smallest element in this list greater than (or equal to, if inclusive is True) the given element,
        raise LookupError if there is no such element."""
        node = self.__ceiling(value, inclusive)
        if node.value is _sentinel_value:
            if default != _sentinel_value:
                return default
            raise LookupError('Cannot find a value greater then %s.' % value)
        else:
            return node.value

    def floor(self, value, inclusive=True, default=_sentinel_value):
        """Returns the greatest value in this list less than (or equal to, if inclusive is True) the given value, or null if there is no such element."""
        node = self.__floor(value, inclusive)
        if node.value is _sentinel_value:
            if default != _sentinel_value:
                return default
            raise LookupError('Cannot find a value smaller then %s.' % value)
        else:
            return node.value

    def range(self, start, end, include_start=True, include_end=False):
        """Returns an iterator of items between start and end."""
        start = self.__ceiling(start, include_start)
        end = self.__floor(end, include_end).next
        if end is not self.__sentinels[0] and self.__comparator.gt(start.value, end.value):
            end = start
        return self.__range(start, end)

    def after(self, value, inclusive=True):
        """Returns an iterator of values greater than (or equal to, if inclusive is True) given value."""
        start = self.__ceiling(value, inclusive)
        return self.__range(start, self.__sentinels[0])

    def before(self, value, inclusive=False):
        """Returns an iterator of values smaller than (or equal to, if inclusive is True) given value."""
        end = self.__floor(value, inclusive).next
        return self.__range(self.__sentinels[0].next, end)

    def copy(self):
        """Returns a shallow copy of this list."""
        return SkipList(self)

    def __contains__(self, value):
        """Returns true if this list contains the specified value."""
        found = self.__trace(value)[-1].value
        return found is not _sentinel_value and self.__comparator.eq(found, value)

    def __len__(self):
        """Returns the number of elements in this list."""
        return self.__size

    def __setitem__(self, index, value):
        """Not supported"""
        raise TypeError("'SkipList' object does not support item assignment.")

    def __getitem__(self, index):
        """Gets item(s) by index."""
        if isinstance(index, slice):
            if index.step is not None and index.step <= 0:
                raise ValueError('step for SkipList must be a positive integer or None.')
            start = index.start
            if start is not None and start < 0:
                start = max(start + self.__size, 0)
            stop = index.stop
            if stop is not None and stop < 0:
                stop = max(min(stop + self.__size, self.__size), 0)
            return SkipList(_islice(self, start, stop, index.step))
        else:
            if index < -self.__size or index >= self.__size:
                raise IndexError('list index out of range')
            return self.__iloc(index).value

    def __delitem__(self, index):
        """Removes the item at the specified index."""
        return self.remove(self.__iloc(index).value)

    def __reversed__(self):
        """Returns an iterator over the elements in this list in descending order."""
        current, end = self.__sentinels[0].prev, self.__sentinels[0]
        while current.value is not _sentinel_value and current != end:
            yield current.value
            current = current.prev

    def __iter__(self):
        """Returns an iterator over the elements in this list in ascending order."""
        return self.__range(self.__sentinels[0].next, self.__sentinels[0])

    def __eq__(self, other):
        """Returns True if the other container is a SkipList and has the same content."""
        if isinstance(other, SkipList) and self.__size == other.__size:
            for a, b in zip(self, other):
                if a != b:
                    return False
            return True
        return False

    def __repr__(self):
        """Return the string prepresentation of the list."""
        if (self.__size > 48):
            content = ', '.join(str(i) for i in _islice(self, 40))
            return f'SkipList([{content}... and {self.__size - 40} more])'
        return 'SkipList([%s])' % ', '.join(str(i) for i in self)
