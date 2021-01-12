import unittest
import random
import time
import itertools
from skiplist import SkipList
from math import log2
from collections import Counter
from functools import lru_cache

def pairwise(node):
    if type(node.key) != int and hasattr(node, 'next'):
        # node is a head node
        node = node.next
    while hasattr(node, 'next') and type(node.next.key) == int:
        yield node, node.next
        node = node.next

@lru_cache(maxsize=2)
def get_height(node):
    height = 0
    while hasattr(node, 'below'):
        node = node.below
        height += 1
    return height


class SkipListTest(unittest.TestCase):

    def get_list(self, *args, **kwargs):
        return SkipList(*args, **kwargs)

    def check_structure(self, node):
        for n1, n2 in pairwise(node):
            self.assertTrue(n1.key < n2.key)
            self.assertEqual(type(n1), type(n2))
            self.assertEqual(get_height(n1), get_height(n2))

    def check_content(self, skiplist, iterable, test_key=None):

        content = tuple(sorted(iterable))
        keys = tuple(i[0] for i in content)
        values = tuple(i[1] for i in content)

        # __len__
        self.assertEqual(len(skiplist), len(content))
        # __iter__
        self.assertEqual(tuple(skiplist), keys)
        # __reversed__
        self.assertEqual(tuple(reversed(skiplist)), tuple(reversed(keys)))
        # keys
        self.assertEqual(tuple(skiplist.keys()), keys)
        # values
        self.assertEqual(tuple(skiplist.values()), values)
        # items
        self.assertEqual(tuple(skiplist.items()), content)
        # __eq__
        self.assertEqual(skiplist, skiplist)
        for k, v in content:
            # get
            self.assertEqual(skiplist.get(k), v)
            # __getitem__
            self.assertEqual(skiplist[k], v)
            # contains
            self.assertTrue(k in skiplist)

        if content:
            # first
            self.assertEqual(skiplist.first(), content[0])
            # last
            self.assertEqual(skiplist.last(), content[-1])

            if test_key != None:
                before = tuple(i for i in content if i[0] < test_key)
                self.assertEqual(tuple(skiplist.before(test_key)), before)
                after = tuple(i for i in content if i[0] >= test_key)
                self.assertEqual(tuple(skiplist.after(test_key)), after)

        for i in skiplist._SkipList__heads:
            self.check_structure(i.next)


    def test_checkers(self):
        items = (
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
        )
        l = self.get_list(items, random_height=lambda x: 5)
        for i, (n1, n2) in enumerate(pairwise(l._SkipList__heads[-1])):
            self.assertEqual(get_height(n1), 5)
            self.assertEqual(get_height(n2), 5)
        for i, (n1, n2) in enumerate(pairwise(l._SkipList__heads[0])):
            self.assertNotEqual(n1, n2)
            self.assertEqual((n1.key, n1.value), items[i])
            self.assertEqual((n2.key, n2.value), items[i + 1])
            self.assertEqual(get_height(n1), 0)
            self.assertTrue(i < len(items))


    def test_empty(self):
        l = self.get_list()
        self.check_content(l, [])

    def test_creation(self):
        items = (
            (3, 3),
            (2, 2),
            (1, 1),
            (4, 4),
        )
        l1 = self.get_list(items)
        self.check_content(l1, items)

        l2 = self.get_list(l1.items())
        self.check_content(l2, items)

        self.assertEqual(l1, l2)

    def test_insertion(self):
        a = (
            (2, 2),
            (3, 3),
            (1, 1),
            (4, 4),
        )
        b = (
            (2, -2),
            (3, -3),
            (1, -1),
            (4, -4),
        )

        l = self.get_list(a)
        self.check_content(l, a)

        for k, v in b:
            l.insert(k, v)
        self.check_content(l, b)

        for k, v in a:
            l[k] = v
        self.check_content(l, a)

    def test_removal(self):
        a = (
            (4, 4),
            (2, 2),
        )
        b = (
            (1, 1),
            (3, 3),
        )
        l = self.get_list(a + b)
        for k, v in b:
            l.remove(k)
        self.check_content(l, a)
        for k, v in a:
            l.remove(k)
        self.check_content(l, ())

    def test_range(self):
        items = [(i, i) for i in (
            -2, 1, 5, 7, 3, -3, 2, -4, -1, 9, 0, -5, 8, 6, 4
        )]
        l = self.get_list(items)

        self.check_content(l, items, test_key=2)
        self.assertEqual(len(tuple(l.range(0, 6))), 6)
        self.assertEqual(len(tuple(l.range(6, 0))), 0)

    def test_estimation(self):
        items = [(i, i) for i in (
            -2, 1, 7, 14, 55, 972
        )]
        l = self.get_list(items)

        self.check_content(l, items, test_key=9)
        self.assertEqual(l.ceiling(9), (14, 14))
        self.assertEqual(l.floor(9), (7, 7))
        self.assertEqual(l.ceiling(9, False), (14, 14))
        self.assertEqual(l.floor(9, False), (7, 7))
        self.assertEqual(l.ceiling(14), (14, 14))
        self.assertEqual(l.floor(14), (14, 14))
        self.assertEqual(l.ceiling(14, False), (55, 55))
        self.assertEqual(l.floor(14, False), (7, 7))
        self.assertEqual(l.ceiling(7), (7, 7))
        self.assertEqual(l.floor(7), (7, 7))
        self.assertEqual(l.ceiling(7, False), (14, 14))
        self.assertEqual(l.floor(7, False), (1, 1))

    def test_height(self):
        size = 4000
        items = list((i, i) for i in range(size))
        random.Random('shuffle').shuffle(items)

        r = random.Random('list')
        def _random_height(limit):
            """returns a non-negative integer"""
            return min(int(-log2(1 - r.random())), limit)

        expected_dist = list(_random_height(16) for i in range(size))
        r = random.Random('list')

        dist = {}
        def count_nodes(node):
            while hasattr(node, 'next'):
                if type(node.key) == int:
                    height = 0
                    current = node
                    while hasattr(current, 'below'):
                        current = current.below
                        height += 1
                    dist[current.key] = height
                node = node.next
        l = SkipList(items, random_height=_random_height)
        heads = l._SkipList__heads
        lengths = []
        for i in heads:
            lengths.append(count_nodes(i))

        self.assertEqual(len(expected_dist), len(dist.values()))
        self.assertEqual(Counter(expected_dist), Counter(dist.values()))


if __name__ == '__main__':
    unittest.main()
