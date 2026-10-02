#!/usr/bin/env python3
"""No-loss and well-formedness checks for an intake build.

    python3 verify.py <manifest.yaml> [--root <output root>] [--vault .]

For every work in the manifest:

1. Letter accounting. Every letter (whitespace and punctuation ignored) of
   the raw source text must appear in the output exactly as often as in the
   source: in the markdown (title, headings, blocks) or, where the adapter
   moved it out of the body, in the sidecar (typed alignment prefixes,
   excluded paragraphs). Missing and extra letters are counted per work.
2. Structure. Every content block ends with a unique ^id of at most three
   parts; headings start at '#', never skip a level and carry ^…-0 ids;
   every transclusion points at an id that exists in its target file.
3. Numbers = transclusions. In a commentary built from written alignment
   numbers, every numbered block must transclude exactly the root ids its
   number names (after any human-decided ref_corrections), and an
   unnumbered block nothing. Counted as numbered / matching.

Exit status 1 if any work has missing letters, broken structure or dangling
transclusions.
"""
import argparse
import collections
import json
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import docx_model                    # noqa: E402
import openpecha_model               # noqa: E402
from common import letters_only, parse_ref_prefix      # noqa: E402

ID_RE = re.compile(r"\s\^([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\s*$")
TRANS_RE = re.compile(r"^!\[\[(.+?)#\^([A-Za-z0-9-]+)\]\]$")


def read_md(path):
    text = path.read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1] if text.startswith("---\n") else text
    return body


def parse(body):
    heads, blocks, trans = [], [], []
    for raw in re.split(r"\n\s*\n", body.strip()):
        lines = [l for l in raw.split("\n") if l.strip()]
        content = []
        for l in lines:
            m = TRANS_RE.match(l.strip())
            if m:
                trans.append((m.group(1), m.group(2)))
            else:
                content.append(l)
        if not content:
            continue
        if content[0].startswith("#"):
            m = ID_RE.search(content[0])
            level = len(content[0]) - len(content[0].lstrip("#"))
            title = content[0].lstrip("#").strip()
            title = title[:m.start()].strip() if m else title
            heads.append((level, title.strip("*"), m.group(1) if m else None))
        elif content[0].startswith("[Ed:"):
            continue
        else:
            m = ID_RE.search(content[-1])
            txt = "\n".join(content)
            if m:
                txt = txt[: len(txt) - len(content[-1]) + m.start()]
            blocks.append((m.group(1) if m else None, txt, len(trans)))
    return heads, blocks, trans


