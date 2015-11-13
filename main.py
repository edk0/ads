from problem import Problem
from solution import Solution
from solver import solve, opt
from util import distance

import random
import logging
import sys


def mean(l):
    return sum(l) / len(l)


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


def main():
    enable_debug()
    with open(sys.argv[1]) as f:
        p = Problem.load(f)
    pd = []
    for i in range(100):
        p1 = random.choice(p.customers)
        d = []
        for j in range(100):
            p2 = random.choice(p.customers)
            d.append(distance(p1, p2))
        pd.append(min(d))

    s = solve(p, max_dist=median(pd))
    print(' - ')
    solution_info(p, s)
    print(' - ')
    s = opt(p, s)
    print(' - ')
    solution_info(p, s)
    print(' - ')
    with open(sys.argv[2], 'w') as f:
        Solution(s).write(f)


if __name__ == '__main__':
    main()
