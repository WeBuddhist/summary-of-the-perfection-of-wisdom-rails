# Plans — per-plan convention

This folder holds calendar-driven study and practice arcs: daily readings,
weekly retreat sessions, year-long courses, chanting schedules. Each plan
organises engagement with the text along a calendar, generating per-session
content from rails (and often from completed Translation or Adaptation
outputs).

See [`../About Transformations.md`](../About%20Transformations.md) for the
top-level rules that govern all transformation categories.

The rest of this file is the binding convention for a plan. Its central claim:
**a plan's shape lives in the plan's own files, never in a skill.** Every
parameter the pipeline needs — the section list, the ceilings, the voices, the
verse sources, the naming — is declared once in `About <plan-name>.md` and read
from there by every skill. A shape that lives in a generator drifts: the
evaluator falls out of sync with it, a second language stream invents its own
section list, and nobody can say what the contract is.

---

## 1. Folder layout

Each plan is one subfolder. Inside it, **language streams are completely
separate** — one subfolder per language code. The plan root holds only the
cross-stream overview.

```
Plans/
└── <plan-name>/
    ├── About <plan-name>.md          # the contract: shape, streams, sources, naming
    └── <lang>/                       # one folder per published language
        ├── requirements.md           # style contract for this stream (in that language)
        ├── termbase.md               # vocabulary contract (authoring)
        ├── termbase-translation.md   # the translation fork (translation streams only)
        ├── schedule.md               # day-by-day calendar for this stream
        ├── qa-report.md              # dated QA runs, appended, never rewritten
        ├── days/                     # per-session output files
        │   └── Archive/              # superseded versions, never deleted
        ├── communications/           # cross-day outreach copy
        └── assets/
            ├── liturgy.md            # every Fixed section's text, verbatim
            ├── section-spec.json     # machine-readable form of the section declaration
            └── images/
```

**Why per-language subfolders.** Keeping each stream self-contained lets teams
work independently — the English drafters do not touch the Bengali folder, and
each stream can sit at a different completion stage with no risk of mixing
content.

**Day folders may be grouped.** `days/` is flat by default. A long plan may
group days into chapter folders (`days/Chapter-<C> D<first>-D<last>/`) when a
flat folder of several hundred files becomes unworkable. Whichever is used is
declared in `About <plan-name>.md`; it is not a per-file decision.

---

## 2. The plan root: `About <plan-name>.md`

Written in English regardless of which languages the plan publishes. Eight
required parts, in this order — the pipeline reads them by heading.

### 2.1 Purpose

What the plan is, how long it runs, how it is delivered, how long one session
takes.

### 2.2 Audience

Prior knowledge, what the reader already practises, what they have not studied,
time budget, what they are sceptical of.

### 2.3 Streams

Exactly one stream is the **authoring stream**: its day files are written from
the rails. Every other stream is a **translation stream**: its day files are
produced by translating the authoring stream's day file, section by section.

| Stream | Language | Role | Status | Designated verse source |
|---|---|---|---|---|
| `bo` | Tibetan | authoring | in progress | `1-SOURCES/Text/<root>.md` |
| `en` | English | translation | in progress | `3-TRANSFORMATIONS/Translations/<track>/<file>.md` |

**One authoring stream, always.** Authoring two streams independently from the
same rails makes them diverge, and no QA check can pull them back. One is
authored; the others are renderings of it. That is what keeps every stream
saying the same thing on the same day.

**The verse source is exclusive.** For each stream, verse text is inlined
verbatim by block ID from the file named in this table and from no other. Where
the vault holds a second file that also looks like that stream's verses, name it
here and state plainly that it must never be quoted in a day file. Two
plausible verse files is the single most expensive ambiguity a plan can carry.

### 2.4 Session shape

The **section-type declaration** — one row per section, in day-file order:

| Column | Meaning |
|---|---|
| `id` | Stable machine id (`opening`, `verses`, `commentary`, `practice`). Never changes, even when the display heading does. |
| `type` | `Fixed` · `Extracted` · `Generated` · `Translated`. |
| `voice` | `neutral` / `first person` / `second person` / `none`. |
| `ceiling` | A hard maximum **with its unit** — `150 words`, `300 syllables` — or `—`. |
| `formula` | A required opening or closing phrase, quoted verbatim, or `—`. |
| `absent` | `may be absent` when the section is legitimately dropped if its source has nothing; otherwise `required`. |
| `grounding` | Exactly where the content comes from: `assets/liturgy.md`, the verse source, a named rail layer, the authoring-stream section. |

