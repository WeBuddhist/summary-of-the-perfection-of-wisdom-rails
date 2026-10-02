#!/usr/bin/env python3
"""Add Obsidian block IDs to headings and body-text blocks in a note.

General-purpose, in-place version of the vault's block-id stamper. Unlike
the liturgy pipeline's block_ids.py (which reads from 0-INBOX and writes
prepared copies to 1-SOURCES/Text), this script works on any note you point
it at and writes the stamped result back to that same file.

It never touches the wording, order, or segmentation of the note. It only
appends an id to the last line of each heading and each body-text block
(a run of consecutive non-blank lines). If a note's structure isn't
correct yet (headings, blank-line breaks between blocks), fix that first —
this tool is purely mechanical.

ID scheme
---------
    # Heading                 ^0
    ## Heading                ^1-0        first H2 = section 1, "segment 0"
    <body text block>         ^1-1
    <body text block>         ^1-2
    ### Heading               ^1-1-0      first H3 under section 1
    <body text block>         ^1-3        body ids follow the H2, not the H3
    ## Heading                ^2-0        second H2 restarts the count
    <body text block>         ^2-1

Rules:
  - H1 gets ^0. There must be at most one H1, and if present it must be the
    first thing in the note.
  - H2 headings are numbered 1, 2, 3, ... in order: ^1-0, ^2-0, ^3-0, ...
  - H3 headings are numbered within their parent H2: ^1-1-0, ^1-2-0, ...
  - STRICT: body-text block ids are always based on the H2 section only —
    ^<h2>-<n>. The counter restarts at every H2 and runs straight through
    any H3 subheadings inside it (an H3 never resets it and never appears
    in a body-text id). Only H3 headings themselves carry three parts.
  - A flat note with no H2 anywhere numbers its body blocks straight
    through: ^1, ^2, ^3, ...
  - Body text sitting directly under an H1, before the first H2, is treated
    as section 0: ^0-1, ^0-2, ...
  - A note with no headings at all numbers straight through from ^1.
  - Headings deeper than H3, or an H3 before any H2, can't be expressed by
    this scheme — the file is aborted with a reason rather than guessed at.
  - Line endings (LF or CRLF) are preserved as found.

Guarantees
----------
Frontmatter (a leading YAML block delimited by `---` lines), if present, is
left byte-for-byte untouched. For the body, ``strip(stamp(x)) == x``
exactly — trailing whitespace, blank runs, and a missing final newline are
all preserved. ``stamp`` asserts this round-trip before every write, so a
bad parse can never corrupt a file.

Usage
-----
    add_block_id.py plan   <path>...              dry run, print the id plan
    add_block_id.py stamp  <path>...  [--restamp] write ids in place
    add_block_id.py strip  <path>...  [--in-place] remove block ids
    add_block_id.py lint   <path>...              check already-stamped notes

<path> may be a file or a directory (*.md, non-recursive).
"""

from __future__ import annotations

import argparse
import os
import re
import sys

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*)$")
ID_RE = re.compile(r" \^\d+(?:-\d+)*$")
FM_OPEN = "---\n"
FM_CLOSE = "\n---\n"


class Abort(Exception):
    """File rejected — reported, never worked around."""


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

class Unit:
    """One heading line, or one body-text block (a run of content lines).

    ``lines`` holds the raw source lines verbatim. ``idx`` is the index into
    the body's line list of this unit's LAST line — the line the id is
    appended to.
    """

    __slots__ = ("kind", "level", "lines", "idx", "bid")

    def __init__(self, kind, level, lines, idx):
        self.kind = kind          # "heading" | "block"
        self.level = level        # heading depth, or 0 for a body-text block
        self.lines = lines
        self.idx = idx
        self.bid = None           # assigned by assign_ids()


def split_frontmatter(raw: str):
    """Return (frontmatter, body). Frontmatter is returned verbatim.

    Frontmatter is optional for a general note — only split it off when the
    file actually starts with a '---' block.
    """
    if not raw.startswith(FM_OPEN):
        return "", raw
    close = raw.find(FM_CLOSE, len(FM_OPEN) - 1)
    if close == -1:
        raise Abort("frontmatter is opened with '---' but never closed")
    end = close + len(FM_CLOSE)
    return raw[:end], raw[end:]


