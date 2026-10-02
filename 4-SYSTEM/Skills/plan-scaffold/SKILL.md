---
name: plan-scaffold
description: >
  Create a new calendar-driven plan track under `3-TRANSFORMATIONS/Plans/` from a
  session-shape declaration and a verse-distribution rule. Writes the plan root
  brief `About <plan-name>.md` — purpose, duration, audience, the authoring
  stream and the translation streams, the section-type declaration table, the
  practice-category list, the designated verse source per stream, the commentary
  source mode, the day-file naming pattern, the heading-alias table and the
  status rules — and then, for every declared stream, `requirements.md`,
  `termbase.md`, an optional `termbase-translation.md` fork, `schedule.md`,
  `assets/liturgy.md`, `days/` and `communications/`.

  Trigger on "start a new plan", "scaffold a plan", "set up a daily practice
  plan", "create a 365-day plan", "new study plan for this text", "add a
  language stream to <plan>", "make the plan folder", "we need an About file
  for the plan".

  This skill only creates the contracts and the empty folders. `plan-schedule`
  fills the calendar, `plan-day-generate` writes the authoring stream's days,
  `plan-day-translate` produces the other streams.
---

# plan-scaffold

Creates the folder set and the governing contracts for one plan track, so that
every later skill in the plan pipeline reads its parameters out of the plan's
own files instead of having them hard-coded.

A plan is a **calendar** (which verses on which day), a **session shape** (what
a day file contains, section by section), and a set of **streams** (one
language each). This skill writes all three down before any day is generated.
The recurring failure it prevents is a plan whose shape lives only in a
generator skill: when that happens the evaluator drifts out of sync with the
generator, a second language stream invents its own section list, and nobody
can say what the contract actually is.

Correct output is a plan folder whose `About <plan-name>.md` answers, without
reference to any skill file, every question the rest of the pipeline asks:
which stream is authored and which are translated, what sections a day has and
of what type, what each section's ceiling and voice are, where verse text comes
from for each stream, and what a day file is called.

**Nothing in this skill is language-specific or text-specific.** Every
liturgy text, heading, emoji, ceiling, category name and commentator name is a
value the human contributor supplies; the templates carry placeholders, never
content from another vault.

---

## Inputs

Gather all of the following before writing anything. Where the human has not
decided, ask — do not pick a default for them and do not copy a value from
another plan in this vault or another vault.

| Input | Description | Example |
|---|---|---|
| `plan-name` | Folder name under `3-TRANSFORMATIONS/Plans/`. Lowercase, hyphenated, no diacritics. | `one-year-practice` |
| `purpose` | What the plan is for, in two or three sentences. | a morning practice arc delivered by phone notification |
| `duration` | Number of sessions and the calendar span. | 365 days, one year |
| `audience` | Who reads it: prior knowledge, time budget, delivery channel. | lay readers new to the commentarial tradition, 5–10 minutes |
| `authoring-stream` | The one language whose day files are authored from rails. | `bo` |
| `translation-streams` | Every other published language. | `en`, `hi` |
| `session-shape` | The ordered section list with, per section: id, display heading per stream, type, voice, ceiling, required opening/closing formula, whether it may be absent, and its grounding source. | see *Section-type declaration* below |
| `practice-categories` | The controlled list a practice line's explanation is tagged with, if the shape has a practice section. | supplied by the human, in the authoring language |
| `verse-source` per stream | The file each stream's verse text is inlined from, by block ID. | authoring: `1-SOURCES/Text/<root>.md`; `en`: `3-TRANSFORMATIONS/Translations/<track>/<file>.md` |
| `commentary-mode` | `rails` (synthesise from `2-RAILS/Verses/<id>.md`) or `teaching-file` (copy verbatim from a pre-assigned teaching file). | `rails` |
| `teaching-file` | Required only when `commentary-mode: teaching-file`: the path of the day→teaching assignment file. | `3-TRANSFORMATIONS/Plans/<plan>/assets/teaching-assignment.md` |
| `source-mode` | `rails` (default) or `direct-source`. `direct-source` is the declared, recorded exception that lets a stream transclude or quote `1-SOURCES/` directly. | `rails` |
| `verse-distribution` | Verses per day, start date, and any dates to skip. | 2 verses/day, start 2026-07-06, skip Sundays |
| `naming` | The day-file name pattern and whether `days/` is flat or grouped. | `day-{day}-ch{chapter}-v{start}-{end}.md`, flat |
| `consumer` | Who reads the day files: `app` / `notification` / `obsidian`. Decides inline-vs-transclude. | `app` |

