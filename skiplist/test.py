import unittest
import random
import time
import itertools
import timeit
from skiplist import SkipList
from math import log2
from collections import Counter
from functools import lru_cache

def pairwise(node):
    if type(node.value) != int and hasattr(node, 'next'):
        # node is a head node
        node = node.next
    while hasattr(node, 'next') and type(node.next.value) == int:
        yield node, node.next
        node = node.next

@lru_cache(maxsize=2)
def measure_height(node):
    height = 0
    while hasattr(node, 'below'):
        node = node.below
        height += 1
    return height


class RandInt:
    """Practically only shuffles all integers within the limit, use a prime number as increment"""
    def __init__(self, increment = 723761, limit = 2**20):
        self.state = int(limit * 0.4)
        self.increment = increment
        self.limit = limit

    def next(self):
        self.state = (self.state + self.increment) % self.limit
        return self.state


class SkipListTest(unittest.TestCase):

    def get_list(self, *args, random_height=None, **kwargs):
        if random_height == None:
            r = random.Random('SkipListTest')
            random_height = lambda: min(int(-log2(1 - r.random())), 16)
        return SkipList(*args, **kwargs, random_height=random_height)

    def check_structure(self, node):
        for n1, n2 in pairwise(node):
            self.assertTrue(n1.value < n2.value)
            self.assertEqual(type(n1), type(n2))
            self.assertEqual(measure_height(n1), measure_height(n2))

    def check_content(self, skiplist, iterable, test_value=None):
        content = tuple(sorted(iterable))
        # __len__
        self.assertEqual(len(skiplist), len(content))
        # __iter__
        self.assertEqual(tuple(skiplist), content)
        # __reversed__
        self.assertEqual(tuple(reversed(skiplist)), tuple(reversed(content)))
        # __eq__
        self.assertEqual(skiplist, skiplist)
        # contains
        for i in content:
            self.assertTrue(i in skiplist)
        # index access
        for i, v in enumerate(content):
            self.assertEqual(skiplist[i], v)

        if content:
            # first
            self.assertEqual(skiplist.first(), content[0])
            # last
            self.assertEqual(skiplist.last(), content[-1])

            if test_value != None:
                before = tuple(i for i in content if i < test_value)
                self.assertEqual(tuple(skiplist.before(test_value)), before)
                after = tuple(i for i in content if i >= test_value)
                self.assertEqual(tuple(skiplist.after(test_value)), after)

        for i in skiplist._SkipList__sentinels:
            self.check_structure(i.next)

    def test_checkers(self):
        items = (1, 2, 3, 4, 5)
        l = self.get_list(items, random_height=lambda: 5)
        for i, (n1, n2) in enumerate(pairwise(l._SkipList__sentinels[-1])):
            self.assertEqual(measure_height(n1), 5)
            self.assertEqual(measure_height(n2), 5)
        for i, (n1, n2) in enumerate(pairwise(l._SkipList__sentinels[0])):
            self.assertNotEqual(n1, n2)
            self.assertEqual(n1.value, items[i])
            self.assertEqual(n2.value, items[i + 1])
            self.assertEqual(measure_height(n1), 0)
            self.assertTrue(i < len(items))

    def test_empty(self):
        l = self.get_list()
        self.check_content(l, [])
        with self.assertRaises(Exception) as context:
            broken_function()

        self.assertRaises(KeyError, l.remove, 2)
        self.assertRaises(LookupError, l.first)
        self.assertRaises(LookupError, l.last)
        self.assertRaises(IndexError, l.shift)
        self.assertRaises(IndexError, l.pop)
        self.assertRaises(LookupError, l.ceiling, -9)
        self.assertRaises(LookupError, l.floor, 9)
        self.assertEqual(tuple(l.before(2)), ())
        self.assertEqual(tuple(l.after(2)), ())
        self.assertEqual(tuple(l.range(2, 3)), ())
        self.assertEqual(tuple(l.copy()), ())
        self.assertFalse(0 in l)
        self.assertEqual(len(l), 0)
        self.assertRaises(IndexError, l.__getitem__, 0)
        self.assertRaises(IndexError, l.__getitem__, 2)
        self.assertEqual(tuple(l[-2:9]), ())
        self.assertEqual(l, l.copy())
        self.assertEqual(str(l), 'SkipList([])')
        l.clear()

    def test_creation(self):
        items = (3, 2, 1, 4)
        l1 = self.get_list(items)
        self.check_content(l1, items)

        l2 = self.get_list(l1)
        self.check_content(l2, items)
        self.assertEqual(l1, l2)

    def test_insertion(self):
        a = (2, 3, 1, 4)
        b = (5, 8, 6, 7)

        l = self.get_list()
        self.check_content(l, ())
        l.extends(a)
        self.check_content(l, a)
        for i in b:
            l.insert(i)
        self.check_content(l, a + b)

    def test_removal(self):
        a = (4, 2)
        b = (1, 3)
        l = self.get_list(a + b)
        for i in b:
            l.remove(i)
        self.check_content(l, a)
        for i in a:
            l.remove(i)
        self.check_content(l, ())

        l = self.get_list((4, 2, 3, 1))
        l.clear()
        self.check_content(l, ())

        l = self.get_list((4, 2, 3, 1))
        del l[2]
        self.check_content(l, (1, 2, 4))
        del l[0]
        self.check_content(l, (2, 4))
        del l[0]
        self.check_content(l, (4,))

    def test_index_access(self):
        items = [0, 1, 2]
        l = self.get_list(items)
        self.assertRaises(TypeError, l.__setitem__, 1, 1)
        self.assertRaises(IndexError, l.__getitem__, 5)
        self.assertRaises(IndexError, l.__getitem__, -7)
        for i in items:
            self.assertEqual(l[i], items[i])
        self.assertEqual(tuple(l[::]), tuple(items[::]))
        self.assertEqual(tuple(l[::2]), tuple(items[::2]))
        for start in range(-5, 5):
            for stop in range(-5, 5):
                for step in range(1, 10):
                    self.assertEqual(tuple(l[start:stop:step]), tuple(items[start:stop:step]))

    def test_popping(self):
        l = self.get_list((4, 2, 3, 1))
        l.pop()
        self.check_content(l, (1, 2, 3))
        l.pop()
        self.check_content(l, (1, 2))
        l.pop()
        self.check_content(l, (1,))
        l.pop()
        self.check_content(l, ())

        l = self.get_list((4, 2, 3, 1))
        l.shift()
        self.check_content(l, (2, 3, 4))
        l.shift()
        self.check_content(l, (3, 4))
        l.shift()
        self.check_content(l, (4,))
        l.shift()
        self.check_content(l, ())

    def test_reversal(self):
        items = (1, 2, 3, 4)
        l = self.get_list((1, 2, 3, 4))
        self.assertEqual(tuple(reversed(l)), tuple(reversed(items)))

        l = self.get_list((4, 2, 3, 1))
        self.assertEqual(tuple(reversed(l)), tuple(reversed(items)))

    def test_range(self):
        items = [-2, 1, 5, 7, 3, -3, 2, -4, -1, 9, 0, -5, 8, 6, 4]
        l = self.get_list(items)

        self.check_content(l, items, test_value=2)
        self.assertEqual(tuple(l.range(-2, 3)), (-2, -1, 0, 1, 2))
        self.assertEqual(tuple(l.range(-2.2, 2.5)), (-2, -1, 0, 1, 2))
        self.assertEqual(tuple(l.range(-2, 3, False)), (-1, 0, 1, 2))
        self.assertEqual(tuple(l.range(-2, 3, True, True)), (-2, -1, 0, 1, 2, 3))
        self.assertEqual(tuple(l.range(-2, 3, False, True)), (-1, 0, 1, 2, 3))
        self.assertEqual(len(tuple(l.range(0, 6))), 6)
        self.assertEqual(len(tuple(l.range(6, 0))), 0)

    def test_estimation(self):
        items = [-2, 1, 7, 14, 55, 972]
        l = self.get_list(items)

        self.check_content(l, items, test_value=9)
        self.assertEqual(l.ceiling(9), 14)
        self.assertEqual(l.floor(9), 7)
        self.assertEqual(l.ceiling(9, False), 14)
        self.assertEqual(l.floor(9, False), 7)
        self.assertEqual(l.ceiling(14), 14)
        self.assertEqual(l.floor(14), 14)
        self.assertEqual(l.ceiling(14, False), 55)
        self.assertEqual(l.floor(14, False), 7)
        self.assertEqual(l.ceiling(7), 7)
        self.assertEqual(l.floor(7), 7)
        self.assertEqual(l.ceiling(7, False), 14)
        self.assertEqual(l.floor(7, False), 1)

    def test_height(self):
        size = 40
        items = list(i for i in range(size))
        random.Random('shuffle').shuffle(items)

        r = random.Random('list')
        def _random_height():
            """returns a non-negative integer"""
            return min(int(-log2(1 - r.random())), 16)

        expected_dist = list(_random_height() for i in range(size))
        r = random.Random('list')

        dist = {}
        def count_nodes(node):
            while type(node.next.value) == int:
                node = node.next
                height = 0
                current = node
                while hasattr(current, 'below'):
                    current = current.below
                    height += 1
                dist[current.value] = height
        l = SkipList(items, random_height=_random_height)
        heads = l._SkipList__sentinels
        lengths = []
        for i in heads:
            lengths.append(count_nodes(i))

        self.assertEqual(len(expected_dist), len(dist))
        self.assertEqual(Counter(expected_dist), Counter(dist.values()))

    def test_repr(self):
        items = (3, 2, 1, 4)
        l = self.get_list(items)
        self.assertEqual(str(l), 'SkipList([1, 2, 3, 4])')
        l = self.get_list(range(200))
        self.assertEqual(str(l), 'SkipList([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39... and 160 more])')

    def test_time_complexity(self):
        error_tolerance = 0.1
        r = RandInt(26153, 2**15)
        data = list(r.next() for i in range(2**15))
        l_1n = SkipList(itertools.islice(data, 2**12))
        l_8n = SkipList(data)

        def task(l):
            for i in itertools.islice(data, 2**12):
                if i not in l:
                    raise Exception('bad data')

        for i in range(5):
            t1 = min(timeit.Timer('task(l_1n)', globals=locals()).repeat(repeat=1, number=1))
            t2 = min(timeit.Timer('task(l_8n)', globals=locals()).repeat(repeat=1, number=1))
            if (t2 / t1 < 15 / 12 * (1 + error_tolerance)):
                break
        else:
            self.fail('SkipList.__contains__ operation took more than log(n) time')


if __name__ == '__main__':
    unittest.main()
