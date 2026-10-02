#!/usr/bin/env python3
"""
find_contested.py — identify terms with genuine rendering variation
===================================================================
Reads a consolidated bilingual glossary (glossary-combine output format) and
identifies terms where rendering variation is significant enough to warrant
an explicit termbase decision before zero-shot translation.

A term is contested when ALL of:
  - total attestations >= min_total (default 5)
  - second-most-frequent rendering has >= min_second attestations (default 2)
  - variation score = 1 - (max_freq / total_freq) >= min_variation (default 0.15)

Variation score: 0 = one rendering dominates completely; ~1 = all renderings equal.

Usage:
    python3 find_contested.py <consolidated_glossary.md> <output.md> [options]

Options:
    --min-total N     Minimum total attestations (default 5)
    --min-second N    Minimum second-rendering attestations (default 2)
    --min-variation F Minimum variation score (default 0.15)
    --top N           Only output the top N most contested terms (default: all)
"""

import argparse
import re
import sys
from pathlib import Path


def parse_consolidated_glossary(path):
    """Parse consolidated bilingual glossary into list of (keyword, renderings, wiki) tuples.
    renderings is [(rendering_str, freq_int), ...] sorted by freq desc.
    """
    entries = []
    current_keyword = None
    renderings = []
    wiki_link = ""
    in_table = False

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            # New keyword section
            if line.startswith("## "):
                if current_keyword and renderings:
                    entries.append((
                        current_keyword,
                        sorted(renderings, key=lambda x: -x[1]),
                        wiki_link,
                    ))
                current_keyword = line[3:].strip()
                renderings = []
                wiki_link = ""
                in_table = False
                continue

            # Table header row (contains "Rendering")
            if "| Rendering" in line or "| rendering" in line:
                in_table = True
                continue

            # Table separator row
            if re.match(r"\s*\|[-:\s|]+\|\s*$", line):
                continue

            # Table data row
            if in_table and line.startswith("|"):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if len(cols) >= 3:
                    rendering = cols[0]
                    # Total frequency is the third column
                    try:
                        freq = int(re.sub(r"[^\d]", "", cols[2]) or "0")
                    except (ValueError, IndexError):
                        freq = 0
                    # Wiki link from last column
                    if len(cols) >= 4 and cols[3] not in ("", "—"):
                        wiki_link = cols[3]
                    if rendering and rendering.lower() not in ("rendering", "—"):
                        renderings.append((rendering, freq))
                continue

            # Non-table, non-heading line resets table mode
            if line.strip() and not line.startswith("|") and not line.startswith("#"):
                in_table = False

    # Save last entry
    if current_keyword and renderings:
        entries.append((
            current_keyword,
            sorted(renderings, key=lambda x: -x[1]),
            wiki_link,
        ))

    return entries


def variation_score(renderings):
    """1 - (max_freq / total_freq). 0 = uncontested, approaching 1 = highly contested."""
    total = sum(f for _, f in renderings)
    if total == 0 or not renderings:
        return 0.0
    return 1.0 - renderings[0][1] / total


def filter_contested(entries, min_total=5, min_second=2, min_variation=0.15):
    """Return entries meeting all contestedness thresholds, sorted by score desc."""
    result = []
    for keyword, renderings, wiki in entries:
        total = sum(f for _, f in renderings)
        second = renderings[1][1] if len(renderings) >= 2 else 0
        score = variation_score(renderings)
        if total < min_total:
            continue
        if second < min_second:
            continue
        if score < min_variation:
            continue
        result.append((keyword, renderings, wiki, total, score))
    return sorted(result, key=lambda x: -x[4])


def write_output(contested, out_path, source_path):
    lines = [
        "---",
        f"source: {source_path}",
        f"total_contested: {len(contested)}",
        "---",
        "",
        "# Contested terms — termbase candidates",
        "",
        "Terms are ranked by variation score (1 − max_freq / total_freq).",
        "A score of 0 means one rendering dominates; 1 means renderings are equally split.",
        "These are the terms most likely to be rendered inconsistently in zero-shot translation.",
        "",
        "| Term | Top rendering | Alternatives | Total | Score |",
        "|------|---------------|--------------|-------|-------|",
    ]

    for keyword, renderings, wiki, total, score in contested:
        top = f"{renderings[0][0]} ({renderings[0][1]})" if renderings else "—"
        alts = ", ".join(f"{r} ({f})" for r, f in renderings[1:]) or "—"
        lines.append(f"| {keyword} | {top} | {alts} | {total} | {score:.2f} |")

    lines += ["", "---", "", "## Term details", ""]

    for keyword, renderings, wiki, total, score in contested:
        n = len(renderings)
        lines.append(f"### {keyword}")
        lines.append("")
        lines.append(
            f"**Variation score:** {score:.2f}  "
            f"**Total attestations:** {total}  "
            f"**Distinct renderings:** {n}"
        )
        if wiki and wiki != "—":
            lines.append(f"**Local-Wiki:** {wiki}")
        lines.append("")
        lines.append("| Rendering | Frequency | Share |")
        lines.append("|-----------|-----------|-------|")
        for r, f in renderings:
            share = f"{100 * f / total:.0f}%" if total else "—"
            lines.append(f"| {r} | {f} | {share} |")
        lines.append("")

    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(
        description="Identify contested terms in a consolidated bilingual glossary"
    )
    p.add_argument("glossary", help="Consolidated bilingual glossary (.md)")
    p.add_argument("output",   help="Output markdown file")
    p.add_argument("--min-total",     type=int,   default=5,    help="Min total attestations (default 5)")
    p.add_argument("--min-second",    type=int,   default=2,    help="Min second-rendering count (default 2)")
    p.add_argument("--min-variation", type=float, default=0.15, help="Min variation score (default 0.15)")
    p.add_argument("--top",           type=int,   default=None, help="Only output top N terms")
    args = p.parse_args()

    print(f"Reading: {args.glossary}", file=sys.stderr)
    entries = parse_consolidated_glossary(args.glossary)
    print(f"Keywords: {len(entries)}", file=sys.stderr)

    contested = filter_contested(
        entries,
        min_total=args.min_total,
        min_second=args.min_second,
        min_variation=args.min_variation,
    )
    print(f"Contested: {len(contested)}", file=sys.stderr)

    if args.top:
        contested = contested[:args.top]

    write_output(contested, args.output, args.glossary)
    print(f"Output: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