def parse_body(body: str):
    """Tokenise the body into Units (headings and body-text blocks).

    A line is blank if it strips to empty. Blank runs and their exact
    contents are preserved; they are simply not part of any unit.
    """
    lines = body.split("\n")
    units, cur = [], []

    def flush(i):
        if cur:
            units.append(Unit("block", 0, list(cur), i - 1))
            cur.clear()

    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            flush(i)
            level = len(m.group(1))
            if level > 3:
                raise Abort(f"line {i + 1}: heading depth {level} (max ###)")
            if not m.group(2).strip():
                raise Abort(f"line {i + 1}: empty heading")
            units.append(Unit("heading", level, [line], i))
        elif not line.strip():
            flush(i)
        else:
            cur.append(line)
    flush(len(lines))
    return lines, units


def check_structure(units):
    """Reject anything the id scheme cannot express unambiguously."""
    h1 = [u for u in units if u.kind == "heading" and u.level == 1]
    if len(h1) > 1:
        raise Abort(f"{len(h1)} H1 headings (expected at most 1)")
    if h1 and units[0] is not h1[0]:
        raise Abort("H1 is not the first thing in the note")

    seen_h2 = False
    for u in units:
        if u.kind == "heading" and u.level == 2:
            seen_h2 = True
        elif u.kind == "heading" and u.level == 3 and not seen_h2:
            raise Abort("H3 appears before any H2")


def assign_ids(units):
    """Walk the units, assigning every one its block id."""
    check_structure(units)

    sectioned = any(u.kind == "heading" and u.level == 2 for u in units)
    h2 = h3 = 0            # section counters
    n = 0                  # body-block counter within the current scope

    for u in units:
        if u.kind == "heading" and u.level == 1:
            u.bid = "0"
            n = 0
        elif u.kind == "heading" and u.level == 2:
            h2 += 1
            h3 = 0
            n = 0
            u.bid = f"{h2}-0"
        elif u.kind == "heading" and u.level == 3:
            h3 += 1
            # STRICT RULE: an H3 does NOT reset the body counter — body-text
            # ids are always based on the enclosing H2.
            u.bid = f"{h2}-{h3}-0"
        else:
            n += 1
            if not sectioned:
                u.bid = str(n)              # flat note: ^1, ^2, ...
            elif h2 == 0:
                u.bid = f"0-{n}"            # body text before the first H2
            else:
                u.bid = f"{h2}-{n}"         # always H2-based, even under an H3
    return units


# --------------------------------------------------------------------------
# transforms
# --------------------------------------------------------------------------

def is_stamped(raw: str) -> bool:
    _, body = split_frontmatter(raw)
    return any(ID_RE.search(line) for line in body.split("\n"))


def stamp_text(raw: str, restamp: bool = False) -> str:
    if is_stamped(raw):
        if not restamp:
            raise Abort(
                "already carries block ids — pass --restamp to replace them"
            )
        raw = strip_text(raw)

    fm, body = split_frontmatter(raw)
    lines, units = parse_body(body)
    assign_ids(units)
    out = list(lines)
    for u in units:
        # Appended verbatim: a line that already ends in a space keeps it, so
        # stripping the id restores the original byte-for-byte.
        out[u.idx] = out[u.idx] + " ^" + u.bid
    return fm + "\n".join(out)


def strip_text(raw: str) -> str:
    """Inverse of stamp_text. Removes ' ^id' only from unit-final lines."""
    fm, body = split_frontmatter(raw)
    lines, units = parse_body(body)
    out = list(lines)
    for u in units:
        out[u.idx] = ID_RE.sub("", out[u.idx])
    return fm + "\n".join(out)


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

def describe(raw: str):
    """(kind, n_blocks, n_h2, n_h3, units) for a PRE-stamp file."""
    _, body = split_frontmatter(raw)
    _, units = parse_body(body)
    assign_ids(units)
    h1 = sum(1 for u in units if u.kind == "heading" and u.level == 1)
    h2 = sum(1 for u in units if u.kind == "heading" and u.level == 2)
    h3 = sum(1 for u in units if u.kind == "heading" and u.level == 3)
    blocks = sum(1 for u in units if u.kind == "block")
    if not h1 and not h2:
        kind = "headless"
    elif h3:
        kind = "h1+h2+h3"
    elif h2:
        kind = "h1+h2"
    else:
        kind = "flat"
    return kind, blocks, h2, h3, units


