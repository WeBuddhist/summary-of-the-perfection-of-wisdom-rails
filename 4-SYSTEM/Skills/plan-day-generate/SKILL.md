---
name: plan-day-generate
description: >
  Author one or more day files for a plan's **authoring stream** from the
  stream's schedule, the verse rails and the plan's fixed assets, section by
  section, following the section-type declaration in `About <plan-name>.md`:
  Fixed sections copied verbatim from `assets/liturgy.md`, Extracted sections
  inlined verbatim by block ID from the stream's designated verse source, and
  Generated sections composed inside their declared ceiling, voice and formula
  and grounded only in the day's rails (or, in `teaching-file` mode, copied
  verbatim from a pre-assigned teaching). Then verifies the result
  mechanically and reports out of band.

  Trigger on "generate day 45", "day-1", "days 20 to 35", "make the plan for
  days 100-105", "write the practice plan for day X", "fill in the day file",
  "generate this week's days".

  Use `plan-day-translate` for any stream that is not the authoring stream.
---

# plan-day-generate

Produces complete day files for the **authoring stream** of one plan. Each day
is a single file built from the sections the plan declares — some fixed, some
extracted, some generated — with every generated sentence grounded in that
day's rails.

**Generated vs fixed vs extracted — the core discipline of this skill.** Fixed
sections are reproduced character-for-character from `<lang>/assets/liturgy.md`,
every time, for every day — never paraphrased, reordered, or "improved".
Extracted sections are inlined verbatim by block ID from the stream's
designated verse source — not generated at all, and never retyped from memory.
Only Generated sections are composed, and they are composed inside a declared
ceiling, a declared voice, a declared formula, and a declared grounding source.

