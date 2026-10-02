---
name: format-tibetan-root-text
description: >
  Format a Tibetan root-text markdown file into clean, navigable verse with
  block IDs (^chapter-verse), chapter headings with ^N-0 anchors, and one
  stanza per paragraph with each verse-line on its own line, using the two
  bundled formatters (4-SYSTEM/Skills/format-tibetan-root-text/scripts/format_bca.py, colophon-driven;
  4-SYSTEM/Skills/format-tibetan-root-text/scripts/format_bo_root.py, table-driven). Reads a cleaned draft in
  0-INBOX/temp/ and writes a segmented one beside it.

  Trigger this skill for any Tibetan root-text formatting or segmentation —
  "format the Tibetan text", "segment the verses", "add chapter headings
  and block IDs to the bo file".

  Language scope: **Tibetan root texts only.** Not commentaries (use
  `format-commentary`), not other languages (use `format-root-text`).
---

# format-tibetan-root-text

Format a Tibetan root-text `.md` file into clean, navigable verse with block
IDs that support internal linking (e.g. `[[file#^1-23]]`), chapter headings
with `^N-0` TOC anchors, and one stanza per paragraph with each verse-line on
its own line.

Applicable texts: any structured Indian/Tibetan Buddhist root text in verse
form — the Bodhisattvacaryāvatāra (BCA), Abhisamayalaṃkāra,
Mūlamadhyamakakārikā, and similar. Examples throughout this document are
drawn from the Bodhicaryāvatāra (BCA) and are labelled accordingly; the
underlying procedure is generic.

## CRITICAL — heading anchor convention

