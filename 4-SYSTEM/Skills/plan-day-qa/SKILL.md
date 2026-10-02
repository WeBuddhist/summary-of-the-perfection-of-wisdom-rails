---
name: plan-day-qa
description: >
  Grade one plan day file against the plan's own contracts — structure and
  fidelity against the section declaration in `About <plan-name>.md`, grounding
  against the rails (authoring stream) or the authoring-stream day file
  (translation streams), voice and style against `<lang>/requirements.md`, and
  the declared limits — producing a scorecard with a severity per failure, the
  offending text quoted, a one-line fix, a computed score out of 10 and a hard
  verdict gate. Appends each dated run to `<lang>/qa-report.md`.

  Trigger on "check day 14", "review this day file", "QA the day", "grade the
  plan session", "is this day ready to mark complete", "score the English day",
  "evaluate the translated day".

  This skill reads and reports only. It never edits the day file, and it never
  sets `status: complete`.
---

# plan-day-qa

Grades one already-written day file for one stream of one plan. It does not
rewrite the day; it reports what passes, what fails, and exactly where, so a
reviewer can decide and a domain specialist can sign off.

It is the QA companion to `plan-day-generate` and `plan-day-translate`. **Every
criterion is read from the plan's own contracts, not from this file** — the
section list, the headings, the ceilings, the bands, the voice per section, the
practice categories and the forbidden elements all come from
`About <plan-name>.md` and `<lang>/requirements.md`. That is what keeps the
evaluator from drifting out of sync with the generator, which is exactly what
happened to every hard-coded evaluator this one replaces.

## When to use

- The user asks to check, review, evaluate, grade, QA or score a day file.
- A day is being considered for promotion from `status: draft` to
  `status: complete`.
- After generating or translating a day, as a self-check before saving.

---

## Inputs

1. **The day file** to evaluate.
2. **The plan's contracts**, which define every check:
   - `About <plan-name>.md` — the section declaration (ids, headings, types,
     voices, ceilings, formulas, may-be-absent, grounding), the practice
     categories, the verse source per stream, the naming pattern, the status
     rules.
   - `<lang>/requirements.md` — register, per-section rendering rules, the
     forbidden-elements list, the word-count bands.
   - `<lang>/termbase.md`, and `<lang>/termbase-translation.md` for a
     translation stream.
   - `<lang>/assets/section-spec.json` — the machine-readable section spec.
3. **The grounding sources**, by stream role:
   - *Authoring stream*: `2-RAILS/Verses/<verse-id>.md` for every verse in the day's
     range (or the declared interim source, if the day's `generation_note` says
     one was used); the teaching-assignment file in `teaching-file` mode.
   - *Translation stream*: the authoring-stream day file named in
     `translated_from:`, and this stream's designated verse source.
4. `<lang>/schedule.md` — the expected chapter, verse range and date.
5. `<lang>/assets/liturgy.md` — the Fixed sections' text.

Read the day file and every relevant source before scoring. **Do not score
grounding from memory.**

## Output

A scorecard in the reply, and the same run appended to
`3-TRANSFORMATIONS/Plans/<plan>/<lang>/qa-report.md` under a dated heading. Runs
accumulate; an earlier run is never deleted or rewritten, so the report shows
whether a day is improving.

---

## Output file format

```markdown
## <YYYY-MM-DD> — Day <N> (<file>)

Verdict: READY TO COMPLETE | NEEDS FIXES (n critical, n major, n minor)

### Critical
- [check] — "quoted offending text" → suggested fix

### Major
- [check] — "quoted offending text" → suggested fix

### Minor
- [check] — "quoted offending text" → suggested fix

### Passed
- short list of the notable checks that passed (structure, grounding, …)

### Rating
[N]/10 — [label]. Show the arithmetic (e.g. "10 − 2 majors − 1 minor = 7,
capped at 6 → 6") plus one plain sentence.
```

The rating is always the last thing in the report.

Rules for the report:

