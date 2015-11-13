import csv

from functools import partial

from util import Point

class Problem:
    def __init__(self):
        self.depot = None
        self.capacity = None
        self.customers = []

    @classmethod
    def load(cls, s):
        self = cls()
        reader = map(partial(map, int), csv.reader(s))
        *depot, self.capacity = next(reader)
        self.depot = Point(depot)
        for v in reader:
            x, y, vol = v
            self.customers.append(Point(x, y, volume=vol))
        return self

    def __repr__(self):
        return "<Route depot={self.depot!r} \
capacity={self.capacity!r} \
customers={self.customers!r}>".format(self=self)
