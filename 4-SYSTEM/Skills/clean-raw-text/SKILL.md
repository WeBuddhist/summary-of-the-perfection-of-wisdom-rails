---
name: clean-raw-text
description: >
  Inspect a raw text for mechanical damage — page markers, running headers and
  footers, OCR index numbers, stray spacing, encoding artifacts — generate a targeted
  cleaning script for exactly what that file has, run it, and save the cleaned draft.

  Trigger on "clean this text", "clean the raw file", "strip the page markers", "remove
  the headers and footers", "this OCR is messy", "prepare this for formatting".

  The first step of any ingest. Removes artifacts only — never edits the text itself.
---

# Clean a raw text of mechanical artifacts

Works on any raw file — a root text, a translation, or a commentary. A
commentary usually carries more artifacts than a root text (running headers on
every page, folio markers, orphaned line fragments), but they are the same kinds
of artifact and the same procedure removes them.

**Profile the file before you change anything.** The first step is always a
read-only inspection pass that produces a profile of what is actually wrong with
*this* file, printed for a human to see. Nothing is edited until that profile
exists and the ambiguous items in it have been resolved. Skipping the profile is
how real content gets deleted as if it were a header.

**Generate a script for the file in front of you; do not reuse last file's script.**
Every scanned source is damaged in its own way — one has running headers every 40
lines, another has page numbers inline mid-sentence, a third has a footer that looks
like body text. A generic cleaner either misses most of it or eats real content.
Inspect first, then write the cleaner, then run it, and keep the script next to the
output so the cleaning is reproducible and reviewable.

**The line that must not be crossed.** This skill removes *artifacts of reproduction*
— things the scanner or typesetter added. It does not touch the text: no spelling
normalisation, no punctuation fixes, no "obvious" corrections. Those are editorial
acts, they belong downstream with an `[Ed: …]` note, and doing them here makes them
invisible.

When a file is dirty enough that you cannot tell artifact from text, stop and ask.

---

## What this removes

This skill removes the mechanical debris that OCR and PDF-to-text conversion
leave behind in a raw text file: repeated page headers and footers,
page-number markers, mid-word spaces inserted by PDF justification engines,
and non-breaking tsheg characters (for Tibetan text) that block correct
syllable detection. It does **not** restructure headings, add block IDs, or
fix broken syllables — those tasks belong to the format skills
(`format-root-text`, `format-tibetan-root-text`, `format-sanskrit-root-text`,
`format-commentary`). Run this skill first, then hand the cleaned draft to the
appropriate format skill.

The output is a draft in `0-INBOX/temp/<text-id>/` — the original file is never
overwritten and stays untouched as the ingest artifact.

---

### Inputs

| Input | Description | Example |
|---|---|---|
| `source_path` | Full path to the raw file | `0-INBOX/raw-data/<file>.md`, or the file under `1-SOURCES/` |
| `text-id` | Short identifier for this text; names the working folder and the generated script. Derive it from the filename if the caller does not give one. | `bo-spyod-jug-srung-grel` |

If `source_path` is missing, stop and ask before proceeding.

---

### Output

| File | What it is |
|---|---|
| `0-INBOX/temp/<text-id>/cleaned.md` | The cleaned draft |
| `0-INBOX/temp/<text-id>/clean-<text-id>.py` | The cleaner written for this file — kept so the run is reproducible and reviewable |
| `0-INBOX/temp/<text-id>/README.md` | Issue registry and runs log for this text (see below) |

The cleaned file is a plain Markdown draft containing only the text body — no
frontmatter, no block IDs. It is ready for the appropriate format skill (which
adds heading structure and block IDs) and subsequently `frontmatter`.

**The generated script goes in `0-INBOX/temp/<text-id>/`, never into `4-SYSTEM/Skills/`.**
`4-SYSTEM/` is not a write target for a skill run, and a one-off cleaner written
for one file is not a skill — it is an artifact of that file's ingest and it
belongs with that file's working copy.

---

### Output file format

The cleaned file has no special structure at this stage — it is a flat
Markdown text body. After cleaning, each logical paragraph should sit on its
own line with a blank line before and after it. No YAML frontmatter is added
by this skill.

```
<cleaned paragraph 1>

<cleaned paragraph 2>

<cleaned paragraph 3>
```

---

### Rules