**Language discipline.** Every word of prose in the output is in the authoring
stream's language. The only foreign tokens permitted are `^chapter-verse` block
IDs (the vault's citation convention requires Arabic digits) and whatever the
plan's section headings themselves contain. Filenames and paths are filesystem
identifiers, not plan content, and are exempt.

**Reading level.** The register declared in `<lang>/requirements.md` §1 governs
every generated section, and it must be restated explicitly in every generation
prompt — do not rely on it being inferred. This rule governs register only: it
never licenses paraphrasing, omitting or softening the underlying content, and
it never applies to Fixed or Extracted sections, which are reproduced exactly as
attested however classical their language.

Correct output is a day file whose headings, order, ceilings, formulas and block
IDs pass `4-SYSTEM/Skills/plan-day-generate/scripts/check_day_file.py` with zero errors, where every
generated claim traces to a passage in the day's rails, and where the previous
version of the file — if there was one — is in `days/Archive/`, not overwritten.

---

## Inputs

Read all of these before writing anything. Every parameter comes from the
plan's own files; none is hard-coded here.

| Input | Where it comes from |
|---|---|
| Day number(s) | The user's request. Expand a terse form (`day-1`, `days 20 to 35`, `45, 46, 50`) into an explicit list before starting. |
| Session shape | `About <plan-name>.md` → **Session shape**: the section-type declaration, the headings for this stream, and the sub-block labels. |
| Schedule | `<lang>/schedule.md` — the day's chapter, verse range, index and date. |
| Verse source | `About <plan-name>.md` → **Streams**: the file this stream's verse text is inlined from. Authoring streams normally read the root text. |
| Rails | `2-RAILS/Verses/<verse-id>.md` for every verse in the day's range; `2-RAILS/Sections/<node-id>.md` for a transition day. |
| Fixed text | `<lang>/assets/liturgy.md` — one `##` block per Fixed section id. |
| Contracts | `<lang>/requirements.md` (register, forbidden elements, bands) and `<lang>/termbase.md` (vocabulary). |
| Practice categories | `About <plan-name>.md` → **Practice categories**. |
| Teaching file | `About <plan-name>.md` → **Sources**, when `commentary-mode: teaching-file`. |
| Naming | `About <plan-name>.md` → **Naming**: the day-file pattern, the folder grouping, the archive folder. |
| Section spec | The machine-readable form of the declaration, `<lang>/assets/section-spec.json` — scaffold it from `4-SYSTEM/Skills/plan-day-generate/templates/section-spec.json` the first time. |

If a required input is missing, stop and say which one. Do not substitute a
neighbouring file and do not guess a verse range.

## Output

One day file per requested day, at the path the plan declares, with
`status: draft`.

```
3-TRANSFORMATIONS/Plans/<plan>/<lang>/days/<declared pattern>
```

A previous version of that file, when one exists, is moved to
`<lang>/days/Archive/` before the new one is written.

---

## Output file format

The day file carries the frontmatter declared in `About <plan-name>.md`:

```yaml
---
day: <N>
chapter: <C>
verses: "<C>-<start> to <C>-<end>"
date: <YYYY-MM-DD>
transformation_type: plan-session
stream: <lang>
verse_source: <path the verse text was inlined from>
context_packages:
  - 2-RAILS/Verses/<verse-id>.md
pending_terms: []
generation_date: <YYYY-MM-DD>
generated_by: plan-day-generate
status: draft
---
```

Then the declared sections, in the declared order, each under the heading
declared for this stream. Nothing else goes on the page: no generation note, no
source list, no translator's note, no QA commentary. The day file is a
reader-facing document; everything a reviewer needs is reported in the reply.

A Generated section marked **may be absent** is dropped heading and all when its
source genuinely has nothing — and the absence is stated in the report, never
silently.

---

## Rules

1. **Never quote a verse from memory.** Open the stream's designated verse
   source, locate each verse by its `^chapter-verse` block ID, and copy the text
   exactly as written, including line-final punctuation and the block ID. If a
   block ID is missing from the file, stop and report it — do not substitute or
   invent the verse.
2. **Never let a generator retype a verse.** Where a Generated section must
   repeat a verse (a practice section quoting the verse it is built on), insert
   the already-verified text from the extraction step. A retyped verse drifts
   silently from the source.
3. **Preserve the source's line breaks** inside a verse. A verse lineated across
   four lines stays four lines; do not collapse it into a paragraph.
4. **Fixed sections are byte-identical** to their block in
   `<lang>/assets/liturgy.md`. No paraphrase, no reordering, no punctuation
   drift, no added or dropped lines.
5. **A generated section is grounded only in the day's declared source.** No
   outside knowledge, however plausible. If the rails are thin, the section is
   shorter or absent — never padded with general knowledge.
6. **Ceilings are ceilings, not targets.** Instruct against padding toward them,
   and prefer a shorter, well-chosen answer. Verify every ceiling with
   `check_day_file.py`, not by eye.
7. **The rail-status decision point is mandatory** (see Phase 1, Step 4). A day
   generated from rails that are not `status: complete`, without a
   `generation_note`, is a defect.
8. **Vary what is meant to vary.** Where the plan offers a list — practice
   categories, alternative opening formulas — the choice must follow what the
   commentary actually supports. Choosing the same one every day means the list
   is not being used.
9. **Never overwrite silently.** If the target file exists, archive the existing
   version to `<lang>/days/Archive/` and then write. Say in the reply that you
   did. This holds even when the existing file is an empty stub.
10. **Check the filename against the schedule before writing.** The day-file
    pattern encodes the chapter and verse range redundantly. A mismatch between
    the filename you resolved and the range you computed means either the
    schedule lookup or the file search went wrong — stop and report it.
11. **`status: draft`, always.** A skill never sets `complete`. That is a domain
    specialist's call.
12. **Report out of band.** Absent sections, out-of-band word counts, missing
    rails, ambiguities resolved, files archived — all of it goes in the reply,
    never into the day file.
13. **Do not write into `1-SOURCES/` or `2-RAILS/`.** This skill writes only
    under the stream's `days/` folder.

---

## Procedure

### Phase 0 — Parse the day request

Expand whatever the user gave into an explicit list of day numbers. Run Phases
1–3 once per day in the list; batch the lookups (schedule, verse source, rails)
where consecutive days share a chapter, so the same file is not re-read for
every day.

Read the plan's contracts once for the whole run: `About <plan-name>.md`,
`<lang>/requirements.md`, `<lang>/termbase.md`, `<lang>/assets/liturgy.md`.

### Phase 1 — Collect (per day)

Do all five steps, and read every file involved, before writing anything.

**Step 1 — Confirm the day exists.** Find the day's row in `<lang>/schedule.md`.
If there is no row, stop and report the gap rather than guessing a verse range.

**Step 2 — Resolve the verse range.** Read the range cell: `<C>.<start>–<C>.<end>`,
or `<C>.<verse>` for a single-verse day. Extract chapter, start verse, end verse.
Also take the date and, if present, the index.

**Step 3 — Extract the verses.** Open the stream's designated verse source and
locate each verse in the range by its block ID. Copy the text exactly (Rule 1).

**Step 4 — Rail-status decision point.** For every verse in range, check
`2-RAILS/Verses/<verse-id>.md`:

| Rail state | What to do |
|---|---|
| `status: complete` | Use it. This is the intended path. |
| exists but not `complete` | Use the interim source the plan declares, and record `generation_note:` in the day's frontmatter saying which source was used and why. |
| neither exists | **Stop and flag the dependency.** Do not invent content, and do not fall back to a commentary file the plan has not declared. |

Where `commentary-mode: teaching-file`, the day's commentary comes from the
pre-assigned teaching instead: open the teaching-assignment file, find this day's
section, and read the blocks assigned to it. The rail check still applies to any
*other* Generated section that is grounded in rails.

**Step 5 — Collect the grounding, layer by layer.** From each verse's rail, note
which layer feeds which Generated section, per the declaration's `grounding`
column: the commentary explanations, the attested stories and similes, the
scriptural quotations, the main teaching points, the key terms, the synthesis,
and the practical-application layer that grounds the practice line. If a verse's
rail is missing a layer a section depends on, note the gap explicitly — it
limits what that section can say. Do not invent material to fill it.

### Phase 2 — Compose, section by section

Walk the declaration in order. For each section, its `type` decides the method.

**Fixed** — copy the matching `##` block from `<lang>/assets/liturgy.md`
character-for-character under this stream's declared heading.

**Extracted** — paste the verses retrieved in Step 3, verbatim, each ending with
its block ID, in order. No commentary, no per-verse headers unless the plan
declares them, no editorialising.

**Generated** — for each one, assemble: the grounding material collected in
Step 5, quoted; the declared voice; the declared ceiling and its unit; the
declared opening or closing formula, spelled out; the register rule from
`<lang>/requirements.md` §1, stated explicitly; and the forbidden-elements list.
Then compose within those constraints.

- If a required **citation or ordinal phrase** is part of the formula, build it
  by hand from the reference tables in `<lang>/requirements.md` §6 **before**
  composing, and double-check it. Number words are irregular and easy to get
  wrong by guessing.
- A Generated section declared **may be absent** is left out entirely when the
  source has nothing standout to say. Do not manufacture something to fill it.
  If several good candidates exist, pick the one that best supports the rest of
  the day rather than stitching them together.
- A verbatim quotation inside a generated section keeps its own register; the
  plain-register rule applies to the sentences that introduce and explain it.

**Teaching-file mode.** When `commentary-mode: teaching-file`, the commentary
section is **not generated**. Copy the day's pre-assigned blocks verbatim from
the teaching-assignment file, preserving paragraph breaks, under the teaching
title the assignment file gives, and close the section with the citation line
the plan declares, naming the blocks used. Do not rephrase, summarise, or
supplement with any other material.

**The practice line** (a Generated section, wherever the plan places it) has its
own three tests. All three must hold:

1. **Actionable today.** One concrete action an ordinary person with no special
   training could complete today, in ordinary daily life. Not a vague
   aspiration, not a retreat activity, not a generic mindfulness statement that
   would fit any day. "Give lunch to someone who has none" passes; "contemplate
   impermanence and do not waste time" does not.
2. **Within the ceiling**, in the declared unit, in the declared voice — for a
   commitment, first person and forward-looking ("today I will…"), never second
   person and never a third-person description of a practitioner.
3. **Tagged with one category** from the plan's list, wrapped exactly as
   `_(category)_`, opening the explanation (not the practice line itself). The
   category must genuinely fit; do not default to the same one every day.

The explanation is a bridge: it says how *today's specific action* enacts *this
verse's* teaching, referencing what the verse actually says rather than making a
generic spiritual statement. Where the plan has a commentary layer, the practice
must draw on **both** the verse and that day's commentary. Its grounding is the
verse rail's practical-application layer, not free invention.

The action must trace back to what the chosen verse actually says. If the
connection to the verse is not clear, the action is wrong — not merely
under-explained.

Where the day covers several verses and the plan builds the practice around one,
choose the most concretely actionable verse in the range, and build all of the
practice sub-blocks around that one verse only.

### Phase 2a — Optional: generation by a second model

A plan may require that Generated sections be produced by a named generation
tool rather than written directly, to keep the prose out of the authoring
model's own voice. When it does, the same discipline applies either way: the
agent's job is to assemble the grounding and the constraints, make the call, and
then **verify the result mechanically** — counts by script, required formula
present, tag wrapper correct, grammar table honoured.

Mechanical cleanup of a tool's output (stripping stray markdown fencing or a
preamble, fixing the tag wrapper, correcting a grammar-table mismatch) is
cleanup, not authorship, and is expected. Composing the prose by hand when the
plan requires the tool is not. If the output violates a hard constraint —
language, register, a generic formulaic closing — regenerate with the failing
line quoted back as an explicit example of what not to repeat, rather than
hand-fixing it.

