#!/usr/bin/env python3
"""
toc_tree_ingest.py -- TOC Tree Ingestion Tool

Two modes:

  parse   Parse a toc-tree-*.md file into a JSON node list.
          Run once per commentary; output cached for all subsequent ingest runs.

          python3 toc_tree_ingest.py parse \
              --input  2-RAILS/TOC-Trees/X.md \
              --out    /tmp/toc-tree-X.json

  ingest  Insert ALL headings into the commentary in a single pass,
          processing ALL depth levels in document order.

          python3 toc_tree_ingest.py ingest \
              --tree        /tmp/toc-tree-X.json \
              --commentary  1-SOURCES/Commentaries/X.md

          (edits the canonical commentary file in 1-SOURCES/ IN PLACE — no
          .toc.md side-copy; take a backup first if you want an undo path)

Anchor strategy — LINE-NUMBER POINTERS, not text search:
  Each tree node carries a `[[N]]` (1-based source line number) or `[[?]]`
  (unresolved) pointer, written by toc-tree-extraction's Pass 3/4 and QC'd by
  qc_tree_vs_source.py against the exact source file the pointers were
  computed against. This script inserts each node's heading directly before
  its pointed-to line — no text matching, no cursor disambiguation, because
  the pointer already IS the disambiguated position.

  (An earlier version of this script searched for a `[[context text]]`
  snippet instead of a line number, with cursor-based disambiguation for
  repeated phrases. That anchor scheme never matched what
  qc_tree_vs_source.py actually validates — a `\\d+|\\?`-only pointer — so a
  tree QC'd clean by that checker could not be consumed by this script
  correctly. Retired 2026-08-04; line-number pointers are the one format
  both tools agree on.)

  Nodes are inserted in REVERSE document order (highest line number first),
  so each insertion never shifts the line numbers still-to-be-processed
  earlier nodes point at. A node whose pointer is `?` is reported not-found
  for manual placement, same as before.

Node JSON schema:
  {
    "decimal_id":  "1.3.2",        # dot-separated path
    "depth":       3,              # number of segments
    "label":       "Tibetan...",   # heading label text
    "block_id":    "^1-3-2-0",     # derived block id
    "pointer":     42,             # 1-based source line number, or null if unresolved
    "doc_order":   5               # 0-based position in toc-tree file
  }
"""

import argparse
import json
import re
import sys
from pathlib import Path
from collections import Counter


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HEADING_LEVELS = {1: "##", 2: "###", 3: "####", 4: "#####"}
DEFAULT_HEADING = "######"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def depth_to_heading(depth: int) -> str:
    return HEADING_LEVELS.get(depth, DEFAULT_HEADING)


def decimal_to_block_id(decimal_id: str) -> str:
    """'1.3.2.2' -> '^1-3-2-2-0'"""
    segments = decimal_id.rstrip(".").split(".")
    return "^" + "-".join(segments) + "-0"


_TREE_LINE_RE = re.compile(
    r"^(?P<indent>[ \t]*)\*[ \t]+(?P<dec>\d+(?:\.\d+)*)\.?[ \t]+"
    r"(?P<label>.*?)(?:[ \t]*\[\[(?P<pointer>\d+|\?)\]\])?[ \t]*$"
)


def parse_toc_line(line: str):
    """
    Parse one line of the toc-tree-*.md file.

    Expected format (any leading whitespace) — the same format
    qc_tree_vs_source.py validates:
        * N.N.N Tibetan label [[123]]
        * N.N.N Tibetan label [[?]]

    Returns a dict or None if the line is not a node line.
    """
    if not line.lstrip().startswith("* "):
        return None

    m = _TREE_LINE_RE.match(line.rstrip("\n"))
    if not m:
        return None

    raw_id = m.group("dec")
    label = m.group("label").strip()
    pointer_raw = m.group("pointer")
    pointer = None if pointer_raw in (None, "?") else int(pointer_raw)
    depth = raw_id.count(".") + 1

    return {
        "decimal_id": raw_id,
        "depth": depth,
        "label": label,
        "block_id": decimal_to_block_id(raw_id),
        "pointer": pointer,
    }


# ---------------------------------------------------------------------------
# parse command
# ---------------------------------------------------------------------------