1. **Never overwrite the source.** Output goes to `0-INBOX/temp/<text-id>/` only. Never write into `1-SOURCES/` or `4-SYSTEM/`.
2. **Do not interpret text.** Do not fix spelling, do not paraphrase, do not add or remove content beyond the mechanical issues listed in the Procedure.
3. **Preserve all verse lines.** Verse stanzas must not be collapsed into prose.
4. **Profile first, and report it.** Emit the profile JSON to the conversation before any script is written or run, so a human can verify what will be changed.
5. **Do not mark the output `status: complete`.** A human contributor reviews a cleaned draft before it is promoted further.
6. **If a repeated line is ambiguous** (appears many times but may be substantive), flag it in the profile and ask before removing it.
7. **Non-breaking tshegs (U+0F0C ༌), for Tibetan text,** are always replaced with the standard inter-syllable tsheg (U+0F0B ་). This is never ambiguous.
8. **Extra mid-word spaces** (a space between two script characters where no sentence boundary exists) are removed — the space is deleted, not replaced.
9. **Orphaned line fragments, for Tibetan text.** A line that does not end in a sentence-closing shad (`། །` or `།།`) has been broken mid-sentence by the typesetter; if the following line is a short orphaned fragment, join the two with a single space. Do not apply this to verse lines, and do not apply the shad test to a non-Tibetan script — work out that script's own sentence-closing mark first.
10. **Record what you found.** Every run appends to `0-INBOX/temp/<text-id>/README.md` (see *Issue registry*).

---

### Procedure

#### Step 1 — Inspect: profile the source file

Read the source file in chunks (the file may exceed a single-read limit — use
`offset` and `limit`). Build a **profile JSON** containing:

```json
{
  "source_path": "<path>",
  "total_lines": <N>,
  "issues": {
    "page_markers": {
      "pattern": "^\\s*-\\d+-\\s*$",
      "count": <N>,
      "examples": ["line 18: '-1-'", "line 41: '-2-'"]
    },
    "running_headers": {
      "description": "Lines that repeat verbatim more than 5 times",
      "count": <N>,
      "items": [["<line text>", <occurrence_count>]]
    },
    "mid_word_spaces": {
      "description": "Space between two script characters that should be one word",
      "count": <N>,
      "examples": ["line 6: '<example>'"]
    },
    "non_breaking_tshegs": {
      "char": "U+0F0C ༌ (Tibetan text only)",
      "count": <N>,
      "examples": ["line 22: '...'"]
    },
    "orphaned_line_fragments": {
      "description": "Lines ≤15 characters that appear mid-paragraph",
      "count": <N>,
      "examples": ["line 95: '...'"]
    }
  }
}
```

Print the profile to the conversation. If the `running_headers` list contains
any line that looks like substantive text (rather than a clear header or
footer), flag it and ask the human before proceeding.

#### Step 2 — Check for an existing cleaner script

Look in `0-INBOX/temp/<text-id>/` for a file matching `clean-<text-id>.py`.

- **Found →** skip to Step 4 (run the existing script directly).
- **Not found →** proceed to Step 3.

#### Step 3 — Generate the cleaning script

Before writing, read `examples/README.md` (next to this SKILL.md) — it
introduces two real, filled-in cleaning scripts from a past text, useful as
a reference for what a finished script looks like (reference only; their
paths are hardcoded to the old vault, so never run them as-is).

Write a Python script to `0-INBOX/temp/<text-id>/clean-<text-id>.py`. The
script must:

1. **Remove page markers** — delete every line matching `^\s*-\d+-\s*$` and the surrounding blank lines.
2. **Remove running headers / footers** — delete every line whose stripped content matches any string in the `running_headers` list from the profile.
3. **Replace non-breaking tshegs (U+0F0C ༌)**, for Tibetan text, with standard tshegs (U+0F0B ་) throughout.
4. **Remove mid-word spaces** — in lines that are not verse lines, collapse repeated intra-word spaces (repeat until stable). For Tibetan, use `([ༀ-࿿]) +([ༀ-࿿])` → `\1\2`; adapt the character range for other scripts.
5. **Join orphaned line fragments** — if a line ends without a sentence-closing mark and the next line is an orphaned fragment, join them with a single space. For Tibetan the closing mark is a shad group (`། །` / `།།`); for another script, use that script's own sentence-closing mark.
6. **Normalise blank lines** — collapse runs of more than one blank line into a single blank line.
7. Write the result to `0-INBOX/temp/<text-id>/cleaned.md`.
8. Print a brief summary: lines removed, replacements made, output path.

Use UTF-8 throughout. Do not use any external dependencies beyond the Python
standard library.

Script template (Tibetan example — adapt the character ranges for other
scripts):

