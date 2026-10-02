#!/usr/bin/env python3
"""verify_claims.py — deterministic verification for a tree-guided-claims output file.

A tree-scaffolded claims run that is in fact an earlier pass re-bucketed under the tree
inherits that pass's transcription errors and its stale ``claim_count`` while looking like
an independent confirmation of them. ``commentary-claims`` Strategy 1 states five guards
against that; this script is the automated half of four of them (the fifth, "never
re-bucket", is a matter of how the extraction is *run* — see that skill's Procedure Step 4
— and is not something a static checker over the finished file can detect: a sufficiently
careful copy could still pass every check below).

Checks performed, in this order:

1. **Quote containment.** Every claim's ``**Original:**`` string (the legacy label
   ``**བོད་ཡིག:**`` is still accepted) is NFC-normalised and tsheg/shad-stripped, and must
   then be a literal substring of its cited
   block. Ellipsis-joined fragments (``…`` or ``...``) are tested individually — a claim
   quoting two non-contiguous phrases from the same block is legitimate; a claim quoting
   one real phrase and one invented one is not, and splitting is what catches the latter.
2. **`claim_count` recomputation.** The frontmatter's declared count must equal the number
   of regular (non-tension) claim headings actually present. Tension entries (⚑) are
   reported separately and are never folded into this count — the ``claims + tensions``
   double-counting seen in earlier runs does not recur here because the two are simply never
   added together.
3. **ID-collision scan.** Every claim ID must match the ``c-<decimal-with-dashes>-<n>``
   scheme, no two claims may share an ID, and no claim ID's de-prefixed form may coincide
   with any node's own decimal — the load-bearing property that keeps ``1.1`` from meaning
   both a claim and a section.
4. **`stated`-referent validation.** Every ``Referent: ... (stated)`` tag must name a
   Grounding-index entry whose verbatim name actually occurs inside *that claim's own*
   quoted original-language string — not merely somewhere in the source. This is the check
   that keeps the Grounding index verifiable.
5. **Citation sanity + coverage summary** (partial, reported as info, not hard issues): every
   cited block ID must exist in the source; a plain cited-vs-uncited block count is
   reported so a human can cross-check it against the file's own "Segments yielding no
   claim" prose — free-text range parsing is too fragile to gate on automatically, so this
   is a prompt for review, not a pass/fail claim.

Deliberately standalone: standard library only, so it runs with the Python already on the
system, independent of any pipeline venv — consistent with every other script bundled with
a skill.

Usage
-----
    python verify_claims.py CLAIMS.md --source SOURCE.md [--out REPORT.md]

Exit code = number of hard issues (checks 1-4). Check 5 never contributes to the exit code.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

# ------------------------------------------------------------------------------
# Tibetan normalisation — NFC + tsheg/shad-stripped, matching the comparison
# report's own method exactly (its Quotation fidelity section names this
# normalisation verbatim).
# ------------------------------------------------------------------------------

_DROP_CHARS = "།༎་༅༄༈"  # shad, nyis shad, tsheg, and the two head marks + ༈


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def strip_delims(s: str) -> str:
    """NFC, then every tsheg/shad/head-mark and all whitespace removed."""
    s = nfc(s)
    return "".join(ch for ch in s if ch not in _DROP_CHARS and not ch.isspace())


_ELLIPSIS_RE = re.compile(r"…|\.\.\.")


def split_ellipsis(quote: str) -> list[str]:
    """Split a claim's quotation on an ellipsis into independently-checkable fragments."""
    parts = [p.strip() for p in _ELLIPSIS_RE.split(quote)]
    return [p for p in parts if p]


# ------------------------------------------------------------------------------
# Frontmatter
# ------------------------------------------------------------------------------

