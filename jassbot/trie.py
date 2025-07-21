class Trie:
    def __init__(self):
        self.children = {}
        self.done = False

    def insert(self, val):
        if not val:
            self.done = True
        else:
            c = val[0]
            cs = val[1:]

            if c not in self.children:
                self.children[c] = Trie()

            self.children[c].insert(cs)

    def toRegexp(self):
        def recur(c, n):
            return c + n.toRegexp()

        r = "|".join(recur(c, n) for c,n in sorted(self.children.items()))
        if (self.done and len(self.children) > 0):
            return "(?:" + r + ")?"
        elif len(self.children) > 1:
            return "(?:" + r + ")"
        else:
            return r