If a needed input is missing, stop and ask. A plan scaffolded with guessed
parameters is worse than no plan, because the day generator will honour the
guesses.

---

## Output

```
3-TRANSFORMATIONS/Plans/<plan-name>/
├── About <plan-name>.md              # the cross-stream brief — the contract
└── <lang>/                           # one folder per stream, authoring first
    ├── requirements.md               # style contract, written in that language
    ├── termbase.md                   # vocabulary contract
    ├── termbase-translation.md       # translation streams only (fork)
    ├── schedule.md                   # day-by-day calendar for this stream
    ├── days/                         # per-session output files (empty)
    ├── communications/               # cross-day outreach copy (empty)
    └── assets/
        └── liturgy.md                # every Fixed section's text, verbatim
```

Templates for each file ship in `4-SYSTEM/Skills/plan-scaffold/templates/`. Copy the template, fill
every placeholder, and delete every unused optional block — a scaffolded file
that still contains `<…>` placeholders is not done.

---

## Output file format

### `About <plan-name>.md` — the declaration

Eight required parts, in this order. The rest of the pipeline reads them by
heading, so keep the heading wording.

1. **Purpose** — what the plan is, its duration, and its delivery channel.
2. **Audience** — prior knowledge, time budget, what they are sceptical of.
3. **Streams** — one row per language: code, role (`authoring` /
   `translation`), status, and the designated verse source for that stream.
4. **Session shape** — the section-type declaration table (below) plus the
   per-stream heading table.
5. **Practice categories** — the controlled list, if a practice section exists.
6. **Sources** — commentary mode, source mode, rail dependencies, and (when
   `commentary-mode: teaching-file`) the teaching-assignment file.
7. **Naming** — day-file pattern, folder grouping, schedule path.
8. **Status rules** — what `draft` / `partial` / `complete` mean here and who
   may set `complete`.

#### Section-type declaration

The table every generator, translator and evaluator reads:

| Column | Meaning |
|---|---|
| `id` | Stable machine id for the section, e.g. `opening`, `verses`, `commentary`, `practice`. Never changes, even if the display heading does. |
| `type` | `Fixed` · `Extracted` · `Generated` · `Translated` (defined below). |
| `voice` | `neutral` / `first person` / `second person` / `none` (for verse-only sections). |
| `ceiling` | A hard maximum, with its unit — `150 words`, `300 syllables` — or `—`. A ceiling is a ceiling, never a target. |
| `formula` | A required opening or closing phrase, quoted verbatim, or `—`. |
| `absent` | `may be absent` when the section is legitimately dropped if its source has nothing, otherwise `required`. |
| `grounding` | Where the content must come from: `assets/liturgy.md`, the verse source, a named rail section, the authoring-stream day file. |

The four types:

- **Fixed** — reproduced character-for-character from `<lang>/assets/liturgy.md`
  every day, for every day. Never paraphrased, reordered or "improved".
- **Extracted** — copied verbatim from the stream's designated verse source by
  block ID. Not generated at all.
- **Generated** — composed for this day from the day's grounding material,
  within the declared ceiling, voice and formula.
- **Translated** — rendered from the corresponding section of the authoring
  stream's day file. Only translation streams have these.

Example row set (the ids are generic; the headings, ceilings and formulas are
whatever the human declares):

```markdown
| id | type | voice | ceiling | formula | absent | grounding |
|---|---|---|---|---|---|---|
| refuge    | Fixed     | none         | —            | —                | required      | assets/liturgy.md |
| opening   | Generated | neutral      | 60 words     | "<citation phrase>" | required   | verse rail synthesis |
| verses    | Extracted | none         | —            | —                | required      | verse source, by block ID |
| commentary| Generated | neutral      | 150 words    | —                | may be absent | verse rail: commentary layer |
| dedication| Fixed     | none         | —            | —                | required      | assets/liturgy.md |
| practice  | Generated | first person | 30 syllables | category tag `_(…)_` | required | verse rail: practical application |
```