_FRONT_MATTER_RE = re.compile(r"\A---\r?\n(?P<body>.*?)\r?\n---[ \t]*\r?\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Very small ``key: value`` reader — good enough for this file's flat fields.
    Returns ``(fields, body)``. Not a general YAML parser: list/mapping values are
    left as their raw string form, which is all the checks below need.
    """
    match = _FRONT_MATTER_RE.match(text.lstrip("﻿"))
    if not match:
        return {}, text
    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        m = re.match(r"^([A-Za-z_][\w]*):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields, text[match.end() :]


# ------------------------------------------------------------------------------
# Claims-file parsing
# ------------------------------------------------------------------------------

#: A node heading: `0`/`Z`/`z` or a pure decimal, never starting with `c-`.
_NODE_HEADING_RE = re.compile(r"^#{2,6}[ \t]+(0|[Zz]|\d+(?:\.\d+)*)\.?[ \t]")
#: A claim heading: `### c-1-2-1 <label>`.
_CLAIM_HEADING_RE = re.compile(r"^(#{2,6})[ \t]+(c-[\w-]+)[ \t]+(.*)$")
#: A tension entry: `⚑ **c-1-1-2 <label>**`.
_TENSION_HEADING_RE = re.compile(r"^⚑[ \t]+\*\*(c-[\w-]+)[ \t]+(.*?)\*\*[ \t]*$")

_FIELD_RE = re.compile(r"^\*\*([^*:]+):\*\*[ \t]*(.*)$")
_CITE_RE = re.compile(r"\(([^()]*?\.md#\^[\w-]+)\)")
_POSITION_RE = re.compile(r"^-\s*\*\*Position\s+(\d+):\*\*\s*(.*)$")

_GROUNDING_ROW_RE = re.compile(
    r"^\|\s*([A-Z]{3}-\d+)\s*\|\s*(.*?)\s*\|"  # ID | Name (verbatim) | ...rest
)


@dataclass
class Claim:
    claim_id: str
    heading_hashes: str
    label: str
    bo_text: str = ""
    referent_raw: str = ""
    cite: str = ""
    lineno: int = 0


@dataclass
class Tension:
    claim_id: str
    label: str
    positions: list[tuple[str, str]] = field(default_factory=list)  # (quote, cite)
    lineno: int = 0


@dataclass
class ParsedClaimsFile:
    node_decimals: list[str]
    claims: list[Claim]
    tensions: list[Tension]
    grounding: dict[str, str]  # ID -> verbatim name
    parse_issues: list[str]


def parse_claims_file(text: str) -> ParsedClaimsFile:
    lines = text.splitlines()
    node_decimals: list[str] = []
    claims: list[Claim] = []
    tensions: list[Tension] = []
    grounding: dict[str, str] = {}
    issues: list[str] = []

    current: Claim | None = None
    current_tension: Tension | None = None

    def flush() -> None:
        nonlocal current, current_tension
        if current is not None:
            claims.append(current)
            current = None
        if current_tension is not None:
            tensions.append(current_tension)
            current_tension = None

    for i, raw in enumerate(lines, start=1):
        node_m = _NODE_HEADING_RE.match(raw)
        if node_m:
            flush()
            node_decimals.append(node_m.group(1))
            continue

        claim_m = _CLAIM_HEADING_RE.match(raw)
        if claim_m:
            flush()
            current = Claim(
                claim_id=claim_m.group(2), heading_hashes=claim_m.group(1),
                label=claim_m.group(3).strip(), lineno=i,
            )
            continue

        tension_m = _TENSION_HEADING_RE.match(raw)
        if tension_m:
            flush()
            current_tension = Tension(claim_id=tension_m.group(1), label=tension_m.group(2), lineno=i)
            continue

        grounding_m = _GROUNDING_ROW_RE.match(raw.strip())
        if grounding_m and grounding_m.group(1) not in grounding:
            grounding[grounding_m.group(1)] = grounding_m.group(2)
            continue

        if current is not None:
            field_m = _FIELD_RE.match(raw.strip())
            if field_m:
                name, value = field_m.group(1).strip().lower(), field_m.group(2).strip()
                if name in ("original", "བོད་ཡིག", "bo", "bod yig"):
                    current.bo_text = value
                elif name == "referent":
                    current.referent_raw = value
                elif name == "cite":
                    cite_m = _CITE_RE.search(value)
                    current.cite = cite_m.group(1) if cite_m else value

        if current_tension is not None:
            pos_m = _POSITION_RE.match(raw.strip())
            if pos_m:
                cite_m = _CITE_RE.search(pos_m.group(2))
                cite = cite_m.group(1) if cite_m else ""
                quote = _CITE_RE.sub("", pos_m.group(2)).strip(" —-—")
                current_tension.positions.append((quote, cite))

    flush()
    return ParsedClaimsFile(node_decimals, claims, tensions, grounding, issues)


# ------------------------------------------------------------------------------
# Source-block resolution — a minimal, standalone block-ID parser.
# ------------------------------------------------------------------------------

_BLOCK_ID_RE = re.compile(r"\^([\w-]+)[ \t]*$")


def parse_source_blocks(source_text: str) -> dict[str, str]:
    """``{block_id: block_text}`` — blank-line-delimited blocks, ID from the
    trailing ``^id`` on the block's last non-blank line. A light reimplementation
    of ``stages.commentary.parse_blocks``'s block ID contract, deliberately not
    imported so this script has no dependency on the pipeline package.
    """
    front_body_split = re.match(r"\A---\r?\n.*?\r?\n---[ \t]*\r?\n", source_text, re.DOTALL)
    body = source_text[front_body_split.end():] if front_body_split else source_text

    blocks: dict[str, str] = {}
    current: list[str] = []
    for line in body.splitlines():
        if not line.strip():
            if current:
                _flush_block(current, blocks)
                current = []
            continue
        current.append(line)
    if current:
        _flush_block(current, blocks)
    return blocks


def _flush_block(lines: list[str], blocks: dict[str, str]) -> None:
    last = lines[-1]
    m = _BLOCK_ID_RE.search(last)
    if not m:
        return
    block_id = m.group(1)
    cleaned_last = _BLOCK_ID_RE.sub("", last).rstrip()
    text = "\n".join([*lines[:-1], cleaned_last])
    blocks[block_id] = text


def cite_to_block_id(cite: str) -> str | None:
    m = re.search(r"#\^([\w-]+)$", cite.strip())
    return m.group(1) if m else None


# ------------------------------------------------------------------------------
# Checks
# ------------------------------------------------------------------------------


def check_quote_containment(claims: list[Claim], tensions: list[Tension], blocks: dict[str, str]) -> list[str]:
    issues: list[str] = []

    def check_one(claim_id: str, quote: str, cite: str, sub_label: str = "") -> None:
        if not quote or not cite:
            issues.append(f"{claim_id}{sub_label}: missing quote or citation")
            return
        block_id = cite_to_block_id(cite)
        if block_id is None:
            issues.append(f"{claim_id}{sub_label}: citation {cite!r} has no parseable block ID")
            return
        block_text = blocks.get(block_id)
        if block_text is None:
            issues.append(f"{claim_id}{sub_label}: cited block ^{block_id} does not exist in the source")
            return
        block_key = strip_delims(block_text)
        for fragment in split_ellipsis(quote):
            if strip_delims(fragment) not in block_key:
                issues.append(
                    f"{claim_id}{sub_label}: quoted text not found in block ^{block_id} "
                    f"(fragment: {fragment[:40]!r})"
                )

    for c in claims:
        check_one(c.claim_id, c.bo_text, c.cite)
    for t in tensions:
        for idx, (quote, cite) in enumerate(t.positions, start=1):
            check_one(t.claim_id, quote, cite, sub_label=f" (position {idx})")

    return issues


def check_claim_count(declared: str | None, claims: list[Claim]) -> list[str]:
    if declared is None:
        return ["frontmatter has no claim_count field"]
    try:
        declared_n = int(re.match(r"\d+", declared.strip()).group(0))
    except (AttributeError, ValueError):
        return [f"claim_count {declared!r} is not a parseable integer"]
    actual = len(claims)
    if declared_n != actual:
        return [
            f"claim_count declares {declared_n} but {actual} regular (non-tension) claim "
            f"headings are actually present — recompute, never inherit (guard 2)"
        ]
    return []


_CLAIM_ID_RE = re.compile(r"^c-([a-z0-9-]+)-(\d+)$")


def check_id_collisions(claims: list[Claim], tensions: list[Tension], node_decimals: list[str]) -> list[str]:
    """Guard 1's automated half: every claim ID is well-formed and unique.

    Note what this deliberately does NOT flag: a claim ID's node-portion (``c-1-2-3-4``
    stripped of its trailing claim index -> ``1.2.3``) is *supposed* to equal its parent
    node's own decimal — that correspondence is what makes the ID traceable, not a
    collision. The actual property guard 1 protects is that a claim ID and a node
    identifier can never be *confused* when read out of context, and the mandatory
    ``c-`` prefix (present on every claim ID, absent from every node heading — see
    ``_NODE_HEADING_RE``) already guarantees that unconditionally. So the checks below
    are the two that can actually fail: a claim ID that skipped the ``c-`` prefix (a
    node number typo'd in as a claim heading, or vice versa) and two claims sharing one
    ID (a copy-paste that forgot to renumber).
    """
    issues: list[str] = []
    node_set = set(node_decimals)  # kept for the malformed-ID check below
    seen: dict[str, int] = {}

    all_ids = [(c.claim_id, c.lineno) for c in claims] + [(t.claim_id, t.lineno) for t in tensions]
    for claim_id, lineno in all_ids:
        if not _CLAIM_ID_RE.match(claim_id):
            issues.append(f"L{lineno}: claim ID {claim_id!r} does not match the c-<decimal-with-dashes>-<n> scheme")
        bare = claim_id[2:] if claim_id.startswith("c-") else claim_id
        if bare.replace("-", ".") in node_set:
            issues.append(
                f"L{lineno}: claim ID {claim_id!r} without its 'c-' prefix would read as node "
                f"decimal {bare.replace('-', '.')!r} verbatim (no trailing claim index) — check "
                "this was not written as a bare node reference by mistake"
            )
        if claim_id in seen:
            issues.append(f"L{lineno}: claim ID {claim_id!r} duplicates the one at L{seen[claim_id]}")
        else:
            seen[claim_id] = lineno
    return issues


_REFERENT_TOKEN_RE = re.compile(r"([A-Z]{3}-\d+)\s*\(([^)]*)\)")


def check_stated_referents(claims: list[Claim], grounding: dict[str, str]) -> list[str]:
    issues: list[str] = []
    for c in claims:
        if not c.referent_raw or c.referent_raw.strip() == "[unanchored]":
            continue
        claim_key = strip_delims(c.bo_text)
        for ref_id, basis in _REFERENT_TOKEN_RE.findall(c.referent_raw):
            if "stated" not in basis.lower():
                continue
            name = grounding.get(ref_id)
            if name is None:
                issues.append(f"{c.claim_id}: Referent cites {ref_id} (stated), which is not in the Grounding index")
                continue
            if strip_delims(name) not in claim_key:
                issues.append(
                    f"{c.claim_id}: Referent {ref_id} tagged (stated), but {name!r} does not occur "
                    f"in this claim's own quoted Tibetan (guard 4) — retag as (node)/(section-opener) "
                    f"or [unanchored] if the claim's own text genuinely does not name it"
                )
    return issues


def citation_coverage_summary(claims: list[Claim], tensions: list[Tension], blocks: dict[str, str]) -> list[str]:
    cited: set[str] = set()
    for c in claims:
        bid = cite_to_block_id(c.cite)
        if bid:
            cited.add(bid)
    for t in tensions:
        for _, cite in t.positions:
            bid = cite_to_block_id(cite)
            if bid:
                cited.add(bid)
    total = len(blocks)
    uncited = sorted(set(blocks) - cited, key=lambda x: (len(x), x))
    return [
        f"(info) {len(cited)} of {total} source blocks are cited by at least one claim; "
        f"{len(uncited)} uncited — cross-check these against the file's own 'Segments "
        f"yielding no claim' note rather than trusting this count alone "
        f"(sample uncited: {', '.join('^' + b for b in uncited[:12])}"
        + (", …" if len(uncited) > 12 else "") + ")"
    ]


# ------------------------------------------------------------------------------
# Orchestration
# ------------------------------------------------------------------------------


def verify_claims(claims_text: str, source_text: str) -> tuple[list[str], list[str]]:
    """Return ``(hard_issues, info_notes)``."""
    fields, body = parse_frontmatter(claims_text)
    parsed = parse_claims_file(body)
    blocks = parse_source_blocks(source_text)

    hard: list[str] = []
    hard += check_quote_containment(parsed.claims, parsed.tensions, blocks)
    hard += check_claim_count(fields.get("claim_count"), parsed.claims)
    hard += check_id_collisions(parsed.claims, parsed.tensions, parsed.node_decimals)
    hard += check_stated_referents(parsed.claims, parsed.grounding)

    info = citation_coverage_summary(parsed.claims, parsed.tensions, blocks)
    return hard, info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("claims_file", help="A tree-guided-claims output .md file")
    ap.add_argument("--source", required=True, help="The 1-SOURCES/Commentaries/*.md file it cites")
    ap.add_argument("--out", default=None, help="Write a markdown report here instead of printing")
    args = ap.parse_args()

    claims_text = Path(args.claims_file).read_text(encoding="utf-8")
    source_text = Path(args.source).read_text(encoding="utf-8")

    hard, info = verify_claims(claims_text, source_text)

    if args.out:
        lines = [f"- {x}" for x in hard] if hard else ["- (none)"]
        info_lines = [f"- {x}" for x in info] if info else ["- (none)"]
        Path(args.out).write_text(
            "# tree-guided-claims verification report\n\n"
            f"issues: {len(hard)}\n\n"
            "## Issues\n\n" + "\n".join(lines) + "\n\n"
            "## Notes (not counted as issues)\n\n" + "\n".join(info_lines) + "\n",
            encoding="utf-8",
        )
        print(f"{'✓' if not hard else '⚑'} {len(hard)} issue(s) → {args.out}")
    else:
        if not hard:
            print("✓ 0 issues.")
        else:
            print(f"{len(hard)} issue(s):")
            for x in hard:
                print(f"  - {x}")
        for x in info:
            print(f"  {x}")

    return len(hard)


if __name__ == "__main__":
    sys.exit(main())
