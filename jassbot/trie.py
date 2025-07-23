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

        r = []
        all_single = True
        for sub_regexp in (recur(c, n) for c,n in sorted(self.children.items())):
            all_single = all_single and len(sub_regexp) == 1
            r.append(sub_regexp)

        if all_single and len(r) > 2:
            classes = []
            start = None
            last = None
            for char in r:
                if last is None:
                    start = char
                    last = char
                elif ord(last)+1 == ord(char):
                    last = char
                else:
                    classes.append((start, last))
                    start = char
                    last = char
            classes.append((start, last))
            r = "["
            for (start, end) in classes:
                if ord(end) - ord(start) >= 2:
                    r += f"{start}-{end}"
                else:
                    r += "".join(chr(x) for x in range(ord(start), ord(end)+1))
            r += "]"
        else:
            r = "|".join(r)

        if r == "[0-9]" or r == "[0123456789]":
            r = "\\d"

        if self.done and len(self.children) > 0:
            return "(?:" + r + ")?"
        elif len(self.children) > 1:
            return "(?:" + r + ")"
        else:
            return r