Then the per-stream headings, one row per section:

```markdown
| id | bo | en | hi |
|---|---|---|---|
| opening | <heading> | <heading> | <heading> |
```

And the **heading-alias table** used by `plan-day-translate` when it matches
sections in the authoring stream's day files by normalised text: every accepted
spelling of each section's heading, including historical ones still on disk.

```markdown
| id | accepted headings in the authoring stream |
|---|---|
| commentary | `<current heading>`, `<older heading still in use>` |
```

Declare an alias the moment a second spelling appears on disk. A translator
that matches a section by position instead of by text will eventually render a
dedication as a practice instruction.

### Day-file frontmatter

Declared here once so every generator writes the same keys:

```yaml
---
day: <N>
chapter: <C>
verses: "<C>-<start> to <C>-<end>"
date: <YYYY-MM-DD>
transformation_type: plan-session
stream: <lang>
translated_from: <path to the authoring-stream day file, or omit>
verse_source: <path the verse text was inlined from>
context_packages:
  - 2-RAILS/Verses/<verse-id>.md
pending_terms: []
generation_date: <YYYY-MM-DD>
generated_by: <skill name>
status: draft
---
```

---

## Rules

1. **One authoring stream.** Exactly one stream is authored from rails; every
   other stream is translated from it. That is what keeps the streams saying
   the same thing on the same day. A plan that authors two streams
   independently from the rails will diverge, and no QA check can pull it back.
2. **The `About` file is the contract, not the skills.** Any parameter a later
   skill needs — section list, ceilings, categories, verse sources, naming —
   goes here. If a generator needs a value that is not declared, the fix is to
   declare it, never to hard-code it in the skill.
3. **Fixed text lives in `assets/liturgy.md`, once per stream.** Never inside a
   skill, never duplicated across day files' templates. Each Fixed section is a
   `##` block in that file keyed by its section id.
4. **Every ceiling carries its unit** and is enforced mechanically, not by eye.
   Word ceilings for alphabetic scripts, syllable ceilings for Tibetan.
5. **Declare the verse source per stream, by file.** The authoring stream reads
   the root text; each translation stream reads its own designated translation
   track file. Two files in the same vault that both look like "the English
   verses" is the single most expensive mistake observed in a plan — name the
   one that is authorised and say plainly that the other must never be used.
6. **`source-mode: direct-source` is a declaration, not a default.** The
   citation chain is `1-SOURCES/ → 2-RAILS/ → 3-TRANSFORMATIONS/`. A stream may
   quote or transclude `1-SOURCES/` directly only when `About <plan>.md`
   declares `source_mode: direct-source`, and each day file that does so
   records it in `generation_note`. Without the declaration, it is a defect.
7. **Inline by default; transclude only for Obsidian.** Day files consumed by
   an app or a notification system must inline verse text verbatim by block ID.
   Use `![[…]]` transclusion only when `consumer: obsidian` is declared.
8. **`termbase-translation.md` is a fork, not a copy.** It carries
   `forked_from:` pointing at the stream's `termbase.md`, a "Pending terms"
   table, and only the rules that differ for translation. Two unlinked
   termbases in one stream drift within a chapter.
9. **Never write into `1-SOURCES/`.** This skill writes only under
   `3-TRANSFORMATIONS/Plans/<plan-name>/`.
10. **Never overwrite an existing plan file.** If `About <plan-name>.md` or any
    stream contract already exists, stop, report the conflict, and ask. Adding
    a *new* stream to an existing plan is fine; rewriting a contract is a human
    decision.
11. **Scaffold is not generation.** This skill creates no day files and fills
    no schedule rows by hand. The calendar comes from `plan-schedule build`.

---

## Procedure

### Step 1 — Resolve scope

Confirm the plan name, the streams and their roles, and whether this is a new
plan or a new stream on an existing plan. Check
`3-TRANSFORMATIONS/Plans/<plan-name>/` — if it exists, list what is already
there and confirm with the human before touching anything.

