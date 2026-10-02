#!/usr/bin/env python3
"""Project character offsets between two near-identical versions of a text.

The same human work often reaches us twice — e.g. an OpenPecha API instance and
a Google-Docs export of the same commentary — with different whitespace,
punctuation spacing, inserted heading lines or the odd corrected letter. A
span annotated on one version (an alignment, a segment, a variant note) is
carried onto the other by matching their *letters* (whitespace and
punctuation ignored) and walking both in step.

The walk is linear: on a mismatch it searches a bounded window ahead in both
texts for the next stretch of `anchor` identical letters and resumes there.
Letters that fall in a skipped stretch have no counterpart and project to
None — callers must report those, never guess.

    m = Projector(a, b)
    m.pos(i)            # offset in b of the letter at offset i in a (or None)
    m.span(start, end)  # (b_start, b_end) covering every mapped letter, or None
    m.stats             # {"letters_a", "letters_b", "matched", "skipped_a", "skipped_b"}
"""
import unicodedata


def is_letter(ch):
    cat = unicodedata.category(ch)
    if cat[0] in ("L", "M", "N"):
        # Tibetan marks and punctuation that behave as separators
        return ch not in "་༌།༎༄༅༔༑༈"
    return False


def letters(s):
    idx = [i for i, ch in enumerate(s) if is_letter(ch)]
    return "".join(s[i] for i in idx), idx


class Projector:
    def __init__(self, a, b, anchor=12, window=4000):
        la, ia = letters(a)
        lb, ib = letters(b)
        self.map = {}
        i = j = 0
        skipped_a = skipped_b = 0
        while i < len(la) and j < len(lb):
            if la[i] == lb[j]:
                self.map[ia[i]] = ib[j]
                i += 1
                j += 1
                continue
            best = None
            # try to resync: skip k letters in a and/or l letters in b
            probe_a = la[i:i + anchor]
            probe_b = lb[j:j + anchor]
            l = lb.find(probe_a, j, j + window) if len(probe_a) == anchor else -1
            k = la.find(probe_b, i, i + window) if len(probe_b) == anchor else -1
            if l != -1:
                best = (0, l - j)
            if k != -1 and (best is None or (k - i) < sum(best)):
                best = (k - i, 0)
            if best is None:
                # substitution: try skipping one letter on both sides
                for d in range(1, 200):
                    pa = la[i + d:i + d + anchor]
                    pos = lb.find(pa, j, j + window) if len(pa) == anchor else -1
                    if pos != -1:
                        best = (d, pos - j)
                        break
            if best is None:
                skipped_a += len(la) - i
                skipped_b += len(lb) - j
                i, j = len(la), len(lb)
                break
            skipped_a += best[0]
            skipped_b += best[1]
            i += best[0]
            j += best[1]
        skipped_a += len(la) - i
        skipped_b += len(lb) - j
        self.stats = {"letters_a": len(la), "letters_b": len(lb), "matched": len(self.map),
                      "skipped_a": skipped_a, "skipped_b": skipped_b}
        self._sorted = sorted(self.map)

    def pos(self, i):
        return self.map.get(i)

    def span(self, start, end):
        """Smallest b-span covering every mapped letter of a[start:end]."""
        import bisect
        lo = bisect.bisect_left(self._sorted, start)
        hi = bisect.bisect_left(self._sorted, end)
        if lo >= hi:
            return None
        b = [self.map[k] for k in self._sorted[lo:hi]]
        return min(b), max(b) + 1