This phase is **optional**. When the plan names no generation tool, compose
directly under the same constraints and run the same verification.

### Phase 3 — Assemble and save

1. Concatenate the sections in the declared order, each under its declared
   heading, separated by a blank line. Prepend the document title if the plan
   declares one.
2. Write the frontmatter (Output file format above), including
   `context_packages:` listing every rail consulted, and `generation_note:` if
   the rail-status decision point required one.
3. Resolve the target path from the plan's naming pattern; if the plan groups
   days into chapter folders, resolve the folder first and create it if absent.
4. **Consistency check** — the chapter and verse range encoded in the filename
   must match the range computed in Step 2. On a mismatch, stop and report.
5. **Archive, then write.** If the target exists, move it to
   `<lang>/days/Archive/` first (keeping its name; add a numeric suffix if a file
   of that name is already archived), then write the new file.
6. Repeat for every day in the request.

### Phase 4 — Verify

Run the mechanical checker on every day produced, before considering it done:

```bash
python3 "4-SYSTEM/Skills/plan-day-generate/scripts/check_day_file.py" \
  --spec "3-TRANSFORMATIONS/Plans/<plan>/<lang>/assets/section-spec.json" \
  --verses "<C>-<start>,…,<C>-<end>" \
  "<the day file>"
```

It checks the frontmatter keys, the heading set and order, every ceiling, every
required formula, block-ID presence and contiguity, the forbidden-elements list
and the category tag. Fix every `ERROR` and re-run until it passes. A `warning`
about a band is reported, not padded away.