### Step 2 — Agree the session shape

Work through the section list with the human, one section at a time, filling
every column of the declaration table. For each section ask explicitly:

- What is its id, and its heading in each stream?
- Is it Fixed, Extracted, Generated or Translated?
- Whose voice — neutral, first person, second person?
- What is its hard ceiling, in what unit?
- Is there a required opening or closing formula?
- May it be legitimately absent, and on what condition?
- What exactly grounds it — which file, which layer of the rail?

A section whose grounding cannot be named is not ready to be declared. Say so
rather than writing a row you cannot enforce.

### Step 3 — Write `About <plan-name>.md`

From `4-SYSTEM/Skills/plan-scaffold/templates/About-plan.md`. Fill all eight parts. Leave the
heading-alias table with one row per section (the current heading only) — it
grows as variants appear.

### Step 4 — Create each stream folder

Authoring stream first, then translation streams. For each:

1. `requirements.md` from the template — **written in that stream's language**,
   not in English. It carries the register rules, the sentence-length rules, the
   forbidden elements, and the per-section rendering conventions. The section
   *list* stays in `About <plan>.md`; `requirements.md` says how this language
   renders it.
2. `termbase.md` from the template. Where the vault has a consolidated
   `2-RAILS/Bilingual-Glossaries/<src>-<tgt>.md`, seed it with `glossary-select`; otherwise leave
   the table empty with its columns in place.
3. For translation streams: `termbase-translation.md` from the template, with
   `forked_from:` set and an empty "Pending terms" table.
4. `assets/liturgy.md` from the template — one `##` block per Fixed section id.
   Paste the human-supplied text verbatim. Do not translate a Fixed block from
   another stream; each stream's liturgy is its own attested text.
5. Empty `days/` and `communications/` folders.

### Step 5 — Build the calendar

Hand the verse-distribution rule to `plan-schedule`:

```bash
python "<plan-schedule-skill-dir>/scripts/plan_schedule.py" build \
  --root "<root text path>" \
  --verses-per-day <N> --start-date <YYYY-MM-DD> \
  [--skip-weekday Sun] [--skip-date <YYYY-MM-DD>] \
  --out "3-TRANSFORMATIONS/Plans/<plan-name>/<lang>/schedule.md"
```

Then run `plan-schedule audit` on the result and paste nothing by hand. Each
stream gets its own `schedule.md`; when two streams share a calendar, generate
each from the same rule rather than symlinking or cross-referencing.

### Step 6 — Seed day 1 only

Do not generate day files here. Confirm to the human that the next step is
`plan-day-generate` for day 1 of the authoring stream, reviewed to `complete`
before day 2, and `plan-day-translate` for the other streams.

### Step 7 — Report

State what was created, every placeholder still unfilled, and every input the
human still has to decide. Report in the reply, not in the files.

---

## Completion check

- [ ] `About <plan-name>.md` exists and contains all eight parts, with no `<…>`
      placeholder left.
- [ ] Exactly one stream is marked `authoring`; every other is `translation`.
- [ ] The section-type declaration table has every column filled for every
      section, with units on every ceiling.
- [ ] Every section has a heading declared for every stream, and a row in the
      heading-alias table.
- [ ] Every stream names its own verse source file, and the file exists.
- [ ] `commentary-mode` is declared; if `teaching-file`, the teaching-assignment
      file exists.
- [ ] `source_mode` is declared; if `direct-source`, the reason is stated.
- [ ] Each stream has `requirements.md` (in that language), `termbase.md`,
      `schedule.md`, `assets/liturgy.md`, `days/`, `communications/`.
- [ ] Translation streams additionally have `termbase-translation.md` with
      `forked_from:` set and a Pending terms table.
- [ ] Every Fixed section id has a matching `##` block in each stream's
      `assets/liturgy.md`.
- [ ] `schedule.md` was produced by `plan-schedule build`, not typed, and
      `plan-schedule audit` reports no issues.
- [ ] Nothing was written outside `3-TRANSFORMATIONS/Plans/<plan-name>/`, and no
      pre-existing file was overwritten.