- **Write the feedback in plain, simple language anyone can follow.** Do not use
  this skill's own jargon in the feedback ("major", "minor", "machine-tell",
  "meta label"). Say the problem in everyday words: not "machine-tell:
  em-dashes" but "has long dashes (—) that make it look AI-written"; not
  "liturgy mismatch" but "uses the old prayers, which don't match the current
  ones". The severities still drive the score behind the scenes, but the words
  the reader sees should be plain.
- **Quote the exact text for every failure.** Never describe a problem without
  showing it.
- Give each failure a concrete one-line fix, not a vague note.
- Be specific about location — which section.
- Do not rewrite the whole day. Suggest the fix; let the author apply it.

---

## Rules

1. **Read the contracts first.** A check that is not traceable to
   `About <plan-name>.md` or `<lang>/requirements.md` is not a check — do not
   invent criteria, and do not import criteria from another plan.
2. **This skill reads and reports only.** It does not edit the day file.
3. **The evaluator never sets `status: complete`.** A domain specialist makes
   that call after the critical and major issues are cleared.
4. **Count each distinct issue once.** Five em-dashes are one em-dash issue, not
   five. A heading that is both wrong-named and out of order is one issue (the
   worse one). A pervasive style pattern counts as one major, not many minors.
5. **The severity table decides, not the reviewer.** If an issue could fit two
   severities, the table wins.
6. **If the day was built from interim sources** rather than `complete` rails —
   the day's `generation_note` says so — note it in the report: grounding was
   checked against interim material and still needs specialist confirmation.
7. **Keep this skill in sync with the contracts, not with a generator.** When a
   plan's declaration changes, no change to this file is needed; when a *rule of
   the pipeline* changes, it changes here and in the generator together.

---

## Procedure

Work through the four groups below, plus the mechanical checks. For each check
assign **PASS**, **FAIL** or **N/A**. Give every FAIL a severity and the
evidence.

**Severities**

- **Critical** — breaks trust or fidelity: a claim not traceable to its
  grounding source; verse or fixed text altered; content that is not from the
  sources. A day with any critical issue cannot be marked complete.
- **Major** — a clear rule violation a reader would notice: a wrong or missing
  section, an explanation where the contract asks for an addition, the wrong
  voice, a forbidden element, a paraphrased term, a consequence with no "to
  whom".
- **Minor** — polish: slightly long, a mild filler word, light formatting
  overuse.

For every FAIL, quote the exact offending text and give a one-line suggested fix.

### Group 1 — Structure and fidelity (mostly critical)

- **Sections present and in the declared order**, with the headings declared for
  this stream, at the declared heading level and no deeper.
- **Heading wording exact** — a near-miss heading is a rule violation, not a
  style preference.
- **Fixed sections verbatim**: byte-identical to their blocks in
  `<lang>/assets/liturgy.md` — no added, dropped or reworded lines.
- **Verse text from the declared source**: matches this stream's designated
  verse source exactly, by block ID. No paraphrase, no substitution, no
  re-lineation. Verses that have no rendering in that source are flagged, not
  improvised.
- **Verse range matches the schedule** for that day number, and the filename's
  encoded range matches both.
- **Frontmatter present and correct**, with every key the plan declares, and
  `generation_note` where interim sources were used.
- **A section declared "may be absent" that is absent** is N/A, not a failure —
  provided the report says why.

### Group 2 — Grounding (critical)

- **Every claim in a Generated section traces to a specific passage in its
  declared grounding source.** Locate it. A claim — a story, a number, an
  attribution — that cannot be found in the cited rail or its sources is
  critical, however plausible it sounds.
- **Every instruction in the practice section traces to the idea in the
  commentary section**, which traces to the rails.
- **A commentator or teacher is named** when a specific attribution is made,
  with a one-clause identification on first use, using the display name the
  termbase fixes.
- **A section declared to *add* does not merely *explain*.** Where the plan says
  a commentary section carries something a careful reader of the verses alone
  would not reach, a section that only restates the verse is a major failure.
- **In `teaching-file` mode**: the teaching blocks are verbatim and complete, the
  citation line names the blocks used, and nothing is paraphrased or
  supplemented.

