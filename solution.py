class Solution:
    def __init__(self, s):
        self.routes = s

    def write(self, f):
        def ser(p):
            return '{},{},{}'.format(p.x, p.y, p.volume)
        for r in self.routes:
            f.write(','.join(map(ser, r._points[1:-1])))
            f.write('\n')
