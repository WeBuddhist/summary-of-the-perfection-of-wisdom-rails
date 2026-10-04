#!/usr/bin/env python3
"""Pāda line breaks for the Sanskrit root, taken from the DSBC Devanāgarī
edition (0-INBOX/raw-data/dsbc-ratnagunasancayagatha/dsbc-402-pages.json, one
pāda per line), matched to our rows by letters. Writes
0-INBOX/temp/sa-pada-breaks.json: {row: [clause before which a line starts]}."""
import bisect, json, re, sys, collections
sys.path.insert(0, "4-SYSTEM/Skills/aligned-corpus-intake/scripts")
sys.path.insert(0, "4-SYSTEM/Skills/wiki-toc-import/scripts")
from md_export import read_rows
from project import letters, is_letter
from fetch_wiki_outline import _anchor_chain

# the text as the build produces it: editorial numbers removed (→ ॥), brackets removed (D10)
NUM = re.compile(r"॥\s*(?:[०-९]+[,.]\s*[०-९]+|[हल]्प्र्\s*[०-९]+)\s*॥")
rows = [(r["row"], NUM.sub("॥", r["text"]).replace("[", "").replace("]", ""))
        for r in read_rows("0-INBOX/raw-data/phakpadoepa-root-sa(sa-bo).md")]
pages = json.load(open("0-INBOX/raw-data/dsbc-ratnagunasancayagatha/dsbc-402-pages.json"))["pages"]
dsbc = "\n".join(p["text"] for p in pages)
# every DSBC line start, after a leading verse number ("२. ")
starts = [m.end() for m in re.finditer(r"(?m)^[०-९0-9]+\.\s*|^(?=\S)", dsbc)]
comm, spans = "", []
for r, t in rows:
    spans.append((len(comm), len(comm) + len(t), r, t))
    comm += t + "\n"
la, ia = letters(dsbc)
lb, ib = letters(comm)
chain = _anchor_chain(la, lb)
ca = [x for x, _ in chain]
out, stats = collections.defaultdict(list), collections.Counter()
for st in starts:
    h = bisect.bisect_left(ia, st)
    k = bisect.bisect_left(ca, h)
    if k >= len(chain):
        continue
    x, y = chain[k]
    while x > h and y > 0 and la[x - 1] == lb[y - 1] and (k == 0 or x - 1 >= chain[k - 1][0]):
        x, y = x - 1, y - 1
    if x != h and k > 0:
        # or walk forward from the previous anchor while the letters agree
        x0, y0 = chain[k - 1]
        while x0 < h and y0 < len(lb) and la[x0] == lb[y0]:
            x0, y0 = x0 + 1, y0 + 1
        if x0 == h:
            x, y = x0, y0
    gap = x - h
    if gap > 4:                                 # the line's opening letters are not in our text
        stats["unplaced"] += 1
        continue
    # a variant in the line's first letters: step back as many letters in our text
    yy = max(0, y - gap)
    pos = ib[yy]
    if gap:
        stats["variant start"] += 1
    s, e, r, t = next(sp for sp in spans if sp[0] <= pos <= sp[1])
    off = pos - s
    if not any(is_letter(c) for c in t[:off]):
        stats["row start"] += 1
        continue
    # snap to a word boundary: the cut must follow a space or a daṇḍa
    for d in (0, -1, 1, -2, 2, -3, 3):
        o = off + d
        if 0 < o < len(t) and (t[o - 1] in " ।" or t[o] == " ") and is_letter(t[o] if t[o] != " " else t[min(o + 1, len(t) - 1)]):
            off = o + (1 if t[o] == " " else 0)
            break
    else:
        stats["no boundary"] += 1
        continue
    n = 6
    while t.count(t[off:off + n]) > 1 and off + n < len(t):
        n += 3
    clause = t[off:off + n]
    if t.count(clause) != 1:
        stats["not unique"] += 1
        continue
    out[r].append(clause)
    stats["breaks"] += 1
# rows whose DSBC reading differs too much to place every pāda: breaks read off the metre by Claude
MANUAL = {145: ["सर्वान् अमात्य", "यावन्ति बुद्धक्रिय", "प्रज्ञाय पारमित सर्व"],
          146: ["सर्वं च आददति", "न च बोधिसत्त्व चलते", "सर्वांश्च आददति"],
          336: ["सत्त्वान शून्यवरधर्म"],
          344: ["दुःशील भोति"],
          373: ["लेखकप्रशस्तिः", "समाप्तम्"]}
for r, cl in MANUAL.items():
    t = dict(rows)[r]
    for c in cl:
        assert t.count(c) == 1, (r, c)
        if c not in out[r]:
            out[r].append(c)
            stats["manual"] += 1
for r in out:                                   # in text order, no duplicates
    t = dict((a, b) for a, b in rows)[r]
    out[r] = sorted(dict.fromkeys(out[r]), key=t.index)
json.dump({str(k): v for k, v in sorted(out.items())}, open("0-INBOX/temp/sa-pada-breaks.json", "w"), ensure_ascii=False, indent=1)
dist = collections.Counter(len(v) for v in out.values())
print(dict(stats), "rows:", len(out), "breaks per row:", sorted(dist.items()))