Then apply the two judgements a script cannot make:

**The authenticity test.** Each generated section must be specific to *these*
verses — not interchangeable with another day's. Swapping today's commentary
note with yesterday's should be immediately obvious. A section that names no
image, no stake and nothing particular to today has failed, however well it
reads.

**The grounding test.** For every claim in a generated section, name the rail
passage it came from. A claim you cannot locate is an addition — cut it.

Finally, report in the reply: which days were produced, which files were
archived, any section legitimately absent and why, measured counts with any that
fell outside their band, any rail that was missing or not `complete` and what
was used instead, and any ambiguity where a reading had to be chosen.

---

## Completion check

- [ ] Every requested day has a row in `<lang>/schedule.md`; none was guessed.
- [ ] The filename's chapter and verse range match the schedule's, verified
      before writing.
- [ ] Any pre-existing file was archived to `<lang>/days/Archive/`, not
      overwritten, and the archiving is stated in the reply.
- [ ] All declared sections are present, in order, under this stream's declared
      headings — except sections legitimately absent, which are named in the
      report with the reason.
- [ ] Fixed sections are byte-identical to their blocks in
      `<lang>/assets/liturgy.md`.
- [ ] Extracted sections contain only the day's verses, copied verbatim from the
      declared verse source, block IDs intact and contiguous, line breaks
      preserved, no commentary mixed in.
