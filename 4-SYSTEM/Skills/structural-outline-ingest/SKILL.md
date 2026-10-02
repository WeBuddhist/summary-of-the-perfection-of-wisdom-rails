---
name: structural-outline-ingest
description: >
  Extract the structural outline of one source (root text, commentary, translation
  or reference) and write it as a citable rail at 2-RAILS/Sections/Raw/outline/<source-id>.md.
  One source at a time; run it before any verse-package work on that text.

  This is the **prose-outline** route to a text's structure — for a source whose
  divisions are stated separately from the running prose (a table of contents, an
  editor's synopsis, titled/numbered sections, adhikara labels), or must be inferred
  from topic transitions. A Tibetan text that announces its own divisions *inline*
  (sa bcad) uses `toc-generate` instead; a vault running that pipeline already has
  this structure in the QC-clean tree at 2-RAILS/Sections/Raw/toc-tree/<id>.md and does not
  need this skill for that source.
---

# structural-outline-ingest

> **Which skill do you want?** This one, when the source's structure is stated
> **separately** from its prose, or must be inferred. `toc-generate`, when a
> Tibetan text announces its divisions **inline** (*sa bcad*) — that pipeline
> produces a QC-verified tree rail at `2-RAILS/Sections/Raw/toc-tree/<id>.md` which
> already carries this structure, so do not run both on the same source.
> `add-toc`, when the file already has headings and only needs a navigable index.

This skill reads a single source from `1-SOURCES/` and produces an individual
outline file at `2-RAILS/Sections/Raw/outline/<source-id>.md`. It is **Phase 1** of the
rails compilation cycle — structural outlines must exist before verse packages
can be built.

The output is a **rail**: a citable, descriptive file under `2-RAILS/`, not a
scratch working file. Everything in it is attributed to the source it came from.

The output is **not** a summary of every verse. It is a structural tree with
translator-facing study notes: what each chapter and section is *doing*, who
the implied audience is, and what cultural or doctrinal context a translator
would lose without the note. Verse-level content belongs in verse packages, not
here.

---

## When to run this skill

Run once per source, **before** beginning verse packages for that chapter.
Recommended order when multiple sources exist for the same text:

1. The root text itself, if the author provides explicit divisions (check for numbered or titled sections).
2. Any commentary or secondary source with a well-developed traditional outline.
3. Any other available source, in order of how developed its own structural markers are.

After running this skill on two or more sources for the same chapter, run the
**combined-outline synthesis** step (`section-summary-combined`, or the
equivalent compiler registered in your vault) to synthesise them into
`2-RAILS/Sections/<node-id>.md`. If only one source exists, its outline file **is** the
outline for that chapter until a second one arrives.

---

## Input

The user provides a **source ID** — the registered short ID of the source being
outlined. Resolve it to a file under `1-SOURCES/` and confirm before proceeding:

| Source type | File |
|---|---|
| Root text | `1-SOURCES/Text/<filename>.md` |
| Commentary | `1-SOURCES/Commentaries/<filename>.md` |
| Existing translation | `1-SOURCES/Translations/<filename>.md` |
| Reference / secondary literature | `1-SOURCES/References/<filename>.md` |

Each vault registers its own source IDs (see its `vault-annex.md`). If the
source is ambiguous, or the ID is not registered, ask the user to confirm the
file before proceeding — do not guess.

**Output path:** `2-RAILS/Sections/Raw/outline/<source-id>.md`

---

## Step 1 — Read the source file

Read the source file. Focus on:

- The **opening pages**: title, author's stated purpose, any explicit table of contents or section list
- **Structural markers**: for Tibetan texts these are often *sa bcad* (outline labels — see `tag-inline-toc` if the text uses this pattern inline); for Sanskrit, numbered sub-topics; for other languages, chapter headings or explicit divisions
- **Chapter and section boundaries**: wherever the author transitions from one major topic to another
- The **colophon or closing section**: sometimes contains the author's own characterisation of the work's structure

You do **not** need to read every verse. Skim chapter by chapter, extracting
structural markers and reading enough surrounding text to write a meaningful
study note for each section. For long texts (over 200 pages), read the
structural markers and the opening of each major section; skip verse-by-verse
detail.

---

## Step 2 — Determine `outline_basis`

Set `outline_basis` in frontmatter:

- **`explicit`**: the source contains clearly marked structural divisions — a table of contents, numbered sections, *sa bcad* labels, or titled chapter headings that the author placed in the text
- **`implicit`**: no explicit markers; structure must be inferred from topic transitions and argument logic

*Example (from the Bodhicaryāvatāra tradition)* — most Tibetan commentaries on
this text are `explicit` (they use *sa bcad* outline labels); a Sanskrit
commentary in the same tradition (e.g. Prajñākaramati's) is largely
`implicit` at the sub-chapter level — it provides topic (*adhikāra*) labels
but not a full structural outline. Mark any inferred boundary with
`[Ed: implied division]` in the study note.

---

## Step 3 — Build the heading tree

The heading tree **is** the structural outline. Do not produce a separate
block or list — the markdown heading structure itself encodes the tree.

**Heading levels:**

| Level | Use |
|---|---|
| `##` | Chapters (author-defined) |
| `###` | Sections (as divided by this source) |
| `####` | Subsections (only if this source divides further) |

**Heading format:**
```
## Chapter N: [Title] ([verse range]) ^N-0
### N.M [Section title] ([verse range]) ^N-M-0
#### N.M.P [Subsection title] ([verse range]) ^N-M-P-0
```

Verse ranges use the block ID format without the caret: `1-1`, `6-33`. Use
`^N-0` / `^N-M-0` / `^N-M-P-0` heading anchors per `4-SYSTEM/Guidelines/annotation-conventions.md` §2
(the full decimal path plus the reserved `-0` slot, no segment cap) — for
chapters where the range is not yet
confirmed, omit the range and add `[Ed: range unconfirmed]` in the study
note.

**Pre-chapter content** (title, homage, colophon, scribal introduction) goes
under `## 0. Introduction ^0-0`.

**Never** use headings for editor-imposed groupings. If you want to name a
grouping that the source treats implicitly, do so in the study note prose,
not as a heading — and mark it `[Ed: ...]`.

---

## Step 4 — Write study notes

Immediately after each heading, write the study note. No blank heading —
every structural node gets a note.

**Study note structure:**

1. **Opening sentence**: what this chapter or section is *doing* in the text's argument. Use an active verb: "establishes," "refutes," "enumerates," "demonstrates," "transitions."
2. **Implied audience**: who the author seems to be addressing at this point — renunciates, general practitioners, scholars, beginners? Some texts shift audience mid-text.
3. **Cultural or doctrinal context**: what a translator must know to represent this section faithfully. Think: what would be invisible to a reader without the relevant background, or lost in a language without these concepts?
4. **What would be missed without this note**: one concrete example of a translation or adaptation error this study note prevents.
5. **Associated concepts line**: Local-Wiki wiki links to the sense IDs relevant to this section, on their own line at the end of the note.
6. **Citation**: the source passage that grounds the note's claims.

**Prose rules:**
- English throughout
- Original-language terms italicised on first use: *bodhicitta*, *sa bcad*, *maṅgala*
- After first use, use the Local-Wiki wiki-link form: `[[bodhicitta (awakening mind)]]` — one link per attested sense ID in `2-RAILS/Local-Wiki/`
- Present tense for analytical claims ("<commentator> reads this as…"); past tense for historical statements
- **Do not** summarise verses — that belongs in verse packages. Write about what the *section* is doing, not what each verse says.
- **Do not** exceed four paragraphs per study note. Concision is a feature.

**Citation format** — always a path under `1-SOURCES/` plus the block ID:
```
(1-SOURCES/Commentaries/<filename>.md#^block-id)
```
```
(1-SOURCES/Text/<filename>.md#^block-id)
```

Every claim in a study note cites a specific `1-SOURCES/` file. A rail never
cites another rail, and never cites the model's own knowledge. If the source
passage does not yet have a block ID (the file hasn't been through a format
skill yet), cite the chapter and section as closely as possible, add
`[Ed: block ID pending]`, and keep `ingest_status: draft`.

---

## Step 5 — Mark divergences

If you already know from other sources that *this* source's structural
division diverges from another available source, mark it in the study note
with ⚑ and a brief note. This is not required at this stage — divergences are
fully resolved in the combined-outline synthesis step — but flagging known
divergences now makes that step faster.

*Example (from the Bodhicaryāvatāra tradition)*:
> Prajñākaramati treats verses 1-1 through 1-14 as a single undivided unit ⚑; Tibetan commentators subdivide this range into two or three sections.

---

## Step 6 — Write the output file

Write the complete file to `2-RAILS/Sections/Raw/outline/<source-id>.md`.

### Frontmatter template

```yaml
---
source_id: [text-id or a short identifier for the secondary source]
source_type: root-text | commentary | translation | reference
language: [language name]
lang_tag: [tag]
file: 1-SOURCES/[folder]/[filename].md
outline_basis: explicit | implicit
chapters_covered: [1, 2, 3]   # list only chapters whose outline is complete in this file
ingest_date: [ISO date]
ingest_status: draft | partial | complete
---
```

`ingest_status` — how far *this* outline file has been taken:
- `draft` — structure is roughed in but study notes are thin or uncited
- `partial` — some chapters complete, others stubbed
- `complete` — all chapters processed, all study notes cited; ready for the combined-outline synthesis step

`ingest_status` is the LLM's own record of coverage and it may set it. A vault
that also carries a `status:` field on rails follows the vault rule for that
field: `status: complete` is set by a **domain specialist**, never by the LLM,
and only a `status: complete` rail may be used to generate a transformation.
Leave `status: draft` on anything you write.

### Full file template

```markdown
---
[frontmatter]
---

## 0. Introduction ([verse range or "pre-chapter"]) ^0-0

[Study note: what the opening homage, title declaration, or scribal introduction
does. Who is being addressed. What the colophon, if present at the opening,
tells us about transmission context.]

Associated concepts: [[maṅgala (auspicious opening)]] · [[śāstra (treatise)]]
([citation])

---

## Chapter 1: [Title from this source] (1-1–1-N) ^1-0

[Study note: what the chapter does in the text's overall argument. Implied
audience. Cultural context a translator needs. What would be lost without
this note.]

Associated concepts: [[bodhicitta (awakening mind)]] · [[bodhisattva (awakening being)]]
([citation])

---

### 1.1 [Section title] (1-1–1-N) ^1-1-0

[Study note.]

Associated concepts: [[sugata (gone to bliss)]] · [[maṅgala (auspicious opening)]]
([citation])

---

### 1.2 [Section title] (1-N–1-M) ^1-2-0

[Study note.]

Associated concepts: [[term (disambiguating gloss)]] · …
([citation])

---

## Chapter 2: [Title] (2-1–2-N) ^2-0

[...]
```

Use `---` horizontal rules to separate structural nodes at the `##` level. At
`###` and `####` level, the blank line between heading and study note is
sufficient — no extra `---` needed.

---

## Step 7 — Post-write check

Before finishing, verify:

- [ ] Frontmatter complete and accurate
- [ ] Every heading has a study note (no bare headings)
- [ ] Every study note has at least one citation — or is marked `[Ed: citation pending]` with `ingest_status: draft`
- [ ] Every concept mentioned in study notes appears in the Associated concepts line
- [ ] Verse ranges are in `chapter-verse` format (e.g. `1-1`, not `I.1` or `v.1`)
- [ ] Heading anchors are `^N-0` / `^N-M-0` style, never `^TOC-N`
- [ ] No verse-by-verse content summaries in any note
- [ ] Output written to `2-RAILS/Sections/Raw/outline/<source-id>.md` — a rail, not a scratch file
- [ ] Every citation points at a file under `1-SOURCES/`; no rail cites another rail
- [ ] `ingest_status` reflects actual completeness

---

## Source-type specifics

### Tibetan sources

Tibetan sources in this tradition typically open with a *sa bcad* (outline
label) before each section. These are the most reliable structural markers
when present. Use them as heading titles directly (translate into English for
the heading, keep the original in the study note prose, italicised). If the
text has inline sa-bcad structural announcements woven into the prose itself
(not just section-opening labels), consider running `tag-inline-toc` instead
of, or before, this skill.

### Sanskrit sources without explicit labels

*Example (from the Bodhicaryāvatāra tradition)* — Prajñākaramati's Sanskrit
commentary does not use *sa bcad*-style labels. Structural divisions must be
inferred from:
- *adhikāra* labels (topic headings like *"atha bodhicittasyotpādaḥ"*)
- Explicit transitional phrases (*"idānīm..." — "Now..."*)
- The logic of the commentary sequence

Mark all inferred boundaries `[Ed: implied division]`.

### Root text

The root text's structural outline reflects the author's own chapter and, if
any, sub-chapter divisions. *Example (from the Bodhicaryāvatāra)*: chapters
are author-defined; sub-chapter divisions within the root text are **not**
author-defined — if you divide within chapters for the root-text outline
file, mark every such division `[Ed: editorial grouping]`.

---

## Dos and Don'ts

- **DO** read structural markers carefully; skim verse-by-verse prose
- **DO** write study notes for a translator who knows the tradition generally but may not know this specific text
- **DO** flag ⚑ when you already know this source diverges structurally from another
- **DO** cite even rough block-ID locations — an approximate citation is better than none
- **DON'T** summarise verse content in study notes
- **DON'T** impose your own structural divisions — report the source's divisions
- **DON'T** use `####` for editor-imposed groupings; use prose and `[Ed: ...]` instead
- **DON'T** mark `ingest_status: complete` unless every chapter has cited study notes
- **DON'T** start verse packages for a chapter until at least two outline files for that chapter exist and `ingest_status` is at least `partial` for both

---

## Provenance

The vault-specific source-ID table (four named commentaries → fixed vault file
paths) is replaced with the generic per-source contract, with tradition
specifics kept as labelled examples; heading anchors are now `^N-0` /`^N-M-0` /
`^N-M-P-0` per `4-SYSTEM/Guidelines/annotation-conventions.md` §2 (the original used none), and paths use
the logical names in `4-SYSTEM/Guidelines/skill-locations.md`. The rails-vault semantics of the
original are kept intact: the output is a citable rail under `2-RAILS/Sections/Raw/`,
it is Phase 1 of the compilation cycle, and every study note cites `1-SOURCES/`.
The Gemini Gem variant (`Gem-structural-outline-ingest.md`) is not carried over —
this repo targets Claude Code directly, not a standalone Gemini Gem session.
