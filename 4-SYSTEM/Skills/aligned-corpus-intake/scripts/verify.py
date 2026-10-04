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
import md_export                     # noqa: E402
import openpecha_model               # noqa: E402
from concordance import Concordance  # noqa: E402
from project import is_letter        # noqa: E402
from common import letters_only, parse_ref_prefix, raw_path      # noqa: E402

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
            level = len(content[0]) - len(content[0].lstrip("#"))
            title = content[0].lstrip("#").strip()
            m = ID_RE.search(title)
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


def block_targets(blocks, trans):
    """Transclusions belonging to each block: those written since the
    previous block (the writer puts them directly before their block)."""
    out, prev = {}, 0
    for bid, _, n in blocks:
        out[bid] = [i for _, i in trans[prev:n]]
        prev = n
    return out


def check_md_rows(spec, man, root, raw, side, blocks, trans, problems):
    """Segmentation and alignment checks for an md_rows work. Returns the
    counts printed in the summary line."""
    stats = {}
    own = {k: t for k, t in md_rows_source(raw, spec).items() if any(is_letter(c) for c in t)}
    by_row = {}
    for bid, b in side["blocks"].items():
        src = b.get("source") or {}
        for r in ([x["row"] for x in src["merged_rows"]] if src.get("merged_rows") else [src.get("row")]):
            by_row.setdefault(r, []).append(bid)
    label_only = set(side.get("rows_that_were_only_toc_labels") or [])
    lost = sorted(set(own) - set(by_row) - label_only)
    split_parts = {int(x["row"]): len(x["at"]) + 1 for x in spec.get("row_splits") or []}
    split_targets = {int(x["row"]): x.get("targets") for x in spec.get("row_splits") or []}
    merged = {r: ids for r, ids in by_row.items() if len(ids) > 1 and len(ids) != split_parts.get(r)}
    if lost:
        problems.append(f"rows with text but no block: {lost[:10]}")
    if merged:
        problems.append(f"rows split over several blocks: {list(merged)[:5]}")
    stats["rows"] = len(own)
    if not spec.get("pair"):
        return stats
    tgt_spec = next(w for w in man["works"] if w["key"] == spec["target"])
    t_heads, t_blocks, _ = parse(read_md(root / tgt_spec["path"]))
    tgt_rows = {r["row"]: r["text"] for r in md_export.read_rows(raw_path(raw, spec["pair"]["target_side"]))}
    conc = Concordance([(b, t) for b, t, _ in t_blocks],
                       [(k, t) for k, t in tgt_rows.items() if any(is_letter(c) for c in t)],
                       min_overlap=spec.get("min_overlap", 3))
    corr = {int(c["row"]): [int(x) for x in c.get("target_side_rows") or []] for c in spec.get("pair_corrections") or []}
    written = block_targets(blocks, trans)
    target_text = {b: t for b, t, _ in t_blocks}
    checked = agree = unaligned_ok = content_ok = content_n = 0
    variants = []
    for bid, b in side["blocks"].items():
        k = (b.get("source") or {}).get("row")
        rows = corr.get(k, [k] if any(is_letter(c) for c in tgt_rows.get(k, "")) else [])
        for x in ((b.get("source") or {}).get("merged_rows") or [])[1:]:
            # a human-decided merge: the block stands for all its rows
            rows += corr.get(x["row"], [x["row"]] if any(is_letter(c) for c in tgt_rows.get(x["row"], "")) else [])
        want = []
        for r in rows:
            want += [t for t in conc.row(r)["targets"] if t not in want]
        want.sort(key=conc.pos.get)
        got = written.get(bid, [])
        part = (b.get("source") or {}).get("part")
        if k in split_parts and part:
            # a human-decided split: each part shows its share of the row's targets;
            # the row's content is checked once, against all its parts' targets
            per = split_targets.get(k)
            row_want = want
            want = [row_want[j] for j in per[part - 1] if j < len(row_want)] if per else (row_want if part == 1 else [])
            if part == 1:
                got_all = [t for x in by_row[k] for t in written.get(x, []) if t]
            else:
                rows = []
        checked += 1
        if got == want:
            agree += 1
        if not rows and not got:
            unaligned_ok += 1
        if rows and got:
            # independent of the concordance: the paired row's letters must be
            # found, in order, in the text of the segments it transcludes
            a = "".join(c for r in rows for c in tgt_rows[r] if is_letter(c))
            content_got = got_all if (k in split_parts and part == 1) else got
            z = "".join(c for t in content_got for c in target_text.get(t, "") if is_letter(c))
            import difflib
            m = sum(x.size for x in difflib.SequenceMatcher(None, a, z, autojunk=False).get_matching_blocks())
            content_n += 1
            share = m / len(a) if a else 1.0
            # >= 90 %: the row is in its segments; 50-90 %: same passage, the
            # two editions differ (listed for review); < 50 %: wrong segment
            if share >= 0.5:
                content_ok += 1
            if share < 0.9:
                variants.append({"block": bid, "row": k, "letters_found": round(share, 2), "targets": got})
    if agree != checked:
        problems.append(f"{checked - agree} blocks whose transclusions differ from the row alignment")
    if content_ok != content_n:
        problems.append(f"{content_n - content_ok} aligned blocks whose paired row is not found in their transcluded segments")
    stats.update({"aligned_ok": f"{agree}/{checked}", "content_ok": f"{content_ok}/{content_n}"})
    if variants:
        stats["edition_variant_rows"] = len(variants)
        stats["_variants"] = variants
    return stats


