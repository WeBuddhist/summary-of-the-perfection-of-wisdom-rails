---
name: plan-day-translate
description: >
  Produce a translation stream's day file by translating the authoring stream's
  day file section by section — locating each section by normalised heading text
  (never by number or position), retrieving verse text by block ID from that
  stream's own designated verse translation, obeying the stream's
  `termbase-translation.md` fork and its pending-terms loop, then auditing the
  result back against the source with fresh eyes.

  Trigger on "translate day 24", "make the English and Hindi days for day 30",
  "fill in the <lang> day file", "generate the <lang> stream for days 40-45",
  "we need the other languages for this week".

  This is the only path to a non-authoring stream's day file. Do not
  re-synthesise a translation stream's day from the rails — that is what makes
  the streams say different things on the same day.
---

# plan-day-translate

Produces a complete day document for one or more **translation streams** by
translating the **authoring stream's** day file, not by synthesising from
commentary rails.

The editorial premise: the authoring stream's day file is the source of truth,
and every other stream's day is a rendering of it. That is what keeps the
language streams saying the same thing on the same day.

## Translation discipline — the core rule

Do not consult `2-RAILS/`. Do not add explanation, context, or a "point" the
source day does not make. Do not drop anything it does make.

If a sentence in your output has no parent clause in the source, delete it —
even if it reads well, even if it is true, even if a reader would benefit. This
is the difference between this skill and a rails-based generator, and it is the
whole reason the streams stay aligned.

---

## Inputs

| Input | Where it comes from |
|---|---|
| Day number(s) | The user's request. |
| Source stream | `About <plan-name>.md` → **Streams**, the row marked `authoring`. |
| Target stream(s) | `About <plan-name>.md` → the `translation` rows. Default: all of them. |
| Which sections are carried | `About <plan-name>.md` → the section declaration: every section of type `Translated`. Sections of type `Fixed` in the target stream come from that stream's own `assets/liturgy.md`; sections the plan does not carry are not translated at all. |
| Heading aliases | `About <plan-name>.md` → **Heading aliases** — every accepted spelling of each source section's heading. |
| Sub-block labels | `About <plan-name>.md` → **Sub-block labels**: which labelled sub-blocks are carried and which are excluded, and each one's label in the target stream. |
| Verse source per stream | `About <plan-name>.md` → **Streams**: this stream's designated verse translation file. |
| Contracts | `<lang>/requirements.md` (register, bands, forbidden elements) and `<lang>/termbase-translation.md` (vocabulary — **not** `termbase.md`). |
| Naming | `About <plan-name>.md` → **Naming**: output pattern, folder grouping, archive folder. |

Verify the source day file exists and is populated before starting. **An empty
or stub source file is a stop, not a guess.** Verify the verse range against the
stream's `schedule.md`.

Translate **each target stream directly from the authoring stream**, never one
translation from another. A language that carries this material natively loses
that by pivoting through a third language, which imports the pivot's
compromises. Reconcile the streams for parity at Step 6.

## Output

One day file per target stream, at the path the plan declares, with
`status: draft`. A previous version is archived, never overwritten.

---

## Output file format

```yaml
---
day: <N>
chapter: <C>
verses: "<C>-<start> to <C>-<end>"
date: <YYYY-MM-DD>
transformation_type: plan-session
stream: <lang>
translated_from: <path to the authoring-stream day file>
verse_source: <this stream's designated verse translation>
context_packages: []
pending_terms: []
generation_date: <YYYY-MM-DD>
generated_by: plan-day-translate
status: draft
---
```

Then the sections the plan declares for this stream, in the plan's order, under
this stream's declared headings, with the plan's declared sub-block labels.

**No translation note goes in the file.** The day file is a reader-facing
document and ends after its last declared section. Everything a reviewer needs —
sections that fell outside their word band and why, terms added to
`pending_terms`, places the source was ambiguous and a reading had to be chosen,
structural irregularities in the source, and anything the audit corrected — is
reported in the reply at Step 8, not written into the day file.

Never set `status: complete`. That is a domain specialist's call.

---

## Rules

1. **Match sections by normalised heading text, never by number or position.**
2. **Never translate a verse fresh** — retrieve it by block ID from this
   stream's designated verse source.