The four types:

- **Fixed** — reproduced character-for-character from `<lang>/assets/liturgy.md`
  every day, for every day. Never paraphrased, reordered or "improved".
- **Extracted** — copied verbatim from the stream's designated verse source by
  block ID. Not generated at all.
- **Generated** — composed for this day from the declared grounding, inside the
  declared ceiling, voice and formula.
- **Translated** — rendered from the matching section of the authoring stream's
  day file. Translation streams only.

A ceiling is a ceiling, never a target: nothing is padded toward it, and every
ceiling is verified by script rather than by eye. A section whose grounding
cannot be named is not ready to be declared.

Two further tables accompany the declaration:

- **Headings by stream** — `id` × one column per stream, giving the exact
  heading each stream writes.
- **Heading aliases** — every accepted spelling of each section's heading in the
  authoring stream, including historical ones still on disk. Translation
  matches sections by normalised heading text, never by number or position; a
  translator that grabs "section six" will eventually render a dedication as a
  practice instruction. Declare an alias the moment a second spelling appears.

Where a section has labelled sub-blocks, a third table gives each label per
stream and marks which sub-blocks are **carried** and which are **excluded**.
Excluded sub-blocks — editorial notes, supplements, key-term lists, a repeated
verse that restates one already carried — never reach a translated day.

### 2.5 Practice categories

When the shape has a practice section, its explanation opens with exactly one
category from a controlled list, wrapped as `_(category)_`. The list lives here;
each stream's rendering of each category lives in that stream's termbase. A
category not on the list is a stop: propose it, log it under Pending terms, ask.

### 2.6 Sources

- **`commentary_mode: rails | teaching-file`.** `rails` synthesises the
  commentary section from `2-RAILS/Verses/<id>.md`. `teaching-file` copies a
  pre-assigned teaching **verbatim** from a day→teaching assignment file, under
  its own title, closed with a citation line naming the blocks used — nothing
  paraphrased, nothing supplemented. The value of that mode is that the teaching
  reaches the reader in the teacher's own words.
- **`source_mode: rails | direct-source`** — see §7.
- **Rail dependencies** — which rails each session draws on, and the interim
  fallback (or "none — stop").
- **`consumer: app | notification | obsidian`** — decides inline vs transclude
  (§6).

### 2.7 Naming

Schedule path and columns; the day-file name pattern; folder grouping; the
archive folder; and the rule that **the day number is absolute across the whole
plan**, never chapter-relative, in the filename, the `day:` frontmatter and any
folder range.

The verse range is encoded redundantly in the day-file name and validated
against the schedule before any write. A mismatch means the schedule lookup or
the file search went wrong — it is a stop, not something to reconcile silently.

### 2.8 Status rules

What `draft` / `partial` / `complete` mean for this plan, and who may set
`complete` (§9).

---

## 3. Per-stream files

### `requirements.md` — the stream's style contract

Written **in that stream's language**. The section *list* is declared once in
`About <plan-name>.md`; this file says how this language renders it. It covers:
audience and register (reading level, sentence length, voice, honorific policy);
per-section rendering conventions; terms, names and epithets; the **forbidden
elements** list, written as checkable lines; word-count **bands** as
diagnostics; language-specific grammar rules given as right/wrong tables; and
communications style.

Register rules belong here and nowhere else. A rule buried in a skill cannot be
edited by the person who owns the stream, and a skill that carries one
language's rules cannot serve a second.

### `termbase.md` — the vocabulary contract

One chosen rendering per keyword that appears in this stream's day files, built
by `glossary-select` from `2-RAILS/Bilingual-Glossaries/<src>-<tgt>.md` guided by
`requirements.md`. It also holds the display-name table (machine id → display
name) and any controlled vocabulary the day files use.

### `termbase-translation.md` — the translation fork

Translation streams only. A **fork**, not a copy: it carries `forked_from:`
pointing at the stream's `termbase.md`, states only what differs for translation,
and holds the practice-category labels, the sub-block labels, the diacritics
policy, and a **Pending terms** table.

The pending-terms loop: an unknown term is never improvised silently. Pick a
rendering and log it in two places — the day file's `pending_terms:` frontmatter
and this table, with the day it first appeared in. When a human approves it, it
moves into the main table, drops off the pending list, and is cleared from any
day file that carries it the next time that file is touched. Before generating a
new day, reuse a rendering already pending rather than inventing a second one.
An entry older than one chapter of generation means the review step is not
happening — report it.

