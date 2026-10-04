#!/usr/bin/env python3
"""From a scratch build, compute row_splits that let each numbered TOC-doc label
of comm-3/comm-4 stand exactly where the doc puts it (D7 applied to labels).
Writes 0-INBOX/temp/label-splits.json.  Usage: python3 label_splits.py <build root>"""
import json, pathlib, sys
sys.path.insert(0, "0-INBOX/temp")
sys.path.insert(0, "4-SYSTEM/Skills/aligned-corpus-intake/scripts")
import make_manifest as mm
from md_export import read_rows
root = pathlib.Path(sys.argv[1])
prev = mm.Prev(root)
out = {}
for key, i in (("bo-shasana-dibam-bedon-dronme", 3), ("bo-khenrab-jamyang-norbu-dronme", 4)):
    rows = {r["row"]: r["text"] for r in read_rows(f"0-INBOX/raw-data/phakpadoepa-comm-{i}(root-comm).md")}
    d = json.loads((root / f"1-SOURCES/Annotations/{key}.annotations.json").read_text(encoding="utf-8"))
    hs = d["headings"].values() if isinstance(d["headings"], dict) else d["headings"]
    cuts = {}
    for h in hs:
        s = h.get("source") or {}
        ir = s.get("inside_row")
        # a label within 15 letters of a row edge already stands at the right boundary
        if ir and ir["letters_before"] >= 15 and ir["letters_after"] >= 15:
            cuts.setdefault(s["row"], {})[s["offset_in_row"]] = h.get("path")
    tt = prev.block_texts(mm.ROOT_FILE)
    splits = []
    for r, offs in sorted(cuts.items()):
        t = rows[r]
        at = []
        for off in sorted(offs):
            n = 8
            while t.count(t[off:off + n]) > 1 and off + n < len(t):
                n += 4
            j = t.find("།", off + n - 1)
            c = t[off:j + 1] if j != -1 and j - off < 120 and t.count(t[off:j + 1]) == 1 else t[off:off + n]
            assert t.count(c) == 1 and len(c) >= 8, (key, r, off, c)
            at.append(c)
        tg = prev.row_targets(key, r)
        per = mm.part_targets(mm.split_parts(t, at), [tt.get(x, "") for x in tg])
        splits.append({"row": r, "at": at, "targets": per,
                       "reason": (f"The TOC doc puts {len(at)} heading label(s) "
                                  f"({', '.join(str(offs[o]) for o in sorted(offs))}) inside this alignment row; it is "
                                  "cut there so each heading stands where the doc has it. Each root segment the row "
                                  "transcludes is shown once, with the first part that quotes it (the first part if none does)."),
                       "decided_by": (f"{mm.STANDING}, D7 \"split the rows\" applied to the TOC doc's label positions; "
                                      "applied by Claude"),
                       "date": mm.TODAY})
    out[key] = splits
    print(key, len(splits), "rows split,", sum(len(s["at"]) for s in splits), "cuts")
pathlib.Path("0-INBOX/temp/label-splits.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
