import math

from functools import reduce


def min_index(l):
    ita = iter(l)
    i, m = 0, next(ita)
    for k, v in enumerate(ita):
        if v < m:
            i, m = k, v
    return i, m


def distance(p1, p2, cutoff=None):
    d2 = (p1.x - p2.x) ** 2 + (p1.y - p2.y ** 2)
    if cutoff is not None and d2 > cutoff ** 2:
        return None
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


class Point:
    __slots__ = ('x', 'y', 'volume')

    def __init__(self, x, y=None, *, volume=None):
        if isinstance(x, (tuple, list)):
            x, y = x
        self.x = x
        self.y = y
        self.volume = volume
        if y is None:
            raise Exception

    def __repr__(self):
        if self.volume is not None:
            return 'Point({!r}, {!r}, volume={!r})'.format(
                    self.x, self.y, self.volume)
        return 'Point({!r}, {!r})'.format(self.x, self.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if isinstance(other, Point):
            return (self.x, self.y) == (other.x, other.y)
        return NotImplemented


class Route:
    __slots__ = ('volume', '_points', 'cost', '_pre_cost', '_post_cost')

    def __init__(self, volume, points, *, _costs=None):
        self.volume = volume
        self._points = list(points)

        if _costs is not None:
            self.cost, self._pre_cost, self._post_cost = _costs
            return

        pp = self._points
        if len(pp) < 3:
            raise ValueError # all routes should involve depot->somewhere->depot
        self._pre_cost = distance(pp[0], pp[1])
        self._post_cost = distance(pp[-2], pp[-1])

        def sum_distance(s, p):
            p1, p2 = p
            return s + distance(p1, p2)
        self.cost = reduce(sum_distance, zip(pp, pp[1:]), 0)

    def __repr__(self):
        return '<Route points={self._points!r} volume={self.volume!r} \
cost={self.cost!r}>'.format(self=self)

    def __hash__(self):
        return hash((self.volume, tuple(self._points)))

    def __eq__(self, other):
        if isinstance(other, Route):
            return (self.volume, self._points) == \
                   (other.volume, other._points)
        return NotImplemented

