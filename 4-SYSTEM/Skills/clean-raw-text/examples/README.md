# clean-raw-text — worked example

These two scripts are a **historical, one-off example** of the `clean-raw-text`
pattern applied to a real Tibetan commentary in the source vault
(`bo-སྤྱོད་འཇུག་སྒྲུང་འགྲེལ།.md`). They are kept here as reference for what a
generated cleaning script looks like once filled in with real `REMOVE_LINES`
values and a real issue profile — **not** as runnable tools in this repo.

Do not run them as-is: their `SOURCE` / `OUTPUT` paths are hardcoded to the
original vault's absolute paths (`/sessions/.../1-SOURCES/...`,
`0-INBOX/...`), which do not exist here. When you need a cleaning script for a
new text, follow `../SKILL.md` Step 3 to generate a fresh one targeting
`$WORK/<text-id>/clean-<text-id>.py`.

## Files

- `clean-bo-spyod-jug-srung-grel.py` — the main cleaner: removes PDF page
  markers, running headers/footers (including a two-line-wrapped variant),
  replaces non-breaking tshegs (U+0F0C) with standard tshegs (U+0F0B), and
  collapses PDF-justification mid-word spaces.
- `fix-shad-spacing-bo-spyod-jug-srung-grel.py` — a narrower follow-up pass
  that inserts a space after every single shad (།) not already followed by a
  space, shad, or newline (leaves double-shad `།།` untouched).

## Issues this run found (for reference)

Profiled from a 698KB OCR/PDF-extracted source file:

1. **Page number markers** — lines matching `^\s*-\d+-\s*$`, one per printed page. Deleted.
2. **Running header** (single-line form) — a fixed header string repeated on most odd pages. Removed verbatim.
3. **Running header** (split across two lines) — the same header occasionally OCR-wrapped across two lines. Both variants added to `REMOVE_LINES` individually. Caveat: the header text also appears legitimately as a title reference mid-sentence — the script only strips lines where the string is the *entire* stripped line content, never a substring match.
4. **Running footer** — a fixed footer string repeated on most even pages. Removed verbatim.
5. **Non-breaking tshegs (U+0F0C ༌)** — hundreds of occurrences from a PDF encoding quirk; broke word-boundary detection. Replaced globally with the standard tsheg (U+0F0B ་).
6. **Extra mid-word spaces** — PDF full-text justification inserted spaces between syllables; collapsed with `([ༀ-࿿]) +([ༀ-࿿])` → `\1\2`, applied iteratively, skipped on verse lines.
7. **Orphaned line fragments** — short (≤20-char) lines produced by OCR line-boundaries not aligning with sentence boundaries; joined to the preceding line when it did not already end at a sentence boundary.

## Known limitations (still true of the general skill)

- Does not fix broken syllables (e.g. an OCR-separated vowel sign) — that is a
  job for the format skills, not this one.
- Does not add headings, block IDs, or frontmatter.
- The split-header heuristic (issue 3) can, in principle, over-match a title
  string that legitimately opens a section as a running reference — always
  spot-check the Step 5 review in `../SKILL.md`.