### Group 3 — Voice and style (major / minor)

All of these are read from `<lang>/requirements.md`; the wording below is the
shape of the check, not the rule itself.

- **No machine-tells**: no element on the stream's forbidden list — em-dashes in
  body prose, emojis, and whatever else that file names.
- **Terms used, not paraphrased or defined**: termbase terms appear by name, not
  swapped for loose stand-ins and not glossed where the contract says not to.
- **Plain grammar around terms**, per the stream's register rule.
- **Describes what the text does, not what the reader feels** — no claims about
  the reader's emotions, no shaky human-nature generalisations.
- **Consequences name who they fall on.** No floating consequence.
- **No rhetorical question-and-answer** where the contract forbids it;
  importance shown by comparison or result, not labelled "great" or "profound".
- **Mechanisms explained in concrete steps**, not one compressed abstract
  sentence the reader must unpack.
- **Readable at the declared level**: common words, sentences within the
  declared limit, no idiom or figurative phrase that fails if read literally.
- **The practice section carries its declared voice and framing** — an
  invitation where the contract says invitation, a first-person commitment where
  it says commitment; never an assignment, a stack of commands, or a request to
  watch a presumed negative feeling.
- **Formatting is light**: emphasis on a few key phrases only, never whole
  sentences or every paragraph.

### Group 4 — Limits (minor unless far off)

- Every declared ceiling respected (a ceiling breach is major if large).
- Every declared band met, or the deviation explained by the source.
- Notification / hook lines within their declared length, specific to the day,
  and not a rhetorical question where the contract forbids one.
- Script and orthography rules honoured (numerals, diacritics, transliteration).

### Group 5 — Translated streams only

Run these in addition to Groups 1–4, against the day named in
`translated_from:`:

- **Additions.** Every output sentence has a parent clause in the source day.
  One that does not is critical.
- **Omissions.** Every source clause landed somewhere. A dropped closing or
  payoff sentence is critical.
- **Attribution drift.** Every name and every vague attribution is present and
  unchanged in specificity — neither dropped for smoothness nor sharpened into a
  named commentator the source does not name.
- **Cross-stream parity.** Where sibling translation streams exist for the same
  day, they carry the same number of claims and the same closing.
- **Verse retrieval, not translation.** Verse text came from this stream's
  designated verse source by block ID, not translated fresh.
- **Excluded sub-blocks** are absent from the output.
- **Pending terms** are logged in both `pending_terms:` and the termbase's
  Pending terms table; an entry older than a chapter is reported.
- **Practice repetition.** Compared with the two previous days, the practice is
  distinct — a dropped distinguishing clause produces two identical days.

### Mechanical checks

Run before scoring, and fold each failure into the groups above:

```bash
python3 "<plan-day-generate skill dir>/scripts/check_day_file.py" \
  --spec "3-TRANSFORMATIONS/Plans/<plan>/<lang>/assets/section-spec.json" \
  --verses "<C>-<start>,…,<C>-<end>" \
  "<the day file>"
```

