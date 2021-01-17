"""A SkipList Python implementation

It implements an interface similar to Java ConcurrentSkipListMap
https://docs.oracle.com/javase/7/docs/api/java/util/concurrent/ConcurrentSkipListMap.html

A SkipList stores key-value mapping ordered by their keys.
It offers efficient item lookup and support finding closest key or items with keys in a range
"""

import operator as _operator
from collections.abc import MutableMapping as _MutableMapping
from random import random as _random
from math import log2 as _log2
from itertools import tee as _tee, islice as _islice

_null_key = object()


class BaseLinkedListNode:

    __slots__ = ('next', 'key')

    def __init__(self, key):
        self.key = key

    def link(self, other):
        self.next = other


class LinkedListNode(BaseLinkedListNode):

    __slots__ = ('prev', 'value')

    def __init__(self, key, value):
        super().__init__(key)
        self.value = value

    def link(self, other):
        super().link(other)
        other.prev = self


class SkipListNode(BaseLinkedListNode):

    __slots__ = ('below', )

    def __init__(self, key, below):
        super().__init__(key)
        self.below = below


def _link(*args):
    i1, i2 = _tee(args)
    next(i2, None)
    for a, b in zip(i1, i2):
        a.link(b)
    return args

def _random_height(limit):
    """returns a non-negative integer"""
    return min(int(-_log2(1 - _random())), limit)


