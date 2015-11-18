import math

from functools import reduce, partial
from itertools import starmap
from operator import attrgetter


def distance(p1, p2, cutoff=float('inf')):
    """
    The distance between p1 and p2. If cutoff is supplied and is smaller than
    the square of the distance, don't compute the square root and return None
    instead.
    """
    d2 = (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2
    if d2 > cutoff:
        return None
    return math.sqrt(d2)


def trivial_solution(p):
    """
    Return the trivial (route per point) solution for p.
    """
    s = set()
    for customer in p.customers:
        s.add(Route(customer.volume, [p.depot, customer, p.depot]))
    return s


def merge_routes(a, b, cutoff_d2=float('inf')):
    """
    Return a Route that visits all the points on a and b.
    """
    c_merge = distance(a._points[-2], b._points[1], cutoff_d2)
    if c_merge is None:
        return
    c_a = a.cost - a._post_cost
    c_b = b.cost - b._pre_cost
    saving = c_a + c_b - c_merge
    r = Route(a.volume + b.volume,
              a._points[:-1] + b._points[1:],
              _costs=(c_a + c_b + c_merge, a._pre_cost, b._post_cost))
    return r, saving


class Point:
    """
    2d coordinates, possibly with a volume of stuff to be delivered there
    """
    __slots__ = ('x', 'y', 'volume', '_hash')

    def __init__(self, x, y=None, *, volume=None):
        if isinstance(x, (tuple, list)):
            x, y = x
        if y is None:
            raise TypeError
        self.x = x
        self.y = y
        self.volume = volume
        self._hash = hash(x) ^ hash(y) ^ hash(volume)

    def __repr__(self):
        if self.volume is not None:
            return 'Point({!r}, {!r}, volume={!r})'.format(
                    self.x, self.y, self.volume)
        return 'Point({!r}, {!r})'.format(self.x, self.y)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Route:
    """
    A route, i.e. a sequence of points. Stores pre-computed cost and volume.

    Unlike Point we don't override hash() for Route, so Routes will compare
    equal only if they're the exact same object. This is purely a speed
    optimization; we never create two objects for the same route, so we don't
    need to waste the time comparing them properly.
    """
    __slots__ = ('volume', '_points', 'cost', '_pre_cost', '_post_cost')

    def __init__(self, volume, points, *, _costs=None):
        self.volume = volume
        self._points = points = tuple(points)

        if _costs is not None:
            self.cost, self._pre_cost, self._post_cost = _costs
            return

        if len(points) < 3:
            raise ValueError # all routes should involve depot->somewhere->depot
        self._pre_cost = distance(points[0], points[1])
        self._post_cost = distance(points[-2], points[-1])

        def sum_distance(s, p):
            p1, p2 = p
            return s + distance(p1, p2)
        self.cost = reduce(sum_distance, zip(points, points[1:]), 0)

    def __repr__(self):
        return '<Route points={self._points!r} volume={self.volume!r} \
cost={self.cost!r}>'.format(self=self)


def npr(n, k):
    """
    return n_P_k
    """
    return math.factorial(n) // math.factorial(n-k)


def ncr(n, k):
    """
    return n_C_k
    """
    return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))


def solution_cost(s):
    """
    Return the sum of the costs of a set of routes.
    """
    return sum(map(attrgetter('cost'), s))
