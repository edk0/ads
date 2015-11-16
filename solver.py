import math
import sys

from collections import defaultdict
from functools import reduce, partial
from itertools import combinations, permutations, starmap, count
from operator import add, attrgetter, itemgetter

from multiprocessing import Pool

from util import (Point, Route, distance, merge_routes,
                  trivial_solution, ncr, npr, solution_cost)


from grid import MergeGrid


def available_merges(p, l, mirror=False):
    """
    Return the acceptable merges, i.e. combinations of routes taken from l
    that aren't impossible due to the quantity restriction
    """
    if mirror:
        it = combinations(l, 2)
    else:
        it = permutations(l, 2)
    c = []
    for merge in it:
        a, b = merge
        if a.volume + b.volume < p.capacity:
            c.append((a, b, merge_routes(a, b)))
    return sorted(c, key=lambda t: t[0].cost + t[1].cost - t[2].cost, reverse=True)


def available_with_pruning(p, l, cr=False, max_dist=float('inf'), spacing=None, progress_callback=None):
    """
    Return the merges from l that are both possible and appear to be among the
    better merges for one of their inputs.

    cr:       if true, use combinations from l instead of permutations
    max_dist: if supplied, short-circuit for distances that are more than this
              (i.e. avoid doing the work to see what they actually are)
    progress_callback:
              if supplied, is called every 10000 cycles with the number of
              cycles completed.

    available_with_pruning is the high-performance, bounded-memory version of
    available_merges. It stores the few (exactly how many is configurable
    below) best merges for each route; this is suboptimal, because sometimes
    all the best merges for a route will be invalidated by earlier merges, but
    it is easy to check and gives us linear space complexity instead of
    factorial. Using this optimization we can solve problems involving tens or
    hundreds of thousands of points.
    """
    HIGH, LOW = 20, 10  # Tuned for overall performance.
    n = 0
    actual = 0
    sc_radius = 0
    sc_d2 = 0
    if max_dist is not None:
        it = MergeGrid(None, l, cr, max_dist, spacing)
    else:
        if cr:
            it = combinations(l, 2)
        else:
            it = permutations(l, 2)
    best = defaultdict(list)
    key = itemgetter(0)
    if max_dist is None:
        max_dist = float('inf')
    min_dist = -max_dist
    max_d2 = max_dist ** 2

    def insert_merge(mr):
        nonlocal actual
        m, saving = mr
        if a not in best or best[a][0][0] < saving:
            best[a].append((saving, a, b, m))
            if len(best[a]) > HIGH:
                best[a].sort(key=key, reverse=True)
                del best[a][LOW:]
        if b not in best or best[b][0][0] < saving:
            best[b].append((saving, a, b, m))
            if len(best[b]) > HIGH:
                best[b].sort(key=key, reverse=True)
                del best[b][LOW:]
        actual += 1

    def radius_check(a, b):
        nonlocal sc_radius
        radius = a._post_cost - b._pre_cost
        if radius > max_dist or radius < min_dist:
            sc_radius += 1
            return False
        return True

    last = None

    for a, b in it:
        if a is not last:
            n += 1
            last = a
            if n & 0xff == 0:
                progress_callback(n)
        #  Fast distance exit
        if not radius_check(a, b):
            continue
        #  Don't make routes that are over capacity
        if a.volume + b.volume > p.capacity:
            actual += 1
            continue
        mr = merge_routes(a, b, cutoff_d2=max_d2)
        if mr is None:
            sc_d2 += 1
            continue
        insert_merge(mr)

    del a
    del b
    del it

    c = set()
    for v in best.values():
        c.update(v)
    return len(c), map(itemgetter(slice(1, None)), sorted(c, key=key, reverse=True)), (sc_radius, sc_d2)


def filter_merges(l):
    """
    Select merges that don't merge routes we have already selected.
    """
    seen = set()
    for a, b, m in l:
        if a not in seen and b not in seen:
            seen.add(a)
            seen.add(b)
            yield (a, b, m)


def apply_merges(r, l):
    """
    Take a set of routes and a list of (route, route, merged_route), and
    return a new set of routes with the merges applied.
    """
    for a, b, m in l:
        assert a in r and b in r
        r.remove(a)
        r.remove(b)
        r.add(m)
    return r


def solve(p, max_dist=None):
    """
    Find a solution to the given problem using the parallel C&W savings alg.
    """
    r = trivial_solution(p)

    del p.customers  # Hacky, but should save some memory.

    first = True
    num = 0
    increments = 0
    initial_dist = max_dist
    while True:
        num += 1
        print('Cycle {}: finding available merges...'.format(num))

        # Set up d^2 cutoff
        if max_dist is not None:
            print('Using distance cutoff for this pass. Threshold: {}'.format(max_dist))

        # Print a vaguely acceptable-looking percentage
        def progress(n):
            prog = n * 100 / len(r)
            print('\033[2K\r{:6.2f}% '.format(prog), end='')
            sys.stdout.flush()

        n, m, sc = available_with_pruning(p, r, cr=first, max_dist=max_dist, spacing=initial_dist, progress_callback=progress)
        print('\033[2K\r', end='')

        if any(sc):
            print('shortcuts taken: radius: {}, d^2: {}'.format(*sc))

        first = False

        print('Applying merges...')
        f = filter_merges(m)
        del m

        pl = len(r)
        pcost = solution_cost(r)

        apply_merges(r, f)
        del f

        print('Merged {}/{} routes: {} -> {} (cost {} -> {})'.format(
            pl - len(r), n, pl, len(r), pcost, solution_cost(r)))

        if (pl - len(r) < 5) or increments > 0:
            if max_dist is not None and increments < 6:
                max_dist *= math.sqrt(2)
                increments += 1
            else:
                break

    return r
