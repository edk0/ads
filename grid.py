from collections import defaultdict
from math import ceil, isinf, sqrt

import sys

from util import Point

class MergeGrid:
    def __init__(self, problem, route_set, ignore_ordering=False, max_dist=float('inf'), spacing=None):
        self._problem = problem
        self._r = route_set
        self._max_dist = max_dist
        self._grid = {}
        if max_dist == float('inf'):
            max_dist = 100.0
        if spacing is None:
            spacing = max_dist
        self._grid_square = spacing * 6
        self._search_radius = max_dist + self._grid_square / 2.0
        self._search_order = None

        # For the first pass for any solution, the a,b and b,a merges have
        # exactly the same cost. We have no sensible way to choose between
        # them, so we can save time by not looking for half of them at all.
        self.ignore_ordering = ignore_ordering
        if ignore_ordering:
            self._r = list(self._r)
            self._r.sort(key=id)

        print('building merge grid... ', end='')
        sys.stdout.flush()
        self._build_grid()
        self._build_search()
        print('ok')
        print('spacing: {}  max_dist: {}'.format(spacing, max_dist))
        print('search order: {}'.format(self._search_order))

    def _build_grid(self):
        for r in self._r:
            # integer division operator will truncate toward negative infinity
            # so (0, 0) is the inner square of the (+, +) quadrant
            x = r._points[1].x
            y = r._points[1].y
            gc = (int(x // self._grid_square), int(y // self._grid_square))
            if gc not in self._grid:
                self._grid[gc] = []
            self._grid[gc].append(r)

    def _build_search(self):
        sr = self._search_radius ** 2
        so = []
        ir = ceil(self._search_radius)
        for x in range(-ir, ir + 1):
            for y in range(-ir, ir + 1):
                if (x * self._grid_square) ** 2 + (y * self._grid_square) ** 2 <= sr:
                    so.append((x, y))
        self._search_order = tuple(so)

    def _routes_for_point(self, p):
        gc = (int(p.x // self._grid_square), int(p.y // self._grid_square))
        for x, y in self._search_order:
            yield self._grid.get((gc[0] + x, gc[1] + y), ())

    def _routes(self):
        for r in self._r:
            for l in self._routes_for_point(r._points[-2]):
                for q in l:
                    if r is q:
                        continue
                    yield (r, q)

    def _routes_forward(self):
        # Try to do the slow bit at the beginning.
        for r in reversed(self._r):
            for l in self._routes_for_point(r._points[-2]):
                for q in l:
                    if id(q) >= id(r):
                        break
                    yield (r, q)

    def __iter__(self):
        if self.ignore_ordering:
            return self._routes_forward()
        else:
            return self._routes()
