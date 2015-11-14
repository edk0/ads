from collections import defaultdict
from math import ceil, isinf, sqrt

from util import Point

class MergeGrid:
    def __init__(self, problem, route_set, ignore_ordering=False, max_dist=float('inf')):
        self._problem = problem
        self._r = route_set
        self._max_dist = max_dist
        self._grid = defaultdict(list)
        self._grid_square = 100.0 if isinf(max_dist) else max_dist
        self._search_radius = ceil(max_dist / self._grid_square)

        self.ignore_ordering = ignore_ordering

        self._build_grid()

    def _build_grid(self):
        for r in self._r:
            # integer division operator will truncate toward negative infinity
            # so (0, 0) is the inner square of the (+, +) quadrant
            x = r._points[1].x
            y = r._points[1].y
            gc = (int(x // self._grid_square), int(y // self._grid_square))
            self._grid[gc].append(r)

    def _routes_for_point(self, p):
        gc = (int(p.x // self._grid_square), int(p.y // self._grid_square))
        for x in range(-self._search_radius, self._search_radius + 1):
            for y in range(-self._search_radius, self._search_radius + 1):
                yield from self._grid[(gc[0] + x, gc[1] + y)]

    def _routes(self):
        for r in self._r:
            yield from ((r, q) for q in self._routes_for_point(r._points[-2]) if r is not q)

    def _routes_forward(self):
        s = set()
        for r in self._r:
            s.add(r)
            yield from ((r, q) for q in self._routes_for_point(r._points[-2]) if q not in s)

    def __iter__(self):
        if self.ignore_ordering:
            return self._routes_forward()
        else:
            return self._routes()
