#!/usr/bin/env python3
"""Carry a human row alignment from one segmentation of a text onto another.

A commentary (or translation) was aligned, row by row, against its *own copy*
of the root text, cut into rows its own way. The vault stores the root once,
with one segmentation. This module finds, for every row of such a copy, which
segments of the stored root its letters fall in — without changing either
segmentation:

    c = Concordance(target_blocks, copy_rows)
    c.row(k)      # {"targets": [...], "spans": {...}, "flags": [...]} for copy row k

target_blocks  [(block_id, text)] — the stored root, in document order
copy_rows      [(row_no, text)]   — the copy, in document order

Method. Both sides are reduced to their letters (Unicode L/M/N; whitespace,
shad, tsheg, danda and other punctuation ignored — see project.is_letter) and
aligned with a longest-matching-block diff. Every copy letter that pairs with
a target letter votes for that letter's block. Where the two editions differ
(a letter or word present on one side only, a spelling variant) the diff
leaves an insertion, deletion or replacement; letters around it still vote
correctly, so a reading present in one edition and absent in the other never
shifts the rows after it. Replaced letters are mapped proportionally; letters
only in the copy, or only in the target, are recorded as variants of the row
they sit in.

A row's targets are the blocks it has at least `min_overlap` matched letters
in (or the whole of a block shorter than that). Smaller overlaps — a diff
artefact at a boundary — are dropped and reported, never silently kept.
"""
import collections
import difflib

from project import is_letter


def _letters(items):
    chars, owners, offsets = [], [], []
    for key, text in items:
        for i, ch in enumerate(text):
            if is_letter(ch):
                chars.append(ch)
                owners.append(key)
                offsets.append(i)
    return "".join(chars), owners, offsets


class Concordance:
    def __init__(self, target_blocks, copy_rows, min_overlap=3):
        self.order = [b for b, _ in target_blocks]
        self.pos = {b: i for i, b in enumerate(self.order)}
        self.block_text = dict(target_blocks)
        T, t_owner, t_off = _letters(target_blocks)
        C, c_owner, c_off = _letters(copy_rows)
        self.block_letters = collections.Counter(t_owner)
        votes = collections.defaultdict(collections.Counter)      # row -> block -> letters
        spans = collections.defaultdict(dict)                     # row -> block -> [start, end) in block text
        variants = collections.defaultdict(list)
        matched = replaced = copy_only = target_only = 0
        sm = difflib.SequenceMatcher(None, C, T, autojunk=False)

        def vote(i, j):
            r, b = c_owner[i], t_owner[j]
            votes[r][b] += 1
            s = spans[r].get(b)
            o = t_off[j]
            spans[r][b] = [o, o + 1] if s is None else [min(s[0], o), max(s[1], o + 1)]

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    vote(i1 + k, j1 + k)
                matched += i2 - i1
            elif tag == "replace":
                n, m = i2 - i1, j2 - j1
                for k in range(n):
                    vote(i1 + k, j1 + min(m - 1, k * m // n))
                replaced += n
                variants[c_owner[i1]].append({"copy": C[i1:i2], "target": T[j1:j2],
                                              "target_block": t_owner[j1]})
            elif tag == "delete":
                copy_only += i2 - i1
                variants[c_owner[i1]].append({"copy": C[i1:i2], "target": "",
                                              "target_block": t_owner[min(j1, len(t_owner) - 1)] if t_owner else None})
            elif tag == "insert":
                target_only += j2 - j1
                row = c_owner[i1 - 1] if i1 > 0 else (c_owner[0] if c_owner else None)
                variants[row].append({"copy": "", "target": T[j1:j2], "target_block": t_owner[j1]})
        self.stats = {"copy_letters": len(C), "target_letters": len(T), "matched": matched,
                      "replaced": replaced, "copy_only": copy_only, "target_only": target_only,
                      "ratio": round(sm.ratio(), 4)}
        self._rows = {}
        for r, _ in copy_rows:
            v = votes.get(r, collections.Counter())
            keep, dropped = [], []
            for b, n in v.items():
                if n >= min_overlap or n == self.block_letters[b]:
                    keep.append(b)
                else:
                    dropped.append({"block": b, "letters": n})
            keep.sort(key=self.pos.get)
            flags = []
            info = {}
            for b in keep:
                s = spans[r][b]
                full = v[b] == self.block_letters[b]
                info[b] = {"letters": v[b], "of": self.block_letters[b], "span": s, "whole": full}
            if len(keep) > 1:
                flags.append("spans_several_target_segments")
            if dropped:
                flags.append("tiny_overlap_dropped")
            self._rows[r] = {"targets": keep, "detail": info, "dropped": dropped,
                             "variants": variants.get(r, []), "flags": flags}

    def row(self, r):
        return self._rows.get(r, {"targets": [], "detail": {}, "dropped": [], "variants": [], "flags": []})