def cmd_parse(args):
    input_path = Path(args.input)
    out_path = Path(args.out)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    nodes = []
    with input_path.open(encoding="utf-8") as fh:
        for line in fh:
            node = parse_toc_line(line)
            if node:
                node["doc_order"] = len(nodes)
                nodes.append(node)

    if not nodes:
        print("ERROR: no nodes parsed — check input file format.", file=sys.stderr)
        sys.exit(1)

    max_depth = max(n["depth"] for n in nodes)
    output = {
        "source":      str(input_path),
        "total_nodes": len(nodes),
        "max_depth":   max_depth,
        "nodes":       nodes,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, ensure_ascii=False, indent=2)

    print(f"Parsed {len(nodes)} nodes, max depth {max_depth}.")
    unresolved = sum(1 for n in nodes if n["pointer"] is None)
    if unresolved:
        print(f"  {unresolved} node(s) have no pointer ([[?]]) — will be not-found at ingest.")
    print(f"JSON cache written to: {out_path}")

    depth_counts = Counter(n["depth"] for n in nodes)
    for d in sorted(depth_counts):
        print(f"  depth {d:2d}: {depth_counts[d]} nodes")


# ---------------------------------------------------------------------------
# ingest command
# ---------------------------------------------------------------------------

def heading_line(node: dict) -> str:
    hashes = depth_to_heading(node["depth"])
    return f"{hashes} {node['label']} {node['block_id']}"


def cmd_ingest(args):
    tree_path = Path(args.tree)
    commentary_path = Path(args.commentary)

    if not tree_path.exists():
        print(f"ERROR: tree JSON not found: {tree_path}", file=sys.stderr)
        sys.exit(1)
    if not commentary_path.exists():
        print(f"ERROR: commentary file not found: {commentary_path}", file=sys.stderr)
        sys.exit(1)

    with tree_path.open(encoding="utf-8") as fh:
        tree_data = json.load(fh)

    all_nodes = sorted(tree_data["nodes"], key=lambda n: n["doc_order"])

    print(f"Ingesting {len(all_nodes)} nodes across {tree_data['max_depth']} depth levels.")
    print("Strategy: direct line-number insertion, reverse document order.\n")

    text = commentary_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    total_lines = len(lines)

    inserted = 0
    skipped_present = 0
    not_found = []  # (decimal_id, label, reason)

    # Reverse document order: inserting at a later line first means earlier
    # nodes' pointers (smaller line numbers) are never shifted by insertions
    # made for later nodes.
    for node in reversed(all_nodes):
        pointer = node["pointer"]
        block_id = node["block_id"]
        h_line = heading_line(node)

        if pointer is None:
            not_found.append((node["decimal_id"], node["label"], "unresolved pointer ([[?]] in toc-tree)"))
            continue

        if not (1 <= pointer <= total_lines):
            not_found.append((node["decimal_id"], node["label"],
                              f"pointer [[{pointer}]] out of range (file has {total_lines} lines)"))
            continue

        target_line_idx = pointer - 1  # 1-based pointer -> 0-based list index

        # Already-present check: look for block_id in the 1-3 lines before the target
        already = False
        for check_offset in (1, 2, 3):
            check_idx = target_line_idx - check_offset
            if check_idx >= 0 and block_id in lines[check_idx]:
                already = True
                break

        if already:
            skipped_present += 1
        else:
            lines.insert(target_line_idx, "\n")
            lines.insert(target_line_idx, h_line + "\n")
            inserted += 1

    commentary_path.write_text("".join(lines), encoding="utf-8")

    # --- Summary ---
    print("Summary")
    print(f"  Total nodes:           {len(all_nodes)}")
    print(f"  Inserted:              {inserted}")
    print(f"  Already present:       {skipped_present}")
    print(f"  Not found:             {len(not_found)}")

    if not_found:
        print("\nNOT FOUND — insert manually then re-run to confirm:")
        for decimal_id, label, reason in not_found:
            print(f"  [{decimal_id}] {label[:70]}")
            print(f"       {reason}")

    print(f"\nCommentary updated: {commentary_path}")

    if not_found:
        sys.exit(2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="TOC Tree Ingestion Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_parse = subparsers.add_parser("parse", help="Parse toc-tree-*.md to JSON")
    p_parse.add_argument("--input", required=True, help="Path to toc-tree-*.md")
    p_parse.add_argument("--out",   required=True, help="Output JSON path")

    p_ingest = subparsers.add_parser("ingest", help="Ingest all nodes into commentary")
    p_ingest.add_argument("--tree",        required=True, help="Path to JSON cache")
    p_ingest.add_argument("--commentary",  required=True, help="Path to commentary .md file")

    args = parser.parse_args()

    if args.command == "parse":
        cmd_parse(args)
    elif args.command == "ingest":
        cmd_ingest(args)


if __name__ == "__main__":
    main()