Chapter headings use **`^N-0`**, not `^TOC-N`. This is the canonical
convention (`4-SYSTEM/Guidelines/annotation-conventions.md` §2, and the vault's `1-SOURCES/About
Sources.md` §5), and it is what a parser expects when it builds the
table-of-contents payload. A file annotated with `^TOC-N` anchors will parse
without a usable TOC. Every example and instruction below uses `^N-0`.

## Core Principles

Before processing any file, read `4-SYSTEM/Guidelines/annotation-conventions.md` — it is
the canonical spec for block IDs and heading hierarchy in this repo. The
block ID is the single most important linking mechanism for verse-level
references.

---

## Input File Structure

Raw source files typically contain:

| Pattern | Example | Action |
|---|---|---|
| Standalone verse number on its own line | `11` | **Remove** — used only to set block ID |
| Merged stanza (multiple verse-lines on one line) | `...། །...། །...།།` | **Split** at each `། །` separator |
| Mid-verse merged half-lines | `...ཞིག །ནམ་...` | **Split** at `[letter] །[letter]` junction (single shad directly followed by Tibetan syllable) |
| Already-split stanza (4 lines, one per line) | four lines ending with `། །` | Re-validate block ID |
| Chapter-end colophon appended to last verse | `...མཆི། །བྱང་ཆུབ་སེམས་དཔའི་...ལེའུ་དང་པོའོ།། །།` | Strip colophon, keep verse text |
| Blank lines (single or double) | — | Normalise to exactly one blank between stanzas |
| Markdown headings | `## 1. ལེའུ་...` | Pass through |
| Non-Tibetan prose | translator notes, etc. | Pass through verbatim |

---

## Tibetan Text Conventions

- **Verse-line separator**: `། །` (shad U+0F0D, space, shad). Each verse-line ends with this.
- **Mid-verse line break**: A single shad `།` preceded by a space and immediately followed by a Tibetan syllable (no space after the shad). Pattern: `[letter] །[letter]` — e.g. `ག །ན`, `གི །ས`, `གོ །བ`. This marks two half-verses merged onto one physical line and must be split with a newline. The first half retains its trailing ` །`; the second begins on a new line. The negative-lookbehind `(?<![།])` prevents matching the second shad inside a `། །` pair; the positive-lookahead `(?=[^\s།])` prevents matching a shad at end-of-line or before another shad.
- **Stanza**: typically 4 verse-lines (sometimes 2 or 8). One block ID per stanza.
- **Colophon marker**: chapter-end colophons carry a fixed closing formula specific to the text (for BCA: `འཇུག་པ་ལས`). Identify the text's own formula before running Step 1 of the Procedure below. The colophon also ends with `།། །།` (double-shad, space, double-shad).
- **Double-shad** `།།` appears **only** in chapter colophons, never in regular verse. Use this to detect colophon lines reliably.

---

## Output Format

### Chapter headings

```
## N. ORDINAL_LABEL। CHAPTER_NAME ^N-0
```

*Example (from the Bodhicaryāvatāra)* — extracted from BCA colophons:

```
## 1. ལེའུ་དང་པོ། བྱང་ཆུབ་སེམས་ཀྱི་ཕན་ཡོན་བཤད་པ། ^1-0
## 2. ལེའུ་གཉིས་པ། སྡིག་པ་བཤགས་པ། ^2-0
## 3. ལེའུ་གསུམ་པ། བྱང་ཆུབ་ཀྱི་སེམས་ཡོངས་སུ་བཟུང་བ། ^3-0
## 4. ལེའུ་བཞི་པ། བག་ཡོད་བསྟན་པ། ^4-0
## 5. ལེའུ་ལྔ་པ། ཤེས་བཞིན་བསྲུང་བར་བྱ་བ། ^5-0
## 6. ལེའུ་དྲུག་པ། བཟོད་པ་བསྟན་པ། ^6-0
## 7. ལེའུ་བདུན་པ། བརྩོན་འགྲུས་བསྟན་པ། ^7-0
## 8. ལེའུ་བརྒྱད་པ། བསམ་གཏན་བསྟན་པ། ^8-0
## 9. ལེའུ་དགུ་པ། ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ། ^9-0
## 10. ལེའུ་བཅུ་པ། བསྔོ་བ། ^10-0
```

### Block IDs

| Location | Format | Example |
|---|---|---|
| Chapter heading | `^N-0` | `## 1. ... ^1-0` |
| Intro section 0.1 stanzas | `^0-1-N` | `^0-1-1`, `^0-1-2` |
| Intro section 0.2 stanzas | `^0-2-N` | `^0-2-1`, `^0-2-3` |
| Chapter 1 stanzas | `^1-N` | `^1-1`, `^1-39` |
| Chapter 2 stanzas | `^2-N` | `^2-1`, `^2-67` |
| Chapter N stanzas | `^N-N` | `^9-175` |

The number after the hyphen on a content block is the **traditional verse
number** (chapter-relative). When the source file includes standalone verse
numbers, use those. When absent, increment by 1 from the last known verse
number.

### Formatted stanza (4-line example)

```
བདེ་གཤེགས་ཆོས་ཀྱི་སྐུ་མངའ་སྲས་བཅས་དང་། །
ཕྱག་འོས་ཀུན་ལའང་གུས་པར་ཕྱག་འཚལ་ཏེ། །
བདེ་གཤེགས་སྲས་ཀྱི་སྡོམ་ལ་འཇུག་པ་ནི། །
ལུང་བཞིན་མདོར་བསྡུས་ནས་ནི་བརྗོད་པར་བྱ། ། ^0-2-1
```

Block ID goes at the **end of the last line**, separated by a single space.

---

## Verse Numbering: Chapter Starts (Absolute → Chapter-Relative)

Every text has its own absolute-to-chapter-relative mapping, derived by
reading where each chapter's colophon falls in the source numbering.
Chapter-relative verse = absolute verse − chapter_start + 1.

*Example (from the Bodhicaryāvatāra)* — the BCA mapping:

| Chapter | Starts at abs. verse | Tibetan ordinal |
|---|---|---|
| 1 | 1 | དང་པོ |
| 2 | 40 | གཉིས་པ |
| 3 | 107 | གསུམ་པ |
| 4 | 142 | བཞི་པ |
| 5 | 192 | ལྔ་པ |
| 6 | 304 | དྲུག་པ |
| 7 | 444 | བདུན་པ |
| 8 | 523 | བརྒྱད་པ |
| 9 | 710 | དགུ་པ |
| 10 | 885 | བཅུ་པ |

---

## Automation: Python Scripts

Two bundled scripts implement this skill's mechanics; both live in
`scripts/` alongside this SKILL.md and both write `^N-0` chapter-heading
anchors (not `^TOC-N`):

- **`scripts/format_bca.py`** — colophon-driven formatter. Auto-detects
  chapter headings and boundaries by finding the text's own chapter-end
  colophon formula, so it needs no manual `CHAPTER_STARTS` table. Best when
  the source has that kind of embedded colophon (as BCA does).
- **`scripts/format_bo_root.py`** — table-driven formatter. Takes explicit
  `CHAPTER_STARTS` / `COLOPHONS` / `CHAPTER_HEADINGS` maps (edit the
  constants at the top of the script for a new text) and applies them
  mechanically. Best when the source has plain sequential verse numbers with
  no reliable colophon marker to detect automatically.

Both scripts take explicit `--input` / `--output` CLI arguments — run them
from the vault root:

```bash
python3 4-SYSTEM/Skills/format-tibetan-root-text/scripts/format_bca.py \
    --input 0-INBOX/temp/cleaned.md \
    --output 0-INBOX/temp/segmented.md

# or, for the table-driven variant:
python3 4-SYSTEM/Skills/format-tibetan-root-text/scripts/format_bo_root.py \
    --input 0-INBOX/temp/cleaned.md \
    --output 0-INBOX/temp/segmented.md
```

Neither script writes over its input; both read the cleaned draft and write a
new file, so the run is repeatable.

**What `format_bca.py` does (in order):**

1. Scans all lines, extracts chapter names from the colophon lines using
   regex, builds chapter headings with `^N-0` anchors.
2. Keeps the intro block (title, TOC, sections 0.1/0.2, and the Chapter 1
   heading) **unchanged** — this boundary is auto-detected or passed via
   `--intro-end` for a new text; see the script's `--help`.
3. State machine processes the rest of the file:
   - Blank lines → flush stanza buffer, output one blank (suppress doubles)
   - Number-only lines → record verse number, detect chapter transition, insert heading, discard line
   - Colophon lines → strip colophon text, flush last verse, advance chapter counter
   - Tibetan lines → accumulate into stanza buffer
   - Other lines → pass through verbatim
4. On stanza flush: combine buffer lines, clean old block IDs, split on `། །`, append new `^ch-rel` ID to last line.
5. Final pass removes consecutive blank lines.

### Key regex patterns used

```python
SHAD_PAIR        = '། །'                  # verse-line separator
TIBETAN_RANGE    = r'[ༀ-࿿]'              # any Tibetan character
DOUBLE_SHAD      = '།།'                  # colophon-only marker
MID_LINE_SHAD    = r'(?<![།]) །(?=[^\s།])'  # mid-verse break: space+shad not preceded by shad, followed by non-whitespace non-shad
```

*Example (from the Bodhicaryāvatāra)* — BCA's specific colophon markers:
```python
COLOPHON_MARKER  = 'འཇུག་པ་ལས'           # in every BCA colophon
FULL_COLOPHON    = 'བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ་ལས'  # full opener
```

**Ordinal extraction from colophon (BCA pattern):**
```python
re.search(r'(ལེའུ་)(?:སྟེ་)?(\S+?)འོ', col_text)
```

**Chapter name extraction (BCA pattern):**
```python
re.search(
    r'འཇུག་པ་ལས[་།\s]+([\s\S]+?)(?:་ཞེས་བྱ་བ་སྟེ་|་སྟེ་ལེའུ་|འི་ལེའུ་|་ལེའུ་)',
    col_text
)
```

**Clean old block IDs:**
```python
re.sub(r'\s*\^\S+\s*$', '', line)   # removes ^anything at end
re.sub(r'\s+\d+-\d+\s*$', '', line) # removes bare 1-2 style at end
```

---

## Colophon Stripping

Each chapter's last verse often has the colophon appended inline. Strip it by
finding the text's own colophon opener and cutting there.

*Example (from the Bodhicaryāvatāra)*:
```python
full_opener = 'བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ་ལས'
idx = line.find(full_opener)
if idx != -1:
    verse_text = line[:idx].rstrip()
```

Fallback to cutting at the shorter marker (for BCA: `འཇུག་པ་ལས`) if the full
opener is not found.

---

## Applying to a New Text

When formatting a different Tibetan root text:

1. **Find the colophon pattern** — Grep for the text's own chapter-end
   formula (for BCA: `འཇུག་པ་ལས`), or confirm the text has no such marker.
2. **Count chapters** — Read colophon lines to find ordinals and chapter
   names, or consult the text's own table of contents.
3. **Map verse numbers** — Find the first verse number of each chapter to
   build a `CHAPTER_STARTS` table.
4. **Decide which script fits** — `format_bca.py` if a reliable colophon
   marker exists to auto-detect chapters and boundaries; `format_bo_root.py`
   with an edited `CHAPTER_STARTS` / `COLOPHONS` / `CHAPTER_HEADINGS` table
   otherwise.
5. **Adjust the intro boundary** — how many lines of intro/preamble to
   preserve unchanged before per-chapter processing begins.

For texts without embedded verse numbers, rely on sequential increment
(`last_verse + 1`) for all IDs instead of reading numbers from the source.

*Example (from the Bodhicaryāvatāra) — BCA colophon line numbers*, for
reference when working from the original line-numbered source used to build
this skill:

| Chapter | File line (1-based) | Last verse number |
|---|---|---|
| 1 | 161 | 39 |
| 2 | 429 | 106 |
| 3 | 569 | 141 |
| 4 | 769 | 191 |
| 5 | 1217 | 303 |
| 6 | 1777 | 443 |
| 7 | 2093 | 522 |
| 8 | 2841 | 709 |
| 9 | 3541 | 884 |
| 10 | 3789 | (final) |

---

## Anchor Integration

- Block IDs (`^1-23`) allow direct linking: `[[bo-file#^1-23]]`
- Chapter anchors (`^1-0`, `^2-0`, …) allow TOC links: `[[bo-file#^1-0|Chapter 1]]`
- Do **not** use spaces in block IDs — only alphanumeric, hyphens, underscores.

---

## Common Pitfalls

| Issue | Cause | Fix |
|---|---|---|
| Block ID missing `^` | Old-style bare `1-2` at line end | `clean_existing_id()` handles this |
| Stanza not split | Lines without `། །` separator | Check source encoding (U+0F0D) |
| Colophon text appearing in output | `strip_colophon` missed it | Use the full opener string, not just the short marker |
| Double blank lines | Two blanks in source with no stanza between | Final cleanup pass removes these |
| Wrong chapter at boundary | `CHAPTER_STARTS` off by one | Re-verify by reading first number after each colophon |
| Verse numbers jumping (e.g. 3 → 11) | Source doesn't include all verses | Normal — gaps in IDs reflect the traditional verse count |
| Chapter heading uses `^TOC-N` instead of `^N-0` | Working from an outdated example or draft | Fix to `^N-0` — see the CRITICAL note at the top of this document |

---

## Note on the superseded `^TOC-N` anchors

An earlier version of this procedure taught `^TOC-N` chapter-heading anchors.
Every instance is corrected here to the canonical `^N-0` form
(`4-SYSTEM/Guidelines/annotation-conventions.md` §6). A parser expecting `^N-0` does not recognise a
`^TOC-N` anchor, so a file still carrying them silently ends up with no table
of contents and no error. Correct any you encounter before using the file.