It measures every ceiling and band, checks the heading set and order, block-ID
presence and contiguity, the forbidden-elements regexes and the category tag
(present, correctly wrapped, drawn from the plan's list). Never eyeball a count
that a script can produce.

---

## Verdict rule

- **READY TO COMPLETE** only if there are zero critical and zero major issues.
  Minor issues may remain at the reviewer's discretion.
- Any critical issue → **NEEDS FIXES**, and the day must not be promoted to
  `status: complete`.
- The evaluator never sets `status: complete` itself. A domain specialist makes
  that call after the critical and major issues are cleared.
- A translation stream's day may not be promoted past the status of the
  authoring-stream day it was translated from.

---

## Rating — standardised scoring

The score out of 10 is **computed**, not chosen by feel, so the same day always
gets the same number. Two steps: classify each issue using the severity table,
then apply the formula.

### Step 1 — count the issues

Go through the checks and list each failure. Then count how many are
**critical**, **major** and **minor**, using the severity table below. Counting
rules:

- **Count each distinct issue once.** Five em-dashes are one em-dash issue, not
  five. A heading that is both wrong-named and out of order is one issue (the
  worse one).
- A **pervasive** style pattern (emphasis on almost every phrase, dashes
  throughout) counts as **one major**, not many minors.
- If an issue could fit two severities, use the table; the table decides, not
  the reviewer.

### Step 2 — apply the formula

1. Start at **10**.
2. Subtract **2** for each major issue.
3. Subtract **1** for each minor issue.
4. If there is **any major issue**, the result may not exceed **6** (cap).
5. If there is **no critical issue**, the result may not fall below **3**
   (floor).
6. If there is **any critical issue**, ignore steps 1–5: the score is **2**, or
   **1** if there is more than one critical. Critical always wins.

Always show the arithmetic in the report, e.g. "10 − 2 majors − 1 minor = 7,
capped at 6 → **6/10**".

### Bands (for interpretation only)

- **9–10** Excellent, ready · **7–8** Good, ready with small polish · **5–6**
  Needs fixes · **3–4** Weak · **1–2** Do not use.
- **7 or above = "READY TO COMPLETE"; 6 or below = "NEEDS FIXES".**
- The rating is a reviewer aid, not permission to publish. Only a domain
  specialist sets `status: complete`.

### Severity table (fixed classification)

Classify every issue by this table. Do not reclassify by feel.

**Critical** (fidelity / trust — any one forces the 1–2 band):

- A claim in a Generated section that cannot be traced to its declared grounding
  source.
- Verse text altered, paraphrased, re-lineated, or taken from a file other than
  the stream's designated verse source.
- Fixed text with invented or changed lines that alter the meaning of the
  passage.
- Anything presented as commentary that is actually the model's own invention.
- In a translation stream: a sentence with no parent clause in the source day, or
  a source clause dropped entirely.
- `status: complete` set by a generator rather than a specialist.

**Major** (clear rule violation — −2 each, caps at 6):

- A required section missing, or sections out of the declared order.
- A wrong section heading (a near-miss counts).
- Fixed text that is an outdated version — content intact but wording differs
  from the current `assets/liturgy.md`.
- Any element on the stream's forbidden list present in body prose (counts once;
  pervasive use still counts once).
- A section that explains the verse where the contract says it must add
  something the verses do not contain.
- A termbase term paraphrased into a stand-in.
- A consequence stated with no "to whom".
- A rhetorical question-and-answer where the contract forbids one.
- The practice section in the wrong voice or framing — assignment framing, a
  stack of commands, or asking the reader to watch a presumed bad feeling.
- Importance asserted ("great", "profound") instead of shown by comparison or
  result.
- A mechanism compressed into one abstract sentence the reader must unpack.
- A declared ceiling exceeded by more than about 20%.
- A practice category absent, wrongly wrapped, or not on the plan's list.
- An excluded sub-block carried into a translated day.

**Minor** (polish — −1 each):

- A missing optional line the contract asks for (a hook, a one-clause
  identification of a commentator).
- Heading-label inconsistency with other days in the same stream.
- Emphasis a little heavy — the upper edge of "sparing", not pervasive.
- A spelling inconsistency.
- A count over or under a declared band by less than about 20%.
- A meta closing label on the practice ("that is the practice").
- A single idiom or elevated phrase a non-native reader might stumble on.
- A mild filler word or phrase.

---

## Completion check

- [ ] The plan's contracts were read before scoring; every check traces to one
      of them.
- [ ] The day file and every grounding source were read; no grounding was scored
      from memory.
- [ ] `check_day_file.py` was run and its findings folded into the groups.
- [ ] Group 5 was run if and only if the day belongs to a translation stream.
- [ ] Every FAIL quotes the exact offending text and gives a one-line fix.
- [ ] Feedback is in plain language, with no evaluator jargon.
- [ ] The score shows its arithmetic and is the last thing in the report.
- [ ] The run was appended to `<lang>/qa-report.md` under a dated heading, with
      earlier runs left intact.
- [ ] The day file was not edited, and `status: complete` was not set.
