# Parser — Root Text

Takes a source file and its linter output and writes the API payloads for the text, edition, table of contents and (for translations and commentaries) alignment.

Run `linter-root-text` first.

## What it does

1. **extract_text_input** — takes `text_input` from the lint JSON (or `resolved` from a `.lint.errors.json`), drops empty fields and contributors without an id, writes `text.json`
2. **build_edition** — builds the edition content and its segments with character spans from the body text (headings left out), writes `edition.json`
3. **build_toc** — builds a nested table of contents from the headings (headings are used only here), writes `toc.json`
4. **build_alignment** — for `file_type` `translation` or `commentary` only, links segments to the root text through transclusions, writes `alignment.json`

## Output

```
output/
  <stem>.text.json        # text_input payload
  <stem>.edition.json     # edition metadata, content and segments
  <stem>.toc.json         # nested TOC with character spans
  <stem>.alignment.json   # translation/commentary → root-text alignments
```

## Edition

- `metadata.type` comes from `edition_type` (default `critical`); `metadata.source` from `source` or `source_url`
- **Headings are not part of the edition.** They add no segment and no text to `content`; they are used only for the table of contents
- Blocks are separated by blank lines. Each content block becomes one segment, with one span per line, and its block ID (without `^`) as `reference`
- The block ID is removed from the text; lines are joined with no separator
- Blocks without a block ID are skipped with a warning (headings too); so are content blocks whose ID has more than 3 parts
- Transclusion lines (`![[...#^ref]]`) are left out of the content

### Segment types

The type of each segment comes from its block ID. The rows are checked from top to bottom; the first match wins.

| Block / ID | Type | Example |
|------------|------|---------|
| ID starts with `T` or `t` | `top_segment` | `^T-1` |
| Any part is an uppercase Roman numeral | `front_matter` | `^I-1`, `^2-I-3` |
| ID contains `<number>x<number>` | the file's default | `^1-2x3` |
| Last part is `U<number>` (unnumbered) | the file's default | `^1-U4` |
| Any part is lowercase letters only | `back_matter` | `^a-1` |
| Anything else | the file's default | `^1-1` |

The default is `verse`. It is `paragraph` when the file has `commentary_of`, or is a translation whose `root_text` is a commentary.

## Table of contents

- Built from the headings; the heading level (`#` count) sets the nesting
- Spans are character offsets into the edition `content`, which has no heading text. A section starts where the text after its heading starts, and ends where the next heading at the same or a higher level starts (or at the end of the content)
- A heading with no text before the next heading gets an empty span (`start` = `end`)
- Titles are keyed by `lang_tag` (default `en`); Tibetan titles in Wylie are converted to Unicode

## Alignment

Transclusions (`![[<root file>#^ref]]`) link segments of a translation or commentary to segments of the root text.

- `source_segment_reference` — segment in this file
- `target_segment_reference` — segment in the root text

Transclusions in blocks without a block ID are collected and attached to the next block that has one, together with any transclusions in that block. The list then starts over. A group of transclusions before one block therefore gives a many-to-one alignment.

Headings are never aligned, and waiting transclusions are dropped when a heading comes before the next content block. Transclusions that point to a heading in the `root_text` file are skipped with a warning, since headings are not segments.

## Requirements

```
pip install PyYAML pyewts
```

Python 3.8+.

## How to run

Run from the vault root (the folder that contains `1-SOURCES/` and `4-SYSTEM/`):

```bash
python3 4-SYSTEM\scripts\parser-root-text\parser.py "1-SOURCES\Text\<lang>-<title>.md" "4-SYSTEM\scripts\linter-root-text\output\<lang>-<title>.lint.json"
```

## Notes

- If the lint JSON has no alt titles or contributors, the parser warns and carries on
- When given a `.lint.errors.json`, the text payload is named `<stem>.lint.errors.text.json`