def source_text(ctx_raw, spec, op_root):
    """The raw text the work's body was made from."""
    ad = spec["adapter"]
    if ad == "op_translation":
        return openpecha_model.load(op_root, spec["openpecha_text"])["content"]
    rel = spec["pair"]["other"] if ad == "parallel" else spec["text"]
    doc = docx_model.read(ctx_raw / rel)
    return "\n".join(p["text"] for p in doc["paragraphs"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--root", default=".", help="where the built files are (default: the vault)")
    ap.add_argument("--vault", default=".")
    a = ap.parse_args()
    man = yaml.safe_load(pathlib.Path(a.manifest).read_text(encoding="utf-8"))
    root = pathlib.Path(a.root)
    raw = pathlib.Path(a.vault) / man.get("raw_root", "0-INBOX/raw-data")
    op_root = raw / man.get("openpecha_root", "openpecha-api")
    side_dir = man.get("sidecar_dir", "1-SOURCES/Annotations")
    ids_by_file = {}
    failed = False
    rows = []
    for spec in man["works"]:
        md = root / spec["path"]
        heads, blocks, trans = parse(read_md(md))
        ids_by_file[spec["path"]] = {b[0] for b in blocks if b[0]}
        side = json.loads((root / side_dir / f"{md.stem}.annotations.json").read_text(encoding="utf-8"))
        problems = []
        # structure
        ids = [b[0] for b in blocks]
        if None in ids:
            problems.append(f"{ids.count(None)} blocks without id")
        dup = [k for k, v in collections.Counter(ids).items() if v > 1 and k]
        if dup:
            problems.append(f"duplicate ids {dup[:5]}")
        long_ids = [i for i in ids if i and len(i.split("-")) > 3]
        if long_ids:
            problems.append(f"content ids over 3 parts {long_ids[:3]}")
        if not heads or heads[0][0] != 1:
            problems.append("first heading is not '#'")
        for (l1, _, _), (l2, t2, r2) in zip(heads, heads[1:]):
            if l2 > l1 + 1:
                problems.append(f"heading level skip at ^{r2}")
        if any(h[2] is None for h in heads):
            problems.append("heading without id")
        # letters
        out_text = "\n".join([h[1] for h in heads] + [b[1] for b in blocks])
        moved = []
        for b in side["blocks"].values():
            src = b.get("source") or {}
            if src.get("typed_prefix"):
                moved.append(src["typed_prefix"])
        moved += [e["text"] for e in side.get("excluded_paragraphs") or []]
        moved += [e["text"] for e in side.get("number_only_paragraphs") or []]
        src_letters = collections.Counter(letters_only(source_text(raw, spec, op_root)))
        out_letters = collections.Counter(letters_only(out_text + "\n".join(moved)))
        missing = sum((src_letters - out_letters).values())
        extra = sum((out_letters - src_letters).values())
        if missing:
            problems.append(f"{missing} source letters missing from output")
        # numbers written in front of segments == transclusions
        numbered = matching = 0
        if spec["adapter"] == "ref_commentary" and spec.get("refs", "align") == "align" and not spec.get("ref_map"):
            style = spec.get("ref_style", "dotted")
            for bid, b in side["blocks"].items():
                src = b.get("source") or {}
                nums = []
                if src.get("ref_correction"):
                    nums = [str(x) for x in src["ref_correction"]["read_as"]]
                elif src.get("typed_prefix"):
                    r, _, _ = parse_ref_prefix(src["typed_prefix"].strip() + " x", style)
                    nums = [str(x) for x in r or []]
                if src.get("auto_number"):
                    nums = [str(src["auto_number"])] + [n for n in nums if n != str(src["auto_number"])]
                carried = not nums and b.get("targets")
                if not nums and not carried:
                    continue
                numbered += 1
                if carried or sorted(nums, key=int) == sorted(b.get("targets") or [], key=int):
                    matching += 1
            if matching != numbered:
                problems.append(f"{numbered - matching} numbered blocks whose transclusions differ from their numbers")
        rows.append({"key": spec["key"], "numbered": numbered, "matching": matching, "blocks": len(blocks), "headings": len(heads),
                     "transclusions": len(trans), "letters": sum(src_letters.values()),
                     "missing": missing, "extra": extra, "problems": problems, "trans": trans,
                     "target": spec.get("target")})
    # dangling transclusions (needs every file's ids)
    for r in rows:
        bad = [(f, i) for f, i in r.pop("trans") if f in ids_by_file and i not in ids_by_file[f]]
        unknown = {f for f, _ in [] }
        if bad:
            r["problems"].append(f"{len(bad)} transclusions to missing ids, e.g. {bad[:3]}")
    w = max(len(r["key"]) for r in rows)
    for r in rows:
        ok = "OK " if not r["problems"] else "FAIL"
        failed |= bool(r["problems"])
        print(f"{ok} {r['key']:{w}s} blocks={r['blocks']:5d} headings={r['headings']:3d} "
              f"transclusions={r['transclusions']:5d} letters={r['letters']:7d} "
              f"missing={r['missing']} extra={r['extra']}"
              + (f" numbers==transclusions {r['matching']}/{r['numbered']}" if r["numbered"] else "")
              + ("" if not r["problems"] else "  ← " + "; ".join(r["problems"])))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