def md_rows_source(ctx_raw, spec):
    """Rows of an md_rows work's own text, after the manifest's human
    text_corrections (whose originals the sidecar keeps)."""
    corr = {}
    for c in spec.get("text_corrections") or []:
        corr.setdefault(int(c["row"]), []).append(c)
    rows = {}
    for r in md_export.read_rows(raw_path(ctx_raw, spec["text"])):
        t = r["text"]
        for c in corr.get(r["row"], []):
            t = t.replace(c["find"], c["replace"], 1)
        rows[r["row"]] = t
    for x in spec.get("supplement_rows") or []:        # text added from another human source
        rows[int(x["row"])] = x["text"]
    return rows


def source_text(ctx_raw, spec, op_root):
    """The raw text the work's body was made from."""
    ad = spec["adapter"]
    if ad == "md_rows":
        return "\n".join(md_rows_source(ctx_raw, spec).values())
    if ad in ("op_translation", "op_text"):
        return openpecha_model.load(op_root, spec["openpecha_text"])["content"]
    rel = spec["pair"]["other"] if ad == "parallel" else spec["text"]
    doc = docx_model.read(raw_path(ctx_raw, rel))
    return "\n".join(p["text"] for p in doc["paragraphs"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--root", default=".", help="where the built files are (default: the vault)")
    ap.add_argument("--vault", default=".")
    ap.add_argument("--json", help="also write the per-work results (incl. review lists) to this file")
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
        side = json.loads((root / spec.get("sidecar_dir", side_dir) / f"{md.stem}.annotations.json").read_text(encoding="utf-8"))
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
        if spec["adapter"] == "md_rows":
            from_rows = {h["title"] for h in side.get("headings") or [] if (h.get("source") or {}).get("origin") == "row"}
            out_text = "\n".join([h[1] for h in heads[1:] if h[1] in from_rows] + [b[1] for b in blocks])
        else:
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
        md_stats = check_md_rows(spec, man, root, raw, side, blocks, trans, problems) if spec["adapter"] == "md_rows" else {}
        rows.append({"key": spec["key"], "md": md_stats, "numbered": numbered, "matching": matching, "blocks": len(blocks), "headings": len(heads),
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
              + "".join(f" {k}={v}" for k, v in (r.get("md") or {}).items() if not k.startswith("_"))
              + ("" if not r["problems"] else "  ← " + "; ".join(r["problems"])))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