### `schedule.md` — the calendar

Generated by `plan-schedule build`, never typed. Columns:

| Day | Ch.Day | Verses | Index | Date |
|---|---|---|---|---|

- **Day** — absolute session number, no zero-padding.
- **Ch.Day** — the day's ordinal within its chapter.
- **Verses** — a contiguous, gap-free `C.V–C.V` range (or a single `C.V`).
- **Index** — running verse index across the whole text for the downstream
  consumer; `Index − verse` is constant within a chapter, which `plan-schedule
  audit` verifies.
- **Date** — delivery date.

To move a verse between days, use `plan-schedule plan` then `apply`: it ripples
the contiguous ranges and renames the affected day files in the same pass,
all-or-nothing, and never touches day-file content. Boundary verses only, never
across a chapter, never emptying a day. A "Known anomalies" section records
irregularities that are accepted rather than fixed.

### `assets/liturgy.md` — the Fixed text

One `##` block per Fixed section id. This is the only place that text lives — not
in a skill, not in a day-file scaffold. **Each stream's Fixed text is its own
attested text**; a liturgical block is never translated from another stream. If
a language has no attested version, say so and stop.

### `assets/section-spec.json` — the machine-readable declaration

The same section table in JSON, consumed by the mechanical checker. It must
agree with the declaration; when one changes, both change.

### `qa-report.md`, `communications/`, `days/Archive/`

`qa-report.md` accumulates dated QA runs; earlier runs are never deleted, so the
report shows whether a day is improving. `communications/` holds cross-day
outreach content (launch, milestone and closing announcements, social kits,
email series). Per-day notification copy, where the plan has any, lives in the
day file as a declared section — not here.

---

## 4. Day files

### Frontmatter

```yaml
---
day: 24
chapter: 2
verses: "2-22 to 2-24"
date: 2026-07-29
transformation_type: plan-session
stream: en
translated_from: 3-TRANSFORMATIONS/Plans/<plan>/bo/days/<file>.md   # translation streams
verse_source: 3-TRANSFORMATIONS/Translations/<track>/<file>.md
context_packages:
  - 2-RAILS/Verses/2-22.md
pending_terms: []
generation_date: 2026-07-20
generated_by: plan-day-translate
status: draft
---
```

`generation_note:` is added when the rail-status decision point required an
interim source, or when `source_mode: direct-source` was exercised.

### Body

The declared sections, in the declared order, under the headings declared for
that stream. **Nothing else goes on the page**: no generation note, no source
list, no translator's note, no QA commentary. The day file is a reader-facing
document; everything a reviewer needs is reported out of band (§8).

A section declared "may be absent" is dropped heading and all when its source
genuinely has nothing — and the absence is stated in the report, never silently.

### Verse text — inline, never retyped

Verse text is **inlined verbatim by block ID** from the stream's designated
source, with the block ID retained and the source's line breaks preserved. Never
quote a verse from memory; never let a generator retype one. Where a generated
section repeats a verse, it repeats the already-verified extracted text.

`![[…]]` **transclusion is used only when the plan declares
`consumer: obsidian`.** Day files consumed by an app, an API or a notification
system are read outside Obsidian, where a transclusion is an unresolved link
rather than content.

---

## 5. Citation rules

The chain is `1-SOURCES/ → 2-RAILS/ → 3-TRANSFORMATIONS/`, and a plan does not
skip a link.

- **Authoring streams cite `2-RAILS/`.** Every claim in a Generated section
  traces to a specific passage in the day's rails. A claim that cannot be
  located is an addition, and is cut.
- **A rail that is not `status: complete`** triggers the decision point: use the
  interim source the plan declares and record a `generation_note`, or **stop and
  flag the dependency**. Never invent content, and never reach for a commentary
  file the plan has not declared.
- **Translation streams cite the authoring-stream day file** named in
  `translated_from:`, plus their own designated verse track. They do **not**
  consult the rails: if a sentence in the output has no parent clause in the
  source day, it is deleted — however true and however helpful.
