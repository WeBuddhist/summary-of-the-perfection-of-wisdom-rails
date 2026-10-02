#!/usr/bin/env python3
"""Build per-batch context bundles for verse-translate (Step 3).

For each verse in range, emits: the root text, an optional second-language
root, every translation witness you name, the rail's AI Overview, its key-term
table, and its divergence block.

Nothing about a particular text is baked in. The root text, the optional
auxiliary root, the witnesses and the rail path are all command-line
arguments; the rail sections are matched by their English heading names, which
every verse package carries (`## AI Overview`, `## Key Concepts`,
`## Divergences`) whether or not it also carries an original-language label in
parentheses after the name.

Run from the vault root.

    python3 extract_rails_context.py \\
        --range 2-25-2-50 --batch-size 6 --out $WORK/verse-translate \\
        --root 1-SOURCES/Text/<lang>-root-text.md \\
        --aux-root 1-SOURCES/Text/<lang2>-root-text.md \\
        --witness w1=1-SOURCES/Translations/<tgt>-<translator-a>.md \\
        --witness w2=Full Name=1-SOURCES/Translations/<tgt>-<translator-b>.md

Reports any verse whose rail is missing a section, and any witness whose verse
numbering is offset (see SKILL.md Rule 3).
"""
import argparse
import json
import os
import re
import sys

DEFAULT_RAIL = "2-RAILS/Verses/{vid}.md"

# Rail sections are matched on the ENGLISH heading name. A package heading may
# carry an original-language label in parentheses after that name
# (`## AI Overview (བསྡུས་དོན།)`), so each pattern allows an optional trailing
# parenthetical before the end of the heading line. Override any of these with
# --section-regex NAME=PATTERN.
DEFAULT_SECTIONS = {
    "overview": r"## AI Overview(?:\s*\([^)\n]*\))?\s*$.*?(?=\n---|\n## |\Z)",
    "key_terms": r"## Key Concepts(?:\s*\([^)\n]*\))?\s*$.*?(?=\n---|\n## |\Z)",
    "divergences": r"#{3,4} Divergences(?:\s*\([^)\n]*\))?\s*$.*?(?=\n---|\n#{2,4} |\Z)",
    # Fallback when a package carries no Key Concepts layer: the disambiguated
    # restatement is the next most useful thing for a translator.
    "restatement": r"## Disambiguated Restatement(?:\s*\([^)\n]*\))?\s*$.*?(?=\n---|\n## |\Z)",
}
SECTION_FLAGS = re.S | re.M


def parse_blocks(path):
    """Map block ID -> block text for a file using ^block-id suffixes."""
    if not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8").read()
    blocks, buf = {}, []
    for line in text.split("\n"):
        m = re.search(r"\^(\S+)\s*$", line)
        buf.append(re.sub(r"\^\S+\s*$", "", line))
        if m:
            blocks[m.group(1)] = "\n".join(x for x in buf if x.strip())
            buf = []
    return blocks


def strip_transclusions(s):
    return re.sub(r"!\[\[.*?\]\]\n?", "", s).strip()


def parse_range(spec):
    m = re.match(r"^(\d+)-(\d+)-(?:\1-)?(\d+)$", spec) or re.match(
        r"^(\d+)-(\d+)\s*(?:to|\.\.)\s*(?:\1-)?(\d+)$", spec
    )
    if not m:
        sys.exit(f"could not parse --range {spec!r}; use e.g. 2-25-2-50")
    ch, a, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if b < a:
        sys.exit(f"range end {b} precedes start {a}")
    return ch, a, b


def parse_witness(spec):
    """--witness id=path  or  --witness id=Display Name=path"""
    parts = spec.split("=")
    if len(parts) == 2:
        key, path = parts
        return key.strip(), key.strip(), path.strip()
    if len(parts) >= 3:
        key, label, path = parts[0], parts[1], "=".join(parts[2:])
        return key.strip(), label.strip(), path.strip()
    sys.exit(f"could not parse --witness {spec!r}; use id=path or id=Label=path")