3. **Never consult the rails.** The source day file is this skill's only content
   source.
4. **Obey `termbase-translation.md`, not `termbase.md`.** The latter governs
   authored content and carries authoring-only rules.
5. **Excluded sub-blocks stay excluded**, exactly as the plan lists them.
6. **Word-count bands are diagnostics, not targets.** Never pad or trim to hit
   one.
7. **An unknown term is logged, never improvised silently** (Step 4).
8. **Never overwrite a day file.** Archive the existing version first.
9. **Report in the reply, never in the file.**
10. **`status: draft`, always.**

---

## Procedure

### Step 0 — Scope and preconditions

Resolve the day list, confirm the source day file exists and is populated at the
path the plan's naming pattern gives, and confirm the verse range against
`schedule.md`. Load the plan's declaration, the heading-alias table and the
sub-block table before reading any day.

### Step 1 — Locate the sections by heading, never by number

Neither the numbering, the heading level, nor the section order is guaranteed
stable across a long plan. A section's heading can be spelled two ways in two
chapters; a neighbouring track can use the same ordinal for a different section;
a later chapter can drop the numerals entirely and move one section ahead of
another. **A skill that grabs "section six" will eventually render a dedication
as a practice instruction.**

**Normalise before matching.** Strip the leading `#` marks, any emoji, any
numeral (in whatever numeral system) and its punctuation, and trailing
whitespace or `:` — then compare the bare phrase against the plan's
heading-alias table.

Two rules the alias table exists to encode:

- **A section may have more than one accepted heading.** Two spellings in two
  chapters are the same section under two names. Take them as such.
- **A heading phrase may be ambiguous.** The same word can appear as a
  top-level section heading, as a per-verse sub-heading, and as a bold sub-label
  inside another section. Match an ambiguous phrase **only at the declared
  section heading level**, never anywhere it occurs.

Shape checks, per the plan's declaration: a section declared as a single
paragraph is one paragraph; a section declared as continuous prose has no block
quotes; a section declared with labelled sub-blocks opens with a label. If a
slot is missing, empty, or fails its check, **stop and report** — do not
substitute a neighbouring section.

### Step 2 — Parse labelled sub-blocks

Sub-labels vary by chapter and by file. They appear as bold text, as headings of
various levels, or as headings with a trailing colon. Normalise the same way as
Step 1 — strip heading marks, bold markers and any trailing `:` — then match the
bare phrase against the plan's sub-block table.

Translate only the sub-blocks the table marks as carried, using that table's
label for this stream. The excluded ones — notes, supplements, key-term lists,
and the repeated-verse block that closes a practice section — are production
artefacts or restate a verse already carried elsewhere in the day. Carry none of
them.

Note that the same label can mean two different things at two different levels:
a heading that reads "explanation" inside a practice block is the practice's
explanation sub-label, not the day's commentary section. Match by level, not by
word.

**Practice-category label.** This is controlled vocabulary, and
**`termbase-translation.md` holds it, not this file or the plan's skills** —
duplicating it would create two places to edit and two places to drift. A
category not in the termbase table is a stop: propose a rendering, log it under
the termbase's "Pending terms", and ask before writing the day.

### Step 3 — Verses, and verse lines quoted inside a section

Both come from the same place, by block-ID lookup from **this stream's**
designated verse source. **Never translate a verse fresh.** That source is the
only one; do not substitute another file, even one that looks equivalent.

- **The verse block:** one block per verse in the day's range, verbatim, block
  IDs contiguous and matching the `verses:` frontmatter. Reproduce the source's
  lineation and keep the trailing block ID. The source day's own formatting of
  its verses does not change this stream's output format, which follows the
  plan's declaration.
- **Verse lines quoted inside another section:** the source often quotes a
  *partial* verse. Take the matching span, strip the trailing block ID marker,
  and do not re-lineate what you take.

If a block ID is absent from the verse source, **stop and ask** — do not
improvise and do not fall back to another file.

### Step 4 — Translate, one register per section

Load the contracts first: `<lang>/requirements.md` and
`<lang>/termbase-translation.md`.