- **Plans may cite completed outputs of other tracks** (a Translation track's
  verse file, an Adaptation's rendering), recorded in `context_packages:` the
  same way as rails.
- **Direct `1-SOURCES/` citation is a declared exception.** A stream may quote or
  transclude `1-SOURCES/` directly **only** when `About <plan-name>.md` declares
  `source_mode: direct-source`, with the reason; each day file that does so
  records it in `generation_note:`. Undeclared direct citation is a defect, not a
  shortcut — the declaration exists so the exception is visible and bounded
  rather than discovered later in a day file.

---

## 6. Overwrite and archive

**A day file is never overwritten silently.** If the target exists — including
when it is an empty stub — the existing version is moved to
`<lang>/days/Archive/` first, keeping its name (with a numeric suffix if one is
already archived), and only then is the new file written. The archiving is
stated in the reply.

This is a deliberate ruling between two policies that were both in use: "these
files are generation targets, overwrite them in place" and "never overwrite,
archive". Archiving wins. The cost of an extra file is trivial; the cost of a
reviewed day silently replaced by a regenerated one is not.

---

## 7. Reporting out of band

Absent sections and why, measured counts with any that fell outside their band,
rails that were missing or not `complete` and what was used instead, terms added
to `pending_terms`, ambiguities where a reading had to be chosen, structural
irregularities in a source file, and any file archived — **all of it is reported
in the reply, never written into the day file.**

---

## 8. Cross-track day packages (optional)

A plan whose material is consumed by an app or API may also produce a **day
package**: a machine-anchored per-day dossier that carries the plan's session
sections, the day's verses, and every rail layer, with `<!-- … -->` anchors
before each heading and display-only headings whose machine id lives in the
anchor.

Day packages sit in a **top-level folder beside the three categories**
(`3-TRANSFORMATIONS/Day-Packages/`), not inside a plan, because more than one
track reads them — which is exactly the "cross-track shared output" case that
`About Transformations.md` §1 requires to be documented here.

Packages are **protected files**: `protected: true`, an `edit_policy:`, and a
`PROTECTED — SOURCE OF TRUTH` banner under the frontmatter. Regenerating one
counts as editing it, so it is confirmed with a human first. A sha256 drift
guard makes an unauthorised change loud; it is **advisory detection, not
enforcement**, and its baseline is re-recorded only after an approved change.

---

## 9. Status rules

| Status | Meaning |
|---|---|
| `draft` | generated, not yet reviewed |
| `partial` | reviewed in part |
| `complete` | reviewed against the rails and the plan's contracts; publishable |

- Day files are generated as `draft`.
- **No skill and no model ever sets `complete`.** A domain specialist does, after
  the QA run shows zero critical and zero major issues.
- A translation stream's day may not be promoted past the status of the
  authoring-stream day it was translated from.
- Only `complete` day files are published.

---

## 10. Starting a new plan

1. Run `plan-scaffold`: agree the session shape section by section, then write
   `About <plan-name>.md` and each stream's contracts and folders.
2. Run `plan-schedule build` for each stream, then `audit` it.
3. Run `plan-day-generate` for day 1 of the **authoring** stream.
4. Run `plan-day-qa` on it; iterate until zero critical and zero major; have a
   specialist promote it before generating day 2.
5. Run `plan-day-translate` for the other streams, then `plan-day-qa` on each.
6. Optionally run `plan-day-package` when an app consumes the day.
7. Add communications content as the plan rolls out.

---

## 11. Skills

The plan pipeline, in order:

| Skill | What it does |
|---|---|
| `plan-scaffold` | Creates the plan folder set and every contract from a session-shape declaration and a verse-distribution rule. |
| `plan-schedule` | Builds, audits and edits the day ↔ verse calendar; shifts a boundary verse and renames the affected day files in the same pass. |
| `plan-day-generate` | Authors the **authoring stream's** day files from the schedule, the rails and the fixed assets, section by section, then verifies them mechanically. |
| `plan-day-translate` | Produces each **translation stream's** day file from the authoring-stream day, matching sections by normalised heading text and retrieving verses by block ID. |
| `plan-day-qa` | Grades one day against the plan's own contracts; computed score, hard verdict gate, dated run appended to `<lang>/qa-report.md`. Never sets `complete`. |
| `plan-day-package` | Optional: builds the machine-anchored per-day dossier for an app consumer, and enforces it with reorder / conform / validate / guard. |

All six read their parameters from `About <plan-name>.md` and the stream's
contracts. If a skill needs a value that is not declared, the fix is to declare
it — never to hard-code it in the skill.
