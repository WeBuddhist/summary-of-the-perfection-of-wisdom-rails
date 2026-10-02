---
name: format-root-text
description: >
  Format and normalise a root text, a translation, or a commentary in any
  language that does not have a dedicated format skill — Pāli, Chinese,
  English, Hindi and the rest. Handles frontmatter, block IDs (including
  Chapter 0), heading structure, and OCR cleanup.

  Trigger on "format this root text", "structure this sutta", "normalise this
  file", "add the chapter headings".

  Language scope: **everything except Tibetan and Sanskrit.** For Tibetan use
  `format-tibetan-root-text`; for Sanskrit use `format-sanskrit-root-text`;
  for a Tibetan or Chinese commentary use `format-commentary`.
---

# format-root-text

This skill normalises a source file to the vault's structural and linking
standards. It is the generic fallback for languages that do not have a
dedicated format skill — `format-tibetan-root-text` handles Tibetan,
`format-sanskrit-root-text` handles Sanskrit — so use this one for anything
else (Pāli, Chinese, English, Hindi …), or as a general normalisation pass.

**Scope: root texts, translations, and commentaries.** A commentary or
translation carries a few extra obligations (its own `verse_id_format`, a
`root_text:` pointer, `covers_verses:`, and root transclusions) — see Step 4.

## Core Principles
Before processing any file, read `4-SYSTEM/Guidelines/annotation-conventions.md` — it is the canonical
spec for block IDs and heading hierarchy. The block ID is the single most
important linking mechanism for verse-level references.

### 1. Heading Structure (TOC)
- **Level 1 (`#`)**: the title of the work. No block ID.
- **Level 2 (`##`)**: author-defined books or chapters. `^N-0`.
- **Level 3 (`###`)**: author-defined sub-sections (e.g. from the author's own table of contents). `^N-N-0`.
- **Level 4 and deeper (`####`, `#####`, `######`)**: only where the author's own structure genuinely goes that deep. Markdown level follows tree depth and the block ID carries the full decimal path plus `-0` (`4-SYSTEM/Guidelines/annotation-conventions.md` §2). Do **not** invent sub-headings the source does not have — a verse does not need a heading, its block ID addresses it.
- **Chapter 0**: any content preceding Chapter 1 (titles, colophons, homages, scribal intros) goes under `## 0. Introduction ^0-0`.

### 2. Block ID Format
- **Standard**: `^chapter-verse` (e.g., `^1-1`, `^6-33`).
- **Chapter 0**: Verses in the introduction section use `^0-verse` (e.g., `^0-1`, `^0-2`).
- **No Zero-Padding**: Use `^6-33`, NOT `^06-033`.
- **Placement**: At the end of the last line of the verse/passage, preceded by a single space.
- **Numbering**: Verse numbers restart at 1 for each chapter. Convert continuous numbering to per-chapter numbering.
- **Heading anchors**: every heading below the `#` title carries its full decimal path plus the `-0` slot (`^N-0`, `^N-N-0`, `^N-N-N-0`, …) — `4-SYSTEM/Guidelines/annotation-conventions.md` §2. Do not use `^TOC-N`; that scheme is deprecated (§6) and a parser expecting `^N-0` silently finds no structure.
- **Transclusion lines never take a block ID** and never advance a verse counter.

---

## Step 1 — Audit and Identification
Work on a copy in `0-INBOX/temp/` (or, for a file already placed in `1-SOURCES/`, on
that file directly — the edits this skill makes are structural and permitted).
Identify what lacks frontmatter, has missing or incorrect block IDs, or carries
stray line numbers from OCR/PDF extraction.

## Step 2 — Process Formatting
For the file:
1. **Insert/Update Frontmatter**: Ensure the YAML block is at the very top. The `frontmatter` skill owns the full schema.
2. **Standardise Headings**:
    - Ensure Chapter 1 starts with `## 1. [Title] ^1-0`.
    - Ensure pre-chapter material is under `## 0. Introduction ^0-0`.
    - Map author-defined structural divisions to `##` and `###`.
3. **Apply Block IDs**:
    - Add `^0-n` to introduction verses.
    - Add `^c-v` to chapter verses, restarting `v` at 1 for each `c`.
    - If the text turns out to be Sanskrit or Tibetan, stop and hand off to `format-sanskrit-root-text` / `format-tibetan-root-text` rather than approximating their verse-boundary rules here.
4. **Clean Content**:
    - Remove OCR artifacts, page numbers, and stray line-number prefixes (e.g., `7.`, `42.`).
    - Restore two-line formatting for verses if hemistichs are run together.

## Step 3 — Frontmatter Fields
Minimum required fields (full schema: the `frontmatter` skill, and the vault's
`About Sources.md` §4):
```yaml
---
title:
author:
language:
file_type: root-text | commentary | translation | reference
lang_tag: sk | bo | zh | en | pi
source_description: "Detailed source info (required)"
verse_id_format: chapter-verse | verse | book-chapter-verse
---
```

Language tags follow the vault's own list (`About Sources.md` §12) — note
Sanskrit is **`sk`**, not `sa`.

## Step 4 — Commentaries and translations

A commentary or translation carries three obligations a root text does not:

- **Its own block ID system**, declared in its own `verse_id_format:`. A commentary's IDs are its own sequential counters, not the root's verse numbers.
- **`root_text:`** — the full vault-relative path of the root it belongs to — and **`covers_verses:`**, the range it covers (e.g. `1-1–6-33`).
- **Root transclusions** — the relevant root verse(s) transcluded immediately before the commentary on them: `![[1-SOURCES/Text/<root-text>.md#^1-1]]`. Use sequential individual transclusions for a multi-verse section; Obsidian has no range syntax. Placement is `transclusion`'s job, not this skill's.

---

## Dos and Don'ts
- **DO** work on one file at a time.
- **DO** use editorial notes `[Ed: ...]` in English for ambiguous cases.
- **DO** preserve original scripts in content while using English for metadata.
- **DON'T** renumber verses based on your own interpretation; follow the source's logical structure.
- **DON'T** put anything but the `-0` heading anchor on a heading line.
- **DON'T** invent heading levels the source's own structure does not have.
- **DON'T** use `^TOC-N` style chapter anchors — use `^N-0` (`4-SYSTEM/Guidelines/annotation-conventions.md` §6).
- **DON'T** apply this skill to a Tibetan or Sanskrit root text — hand off to `format-tibetan-root-text` / `format-sanskrit-root-text`, which know those scripts' verse-boundary rules.