def parse_section_override(spec):
    if "=" not in spec:
        sys.exit(f"could not parse --section-regex {spec!r}; use name=regex")
    name, pat = spec.split("=", 1)
    return name.strip(), pat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", required=True, help="e.g. 2-25-2-50")
    ap.add_argument("--batch-size", type=int, default=6)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--root",
        required=True,
        help="the root text this vault translates from, per the vault annex",
    )
    ap.add_argument(
        "--aux-root",
        help="optional second-language root / parallel edition, per the vault annex",
    )
    ap.add_argument(
        "--witness",
        action="append",
        default=[],
        metavar="id=path",
        help="a block-aligned existing translation; repeatable. "
        "Also accepts id=Display Name=path.",
    )
    ap.add_argument(
        "--rail-pattern",
        default=DEFAULT_RAIL,
        help=f"path template for the verse package, with {{vid}} (default: {DEFAULT_RAIL})",
    )
    ap.add_argument(
        "--section-regex",
        action="append",
        default=[],
        metavar="name=regex",
        help="override a rail section pattern. Names: "
        + ", ".join(sorted(DEFAULT_SECTIONS))
        + ". Repeatable.",
    )
    args = ap.parse_args()

    sections = dict(DEFAULT_SECTIONS)
    for spec in args.section_regex:
        name, pat = parse_section_override(spec)
        if name not in sections:
            print(f"note: --section-regex defines a new section {name!r}", file=sys.stderr)
        sections[name] = pat

    witnesses = [parse_witness(w) for w in args.witness]

    ch, first, last = parse_range(args.range)
    vids = [f"{ch}-{n}" for n in range(first, last + 1)]
    os.makedirs(args.out, exist_ok=True)

    roots = [("__root", "Root text", args.root)]
    if args.aux_root:
        roots.append(("__aux", "Second-language root", args.aux_root))

    src = {}
    for key, _label, path in roots + witnesses:
        src[key] = parse_blocks(path)

    problems = []
    for key, label, path in roots + witnesses:
        if src.get(key) is None:
            problems.append(f"MISSING FILE  {label}: {path}")
            continue
        absent = [v for v in vids if v not in src[key]]
        if absent:
            problems.append(
                f"OFFSET/GAP    {label}: missing {', '.join(absent)} "
                f"-- verify alignment before using as a witness (SKILL.md Rule 3)"
            )

    rails, rail_problems = {}, []
    for vid in vids:
        path = args.rail_pattern.format(vid=vid)
        if not os.path.exists(path):
            rail_problems.append(f"MISSING RAIL  {path}")
            rails[vid] = {}
            continue
        text = open(path, encoding="utf-8").read()
        got = {}
        for name, pat in sections.items():
            m = re.search(pat, text, SECTION_FLAGS)
            got[name] = m.group(0) if m else ""
        st = re.search(r"^status:\s*(\S+)", text, re.M)
        got["status"] = st.group(1) if st else "unknown"
        if not got.get("overview"):
            rail_problems.append(f"NO AI OVERVIEW {path}")
        if not got.get("key_terms"):
            rail_problems.append(
                f"NO KEY CONCEPTS {path} -- fall back to the Disambiguated Restatement"
            )
        if got["status"] != "complete":
            rail_problems.append(f"STATUS={got['status']:<9} {path}")
        rails[vid] = got

    batches = [vids[i : i + args.batch_size] for i in range(0, len(vids), args.batch_size)]
    for bi, batch in enumerate(batches, 1):
        out = [f"# CONTEXT BUNDLE — batch {bi}: verses {batch[0]} to {batch[-1]}\n"]
        for vid in batch:
            out.append("\n" + "=" * 70)
            out.append(f"## VERSE {vid}")
            out.append("=" * 70 + "\n")
            for key, label, _ in roots:
                blocks = src.get(key)
                out.append(
                    f"### {label}\n"
                    + strip_transclusions(blocks.get(vid, "—") if blocks else "—")
                )
            for key, label, _ in witnesses:
                if not src.get(key):
                    continue
                t = strip_transclusions(src[key].get(vid, ""))
                if t:
                    out.append(f"\n### Witness — {label}\n{t}")
            r = rails.get(vid, {})
            if r.get("overview"):
                out.append("\n### RAIL — AI Overview\n" + r["overview"])
            if r.get("key_terms"):
                out.append("\n### RAIL — Key Concepts\n" + r["key_terms"])
            elif r.get("restatement"):
                out.append(
                    "\n### RAIL — Disambiguated Restatement "
                    "(no Key Concepts layer in this rail)\n" + r["restatement"]
                )
            if r.get("divergences"):
                out.append("\n### RAIL — DIVERGENCES\n" + r["divergences"])
        path = os.path.join(args.out, f"batch{bi}.md")
        open(path, "w", encoding="utf-8").write("\n".join(out))
        print(f"wrote {path}  ({len(batch)} verses)")

    # aggregate key terms for Step 4
    rows = []
    for vid in vids:
        for line in rails.get(vid, {}).get("key_terms", "").split("\n"):
            m = re.match(r"\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|", line)
            if not m:
                m = re.match(r"-\s*\*\*(.+?)\*\*\s*[—-]\s*(.+?)\s*$", line)
            if m:
                rows.append({"verse": vid, "lemma": m.group(1).strip(), "gloss": m.group(2).strip()})
    tb = os.path.join(args.out, "key_terms.json")
    json.dump(rows, open(tb, "w"), ensure_ascii=False, indent=1)

    lemmas = {}
    for r in rows:
        lemmas.setdefault(r["lemma"], []).append(r)
    multi = {k: v for k, v in lemmas.items() if len({x["gloss"] for x in v}) > 1}

    print(f"\nverses            : {len(vids)} ({vids[0]}..{vids[-1]})")
    print(f"batches           : {len(batches)}")
    print(f"key-term rows     : {len(rows)} across {len(lemmas)} unique lemmas -> {tb}")
    print(f"lemmas w/ conflicting glosses (⚑ candidates): {len(multi)}")
    for k in list(multi)[:15]:
        print(f"    {k}  ({len(multi[k])} readings)")

    if problems or rail_problems:
        print("\n--- ATTENTION ---")
        for p in problems + rail_problems:
            print("  " + p)
    else:
        print("\nno source problems detected")


if __name__ == "__main__":
    main()
