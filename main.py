from problem import Problem
from solution import Solution
from solver import solve
from util import distance

import random
import logging
import sys


def median(l, t=0.5):
    l = sorted(l)
    mp = int((len(l) - 1) * t)
    if len(l) % 2 == 0:
        return (l[mp] / 2 + l[mp + 1] / 2)
    else:
        return l[mp]


def enable_debug():
    try:
        import bpdb as pdb
    except ImportError:
        import pdb
    logging.basicConfig(level=logging.DEBUG)

    def hook(typ, value, tb):
        sys.settrace(None)
        sys.__excepthook__(typ, value, tb)
        pdb.post_mortem(tb)

    sys.excepthook = hook


def solution_info(p, s):
    utilization = [r.volume / p.capacity for r in s]
    waste = sum(p.capacity - r.volume for r in s)
    print('Capacity {!r}, median utilization {!r}, min {!r}. Total routes: {!r}'.format(
        p.capacity, median(utilization), min(utilization), len(s)))
    print('Total cost: {}'.format(sum(r.cost for r in s)))


def find_cutoff(p):
    print('Analysing data')
    pd = []
    for i in range(min(100, len(p.customers))):
        p1 = random.choice(p.customers)
        d = []
        for j in range(len(p.customers) // 10 + 1):
            p2, spare = random.sample(p.customers, 2)
            if p2 is p1:
                p2 = spare
            d.append(distance(p1, p2))
        pd.append(min(d))
    return median(pd)


def main():
    enable_debug()

    print('Loading {}'.format(sys.argv[1]))
    with open(sys.argv[1]) as f:
        p = Problem.load(f)

    # A probabilistic optimization: examine some random customers. For
    # each one, find the closest customer from another random sampling.
    # The median of these distances will be used as the distance cutoff for
    # the solver.

    s = solve(p, max_dist=find_cutoff(p))
    print(' - ')
    solution_info(p, s)
    print(' - ')
    with open(sys.argv[2], 'w') as f:
        Solution(s).write(f)


if __name__ == '__main__':
    main()
