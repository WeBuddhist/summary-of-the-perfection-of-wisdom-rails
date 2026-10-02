# <Plan title>

<One-line subtitle in the authoring language, optional.>

## Purpose

<What the plan is, how long it runs, how it is delivered, and how long one
session takes. Two or three sentences.>

- **Duration:** <N sessions over <span>>
- **Delivery:** <push notification / app / printed booklet / mailing list>
- **Session length:** <minutes>

## Audience

<Who reads this. Prior knowledge, what they already practise, what they have
not studied, time budget, and what they are sceptical of.>

## Streams

Exactly one stream is the **authoring stream**: its day files are written from
the rails. Every other stream is a **translation stream**: its day files are
produced by translating the authoring stream's day file, section by section.

| Stream | Language | Role | Status | Designated verse source |
|---|---|---|---|---|
| `<lang>` | <language> | authoring | <not started / in progress / complete> | `<path to the root text or the authoritative source>` |
| `<lang>` | <language> | translation | <status> | `<path to this stream's verse translation track>` |

**The verse source is exclusive.** For each stream, verse text is inlined
verbatim by block ID from the file named above and from no other file. If the
vault holds another file that also looks like this stream's verses, name it
here and state that it must never be quoted in a day file.

> ⚠️ Do not use `<path to the look-alike file>` — it is a different rendering
> of the same verses. <Delete this block if no look-alike exists.>

## Session shape

Every day file, in every stream, contains these sections in this order.

### Section-type declaration

| id | type | voice | ceiling | formula | absent | grounding |
|---|---|---|---|---|---|---|
| `<id>` | Fixed \| Extracted \| Generated \| Translated | neutral \| first person \| second person \| none | `<N words>` \| `<N syllables>` \| — | `"<required opening or closing phrase>"` \| — | required \| may be absent | `<assets/liturgy.md · verse source · rail layer · authoring-stream section>` |

- **Fixed** — reproduced character-for-character from `<lang>/assets/liturgy.md`
  every day. Never paraphrased, reordered or improved.
- **Extracted** — copied verbatim from the stream's verse source by block ID.
- **Generated** — composed for this day from the declared grounding, inside the
  declared ceiling, voice and formula.
- **Translated** — rendered from the matching section of the authoring stream's
  day file. Translation streams only.

A ceiling is a ceiling, not a target. Do not pad toward it.

### Headings by stream

| id | `<lang-1>` | `<lang-2>` | `<lang-3>` |
|---|---|---|---|
| `<id>` | `<heading as written in the day file>` | `<heading>` | `<heading>` |

### Heading aliases (used by `plan-day-translate`)

Sections are located by normalised heading text, never by number or position.
List every spelling that appears in the authoring stream's day files on disk,
including historical ones.

| id | accepted headings in the authoring stream |
|---|---|
| `<id>` | `<current heading>`, `<older heading still present on disk>` |

### Sub-block labels inside a section

<Only if a section has labelled sub-blocks. Give the label in each stream and
say which sub-blocks are carried and which are excluded.>

| Sub-block | `<authoring lang>` | `<target lang>` | Carried? |
|---|---|---|---|
| `<label>` | `<text>` | `<text>` | carried \| **excluded** |

## Practice categories

<Delete this whole part if the shape has no practice section.>

The practice explanation opens with exactly one category from this controlled
list, wrapped as `_(category)_`. Pick the one that genuinely fits; do not
default to the same one every day.

- `<category>` — <gloss>
- `<category>` — <gloss>

A category not on this list is a stop: propose a rendering, log it under the
stream's Pending terms, and ask before writing the day.

## Sources

- **Commentary mode:** `rails` \| `teaching-file`
  - `rails` — Generated commentary sections are synthesised from
    `$VERSES/<verse-id>.md`.
  - `teaching-file` — a single authoritative teaching is pre-assigned per day in
    `<path>` and **copied verbatim** into the day, never paraphrased or
    supplemented, with a citation line naming the blocks used.
- **Teaching-assignment file:** `<path>` <or: not applicable>
- **Source mode:** `rails` \| `direct-source`
  - `rails` (default) — the authoring stream cites `2-RAILS/` only.
  - `direct-source` — this plan declares that <named streams> may quote or
    transclude `1-SOURCES/` directly, because <reason>. Every day file that does
    so records `generation_note:` saying which source and why.
- **Rail dependencies:** `$VERSES/<verse-id>.md` (`status: complete` required);
  `$SECTIONS/<node-id>.md` for transition days.
- **Interim fallback:** <path, or "none — stop if the rail is not complete">.
- **Consumer:** `app` \| `notification` \| `obsidian`. <If not `obsidian`, verse
  text is **inlined** verbatim; `![[…]]` transclusion is not used.>

## Naming

- **Schedule:** `<lang>/schedule.md`, columns `| Day | Ch.Day | Verses | Index | Date |`.
- **Day files:** `<lang>/days/<pattern>` — e.g. `day-{day}-ch{chapter}-v{start}-{end}.md`.
  Single-verse days: `<pattern or "same, with start = end">`.
- **Folder grouping:** flat `days/` \| grouped `days/Chapter-{chapter} D{first}-D{last}/`.
- **Archive:** `<lang>/days/Archive/` — a day file is never overwritten in
  place; the previous version is moved here first.
- **Day number** is the absolute session number across the whole plan, never
  chapter-relative, in the filename, the `day:` frontmatter and the folder range.

## Status rules

- Day files are generated as `status: draft`.
- A domain specialist promotes a day to `complete` after reviewing it against
  the rails and this contract. **No skill and no model ever sets `complete`.**
- Only `complete` day files are published.
- A translation stream's day may not be promoted past the `status` of the
  authoring-stream day it was translated from.
- Rails must be `status: complete` before they ground a Generated section. If
  they are not, either use the declared interim fallback and record a
  `generation_note:`, or stop — never invent content.

## Reading path

- `<lang>/requirements.md` — per-stream style contract, in that language.
- `<lang>/termbase.md` — per-stream vocabulary contract.
- `<lang>/termbase-translation.md` — the translation fork (translation streams).
- `<lang>/schedule.md` — the calendar.
- `<lang>/assets/liturgy.md` — every Fixed section's text.
