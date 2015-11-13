import math
import sys

from collections import defaultdict
from functools import reduce, partial
from itertools import combinations, permutations, starmap, count
from operator import add, attrgetter, itemgetter

from multiprocessing import Pool

from util import Point, Route, distance, min_index


def initial_routes(p):
    r = []
    for customer in p.customers:
        r.append(Route(customer.volume, [p.depot, customer, p.depot]))
    return r


def merge_routes(a, b, max_dist=None):
    """
    Return a Route that visits all the points on a and b.
    """
    assert a._points[0] == a._points[-1] == b._points[0] == b._points[-1]
    c_a = a.cost - a._post_cost
    c_b = b.cost - b._pre_cost
    c_merge = distance(a._points[-2], b._points[1], max_dist)
    if c_merge is None:
        return
    r = Route(a.volume + b.volume,
                 a._points[:-1] + b._points[1:],
                 _costs=(c_a + c_b + c_merge, a._pre_cost, b._post_cost))
    return r


def insert_point(r, p, *, max_cost=None):
    """
    Insert a point into a route where it would have the smallest effect
    on the cost.

    If max_cost is given, return None if the new cost > max_cost.
    """
    d = zip(r._points, r._points[1:])
    costs = starmap(lambda a, b: distance(p, a) + distance(p, b) - distance(a, b), d)
    i, cost = min_index(costs)
    if max_cost is not None and cost > max_cost:
        return
    ps = list(r._points)
    ps[i+1:i+1] = [p]
    return Route(r.volume + p.volume,
                 ps) # XXX add proper cost calc


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


def available_with_pruning(p, l, cr=False, max_dist=None, progress_callback=None):
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
    if cr:
        it = combinations(l, 2)
    else:
        it = permutations(l, 2)
    best = defaultdict(list)
    key = itemgetter(0)
    for merge in it:
        a, b = merge
        n += 1
        if n % 10000 == 0:
            progress_callback(n)
        if a.volume + b.volume < p.capacity:
            m = merge_routes(a, b, max_dist)
            if m is None:
                continue
            saving = a.cost + b.cost - m.cost
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
    c = set()
    for v in best.values():
        c.update(v)
    if len(c) == 0:
        return ()
    return map(itemgetter(slice(1, None)), sorted(c, key=key, reverse=True))


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
    r = set(r)
    for a, b, m in l:
        assert a in r and b in r
        r.remove(a)
        r.remove(b)
        r.add(m)
    return r


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


def solve(p, max_dist=None):
    """
    Find a solution to the given problem using the parallel C&W savings alg.
    """
    D2_PRUNE = 2000  # If we have less than this number of routes to combine,
                     # don't use the d^2 cutoff
    r = set(initial_routes(p))  # Start with trivial solution
    first = True
    while True:
        # Figure out how many merges we're going to check. Mostly for the
        # benefit of humans, but we also use this to decide whether to use
        # the d^2 cutoff
        t = comb = npr(len(r), 2)
        print('Finding available merges ({} possible)...'.format(comb))
        if first:
            t = ncr(len(r), 2)
            print('2-orderings are equivalent. Skipping {} merges'.format(comb-t, 2))

        # Set up d^2 cutoff
        if max_dist is not None and t >= npr(D2_PRUNE, 2):
            print('Using d^2 cutoff for this pass. Threshold: {}'.format(max_dist))
            dc = max_dist
        else:
            dc = None

        # Print a vaguely acceptable-looking percentage
        def progress(n):
            prog = n * 100 / t
            print('\r{:.2f}%'.format(prog), end='')
            sys.stdout.flush()

        m = available_with_pruning(p, r, cr=first, max_dist=dc, progress_callback=progress)
        print('\r', end='')

        first = False

        if not m:
            # This final attempt adds a few seconds and usually doesn't find
            # anything, but the wasted time is fairly insignificant compared
            # with the time taken to get this far
            if dc is not None:
                print('Run out of merges, turning off pruning.')
                max_dist = None
                continue
            else:
                print('No more merges, C&W solution complete.')
                break

        print('Applying merges...')
        f = filter_merges(m)
        nr = apply_merges(r, f)
        print('Merged {} routes: {} -> {} (cost {} -> {})'.format(
            len(r) - len(nr), len(r), len(nr), solution_cost(r), solution_cost(nr)))
        r = nr
    return r


def opt(p, s):
    """
    Apply `redistribute` until it doesn't do anything.
    """
    c0 = solution_cost(s)
    for i in count(1):
        print('Applying redistribute, #{}'.format(i))
        s, sr = redistribute(p, s)
        print('Success rate: {!r}'.format(sr))
        if sr == 0.0:
            break
    c = solution_cost(s)
    print('Saved {!r}'.format(c0-c))
    return s


def redistribute(problem, s):
    """
    A cheap algorithm that tries to break up low-volume routes and
    redistribute their points among the other ones.
    """
    l = sorted(s, key=attrgetter('volume'))
    pop_pos = 0
    i = 0
    cf = 0
    tf, ts = 0, 0
    while len(l) > pop_pos:
        i += 1
        l_next = l[:]
        t = l_next.pop(pop_pos)
        points = t._points[1:-1]
        rcost = 0
        cts = t.cost
        for px in permutations(points):
            failed = False
            rcost = 0
            for p in px: #sorted(points, key=attrgetter('volume'), reverse=False):
                max_cost = None
                change = None
                #rs = distance(p, points[i-1]) + distance(p, points[i+1]) -\
                #              distance(points[i-1], points[i+1])
                for ri, r in enumerate(reversed(l_next)):
                    if r is t:
                        continue
                    if p.volume + r.volume > problem.capacity:
                        continue
                    n = insert_point(r, p, max_cost=max_cost)
                    if n is None:
                        continue
                    max_cost = n.cost
                    change = (n.cost - r.cost, len(l_next) - ri - 1, n)
                if change is None:
                    failed = True
                    break
                cost, ind, nr = change
                rcost += cost
                l_next[ind] = nr
            if not failed:
                break
        if failed:
            #print("Redistribution cycle {!r} failed.".format(i))
            cf += 1
            tf += 1
            pop_pos += 1
        elif cts <= rcost:
            #print("Redistribution cycle {!r} couldn't find a saving: delete {!r}, cost {!r}, saved {!r}".format(
            #    i, cts, rcost, cts - rcost))
            cf += 1
            tf += 1
            pop_pos += 1
        else:
            print('Redistribution cycle {!r}: delete {!r}, cost {!r}, saved {!r}'.format(
                i, cts, rcost, cts - rcost))
            cf = 0
            ts += 1
            l = l_next
        if cf > 10 and ts < tf:
            tf += len(l) - pop_pos
            break
    return set(l), ts/tf
