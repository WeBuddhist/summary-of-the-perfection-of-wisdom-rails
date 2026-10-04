# Parser — Commentary

Takes a commentary file and its linter output and writes the API payloads for the text, edition, table of contents and alignment to the root text.

Forked from `parser-root-text`. Content segments default to **`paragraph`**, and `alignment.json` is always written. Run `linter-commentary` first.

## What it does

1. **extract_text_input** — takes `text_input` from the lint JSON (or `resolved` from a `.lint.errors.json`), drops empty fields and contributors without an id, writes `text.json` (includes `commentary_of` when set)
2. **build_edition** — builds the edition content and its segments with character spans from the body text (headings left out), writes `edition.json`
3. **build_toc** — builds a nested table of contents from the headings (headings are used only here), writes `toc.json`
4. **build_alignment** — links commentary segments to root-text segments through transclusions, writes `alignment.json`

The parser stops if the file's `file_type` is set to anything other than `commentary`.

## Output

```
output/
  <stem>/                  # one folder per source file, named after it
    <stem>.text.json        # text_input payload (with commentary_of)
    <stem>.edition.json     # edition metadata, content and segments
    <stem>.toc.json         # nested TOC with character spans
    <stem>.alignment.json   # commentary → root-text alignments
```

## Edition

Same as `parser-root-text` (see its README): headings add no segment and no text to `content` (they are used only for the TOC), one segment per content block, the block ID as `reference`, `metadata.source` from `source` or `source_url`, `metadata.type` from `edition_type` (default `critical`).

### Segment types

The shape of the block is checked first, then its ID:

| Test | Type | Example |
|------|------|---------|
| **Two or more lines with no empty line between them** | `verse` | a quoted verse, one line per unit |
| ID starts with `T` or `t` | `top_segment` | `^T-1` |
| Any part is an uppercase Roman numeral | `front_matter` | `^I-1`, `^2-I-3` |
| Any part is lowercase letters only | `back_matter` | `^a-1` |
| Anything else | `paragraph` | `^1-1`, `^1-2x3`, `^1-U4` |

**Verse wins over the ID.** A verse in the intro or the colophon is `verse`, not `front_matter` or `back_matter`: those mark where a block sits, and the block's shape says what it is. The ID types only blocks that are not verse.

An empty line inside a block — including a line holding only an invisible character such as a zero-width space — stops it being verse, and the parser warns about it. Such a block is usually two paragraphs that each need their own block ID, and Obsidian shows no gap there, so the warning is the only sign.

A block of prose that was hard-wrapped onto several lines without a blank line between them reads as verse to this rule. Keep a paragraph on one line.

## Alignment

Transclusions in the commentary (`![[1-SOURCES/Text/<lang>-<title>.md#^1-1]]`) say which root-text segment the commentary is discussing.

- `source_segment_reference` — segment in the commentary
- `target_segment_reference` — segment in the root text

A transclusion, or a group of consecutive transclusions, opens a scope. Transclusions written one after another count as one group even when blank lines separate them (keep them on separate lines — the parser joins them). Every commentary block that follows is aligned to those root-text segments until the **next transclusion group**, which replaces the scope.

Headings are ignored by the alignment: they are never aligned, and they neither close nor reset the scope — commentary under a new heading stays aligned to the last transclusion group until a new one appears. (Fork change in this vault; the 21-taras-rails original closed the scope at every heading.) Only blocks before the first transclusion in the file are left unaligned. Transclusions that point to a heading in the `root_text` file are skipped with a warning, since headings are not segments. Only transclusions of the `root_text` file give targets: a transclusion of any other file still opens a new scope, but an empty one, so the commentary under it stays unaligned instead of being paired with a same-numbered block of the root (fork change, 2026-09-26; used by `commentary-realign` for root passages the new root does not contain). Alignment can be many-to-one (several paragraphs on one verse) or many-to-many (several paragraphs on a group of verses).

## Requirements

```
pip install PyYAML pyewts
```

Python 3.8+.

## How to run

Run from the vault root (the folder that contains `1-SOURCES/` and `4-SYSTEM/`):

```bash
python3 4-SYSTEM\scripts\parser-commentary\parser.py "1-SOURCES\Commentaries\<lang>-<title>.md" "4-SYSTEM\scripts\linter-commentary\output\<lang>-<title>.lint.json"
```

## Notes

- If the lint JSON has no alt titles or contributors, the parser warns and carries on
- Blocks without a block ID are skipped with a warning; so are content blocks whose ID has more than 3 parts
- Inline formatting for interlinear glosses (`<small>…</small>`) is dropped from `content`: the gloss text stays, the tags do not. The source file is never changed.
- Non-breaking spaces (U+00A0) become ordinary spaces in `content`.
- Footnotes (`[^n]` markers and `[^n]: …` definition lines) are left out of the edition content, segmentation, TOC and alignment, the same way `<small>` tags are dropped: the backend has no footnote annotations yet. The source file is never changed.
- Headings deeper than level 6 (7+ `#`) are often written in bold, since Obsidian renders only six levels. For those, the `**` markers are dropped from the TOC title.
- Blocks that contain only transclusions are left out of the edition content; they feed alignment only
- TOC spans are offsets into the edition `content` (which has no heading text), built the same way as in `parser-root-text`
- Tibetan TOC titles in Wylie are converted to Unicode
