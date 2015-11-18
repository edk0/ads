from collections import defaultdict
from math import ceil, isinf, sqrt

import sys

class MergeGrid:
    """
    A 2D array of routes taken from route_set and positioned according to the
    last non-depot point in the route.
    Iterating over it yields combinations of routes. Each combination of
    routes with a distance less than `max_dist` between them is guaranteed to
    appear.

    problem:         The Problem object we're working on.
    route_set:       A set of routes to place in the grid.
    ignore_ordering: If true, iteration will exclude one of a,b and b,a for
                     all a and b.
    max_dist:        The largest distance routes can be apart before iteration
                     is permitted to skip them.
    spacing:         The approximate distance between a customer and their
                     closest neighbour.

    Operating theory: the fastest possible strategies for eliminating very
    long-distance matches are never going to be as fast as not generating them
    in the first place. We can achieve this by placing each route in a grid
    square, and for each route being searched, only try to combine it with the
    routes in squares within a certain range.

    If we're `ignore_ordering`, we sort the routes in their individual grid
    squares by their id(). We can then skip whole squares once we've hit one
    duplicate combination. The iterator loop is arranged to skip more
    combinations later in the sequence, because I think it's less worrying to
    see the progress speed up.
    """

    def __init__(self, problem, route_set, ignore_ordering=False, max_dist=float('inf'), spacing=None):
        self._problem = problem
        self._r = route_set
        self._max_dist = max_dist
        self._grid = {}
        # Perhaps not a very sensible default, but nothing is.
        # XXX consider not allowing this?
        if max_dist == float('inf'):
            max_dist = 100.0
        if spacing is None:
            spacing = max_dist
        self._grid_square = spacing * 6  # XXX heuristic
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
        """
        Place each of our Routes into a grid square.
        """
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
        """
        Generate a tuple of tuples of relative x,y coordinates that we'll use
        for iteration.
        """
        sr = self._search_radius ** 2
        so = []
        ir = ceil(self._search_radius)
        for x in range(-ir, ir + 1):
            for y in range(-ir, ir + 1):
                if (x * self._grid_square) ** 2 + (y * self._grid_square) ** 2 <= sr:
                    so.append((x, y))
        self._search_order = tuple(so)

    def _routes_for_point(self, p):
        """
        Routes that might be within range of a Point p.
        """
        gc = (int(p.x // self._grid_square), int(p.y // self._grid_square))
        for x, y in self._search_order:
            yield self._grid.get((gc[0] + x, gc[1] + y), ())

    def _routes(self):
        """
        All the in-range routes we can find, apart from a,a.
        """
        for r in self._r:
            # [-2] is the last point before depot
            for l in self._routes_for_point(r._points[-2]):
                for q in l:
                    if r is q:
                        continue
                    yield (r, q)

    def _routes_forward(self):
        """
        All the in-range routes we can find, excluding b,a for a,b we have
        already yielded.
        """
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