```python
#!/usr/bin/env python3
"""
clean-<text-id>.py
Generated by the clean-raw-text skill.
Removes mechanical OCR/PDF debris from:
  <source_path>
Output:
  <output_path>
"""
import re, sys
from pathlib import Path

SOURCE = Path("<source_path>")
OUTPUT = Path("<output_path>")

# --- Strings to remove (running headers / footers) ---
REMOVE_LINES = {
    # Populate from profile running_headers list
}

PAGE_MARKER = re.compile(r'^\s*-\d+-\s*$')
TIB_RANGE   = re.compile(r'[ༀ-࿿]')
MID_SPACE   = re.compile(r'([ༀ-࿿]) +([ༀ-࿿])')
NBT         = '༌'  # ༌ non-breaking tsheg
STD_TSHEG   = '་'  # ་ standard tsheg

def is_verse_line(line: str) -> bool:
    """Heuristic: verse lines end with །། or ། །"""
    s = line.strip()
    return s.endswith('།།') or s.endswith('། །')

def clean(text: str) -> str:
    lines = text.split('\n')
    out = []
    i = 0
    stats = {'page_markers': 0, 'header_footer_lines': 0,
             'nbt_replacements': 0, 'space_removals': 0}

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 1. Page markers (and adjacent blank lines already handled by normalisation)
        if PAGE_MARKER.match(line):
            stats['page_markers'] += 1
            i += 1
            continue

        # 2. Running headers / footers
        if stripped in REMOVE_LINES:
            stats['header_footer_lines'] += 1
            i += 1
            continue

        # 3. Non-breaking tshegs
        if NBT in line:
            new_line = line.replace(NBT, STD_TSHEG)
            stats['nbt_replacements'] += line.count(NBT)
            line = new_line

        # 4. Mid-word spaces (not on verse lines)
        if not is_verse_line(line):
            prev = None
            while prev != line:
                prev = line
                line, n = MID_SPACE.subn(r'\1\2', line)
                stats['space_removals'] += n

        out.append(line)
        i += 1

    # 5. Normalise blank lines
    result = re.sub(r'\n{3,}', '\n\n', '\n'.join(out))

    print(f"Done — page markers removed: {stats['page_markers']}, "
          f"header/footer lines removed: {stats['header_footer_lines']}, "
          f"NBT replacements: {stats['nbt_replacements']}, "
          f"mid-word spaces removed: {stats['space_removals']}")
    return result

if __name__ == '__main__':
    text = SOURCE.read_text(encoding='utf-8')
    cleaned = clean(text)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(cleaned, encoding='utf-8')
    print(f"Written to: {OUTPUT}")
```

Fill in `SOURCE`, `OUTPUT`, and `REMOVE_LINES` from the profile before saving.
A fully worked example (a real, historical run of this pattern on a Tibetan
commentary) is bundled in `examples/` — see `examples/README.md`.

#### Step 4 — Run the script

Execute the script from the repo root:
```
python3 0-INBOX/temp/<text-id>/clean-<text-id>.py
```

Capture the printed summary and include it in the conversation output.

#### Step 5 — Review the output

Read the first 100 lines of `0-INBOX/temp/<text-id>/cleaned.md` and verify:
- No page markers remain.
- No running header / footer lines remain.
- Text flows without mid-word spaces.
- No non-breaking-tsheg characters remain (Tibetan).
- Paragraph breaks are single blank lines.

Report any remaining issues to the human contributor. Do not mark the draft
complete.

---

### Completion check

- [ ] Profile JSON produced and printed before any file was changed
- [ ] The source file was never overwritten; nothing was written to `1-SOURCES/` or `4-SYSTEM/`
- [ ] Cleaning script written to `0-INBOX/temp/<text-id>/clean-<text-id>.py`
- [ ] Script run successfully with a printed summary
- [ ] Output file exists at `0-INBOX/temp/<text-id>/cleaned.md`
- [ ] First-100-line review completed and findings reported
- [ ] `0-INBOX/temp/<text-id>/README.md` updated with this run's row and any new issues
- [ ] Human contributor notified that the draft is ready for the format step

---

---

## Issue registry and runs log

The cleaner script records *what* was done. The registry records *why*, and it
is what makes a second person able to re-run or extend the cleaning six months
later. Keep it as `0-INBOX/temp/<text-id>/README.md`, next to the script and the
output. It has two parts.

**A runs log** — one row per run:

| Date | Source file | Script | Output | Notes |
|------|-------------|--------|--------|-------|
| 2026-06-17 | `<source>.md` | `clean-<text-id>.py` | `cleaned.md` | first pass; 3 running headers, 412 page markers |

**An issue registry** — one entry per distinct artifact found, in severity
order. Each entry records the pattern, real examples, how often it occurs, what
caused it, what was done about it, and whether it is resolved:

```markdown
### Issue 1 — Page number markers

**Pattern:** Lines matching `^\s*-\d+-\s*$`
**Examples:**
    -1-
    -2-
**Frequency:** every ~15 lines (one per printed page)
**Cause:** PDF-to-text conversion retained the printed page numbers.
**Solution:** Delete every matching line; blank-line normalisation cleans up after it.
**Status:** handled in script (pass 1)
```

An issue the script does **not** handle still gets an entry, with its status
saying so. An unresolved issue that is written down is a known limitation; an
unresolved issue that is not written down is a silent corruption waiting for
whoever reads the text next.

Adding a new text: create `0-INBOX/temp/<text-id>/`, run the profile, start a fresh
README with an empty runs log, then work through the procedure above.

---

## Worked examples

`4-SYSTEM/Skills/clean-raw-text/examples/` holds two real, filled-in cleaning scripts from a past
Tibetan commentary ingest, with `examples/README.md` explaining what each one
does. They are **reference only** — their paths are hard-coded to the run they
came from, so read them for shape and never run them as-is.