- [ ] Every Generated section is grounded only in the day's declared source, and
      every claim in it can be pointed to a specific rail passage.
- [ ] Every ceiling verified with `check_day_file.py`, not eyeballed; no section
      padded toward its ceiling.
- [ ] Every required opening or closing formula present and correct; any
      hand-built citation or ordinal phrase double-checked against the reference
      tables.
- [ ] The practice line passes all three tests: actionable today, within its
      ceiling in the declared voice, tagged with a category from the plan's list
      wrapped as `_(tag)_` — and the action traces to what the chosen verse says.
- [ ] Where the plan repeats a verse inside a generated section, that verse is
      the already-verified extracted text, not a retyped one.
- [ ] In `teaching-file` mode, the teaching blocks are verbatim, with the
      declared citation line, and nothing was paraphrased or supplemented.
- [ ] Rail-status decision point honoured: `complete` rails used, or a
      `generation_note` recorded, or the run stopped.
- [ ] `check_day_file.py` reports `[PASS]` with zero errors.
- [ ] The authenticity test passes: today's generated sections could not be
      swapped for yesterday's without it being obvious.
- [ ] `status: draft`; nothing marked `complete`.
- [ ] No note, source list or QA commentary was written into the day file.

---

## Known failure modes

- Writing a Generated section directly when the plan requires a named generation
  tool — or the reverse, calling a tool the plan does not name and then not
  verifying its output.
- Padding a section to reach its ceiling. The ceilings exist to force concision,
  not to be hit exactly.
- Filling a "may be absent" section with invented or general-knowledge material
  because the rail was thin. Leave it out instead and say so.
- Letting the generator retype the verse in a practice section instead of
  pasting the already-verified extracted text — introduces silent drift.
- Writing a practice line that is verse-agnostic ("be kind today", "notice your
  breath") rather than a commitment that traces to what the chosen verse says.
- Guessing a number word or an ordinal instead of composing it from the plan's
  reference table. Adjacent numbers often use different forms.
- Choosing the same practice category, or the same alternative opening formula,
  every day. Both lists exist precisely so the choice varies with what the
  commentary actually supports.
- Closing a generated section on a generic devotional formula that could be
  pasted onto any day. It reads as filler and fails the authenticity test.
- Creating a new file when the plan's day files already exist as stubs — or
  overwriting one without archiving it first.
- Writing without running the filename-vs-schedule consistency check, so a file
  ends up whose name disagrees with its content.
- Letting generated prose drift into the register of the commentary excerpts fed
  into it. The register rule must be restated in every generation prompt, not
  assumed.
- Reaching into a commentary file directly because the rail feels thin. Rails
  are the declared source; `1-SOURCES/` is reachable only when the plan declares
  `source_mode: direct-source`.
- Mixing numeral systems inside plan prose, when the stream's language has its
  own (Arabic digits are fine only in block IDs and file paths).