**The register rules live in `<lang>/requirements.md`**, not in this skill: the
reading level, the sentence-length limit, the honorific policy, the diacritics
policy, the forbidden elements, and the per-section voice. Read them and apply
them. Two rules recur across streams strongly enough to be worth stating here as
the shape of what that file should say:

- **Break the period.** Commentarial prose in many source languages runs long
  chained clauses landing on a single closing particle. One such clause becomes
  five or six short sentences. Most "awkward translation" is a target-language
  sentence still wearing the source language's syntax, not a wrong word.
- **Names versus epithets.** Keep genuine terms of art and proper names. Render
  epithets and descriptive titles **plainly** — "great bodhisattvas who have
  reached the highest stages", not "lords of the tenth bhumi"; "body, speech and
  mind", not "the three doors". Rendering an epithet as transliterated jargon in
  a sentence otherwise aimed at a beginner is what makes the text unreadable,
  and it is usually done out of reverence rather than necessity. The same
  principle governs ordinary high-frequency vocabulary: the scholarly
  alternative is never the right answer in a plain-register stream. The full
  tables are in the termbase.

Per-section notes come from the plan's declaration: a section declared
**neutral / third person** keeps its attributions exactly as the source states
them — never drop an attribution for smoothness, and never sharpen a vague one
("as the commentaries say") into a named commentator the source does not name. A
section declared **first person and forward-looking** stays that way: converting
a commitment into an instruction flips the section from commitment to command
and is the most common failure in a practice section. A commentary section that
is **narrative** rather than expository is translated as a story: keep the
sequence of events in order, keep the names, and let it run as narrative rather
than flattening it into a summary of its moral. The no-additions rule is
unchanged — do not supply motivation, scene-setting or a closing lesson the
source does not state. A story's ending is usually its point, and the source
states it; do not restate it a second time in your own words.

**Word counts are a diagnostic, not a target.** The plan's bands are in
`<lang>/requirements.md` §5. Do not pad or trim to hit them. Translation length
is set by the source. If a section lands outside its band, that means the source
section is unusually long or short — say so when reporting at Step 8 and leave
the text faithful. Padding to reach a word count is exactly the addition this
skill exists to prevent.

**Unknown terms — never improvise silently.** For any term not in the termbase
fork: check the termbase, then check already-translated days for existing usage,
then pick a rendering **and log it** in two places — the day file's
`pending_terms:` frontmatter, and the termbase's own "Pending terms" table with
the day it first appeared in.

**Closing the loop.** A pending term is not a permanent state. When a human
approves one, it moves into the relevant termbase table, drops off the pending
list, and is cleared from the `pending_terms:` of any day file that carries it,
next time that file is touched. Before generating a new day, check whether any
term it needs is already sitting pending from an earlier day — reuse the pending
rendering rather than inventing a second one. An entry older than one chapter of
generation means the review step is not happening; say so when reporting.

### Step 5 — Output files

Resolve each target path from the plan's naming pattern and folder grouping.
Match an existing filename exactly where one is present — do not invent a
variant spelling of the range.

#### ⚑ Overwrite guard

Days may already have files at these paths, produced by an earlier generator.
**Never overwrite one silently.** If the target exists: say so, get explicit
human confirmation, and on approval move the existing file to the plan's
`days/Archive/` folder beside it rather than destroying it.

### Step 6 — Back-mapping audit

Do not deliver on your own read of what you just wrote. Run a **separate pass
with fresh eyes** — ideally a subagent with no memory of the drafting, since a
drafter reliably cannot see their own additions. Give it the source day file and
the output, and instruct it to find violations, not to summarise or approve:

1. **Additions.** For every output sentence, name the source clause it came
   from. No parent means it is an addition — cut it.
2. **Omissions.** For every source clause, name where it landed. No child means
   it was dropped — restore it. Closing and payoff sentences go missing most.
