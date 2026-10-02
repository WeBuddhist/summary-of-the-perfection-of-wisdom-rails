#!/usr/bin/env python3
"""qc_tree_vs_source.py — deterministic QC for a sa-bcad TOC tree AGAINST THE SOURCE FILE.

Companion to ``qc_check_tree.py``, which checks a tree against the LLM's own
candidates+enumerations corpus. That check catches a tree the model built
inconsistently with what it itself extracted — but a tree can pass it cleanly while
still being wrong about the actual commentary, because "consistent with the
candidates" and "true of the source" are different claims. All three trees shipped
in this vault (``0-INBOX/temp/TOC-{gendun-gyatso,karma-maitri,lobsang-dawa}/
toc-tree-*.md``) reported ``issues_before: 0, issues_after: 0`` from
``qc_check_tree.py`` while carrying, between them: a top-level misattachment (twenty
homage children filed under "explaining the benefits" instead of "the praise
proper"), an unresolved ``[[?]]`` node with an obvious textual anchor one line away,
and seven collided line pointers on karma-maitri (the value ``130`` repeated four
times — the extractor lost its cursor). This script is the check that would have
caught those, because it reads the one thing the other checker cannot: the
commentary itself.

Checks performed, in this order:

1. **Line-pointer validity.** A node's ``[[N]]`` pointer must be an in-range 1-based
   line number in the source body. ``[[?]]`` is *always* reported as an issue — an
   unresolved anchor is not a clean tree, whatever the tree's own QC frontmatter
   claims.
2. **Title attestation near the pointer.** The node's title (leading Tibetan ordinal
   stripped) must appear, canonicalised, at or within a small window of its pointer.
   A title found only *elsewhere* in the file — not near where the tree says it is —
   is exactly the cursor-loss failure mode; a title found nowhere at all is a
   possible hallucination. Bare-ordinal titles ("དང་པོ་", "གཉིས་པ་") carry no
   distinguishing text and are not flagged either way — noted, not checked.
3. **Document-order monotonicity, and repeated-pointer collisions.** Pointers must
   not decrease as the tree is walked in its own document order. Siblings and a
   first child may legitimately share one line (a division and its first branch
   routinely open on the same sa-bcad sentence — ``sanitise_sections`` in
   ``stages/commentary.py`` encodes the same rule) but a later node pointing
   *above* an earlier one is a structural error. Separately, the same pointer
   value recurring three or more times across the whole tree is flagged even when
   it never causes a local decrease — a value repeating three or four times for
   three or four *different* titled subsections is the "extractor lost its
   cursor" signature named in the comparison report (karma-maitri's tree carries
   ``130`` four times), and a purely local monotonicity check can miss it
   whenever an intervening dip recovers before the next repeat. Two-way ties are
   not flagged here — a parent and its first child sharing one line is normal and
   common enough that flagging every pair would swamp the real signal.
4. **Sibling-count congruence** (heuristic, its own category). When a node's own
   announcing text — from its pointer up to its first child's pointer — contains a
   bare Tibetan cardinal-division phrase ("... ལ་གཉིས་...", "... ལ་གསུམ་སྟེ...", up
   to twenty-five), the count named is compared against how many children the tree
   actually gives that node. This is a prompt for human review, not a proof of
   error: Tibetan division phrasing is too varied to parse exhaustively, so it flags
   candidates rather than claiming completeness. Absence of a flag is not proof the
   assignment is right.

Tree line format expected (as ``toc-tree-extraction``'s Pass 3 actually emits it in
this vault): ``<indent>* <decimal> <title> [[<line-or-?>]]``, e.g.
``   * 1.2.20 ཉེར་གཅིག་ [[167]]``. A tree with no ``[[...]]`` suffix at all (the
merged top-level ``0-INBOX/toc-tree-<id>.md`` files sometimes lack it) still gets
checks 1 and 3 skipped for the pointerless nodes — there is nothing to check a
pointer against — and is reported as such rather than silently passing.

**The ``--source`` argument must be the exact file version the tree's line numbers
were computed against.** A tree built before a resegmentation will not validate
against the resegmented file, and that is not a bug in this script — it is what
"check against a source" means. This vault's own 2026-08-04 migration renumbered
every commentary; the three trees shipped before it were built against the
pre-migration body, backed up at ``0-INBOX/migration-backups/2026-08-04/``. Pass
that backup file when re-checking one of those three trees; pass the live
``1-SOURCES/`` file only for a tree built (or rebuilt) after the migration.

Usage
-----
    python qc_tree_vs_source.py TREE.md --source SOURCE.md [--out REPORT.md]

Exit code = total issue count across all four checks (0 = clean).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qc_check_tree as _qc  # noqa: E402  (sibling script; reuse its canonicalisation)

# ------------------------------------------------------------------------------
# Tree parsing — the real on-disk format, [[N]] / [[?]] pointers, not ^toc-N-N IDs.
# ------------------------------------------------------------------------------

_TREE_LINE_RE = re.compile(
    r"^(?P<indent>[ \t]*)\*[ \t]+(?P<dec>\d+(?:\.\d+)*)\.?[ \t]+"
    r"(?P<title>.*?)(?:[ \t]*\[\[(?P<pointer>\d+|\?)\]\])?[ \t]*$"
)

# Bare Tibetan cardinals 2-25 (no trailing པ), longest-first so e.g. བཅུ་གཅིག does
# not get shadowed by a later, shorter match. Used only for the division-phrase
# heuristic (check 4) — this is deliberately not exhaustive Tibetan numeral parsing.
_TIB_CARDINALS: tuple[tuple[str, int], ...] = (
    ("ཉེར་ལྔ", 25), ("ཉེར་བཞི", 24), ("ཉེར་གསུམ", 23), ("ཉེར་གཉིས", 22),
    ("ཉེར་གཅིག", 21), ("ཉི་ཤུ་རྩ་གཅིག", 21), ("ཉི་ཤུ", 20),
    ("བཅུ་དགུ", 19), ("བཅོ་བརྒྱད", 18), ("བཅུ་བདུན", 17), ("བཅུ་དྲུག", 16),
    ("བཅོ་ལྔ", 15), ("བཅུ་བཞི", 14), ("བཅུ་གསུམ", 13), ("བཅུ་གཉིས", 12),
    ("བཅུ་གཅིག", 11), ("བཅུ", 10), ("དགུ", 9), ("བརྒྱད", 8), ("བདུན", 7),
    ("དྲུག", 6), ("ལྔ", 5), ("བཞི", 4), ("གསུམ", 3), ("གཉིས", 2),
)

# A division phrase: "...ལ་<cardinal><boundary>" where boundary is a sentence
# terminator or one of the common closing particles (སྟེ, ཡིན, འོ, ལས). Loose by
# design — see the module docstring's honesty note on this check.
_DIVISION_RE = re.compile(
    "ལ" + _qc._TSHEG + "(" + "|".join(re.escape(w) for w, _ in _TIB_CARDINALS) + ")"
    r"(?:" + _qc._TSHEG + r"?(?:སྟེ|ཡིན|འོ|ལས)|[" + _qc._SHAD_CHARS + r"])"
)
_CARDINAL_VALUE = dict(_TIB_CARDINALS)


@dataclass
class Node:
    tree_lineno: int
    decimal: tuple[int, ...]
    title: str
    pointer: int | None  # None = no pointer syntax at all; -1 sentinel for "?"
    is_unresolved: bool  # True for [[?]]
    had_pointer_syntax: bool  # False if the line had no [[...]] at all


def parse_tree(tree_text: str) -> tuple[list[Node], list[str]]:
    """Parse tree bullet lines into ``Node``s, in file (= document) order.

    Returns ``(nodes, parse_issues)``. A line starting with ``*`` that does not
    match the expected grammar is a parse issue, not a silent skip.
    """
    nodes: list[Node] = []
    issues: list[str] = []
    for lineno, raw in enumerate(tree_text.splitlines(), start=1):
        if not re.match(r"^\s*\*\s", raw):
            continue
        m = _TREE_LINE_RE.match(raw)
        if not m:
            issues.append(f"L{lineno}: unparseable tree line: {raw.strip()}")
            continue
        dec = tuple(int(x) for x in m.group("dec").split("."))
        title = m.group("title").strip()
        pointer_raw = m.group("pointer")
        if pointer_raw is None:
            nodes.append(Node(lineno, dec, title, None, False, False))
        elif pointer_raw == "?":
            nodes.append(Node(lineno, dec, title, None, True, True))
        else:
            nodes.append(Node(lineno, dec, title, int(pointer_raw), False, True))
    return nodes, issues


# ------------------------------------------------------------------------------
# Source access
# ------------------------------------------------------------------------------


def source_body_lines(source_text: str) -> list[str]:
    """1-based-addressable lines of the RAW file, frontmatter included.

    This matches ``chunk_file.py`` exactly: it reads
    ``input_path.read_text(...).splitlines(...)`` with no frontmatter split at all,
    and every pass-1/pass-2 subagent is told to ``sed -n 'START,ENDp' <source>``
    against that same full-file numbering. A pointer ``[[N]]`` in a tree therefore
    means "full-file line N, frontmatter included" — stripping frontmatter here
    before counting would shift every single pointer by the frontmatter's own line
    count, which looks exactly like a tree that lost its cursor when it did not.
    """
    return source_text.splitlines()


# ------------------------------------------------------------------------------
# Check 1 + 2 — pointer validity and title attestation near the pointer
# ------------------------------------------------------------------------------

#: How many source lines on either side of a pointer still count as "near it" —
#: a title's own line and the division sentence that names it are rarely more
#: than a line or two apart once a segmenter has broken prose into blocks.
_NEAR_WINDOW = 3


def _title_has_signal(title: str) -> bool:
    """False for a title that, once its leading ordinal is stripped, is empty —
    a bare "the first"/"the second" placeholder has nothing to attest."""
    return bool(_qc._strip_leading_ordinal(title).strip(_qc._TSHEG + " "))


def check_pointers_and_titles(
    nodes: list[Node], source_lines: list[str], corpus_canon_whole: str
) -> tuple[list[str], int]:
    issues: list[str] = []
    skipped_ordinal_only = 0
    n = len(source_lines)

    # Per-line canonical form, cached once; check 2 searches a small window of
    # these rather than re-canonicalising the whole file per node.
    line_canon = [_qc._canon(line) for line in source_lines]

    for node in nodes:
        label = f"{'.'.join(map(str, node.decimal))} {node.title[:40]}"

        if node.is_unresolved:
            issues.append(f"{label}: pointer is [[?]] — unresolved anchor, not a clean tree")
            continue
        if node.pointer is None:
            if node.had_pointer_syntax is False and node.title:
                pass  # no pointer syntax in this tree file at all; nothing to bound-check
            continue

        if not (1 <= node.pointer <= n):
            issues.append(
                f"{label}: pointer [[{node.pointer}]] is out of range "
                f"(source body has {n} lines)"
            )
            continue

        if not _title_has_signal(node.title):
            skipped_ordinal_only += 1
            continue

        topic = _qc._canon(_qc._strip_leading_ordinal(node.title)) or _qc._canon(node.title)
        if not topic:
            continue

        lo = max(1, node.pointer - _NEAR_WINDOW)
        hi = min(n, node.pointer + _NEAR_WINDOW)
        near_text = "".join(line_canon[lo - 1 : hi])
        if topic in near_text:
            continue

        if topic in corpus_canon_whole:
            # Attested somewhere, just not near the claimed pointer — a possible
            # cursor-loss case, not necessarily a hallucination.
            first_hit_line = next(
                (i + 1 for i, lc in enumerate(line_canon) if topic in lc), None
            )
            issues.append(
                f"{label}: title attested in the source but not near pointer "
                f"[[{node.pointer}]] (found near line {first_hit_line}) — possible "
                f"cursor loss"
            )
            continue

        coverage = _qc._title_bigram_coverage(topic, corpus_canon_whole)
        if coverage < _qc.TITLE_COVERAGE_MIN:
            issues.append(
                f"{label}: title not attested anywhere in the source "
                f"(bigram coverage {coverage:.0%}) — possible hallucination"
            )

    if skipped_ordinal_only:
        issues.append(
            f"(info) {skipped_ordinal_only} node(s) have bare-ordinal-only titles "
            "(e.g. \"དང་པོ་\") with no distinguishing text — title attestation skipped "
            "for these, not counted as clean or as an issue"
        )
    return issues, len([i for i in issues if not i.startswith("(info)")])


# ------------------------------------------------------------------------------
# Check 3 — document-order monotonicity
# ------------------------------------------------------------------------------


#: A pointer value shared by this many nodes or more is the "lost cursor" signature,
#: regardless of whether any single step between them looks like a decrease.
_COLLISION_THRESHOLD = 3


def check_monotonic(nodes: list[Node]) -> list[str]:
    issues: list[str] = []
    pointed = [n for n in nodes if n.pointer is not None]

    for prev, cur in zip(pointed, pointed[1:]):
        if cur.pointer < prev.pointer:
            issues.append(
                f"{'.'.join(map(str, cur.decimal))} points to [[{cur.pointer}]], which "
                f"is BEFORE {'.'.join(map(str, prev.decimal))}'s [[{prev.pointer}]] — "
                "tree runs backwards at this point (document order requires "
                "non-decreasing pointers; ties are fine, a decrease is not)"
            )

    by_value: dict[int, list[Node]] = {}
    for node in pointed:
        by_value.setdefault(node.pointer, []).append(node)
    for value, group in sorted(by_value.items()):
        if len(group) >= _COLLISION_THRESHOLD:
            labels = ", ".join(".".join(map(str, n.decimal)) for n in group)
            issues.append(
                f"pointer [[{value}]] is shared by {len(group)} nodes ({labels}) — "
                "repeated-pointer collision, the extractor likely lost its cursor "
                "partway through this run"
            )
    return issues


# ------------------------------------------------------------------------------
# Check 4 — sibling-count congruence (heuristic)
# ------------------------------------------------------------------------------


def check_sibling_counts(nodes: list[Node], source_lines: list[str]) -> list[str]:
    issues: list[str] = []
    by_decimal = {n.decimal: n for n in nodes}
    children: dict[tuple[int, ...], list[Node]] = {}
    for node in nodes:
        if len(node.decimal) > 1:
            children.setdefault(node.decimal[:-1], []).append(node)

    for parent_dec, kids in children.items():
        parent = by_decimal.get(parent_dec)
        if parent is None or parent.pointer is None:
            continue
        first_child = min(
            (k for k in kids if k.pointer is not None), key=lambda k: k.pointer, default=None
        )
        end = (first_child.pointer - 1) if first_child is not None else parent.pointer
        start = parent.pointer
        if end < start:
            end = start
        window = "".join(source_lines[start - 1 : end])
        window_canon = _qc._canon(window)

        counts_named: set[int] = set()
        for m in _DIVISION_RE.finditer(window_canon):
            counts_named.add(_CARDINAL_VALUE[m.group(1)])
        if not counts_named:
            continue

        actual = len(kids)
        if actual not in counts_named:
            named = ", ".join(str(c) for c in sorted(counts_named))
            issues.append(
                f"{'.'.join(map(str, parent_dec))} '{parent.title[:30]}': announcing "
                f"text names a {named}-way division but the tree gives it {actual} "
                f"child(ren) — verify by hand which is right"
            )
    return issues


# ------------------------------------------------------------------------------
# Orchestration
# ------------------------------------------------------------------------------


def qc_tree_vs_source(tree_text: str, source_text: str) -> tuple[list[str], list[str]]:
    """Return ``(hard_issues, info_notes)``. Exit code should count only the former."""
    nodes, parse_issues = parse_tree(tree_text)
    source_lines = source_body_lines(source_text)
    corpus_canon_whole = _qc._canon("\n".join(source_lines))

    pointer_title_issues, _n = check_pointers_and_titles(nodes, source_lines, corpus_canon_whole)
    monotonic_issues = check_monotonic(nodes)
    sibling_issues = check_sibling_counts(nodes, source_lines)

    info = [i for i in pointer_title_issues if i.startswith("(info)")]
    hard = (
        parse_issues
        + [i for i in pointer_title_issues if not i.startswith("(info)")]
        + monotonic_issues
        + sibling_issues
    )
    return hard, info


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tree_file", help="TOC tree markdown file to check")
    ap.add_argument(
        "--source", required=True,
        help="The commentary/root-text file this tree's [[N]] pointers were built against",
    )
    ap.add_argument("--out", default=None, help="Write a markdown QC report here instead of printing")
    args = ap.parse_args()

    tree_text = Path(args.tree_file).read_text(encoding="utf-8")
    source_text = Path(args.source).read_text(encoding="utf-8")

    hard, info = qc_tree_vs_source(tree_text, source_text)

    if args.out:
        lines = [f"- {x}" for x in hard] if hard else ["- (none)"]
        info_lines = [f"- {x}" for x in info] if info else ["- (none)"]
        Path(args.out).write_text(
            "# TOC tree vs. source QC report\n\n"
            f"issues: {len(hard)}\n\n"
            "## Issues\n\n" + "\n".join(lines) + "\n\n"
            "## Notes (not counted as issues)\n\n" + "\n".join(info_lines) + "\n",
            encoding="utf-8",
        )
        print(f"{'✓' if not hard else '⚑'} {len(hard)} issue(s), {len(info)} note(s) → {args.out}")
    else:
        if not hard:
            print("✓ 0 issues — tree checks out against the source.")
        else:
            print(f"{len(hard)} issue(s):")
            for x in hard:
                print(f"  - {x}")
        for x in info:
            print(f"  {x}")

    return len(hard)


if __name__ == "__main__":
    sys.exit(main())
