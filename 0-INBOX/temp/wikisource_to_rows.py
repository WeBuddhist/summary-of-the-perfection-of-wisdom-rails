#!/usr/bin/env python3
"""A commentary that exists only on Wikisource -> raw rows + a placed outline.

Reads 0-INBOX/raw-data/wikisource-<id>/pages.json (fetch_wikisource_text.py) and writes
  0-INBOX/raw-data/wikisource-<id>/<id>.md        one row per TOC section (numbered list,
                                                  the text between two headings, page line breaks
                                                  removed, page markup dropped, letters verbatim)
  0-INBOX/temp/wiki-toc-<id>/outline.placed.md    the Index's headings, each at the row it opens
--numbered   headings carry a decimal number ("1.2 …"): it is the path
--sequential headings carry none: numbered 1, 2, 3 … in order (a first heading equal to the
             work's title is left out)
"""
import argparse, hashlib, json, pathlib, re, sys, urllib.parse
import yaml
sys.path.insert(0, "4-SYSTEM/Skills/aligned-corpus-intake/scripts")
from project import is_letter

ap = argparse.ArgumentParser()
ap.add_argument("id")
ap.add_argument("--numbered", action="store_true")
ap.add_argument("--sequential", action="store_true")
ap.add_argument("--title", default="", help="the work's title (a heading equal to it is not a TOC node)")
a = ap.parse_args()
src = pathlib.Path(f"0-INBOX/raw-data/wikisource-{a.id}")
d = json.loads((src / "pages.json").read_text(encoding="utf-8"))

TOK = re.compile(r"<noinclude>.*?</noinclude>"
                 r"|(?P<eq>={2,})[ \t]*(?P<head>[^=\n]+?)[ \t]*(?P=eq)"
                 r"|\{\{[Hh]w[-/]bo\|(?P<hwa>[^|}]*)\|\|(?P<hwb>[^}]*)\}\}"
                 r"|\{\{[^{}]*\}\}|<[^>]+>", re.S)
pieces, heads = [], []          # text pieces; headings (index into pieces, label, page, revid)
for p in d["pages"]:
    c, last = p["content"], 0
    for m in TOK.finditer(c):
        pieces.append(c[last:m.start()])
        last = m.end()
        if m.group("head") is not None:
            lab = re.sub(r"<[^>]+>|\{\{[^{}]*\}\}|'''?", "", m.group("head")).strip().strip("\ufeff\u200b ")
            heads.append({"at": len(pieces), "label": lab, "page": p["title"].rsplit("/", 1)[1], "revid": p["revid"]})
        elif m.group("hwa") is not None:
            pieces.append(m.group("hwa") + m.group("hwb"))
    pieces.append(c[last:])

def clean(s):
    s = s.replace("\n", "")                      # pecha lines of the proofread page, not text breaks
    return re.sub(r"[ \t]+", " ", s).strip()

bounds = [h["at"] for h in heads] + [len(pieces)]
segments = [clean("".join(pieces[:bounds[0]]))]
for i, h in enumerate(heads):
    segments.append(clean("".join(pieces[h["at"]:bounds[i + 1]])))
letters = lambda s: "".join(ch for ch in s if is_letter(ch))
rows, nodes, n_seq = [], [], 0
pending = []
for i, seg in enumerate(segments):
    if i:
        h = heads[i - 1]
        lab = h["label"]
        if a.title and letters(lab) == letters(a.title):
            h = None                             # the title heading: not a TOC node
        else:
            if a.numbered:
                m = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$", lab)
                if not m:
                    sys.exit(f"heading without a number: {lab!r}")
                path, lab = m.group(1), m.group(2).strip()
            else:
                n_seq += 1
                path = str(n_seq)
            pending.append({"path": path, "labels": {"bo": lab}, "page": h["page"], "page_revid": h["revid"]})
    if any(is_letter(ch) for ch in seg):
        rows.append(seg)
        for nd in pending:
            nodes.append(dict(nd, start_row=str(len(rows)), clause=seg[:60]))
        pending = []
if pending:
    sys.exit(f"headings with no text after them: {[p['path'] for p in pending]}")
for s in rows:
    if re.match(r"^\d+\.", s) or "[" in s or "]" in s or "*" in s:
        print("WARNING row needs a look:", s[:60])
raw = src / f"{a.id}.md"
raw.write_text("".join(f"{i}. {s}\n" for i, s in enumerate(rows, 1)), encoding="utf-8")
index_page = d["index_page"]
fm = {"outline_id": a.id, "source": "wikisource.org", "index_page": index_page,
      "index_url": "https://wikisource.org/wiki/" + urllib.parse.quote(index_page.replace(" ", "_")),
      "index_revid": d["index_revid"], "retrieved": d["retrieved"], "placed_on": f"bo-{a.id}",
      "placed_on_text": f"0-INBOX/raw-data/wikisource-{a.id}/{a.id}.md",
      "placed_on_sha1": hashlib.sha1(raw.read_bytes()).hexdigest(),
      "placement": ("each row of the text file is the text between two of the Index's headings, so every heading "
                    "stands at the start of the row it opens (wikisource_to_rows.py)")}
out = pathlib.Path(f"0-INBOX/temp/wiki-toc-{a.id}")
out.mkdir(parents=True, exist_ok=True)
(out / "outline.placed.md").write_text(
    "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n\n```yaml\n"
    + yaml.safe_dump({"nodes": nodes}, allow_unicode=True, sort_keys=False) + "```\n\n```text\n"
    + yaml.safe_dump({"row_splits": []}, allow_unicode=True) + "```\n", encoding="utf-8")
sizes = sorted(len(letters(s)) for s in rows)
print(f"{a.id}: {len(rows)} rows, {len(nodes)} nodes; letters per row min {sizes[0]} median {sizes[len(sizes)//2]} max {sizes[-1]}")
