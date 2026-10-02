#!/usr/bin/env python3
"""
scaffold_verse_context.py — produce a structurally complete verse package
scaffold at `2-RAILS/Verses/<verse-id>.md`, leaving the LLM-heavy sections
(per-commentary paraphrase, Synthesis, Divergences, AI Overview, Disambiguated
Restatement) as TODO placeholders for a later fill step.

The schema written here is the one defined in `2-RAILS/About Rails.md` §5.
When this script and About Rails disagree, About Rails wins — fix the script.

Nothing about any particular text is baked in
--------------------------------------------
The root text(s) and the commentaries are **command-line arguments**. There are
no defaults: a run that names none is an error, not a run against somebody
else's text. Resolve them from `4-SYSTEM/Guidelines/vault-annex.md` for the
vault you are working in.

Heuristic for locating commentary blocks
----------------------------------------
Commentary files commonly embed a transclusion of each root-text block
immediately before the commentary that discusses it:

    ![[1-SOURCES/Text/<lang>-root-text.md#^1-1]]

    <commentary prose> ^1-2-1
    <commentary prose> ^1-2-2

    ![[1-SOURCES/Text/<lang>-root-text.md#^1-2]]
    ...

So the scaffold finds the transclusion marker for the target verse and collects
every `^<block-id>` it sees before the next transclusion marker.

**Grouped transclusions.** Some commentaries place several consecutive verse
transclusions together and comment on the whole group after the last one. The
scanner therefore advances past *all* consecutive transclusion lines following
the target, down to the first line of real prose, and collects from there. That
prose belongs to every verse in the run, so the same blocks are emitted for
each verse of the group.

If a commentary contains no transclusion marker for the target verse, its
subsection is emitted with an explanatory TODO so the fill step can decide
whether to drop the commentary from `commentary_coverage:` or to search by
content.

Usage
-----
    python scaffold_verse_context.py 1-1 \\
        --vault-root /path/to/vault \\
        --root-text "Sanskrit=1-SOURCES/Text/sk-root-text.md" \\
        --root-text "Tibetan=1-SOURCES/Text/bo-root-text.md" \\
        --commentary "commentary-a=1-SOURCES/Commentaries/bo-commentary-a.md" \\
        --commentary "commentary-b=1-SOURCES/Commentaries/bo-commentary-b.md"

    python scaffold_verse_context.py 1-1 ... --dry-run     # print to stdout
    python scaffold_verse_context.py 1-1 ... --overwrite   # replace an existing file
    python scaffold_verse_context.py 1-1 --validate        # check an existing package
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

OUTPUT_DIR = "2-RAILS/Verses"

# Block ID anchored anywhere on a line: ^583, ^1-1, ^1-2-3, ^I-4, ^a-2, ^1-0a-1.
BLOCK_ID_RE = re.compile(r"\^([0-9A-Za-z][0-9A-Za-z\-]*)")
# A line that is (only) an Obsidian transclusion of some block.
TRANSCLUSION_LINE_RE = re.compile(
    r"^\s*!\[\[[^\]]*?#\^([0-9A-Za-z][0-9A-Za-z\-]*)\s*\]\]\s*$"
)

# The optional layers About Rails §5 defines, in the order it lists them.
KNOWN_LAYERS = [
    "word-commentary",
    "word-disambiguation",
    "concepts",
    "stories",
    "metaphors",
    "quotations",
    "translation-notes",
    "practical-application",
    "structural-position",
    "morphology",
    "syntax",
    "semantic-gloss",
]

LAYER_HEADING = {
    "word-commentary": "Word Commentary",
    "word-disambiguation": "Word-by-word Disambiguation",
    "concepts": "Key Concepts",
    "stories": "Stories",
    "metaphors": "Metaphors",
    "quotations": "Quotations",
    "translation-notes": "Translation Notes",
    "practical-application": "Practical Application",
    "structural-position": "Structural Position",
    "morphology": "Morphology",
    "syntax": "Syntax",
    "semantic-gloss": "Semantic Gloss",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CommentaryMatch:
    commentary_id: str
    source_file: str
    block_ids: list[str] = field(default_factory=list)
    found_transclusion: bool = False
    grouped_with: list[str] = field(default_factory=list)


@dataclass
class RootText:
    label: str
    path: str


# ---------------------------------------------------------------------------
# Core extraction logic
# ---------------------------------------------------------------------------

def _read_file(path: Path) -> str:
    with path.open("r", encoding="utf-8") as fh:
        return fh.read()


def _verse_exists_in_source(source_text: str, verse_id: str) -> bool:
    return bool(re.search(rf"\^{re.escape(verse_id)}\b", source_text))


def _extract_commentary_blocks(commentary_text: str, verse_id: str) -> CommentaryMatch:
    """Find the transclusion of `verse_id`, walk past any consecutive
    transclusion lines that form a group with it, then collect every block ID
    up to the next transclusion line (or end of file)."""
    lines = commentary_text.split("\n")
    target = None
    for i, line in enumerate(lines):
        m = TRANSCLUSION_LINE_RE.match(line)
        if m and m.group(1) == verse_id:
            target = i
            break
    if target is None:
        return CommentaryMatch(commentary_id="", source_file="", block_ids=[],
                               found_transclusion=False)

    # Walk forward over the rest of the grouped run: further transclusion lines,
    # separated only by blank lines, belong to the same run.
    grouped: list[str] = []
    i = target + 1
    while i < len(lines):
        if lines[i].strip() == "":
            i += 1
            continue
        m = TRANSCLUSION_LINE_RE.match(lines[i])
        if m:
            grouped.append(m.group(1))
            i += 1
            continue
        break  # first line of real prose

    # Collect block IDs from here to the next transclusion line.
    seen: set[str] = set()
    ordered: list[str] = []
    while i < len(lines):
        if TRANSCLUSION_LINE_RE.match(lines[i]):
            break
        for m in BLOCK_ID_RE.finditer(lines[i]):
            bid = m.group(1)
            if bid == verse_id or bid in seen:
                continue
            seen.add(bid)
            ordered.append(bid)
        i += 1

    return CommentaryMatch(commentary_id="", source_file="", block_ids=ordered,
                           found_transclusion=True, grouped_with=grouped)


def gather_matches(
    vault_root: Path,
    verse_id: str,
    root_texts: list[RootText],
    commentaries: list[tuple[str, str]],
) -> list[CommentaryMatch]:
    found_in_any_root = False
    for rt in root_texts:
        source_path = vault_root / rt.path
        if not source_path.exists():
            print(f"warning: root text missing on disk: {source_path}", file=sys.stderr)
            continue
        if _verse_exists_in_source(_read_file(source_path), verse_id):
            found_in_any_root = True
    if not found_in_any_root:
        raise SystemExit(
            f"verse_id ^{verse_id} not found in any root text given with --root-text. "
            "Add the block to the root text first — never paste the verse into the rail."
        )

    matches: list[CommentaryMatch] = []
    for cid, rel in commentaries:
        commentary_path = vault_root / rel
        if not commentary_path.exists():
            print(f"warning: commentary file missing on disk: {commentary_path}; skipping",
                  file=sys.stderr)
            continue
        m = _extract_commentary_blocks(_read_file(commentary_path), verse_id)
        m.commentary_id = cid
        m.source_file = rel
        matches.append(m)
    return matches


# ---------------------------------------------------------------------------
# Scaffold rendering — the About Rails §5 schema
# ---------------------------------------------------------------------------

FRONTMATTER_TEMPLATE = """---
ref: {verse_id}
unit_type: single
unit_verses: [{verse_id}]
coarser_groupings: {{{groupings}}}
template_ref:
commentary_coverage: [{commentary_list}]
tradition_coverage: []
concepts_in_verse: []
concepts_in_commentary: []
stories: []
layer_order: [{layer_list}]
note:{note}
status: draft
---
"""


def render_scaffold(
    verse_id: str,
    root_texts: list[RootText],
    commentary_matches: list[CommentaryMatch],
    layers: list[str],
    language: str | None,
) -> str:
    commentary_list = ", ".join(m.commentary_id for m in commentary_matches)
    groupings = ", ".join(
        "{}: [{}]".format(m.commentary_id, ", ".join([verse_id] + m.grouped_with))
        for m in commentary_matches
        if m.grouped_with
    )
    note = ""
    if any(m.found_transclusion and not m.block_ids for m in commentary_matches):
        note = (
            " citation fallback may be needed — a commentary carries no block IDs of"
            " its own for this verse; see About Rails §5"
        )
    lang = language or "original language"

    out: list[str] = [
        FRONTMATTER_TEMPLATE.format(
            verse_id=verse_id,
            groupings=groupings,
            commentary_list=commentary_list,
            layer_list=", ".join(layers),
            note=note,
        ).rstrip("\n"),
        "",
        "## Source Text",
    ]
    for rt in root_texts:
        out.append("")
        out.append(f"### {rt.label}")
        out.append(f"![[{rt.path}#^{verse_id}]]")
    out.append("")
    out.append("**Variants**")
    out.append(
        "<!-- TODO: [Ed: cross-edition or cross-language variant, with citation] "
        "— or delete this block -->"
    )

    out.append("")
    out.append("## Traditional Interpretation")
    out.append("")
    out.append(
        "<!-- One ### subsection per commentary, in the tier order the vault annex "
        "declares. English paraphrase; every claim cited. -->"
    )
    for m in commentary_matches:
        out.append("")
        out.append(f"### {m.commentary_id}")
        if not m.found_transclusion:
            out.append(
                f"<!-- TODO: no transclusion marker for ^{verse_id} found in this "
                "commentary. If it nonetheless discusses this verse, locate the "
                "blocks by content and cite them here; otherwise drop this "
                "commentary from `commentary_coverage:`. -->"
            )
            continue
        if m.grouped_with:
            out.append(
                "<!-- Grouped transclusion: this commentary reads ^"
                + verse_id
                + " together with "
                + ", ".join("^" + g for g in m.grouped_with)
                + ". The prose below covers the whole group. -->"
            )
        if not m.block_ids:
            out.append(
                "<!-- TODO: transclusion marker found, but no block IDs followed it. "
                "Cite this material to the verse-transclusion anchor "
                f"[[{m.source_file}#^{verse_id}]] and record the fallback in the "
                "frontmatter `note:` field. -->"
            )
            continue
        out.append("<!-- TODO: English paraphrase of this commentary's reading. -->")
        out.append("<!-- Source blocks located for this verse: -->")
        for bid in m.block_ids:
            out.append(f"<!-- ({m.source_file}#^{bid}) -->")

    out.append("")
    out.append("### Synthesis")
    out.append(
        "<!-- TODO: what the sources agree on. Do not flatten disagreement here. -->"
    )
    out.append("")
    out.append("### Divergences")
    out.append(
        "<!-- TODO: only where commentaries genuinely disagree. Attribute each "
        "position, flag ⚑. Delete the heading if there are none. -->"
    )

    out.append("")
    out.append("## AI Overview")
    out.append("")
    out.append(
        "<!-- TODO: the reader-facing compression of Traditional Interpretation "
        f"above, in the {lang}. Headline reading in bold, then 3–6 key points, "
        "each with a trailing citation. Every citation here must already appear "
        "above — verify them one by one before saving. -->"
    )

    out.append("")
    out.append("## Disambiguated Restatement")
    out.append("")
    out.append(
        f"<!-- TODO: short rewrite of the verse in the {lang} with every ambiguity "
        "the synthesis resolved made explicit: referents fixed, senses chosen, "
        "compounds parsed. Cite the blocks that authorise each choice. -->"
    )

    if layers:
        out.append("")
        out.append(
            "<!-- ===== OPTIONAL LAYERS — delete any with no cited material ===== -->"
        )
        for layer in layers:
            out.append("")
            out.append(f"## {LAYER_HEADING.get(layer, layer)}")
            out.append(f"<!-- TODO: see About Rails §5 for what `{layer}` holds. -->")

    out.append("")
    out.append("## Concept Links")
    out.append("<!-- TODO: - [[2-RAILS/Local-Wiki/<term>_(<disambiguator>).md]] -->")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# Validation (for `--validate`)
# ---------------------------------------------------------------------------

REQUIRED_HEADINGS = [
    "## Source Text",
    "## Traditional Interpretation",
    "### Synthesis",
    "## AI Overview",
    "## Disambiguated Restatement",
    "## Concept Links",
]

REQUIRED_FRONTMATTER = [
    "ref:", "unit_type:", "unit_verses:", "commentary_coverage:",
    "tradition_coverage:", "concepts_in_verse:", "concepts_in_commentary:",
    "stories:", "layer_order:", "status:",
]


def validate_scaffold(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, [f"no such file: {path}"]
    text = _read_file(path)
    errors: list[str] = []
    for h in REQUIRED_HEADINGS:
        if h not in text:
            errors.append(f"missing required heading: {h!r}")
    for f in REQUIRED_FRONTMATTER:
        if f not in text:
            errors.append(f"frontmatter missing {f}")
    return (not errors), errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_pair(spec: str, flag: str) -> tuple[str, str]:
    if "=" not in spec:
        raise SystemExit(f"could not parse {flag} {spec!r}; use label=path")
    label, path = spec.split("=", 1)
    label, path = label.strip(), path.strip()
    if not label or not path:
        raise SystemExit(f"could not parse {flag} {spec!r}; use label=path")
    return label, path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("verse_id", help="block ID without caret, e.g. 1-1")

    script_dir = Path(__file__).resolve().parent
    default_root = script_dir.parents[3] if len(script_dir.parents) >= 4 else Path.cwd()

    p.add_argument(
        "--vault-root", "--root", dest="vault_root",
        default=os.environ.get("VAULT_ROOT", str(default_root)),
        help="vault root (defaults to $VAULT_ROOT or the detected vault root)",
    )
    p.add_argument(
        "--root-text", action="append", default=[], metavar="Label=path",
        help="a root text for the Source Text section, as 'Language label=path'. "
             "Repeatable — pass one per source language the vault has. "
             "No default: resolve from 4-SYSTEM/Guidelines/vault-annex.md.",
    )
    p.add_argument(
        "--commentary", action="append", default=[], metavar="id=path",
        help="a commentary, as 'registered-id=path'. Repeatable, in the vault "
             "annex's tier order. No default.",
    )
    p.add_argument(
        "--language", default=None,
        help="label for the original analysis language used in the TODO prompts "
             "(e.g. 'Tibetan'); defaults to the phrase 'original language'",
    )
    p.add_argument(
        "--layer", action="append", default=[], metavar="LAYER",
        help="an optional layer to scaffold, in order. One of: "
             + ", ".join(KNOWN_LAYERS) + ". Repeatable; default: none.",
    )
    p.add_argument("--out", default=None,
                   help="explicit output path; default "
                        "<vault-root>/2-RAILS/Verses/<verse-id>.md")
    p.add_argument("--dry-run", action="store_true", help="print to stdout, do not write")
    p.add_argument("--overwrite", action="store_true", help="overwrite an existing file")
    p.add_argument("--validate", action="store_true",
                   help="validate the existing output file rather than scaffolding")
    args = p.parse_args(argv)

    vault_root = Path(args.vault_root).resolve()
    output_path = (
        Path(args.out) if args.out is not None
        else vault_root / OUTPUT_DIR / f"{args.verse_id}.md"
    )

    if args.validate:
        ok, errs = validate_scaffold(output_path)
        if ok:
            print(f"ok: {output_path}")
            return 0
        for e in errs:
            print(f"error: {e}", file=sys.stderr)
        return 1

    if not args.root_text:
        raise SystemExit(
            "--root-text is required (repeatable, 'Language label=path'). "
            "There is no default root text: read the vault's root text(s) from "
            "4-SYSTEM/Guidelines/vault-annex.md and pass them explicitly."
        )
    if not args.commentary:
        raise SystemExit(
            "--commentary is required (repeatable, 'registered-id=path'). "
            "There is no default commentary set: read the registered commentary "
            "IDs from 4-SYSTEM/Guidelines/vault-annex.md and pass them in the "
            "annex's tier order."
        )

    root_texts = [RootText(*_parse_pair(s, "--root-text")) for s in args.root_text]
    commentaries = [_parse_pair(s, "--commentary") for s in args.commentary]

    unknown = [x for x in args.layer if x not in KNOWN_LAYERS]
    if unknown:
        raise SystemExit(
            f"unknown --layer value(s): {', '.join(unknown)}. Known layers: "
            + ", ".join(KNOWN_LAYERS)
        )

    matches = gather_matches(vault_root, args.verse_id, root_texts, commentaries)
    text = render_scaffold(args.verse_id, root_texts, matches, args.layer, args.language)

    if args.dry_run:
        print(text)
        return 0

    if output_path.exists() and not args.overwrite:
        print(
            f"refusing to overwrite existing file {output_path} "
            "(pass --overwrite to replace it)",
            file=sys.stderr,
        )
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    summary = ", ".join(f"{m.commentary_id}={len(m.block_ids)}" for m in matches)
    print(f"wrote {output_path} ({summary})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