def lint_text(raw: str):
    """Structural checks on an ALREADY-stamped file. Returns list of problems."""
    _, body = split_frontmatter(raw)
    lines, units = parse_body(body)
    problems, seen = [], {}

    for u in units:
        last = u.lines[-1]
        m = ID_RE.search(last)
        if not m:
            problems.append(
                f"line {u.idx + 1}: {u.kind} carries no block id "
                f"({last.strip()[:40]!r})"
            )
            continue
        bid = m.group(0).strip()[1:]
        if bid in seen:
            problems.append(
                f"line {u.idx + 1}: duplicate id ^{bid} "
                f"(also line {seen[bid] + 1})"
            )
        seen[bid] = u.idx
        for j, line in enumerate(u.lines[:-1]):
            if ID_RE.search(line):
                problems.append(
                    f"line {u.idx - len(u.lines) + 1 + j + 1}: "
                    f"id stranded mid-block"
                )

    for i, line in enumerate(lines):
        if "^" in line and not ID_RE.search(line):
            if re.search(r"\S\^\d", line):
                problems.append(
                    f"line {i + 1}: '^' with no space before it — "
                    f"Obsidian will not read it as a block id"
                )
    return problems


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if f.endswith(".md"):
                    out.append(os.path.join(p, f))
        else:
            out.append(p)
    return out


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read().replace("\r\n", "\n")


def write(path, text):
    with open(path, encoding="utf-8", newline="") as fh:
        crlf = "\r\n" in fh.read()
    if crlf:
        text = text.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def cmd_plan(args):
    ok = bad = 0
    for path in collect(args.paths):
        name = os.path.basename(path)
        try:
            kind, blocks, h2, h3, units = describe(read(path))
        except Abort as exc:
            print(f"ABORT  {name}\n         {exc}")
            bad += 1
            continue
        ok += 1
        print(f"{kind:<10} blocks={blocks:<4} h2={h2:<3} h3={h3:<3} {name}")
        if args.verbose:
            for u in units:
                head = u.lines[0] if u.kind == "heading" else u.lines[-1]
                print(f"    ^{u.bid:<8} {u.kind:<7} {head.strip()[:56]}")
    print(f"\n{ok} parsed, {bad} aborted")
    return 1 if bad else 0


def cmd_stamp(args):
    ok = bad = 0
    for path in collect(args.paths):
        name = os.path.basename(path)
        raw = read(path)
        try:
            stamped = stamp_text(raw, restamp=args.restamp)
            # The contract, asserted before every single write.
            baseline = strip_text(raw) if is_stamped(raw) else raw
            if strip_text(stamped) != baseline:
                raise Abort("round-trip check failed — refusing to write")
        except Abort as exc:
            print(f"ABORT  {name}\n         {exc}")
            bad += 1
            continue
        if args.dry_run:
            print(f"would stamp  {name}")
        else:
            write(path, stamped)
            note = "  (ids replaced)" if is_stamped(raw) else ""
            print(f"ok     {name}{note}")
        ok += 1
    verb = "would be stamped" if args.dry_run else "stamped"
    print(f"\n{ok} {verb}, {bad} aborted")
    return 1 if bad else 0


def cmd_strip(args):
    for path in collect(args.paths):
        text = strip_text(read(path))
        if args.in_place:
            write(path, text)
            print(f"stripped {os.path.basename(path)}")
        else:
            sys.stdout.write(text)
    return 0


def cmd_lint(args):
    ok = bad = 0
    for path in collect(args.paths):
        name = os.path.basename(path)
        try:
            problems = lint_text(read(path))
        except Abort as exc:
            problems = [str(exc)]
        if problems:
            print(f"FAIL   {name}")
            for p in problems:
                print(f"         {p}")
            bad += 1
        else:
            ok += 1
            if args.verbose:
                print(f"OK     {name}")
    print(f"\n{ok} OK, {bad} FAILED")
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, help):
        p = sub.add_parser(name, help=help)
        p.add_argument("-v", "--verbose", action="store_true")
        return p

    p = add("plan", "dry run: classify and print the id plan")
    p.add_argument("paths", nargs="+")
    p.set_defaults(fn=cmd_plan)

    p = add("stamp", "add block ids in place")
    p.add_argument("paths", nargs="+")
    p.add_argument("--restamp", action="store_true",
                    help="replace ids on a note that already carries them")
    p.add_argument("--dry-run", action="store_true",
                    help="validate only, write nothing")
    p.set_defaults(fn=cmd_stamp)

    p = add("strip", "remove block ids")
    p.add_argument("paths", nargs="+")
    p.add_argument("--in-place", action="store_true")
    p.set_defaults(fn=cmd_strip)

    p = add("lint", "check an already-stamped note")
    p.add_argument("paths", nargs="+")
    p.set_defaults(fn=cmd_lint)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