3. **Attribution drift.** Every name and every vague attribution ("as the
   commentaries say") in the source is present in the output, unchanged in
   specificity.
4. **Person and tense.** Every section still carries the voice the plan declares
   for it, in every stream.
5. **Parity.** All target streams carry the same content — same number of
   claims, same closing.
6. **Register.** No sentence over the stream's declared limit. No calqued
   phrasing. No word repeated more than twice in a section. Pronouns resolve
   unambiguously — if it is not obvious who a pronoun refers to, name the
   referent.
7. **Practice repetition.** Check the two previous days. Runs of similar verses
   produce similar practices, and if a distinguishing half of the source
   instruction gets dropped, two days end up with the same action.

Verify each finding against the source yourself before acting on it. The auditor
can also be wrong.

### Step 7 — Mechanical checks

Script these; do not eyeball. `plan-day-generate`'s
`scripts/check_day_file.py --spec <stream's section-spec.json>` covers most of
them; the rest are per-stream:

- Verse block IDs contiguous and matching the `verses:` frontmatter.
- Verse text byte-identical to the source span (trailing block ID retained in
  the verse block, stripped in inline quotes elsewhere).
- Heading text and order match this stream's declaration exactly, including its
  own numeral system.
- Sub-labels exactly as the plan's sub-block table gives them for this stream.
- Practice-category label present, correctly wrapped, and drawn from the
  termbase's category table.
- No forbidden element from `<lang>/requirements.md` §4.
- Word counts measured per section (count them with a script, do not estimate)
  and reported at Step 8, with any out-of-band section named.
- Excluded sub-blocks absent from the output.

### Step 8 — Deliver

Write the files, honouring the overwrite guard. The files themselves contain
only the declared content blocks — no note, no commentary on the translation.

Report the following **in the reply, not in the file**:

- Which day(s) were produced, for which streams, and whether any existing file
  was archived.
- Measured word counts per section, naming any that fell outside its band and
  why the source made that unavoidable.
- Any `pending_terms` awaiting approval, and any that have been pending longer
  than a chapter.
- Anything the Step 6 audit found and how it was resolved.
- Any place the source was ambiguous and a reading had to be chosen, and any
  structural irregularity in the source file.

---

## Completion check

- [ ] The source day file exists, is populated, and its verse range matches
      `schedule.md`.
- [ ] Every section was located by normalised heading text against the plan's
      alias table — none by number or position.
- [ ] Every ambiguous heading phrase was matched only at the declared section
      level.
- [ ] Verse text was retrieved by block ID from this stream's designated verse
      source; no verse was translated fresh; no other file was used.
- [ ] Only the carried sub-blocks were translated; every excluded sub-block is
      absent from the output.
- [ ] `termbase-translation.md` was used, not `termbase.md`; every new term is
      logged in both `pending_terms:` and the termbase's Pending terms table.
- [ ] No sentence in the output lacks a parent clause in the source, and no
      source clause is missing from the output — verified by a fresh-eyes audit,
      not by the drafter.
- [ ] Every section carries the voice the plan declares for it.
- [ ] All target streams carry the same content, claim for claim.
- [ ] No section was padded or trimmed to hit a band; out-of-band sections are
      named in the report.
- [ ] Any pre-existing file was archived on explicit human approval, never
      overwritten.
- [ ] Mechanical checks run by script and passing.
- [ ] No translation note, source list or QA commentary in the day file.
- [ ] `status: draft`.

---

## Known failure modes

- Locating a section by number and rendering the dedication as a practice.
- Translating a verse fresh instead of retrieving it, so the same verse reads
  two different ways across the plan.
- Converting a first-person commitment into a second-person instruction.
- Padding or trimming a section to hit a word count, which means adding or
  cutting content the source does not have.
- Preserving the source's sentence length, producing a grammatical but
  unreadable paragraph.
- Rendering an epithet as transliterated jargon in a sentence otherwise aimed at
  a beginner.
- Adding a clarifying clause that is true and helpful but absent from the source
  — the characteristic failure of meaning-based translation.
- Dropping a vague attribution as filler, or resolving it to a named commentator
  the source does not name.
- Reaching into `2-RAILS/` because a section feels thin. It is not this skill's
  source.
- Failing to recognise an aliased heading and stopping on a day that is
  perfectly translatable.
- Matching an ambiguous heading phrase against a sub-label and translating a
  practice explanation as though it were the commentary section.
- Assuming a section's position is stable across chapters. It is not; position
  tells you nothing.
- Pivoting one translation stream through another instead of translating each
  directly from the authoring stream.