class SkipList(_MutableMapping):
    """An ordered mapping type

    accepts a key-value mapping as initial content if provided,
    comparator should implement the operator module if provided, or the key of the items should be comparable,
    random_height function should return a non-negative integer when called.
    """

    def __init__(self, iterable=tuple(), comparator=None, random_height=None):
        """
        random_height should generate the hight of skiplist nodes (start from 0)
        """
        # store options
        self.__comparator = _operator if comparator == None else comparator
        self.__random_height = _random_height if random_height == None else random_height
        # initialise structure
        self.__heads = [LinkedListNode(_null_key, None)]
        self.__tails = [LinkedListNode(_null_key, None)]
        _link(self.__heads[0], self.__tails[0])
        self.__size = 0

        for k, v in iterable:
            self.insert(k, v)

    def __trace(self, key):
        node = self.__heads[-1]
        path = []
        while True:
            while node.next.key is not _null_key and self.__comparator.le(node.next.key, key):
                node = node.next
            path.append(node)
            if hasattr(node, 'below'):
                node = node.below
            else:
                break
        return path

    def __ceiling(self, key, inclusive):
        """Return a key-value tuple of the least key greater than (or equal to, if inclusive is True) the given key."""
        node = self.__trace(key)[-1]
        if self.__comparator.eq(node.key, key) and inclusive:
            return node
        return node.next

    def __floor(self, key, inclusive):
        """Return a key-value tuple of the greatest key less than (or equal to, if inclusive is True) the given key."""
        node = self.__trace(key)[-1]
        if self.__comparator.eq(node.key, key) and not inclusive:
            return node.prev
        return node

    def __range(self, current, end):
        while current.key is not _null_key and current != end:
            yield current.key, current.value
            current = current.next


    def insert(self, key, value=None, replacing=True):
        """Insert the key and value mapping.
        If a mapping with the specified key exists, having replacing=True will update its value, or otherwise leave it unchanged."""
        *intermediates, node = self.__trace(key)
        if node.key is not _null_key and self.__comparator.eq(node.key, key):
            if replacing:
                node.value = value
        else: # create new node
            # generate new layers if needed
            height = self.__random_height(16)
            for i in range(len(self.__heads) - 1, height):
                new_head = SkipListNode(_null_key, self.__heads[-1])
                new_tail = SkipListNode(_null_key, self.__tails[-1])
                _link(new_head, new_tail)
                self.__heads.append(new_head)
                self.__tails.append(new_tail)
                intermediates.insert(0, new_head)
            # insert the linkedlist node
            new_node = LinkedListNode(key, value)
            _link(node, new_node, node.next)
            # insert skiplist nodes
            for n in intermediates[:-height - 1:-1]:
                new_node = SkipListNode(key, new_node)
                _link(n, new_node, n.next)
            self.__size += 1

    def update(self, iterable, replacing=True):
        """Update mappings from the iterable. This is equivlent to insert every item from the iterable to this list."""
        for k, v in iterable:
            self.insert(k, v, replacing)

    def remove(self, key):
        """Removes the mapping with the specified key."""
        self.pop(key)

    def clear(self):
        """Remove all of the mappings from this list."""
        self.__heads = [LinkedListNode(_null_key, None)]
        self.__tails = [LinkedListNode(_null_key, None)]
        _link(self.__heads[0], self.__tails[0])
        self.__size = 0

    def get(self, key):
        """Returns the value to which the specified key is mapped."""
        node = self.__trace(key)[-1]
        if self.__comparator.eq(node.key, key):
            return node.value
        else:
            raise KeyError(key)

    def first(self):
        """Return a key-value tuple of the mapping with the least key."""
        if self.__size == 0:
            raise LookupError('List is empty.')
        else:
            return self.__heads[0].next.key, self.__heads[0].next.value

    def last(self):
        """Return a key-value tuple of the mapping with the greatest key."""
        if self.__size == 0:
            raise LookupError('List is empty.')
        else:
            return self.__tails[0].prev.key, self.__tails[0].prev.value

    def shift(self):
        """Return a key-value tuple of the mapping with the least key and remove the mapping."""
        key, value = self.first()
        self.remove(key)
        return key, value

    def pop(self, key=_null_key):
        """Return a key-value tuple of the mapping with the greatest key (or the specified key if presents) and remove the mapping."""
        if key is _null_key:
            key = self.last()[0]
            return self.pop(key)
        else:
            nodes = self.__trace(key)
            if self.__comparator.ne(nodes[-1].key, key):
                raise KeyError(key)
            if nodes[-1].prev.key is _null_key:
                previous = self.__heads
            else:
                previous = reversed(self.__trace(nodes[-1].prev.key))
            for p, n in zip(previous, reversed(nodes)):
                if p.next is n:
                    _link(p, n.next)
                else:
                    break
            self.__size -= 1
            return nodes[-1].key, nodes[-1].value

    def ceiling(self, key, inclusive=True):
        """Return a key-value tuple of the least key greater than (or equal to, if inclusive is True) the given key."""
        node = self.__ceiling(key, inclusive)
        if node.key is _null_key:
            raise LookupError('Cannot find a key greater then %s.' % key)
        else:
            return node.key, node.value

    def floor(self, key, inclusive=True):
        """Return a key-value tuple of the greatest key less than (or equal to, if inclusive is True) the given key."""
        node = self.__floor(key, inclusive)
        if node.key is _null_key:
            raise LookupError('Cannot find a key less then %s.' % key)
        else:
            return node.key, node.value

    def range(self, start_key, end_key, include_start=True, include_end=False):
        """Returns an iterator of mappings whose keys are between from start_key and end_key."""
        start = self.__floor(start_key, include_start)
        end = self.__floor(end_key, include_end).next
        if self.__comparator.gt(start.key, end.key):
            end = start

        return self.__range(start, end)

    def after(self, start_key, inclusive=True):
        """Returns an iterator of the mappings whose keys are greater than (or equal to, if inclusive is True) start_key."""
        start = self.__ceiling(start_key, inclusive)
        return self.__range(start, self.__tails[0])

    def before(self, end_key, inclusive=False):
        """Returns an iterator of the mappings whose keys are less than (or equal to, if inclusive is True) end_key."""
        end = self.__floor(end_key, inclusive).next
        return self.__range(self.__heads[0].next, end)

    def keys(self):
        """Return an iterator object that iterates the list in order, yielding keys."""
        for i in self.items():
            yield i[0]

    def values(self):
        """Return an iterator object that iterates the list in order, yielding values."""
        for i in self.items():
            yield i[1]

    def items(self):
        """Return an iterator object that iterates the list in order, yielding key-value tuples."""
        return self.__range(self.__heads[0].next, self.__tails[0])

    def copy(self):
        """Return a shallow copy of this object."""
        return SkipList(self)

    def __contains__(self, key):
        """Return True if this list contains the specified key."""
        return self.__comparator.eq(self.__trace(key)[-1].key, key)

    def __len__(self):
        """Return the number of entries in this list."""
        return self.__size

    def __setitem__(self, key, value):
        """Is an alias of insert"""
        return self.insert(key, value, True)

    def __getitem__(self, key):
        """Is an alias of get"""
        if isinstance(key, slice):
            if key.start == None and key.end == None:
                return self.items()
            elif key.start != None:
                return self.after(key.start)
            elif key.stop != None:
                return self.before(key.stop)
            else:
                return self.range(key.start, key.stop)

        else:
            return self.get(key)

    def __delitem__(self, key):
        """Is an alias of remove"""
        return self.remove(key)

    def __reversed__(self):
        """iterate over keys in reversed order."""
        current, end = self.__tails[0].prev, self.__heads[0]
        while current.key is not _null_key and current != end:
            yield current.key
            current = current.prev

    def __iter__(self):
        """Is an alias of items"""
        return self.keys()

    def __eq__(self, other):
        """Return True if the other container has the same mappings and in the same order."""
        if self.__size == other.__size:
            for a, b in zip(self, other):
                if a != b:
                    return False
            return True
        return False

    def __repr__(self):
        """Return the string prepresentation of the list"""
        if (self.__size > 40):
            content = ', '.join('%s: %s' % i for i in _islice(self.items(), 20))
            return f'SkipList({{{content}, ...and {self.__size} more}})'
        return 'SkipList({%s})' % ', '.join('%s: %s' % i for i in self.items())
