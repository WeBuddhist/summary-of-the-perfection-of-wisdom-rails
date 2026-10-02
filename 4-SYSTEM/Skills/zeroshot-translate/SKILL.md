---
name: zeroshot-translate
description: >
  Translate a block-ID'd source text into a target language in one pass, either
  as a full citable track triangulated against a second source language and
  existing human translations (Mode 1), or as a fast unconstrained draft whose
  only purpose is to feed keyword extraction (Mode 2).

  Trigger on "translate this", "zero-shot translation", "translate these blocks into
  X", "translate using the termbase", "translate this chapter".

  Output block IDs always match the source exactly.
---

# Zero-shot translation with terminology control

| Mode | What it is | Use |
|---|---|---|
| **1 — Triangulated** (default) | A full, citable translation track: second source language for disambiguation, existing human translations as witnesses, an evidence-built termbase, the three track contract files, `translation-qa` at the end | Anything that will be published, cited, or reviewed |
| **2 — Unconstrained draft** | A fast block-ID-preserving draft with no termbase and no track | **Only** to give `keyword-extract` something to work on when no block-aligned translation exists yet |

**Mode 1 is the default.** If the user does not say which mode, run Mode 1.

**Mode 2 is not a translation anyone cites.** It exists for exactly one reason:
`keyword-extract`, and through it `graded-translate` Phase 1, needs a
block-aligned pivot translation to key a termbase on. When a text has no human
translation at all, Mode 2 manufactures one. Its terminology is inconsistent by
construction, it has no contract, no QA and no rails behind it, and it goes to
`0-INBOX/temp/`, not to `3-TRANSFORMATIONS/`. Never promote a Mode 2 draft into a
track, never cite it in `context_packages:`, and never hand it to a reader.

Whichever mode: block IDs match the source one-for-one.

---

## Mode 1 — Triangulated — second source language plus human translations

Disambiguates each verse against a second source language where the vault has one, and checks it against block-aligned human translations.

Produces a full translation track directly from `1-SOURCES/` when the `2-RAILS/Verses/<verse-id>.md` packages are not yet `status: complete`.

**Method: evidence-based triangulation.** Every decision is backed by something checkable at the exact verse, never by a pre-built table or parametric knowledge:

- **Meaning** — the primary source named in `4-SYSTEM/Guidelines/vault-annex.md` is the meaning base; a second-language source text, where the annex declares one, resolves ambiguity (homonyms, pāda breaks, philosophical terms); every block-aligned human translation listed in the track's `requirements.md` is compared at the same block ID. Consensus among them confirms a reading; divergence among them marks genuine ambiguity — check the second-language source and flag.
- **Terminology** — the termbase is built empirically as translation proceeds: when a key term first appears, its attested renderings are read from the witnesses *at that block ID*, one is chosen for the track register, and appended with the verse citation as rationale. No glossary seeding.
- **Register** — from the track's existing `requirements.md` / `audience.md`, which are read, never overwritten.

Output matches the vault's transformation conventions: `requirements.md` / `audience.md` / `termbase.md`, one `Chapter-NN.md` per chapter, then one merged full-text file.

---

### Inputs

| Input | Required | Description |
|---|---|---|
| **Target language** | ✓ | ISO-style code or short name, e.g. `en`, `hi`. Determines track folder prefix. |
| **Audience level** | ✓ | The audience label for this track, e.g. `children`, `plain`, `scholar`. Determines register and track suffix. |
| **Chapter scope** | optional | Single chapter (`3`), range (`1-3`), or `all` (default). `all` means every chapter the root text actually has — read them off its `^N-0` headings, never assume a count. |
| **Merge** | optional | `yes` (default) or `no`. When `yes`, run merge after all requested chapters exist. |
| **`--termbase <path>`** | optional | Lock the run to an existing termbase — see § The `--termbase` lock below. |
| **`verse-form`** | optional | `prose` (default) or `pada-aligned` — see § Verse form below. |

If target language or audience level is missing, ask before proceeding.

#### Source files — resolved per vault, never hard-coded

| Role | Where it comes from |
|---|---|
| Primary source | The root text `4-SYSTEM/Guidelines/vault-annex.md` names as primary. This is the meaning base. |
| Second-language reference | The second root text the annex declares, where the vault has one. Optional: a vault with a single-language root simply skips every "second source" step below. |

#### Triangulation set — the witnesses

The witnesses are **every block-aligned file in `1-SOURCES/Translations/` for the target language and for any pivot language**, listed by name in the track's `requirements.md`. `requirements.md` is the authoritative list: if it names a set, load exactly that set, all of them, for every chapter. If the track is new, list the block-aligned `1-SOURCES/Translations/` files yourself, record them in `requirements.md` under **§ Zero-shot sources**, and say so in the report.

A file counts as a witness only if its block IDs align with the primary source's. Verify alignment before relying on one: a witness may omit a verse and then run one behind for the rest of a chapter. Record any offset in the track's notes.

Translations **in the target language** take precedence for terminology evidence over translations in a pivot language.

#### Consolidated glossaries (optional hint only)

The bilingual glossaries under `2-RAILS/Bilingual-Glossaries/` may be consulted for frequency data on a rendering, but they are descriptive and partial, and they are **never** used to seed or override the termbase. Terminology evidence comes from the triangulation set at the exact block ID. (The one exception is a deliberate `--termbase` lock — see below.)

#### Track folder (output root)

```
3-TRANSFORMATIONS/Translations/<lang>-<audience>/
```

---

### Output

| Artifact | Path |
|---|---|
| Localized requirements | `3-TRANSFORMATIONS/Translations/<track>/requirements.md` |
| Localized audience profile | `3-TRANSFORMATIONS/Translations/<track>/audience.md` |
| Track termbase (grows per chapter) | `3-TRANSFORMATIONS/Translations/<track>/termbase.md` |
| Per-chapter translation | `3-TRANSFORMATIONS/Translations/<track>/Chapter-NN.md` |
| Merged full text | `3-TRANSFORMATIONS/Translations/<track>/<text-id>-full-<audience>-<lang>.md` |

---

### Output file format

#### Per-chapter file (`Chapter-NN.md`)

```markdown
---
ref: <N>
title: "Chapter <N> — <chapter title in the target language>"
transformation_type: translation
track: <lang>-<audience>
root_text: 1-SOURCES/Text/<lang>-root-text.md
context_packages:
  - <primary source path> (^<N>-0–^<N>-<last>)
  - <second-language source path, if any> (^<N>-0–^<N>-<last>)
  - <witness path> (^<N>-0–^<N>-<last>)      # one line per witness loaded
generation_date: <YYYY-MM-DD>
status: draft
---

# <Work title>                                  ← Chapter 1 only
### <Audience> <Language> Translation           ← Chapter 1 only
*Zero-shot translation from <primary source, as its frontmatter names it>, cross-checked against <second-language source, if any>*   ← Chapter 1 only

---

## Chapter <N>: <Chapter title>

<One prose paragraph per verse-block, ending with block ID.> ^<N>-<V>

*Thus ends Chapter <N>: "<Chapter title>."*
```

The heading levels above are the file's real levels — `#` for the work title, `###` for the translation label, `##` for the chapter heading. Do not demote them.

Publishing metadata (`text_id`, `edition_id`, `category_id`, `license`, etc.) is added by human editors at publication time — do not invent it.

**Chapter titles.** Read the chapter set and each chapter's title from the primary source's own `^N-0` headings. Render each title into the target language at the track's register. There is no chapter table in this skill: a text may have a chapter `0`, roman-numeral front matter (`^I-…`) and lettered back matter (`^a-…`), and only the source knows.

**The work's title** for the Chapter-1 heading and for the merge comes from the root text's frontmatter `title:` — not from memory.

#### Verse block rule

- One flowing prose paragraph per source verse-block (unless `verse-form: pada-aligned`, below).
- End every paragraph with the source block ID: `^chapter-verse` (e.g. `^3-12`).
- Preserve every verse ID present in the primary source for that chapter — no skips, no duplicate IDs.
- Do not include source-language text in the output (target language only).

---

### Rules

1. **Rails first, zero-shot second.** For each verse, check `2-RAILS/Verses/<verse-id>.md`. If `status: complete`, use its AI Overview and Disambiguated Restatement (plus `2-RAILS/Bilingual-Glossaries/` and Local-Wiki as needed). If not complete, translate zero-shot per the workflow below. This ordering is not negotiable: the rails carry the commentarial tradition, and a zero-shot pass does not.
2. **Never modify `1-SOURCES/`.** Read only.
3. **Never set `status: complete`.** All generated files stay `status: draft` until a domain specialist reviews them (run `translation-qa` before sign-off).
4. **Termbase is law, and evidence-built.** Every keyword rendering must match `termbase.md`. New terms are **appended** at first occurrence with the attested renderings observed in the triangulation set at that block ID, the chosen rendering, and the citation as rationale — never silently change an existing locked rendering once a chapter has shipped. Never re-seed or rewrite an existing termbase.
5. **One chapter per save.** Translate and write one `Chapter-NN.md` at a time. A long chapter may be read in sections but must be written as one complete chapter file. **Never dispatch chapters in parallel.** A register or structural problem caught after one chapter is cheap to fix; the same problem found after several chapters were produced in parallel is not, and parallel work burns tokens on material nobody has reviewed.
6. **Register fidelity.** Follow the localized `requirements.md` and `audience.md` strictly — sentence length, loanword policy, footnote ban, verse-as-prose rule.
7. **The second-language source is reference only.** Where the primary and the second-language source diverge, prefer the primary as the meaning base; use the second language to disambiguate, not to override. Flag real divergences with the editorial note format below.
8. **Triangulation is mandatory, copying is forbidden.** Compare every draft verse against every witness for *meaning* (subject, object, negations, modality, imagery). If the witnesses agree and your draft disagrees, your parse is almost certainly wrong — re-examine the source. If the witnesses disagree *with each other*, the verse is genuinely ambiguous — resolve from the second-language source and flag. Never copy any witness's wording — each is under its own copyright and its register will not match the track.
9. **Divergence flag format.** When sources genuinely disagree or a reading is uncertain, append a bracketed editorial note after the block ID line: `[Ed: <second-language source> reads "…"; <primary> followed.]` or `[Ed: <witness A> and <witness B> read this pāda as X; <witness C> as Y; the <second-language> source supports X.]` English, factual, one sentence.
10. **Sensitive verses.** A verse carrying an outdated cultural assumption gets a brief bracketed editorial note in accessible tracks; a scholarly track may use a footnote-style aside only if `requirements.md` allows it. Which verses those are is a property of the text, not of this skill — flag them as you meet them and list them in the report.
11. **Do not hallucinate.** Translate only what is in the source. No invented explanations, no dropped pādas, no merged verses.
12. **Merge is deterministic.** After all chapters exist, merge with the bundled script (`scripts/merge_chapters.py`) — do not hand-stitch the full text.

---

### The `--termbase` lock (optional)

By default Mode 1 builds its termbase as it goes (Rule 4). When a locked
termbase already exists — the track's own `termbase.md`, or a per-track
bilingual glossary from `bilingual-glossary` Phase 4 — pass it with
`--termbase <path>` and the run switches to **hard-constraint** mode for the
terms it covers. Terms not in it are still handled by the evidence rule.

Under the lock:

1. **Termbase renderings are hard constraints.** If a source token in the text appears as a keyword in the termbase, its rendering in the output must match exactly — no synonyms, no paraphrases. A departure requires an explicit note in the track's notes saying which term, where, and why.
2. **Keep the termbase minimal and high-signal.** The right size is the contested terms — a few dozen — not the whole vocabulary. A bloated termbase creates noise and contradictions; a focused one enforces consistency where it matters.
3. **Translate in batches of 30–50 blocks.** Larger batches risk exceeding context limits and cause drift away from the termbase constraints.
4. **Filter the termbase to the batch.** The termbase injected into the prompt must contain only the terms actually present in that batch. Scan each batch's source tokens against the termbase (match on a normalised/transliterated form so inflected forms hit) and include only those entries. Injecting the full termbase for every batch adds noise and degrades adherence.
5. **Never translate more blocks than exist.** If the requested range includes block IDs not present in the source, stop and report the missing IDs rather than skipping them silently. Likewise, if a batch comes back with IDs that were not in the input, stop and report them — do not generate the difference.
6. **Post-batch check.** After each batch, confirm every source block ID has exactly one output block, and spot-check 2–3 blocks for termbase compliance. On a violation, re-run the batch with the violation added to the prompt as a negative example.

### Verse form (optional)

`verse-form: prose` (the default) produces one flowing prose paragraph per
verse-block, per the verse block rule above.

`verse-form: pada-aligned` produces **line-for-line verse**: each block's
translation mirrors its source's exact line count, with each target-language
line carrying its source line's content — not collapsed into flowing prose and
not mechanically word-wrapped. The block ID still sits at the end of the last
line of the block, exactly where the source puts it. Choose this whenever the
track's `requirements.md` asks for verse form, or the downstream use needs
pāda-level alignment. Structural fidelity and terminology control are
independent: pada-alignment applies whether or not a termbase lock is in force.

Under either verse form, translate **one chapter at a time, in sequence, never
in parallel** (Rule 5).

---

### Per-verse translation workflow

For each verse-block, in order:

1. **Rails check** — if `2-RAILS/Verses/<id>.md` is `status: complete`, translate from its Disambiguated Restatement and skip to step 6.
2. **Parse the primary source** — identify agent, object, verb, negations, and particles; note any homonym or ambiguous syntax.
3. **Read the witnesses** — read every triangulation translation at this block ID. Classify: **consensus** (all agree on meaning) or **split** (they diverge — record who reads what).
4. **Consult the second-language source** — resolve each ambiguity from step 2 and each split from step 3 against the second-language line. Note (do not resolve silently) any real divergence between the two sources. Skip this step in a single-language-root vault and rely on the witnesses plus the rails.
5. **Resolve terminology** — apply locked termbase renderings. For a key term not yet in the termbase: list its renderings across the witnesses at this block ID, choose the one fitting the track register, and queue it for append with the citation (e.g. `<lemma> → "<chosen rendering>" — <witness A> "<x>", <witness B> "<y>", <witness C> "<z>" at ^1-1; register avoids loanwords`).
6. **Draft** — one prose paragraph (or a pāda-aligned block) in the track register per `requirements.md`, in your own wording.
7. **Verify against consensus** — if the witnesses were in consensus and your draft's meaning differs, return to step 2. If the split persists after step 4, keep the reading the second-language source supports and add a divergence note (Rule 9).
8. **Finalise** — append the block ID; add editorial note if flagged.

---

### Procedure

#### Step 1 — Confirm inputs

Resolve:
- `track` = `<lang>-<audience>`
- `track_dir` = `3-TRANSFORMATIONS/Translations/<track>/`
- Primary source and second-language source, from `4-SYSTEM/Guidelines/vault-annex.md`
- Chapter list: read every `^N-0` heading from the primary source and intersect with the requested scope
- Triangulation set (see Inputs)

#### Step 2 — Track folder

**If the track folder already exists (the normal case):** read `requirements.md`, `audience.md`, and `termbase.md` and continue. Do not overwrite, re-localize, or re-seed any of them — an existing termbase grows append-only from this point, however thin it is.

**Only if `track_dir` does not exist:**

1. Create `track_dir`.
2. Write `track_dir/requirements.md`, using an existing track's `requirements.md` in this vault as the structural model where one exists. Localize for the target language and audience level (register, reading level, loanword policy, sentence length). Include **§ Zero-shot sources**: the primary source; the second-language reference, if any; the triangulation set by filename. Fallback rule: use zero-shot when verse rails are not `status: complete`. Write it in the target language, per the vault's transformation rules.
3. Write `track_dir/audience.md`, localized for the audience level: demographics, prior knowledge, use cases, motivations.
4. Create `track_dir/termbase.md` **empty** — header and table columns only (source lemma | chosen rendering | rationale with block-ID citation). Do not seed it: entries are added at first occurrence during translation, from witness evidence (per-verse workflow step 5). If a `--termbase` lock was passed, copy that termbase in as the starting rows and record where it came from.

#### Step 3 — Translate each chapter

For each chapter `N` in scope:

**a. Load sources**

- Read the primary source's chapter: the lines from `^N-0` up to the next `^…-0` chapter heading. Take that next heading from the source's own heading list — the chapter after `N` is whatever the source says it is, which may be a lettered back-matter zone rather than `N+1`.
- Read the same verse IDs from the second-language source, where the vault has one.
- Read the same chapter from **every** witness in the triangulation set.
- Load `termbase.md` and scan for terms appearing in this chapter.

**b–c. Translate**

Apply the **per-verse translation workflow** above to every verse-block in the chapter. Under a `--termbase` lock, work in batches of 30–50 blocks with the termbase filtered to each batch.

**d. Write chapter file**

Save to `track_dir/Chapter-NN.md` using the format above. Set `generation_date` to today.

**e. Update termbase**

Append the terms queued during this chapter (source lemma, chosen rendering, rationale with witness renderings and block-ID citation). Never edit prior rows.

**f. Report progress**

After each chapter, state which chapter finished, which remain, and how many divergence notes were added.

#### Step 4 — Merge full text (when scope is complete)

When all chapters in scope exist and `merge` is not `no`:

```bash
python 4-SYSTEM/Skills/zeroshot-translate/scripts/merge_chapters.py \
  "3-TRANSFORMATIONS/Translations/<track>" \
  --track "<track>" \
  --title "<the root text's frontmatter title:> — Full Text (<Audience> <Language>)" \
  --output "<text-id>-full-<audience>-<lang>.md" \
  --chapters all
```

`--chapters all` merges whichever `Chapter-NN.md` files are present — it assumes no chapter count. The script fails on a missing requested chapter or a duplicate block ID; fix the chapter files and rerun, and never hand-edit the merged output.

#### Step 5 — Self-check before handoff

Run all of these; fix and rerun until clean:

1. **Verse coverage** — for each chapter, extract the unique block IDs from the primary source chapter and from `Chapter-NN.md`; the sets must be identical (no skips, no extras, no duplicates).
2. **Termbase consistency** — for each locked rendering, grep the chapter files to confirm no competing rendering of the same lemma slipped through; every termbase row added this run cites at least one block ID.
3. **Divergence notes** — every `[Ed: …]` note names its source; no unresolved `⚑` or TODO markers remain.
4. **Frontmatter** — every chapter file has `status: draft` and complete `context_packages`.
5. **QA skill** — run `translation-qa` on the per-chapter files (its Stage 0 is `scripts/mqm_mechanical_checks.py`). Iterate until no critical/major errors. **This step is required, not optional.**

---

### Completion check — Mode 1

- [ ] Target language, audience level, primary/second-language sources and triangulation set confirmed from the vault, not assumed.
- [ ] Chapter list read off the primary source's `^N-0` headings.
- [ ] Track folder exists with all three contract files; existing `requirements.md`, `audience.md`, `termbase.md` were read, not overwritten or re-seeded.
- [ ] Every requested chapter saved as `Chapter-NN.md` with correct frontmatter and `status: draft`.
- [ ] Every verse in scope has exactly one block ID in the output (verified against source, not just counted).
- [ ] Every verse triangulated against every witness; splits resolved from the second-language source where one exists, and flagged with `[Ed: …]` notes.
- [ ] `termbase.md` updated append-only, each new row citing witness renderings at a block ID.
- [ ] Under a `--termbase` lock: batches of 30–50 blocks, termbase filtered per batch, no invented or missing block IDs.
- [ ] `verse-form` honoured — pāda line counts mirrored where `pada-aligned`.
- [ ] Merged full-text file written via `scripts/merge_chapters.py` when scope is complete (unless user opted out).
- [ ] `translation-qa` run with no remaining critical/major errors.
- [ ] User told which chapters remain if scope was partial.
- [ ] User reminded that only a domain specialist may promote files to `status: complete`.

---

## Mode 2 — Unconstrained draft (input to `keyword-extract` only)

**Read this first.** Mode 2 produces a working draft, not a translation track.
Its single purpose is to give `keyword-extract` — and through it
`graded-translate` Phase 1 — a block-aligned pivot translation to key a
termbase on, in a vault where no human translation exists. It has no termbase,
no contract files, no rails behind it and no QA gate, so its terminology is
inconsistent by construction and its readings are unverified.

Consequently:

- Output goes to **`0-INBOX/temp/zeroshot/<text-id>-<lang>/`** — never to `3-TRANSFORMATIONS/`.
- It is **never a citable track**. Do not list it in any `context_packages:`, do not give it `transformation_type:`, do not publish it, do not show it to a reader as a translation of the text.
- If the user wants something citable, run Mode 1 instead, or build the rails and use `verse-translate` / `graded-translate`.
- If a block-aligned human translation already exists in `1-SOURCES/Translations/`, use that as the pivot and **do not run Mode 2 at all**.

### Inputs

1. **Source text** — the root text, with block IDs.
2. **Target language** — stated by the user. This mode assumes no default language; confirm it if the request is ambiguous.
3. **Audience profile** — a short profile describing the intended readership, register, and translation goals. A one-paragraph profile written for the run is enough. If none exists, write one with the user rather than guessing at it.

### Workflow

1. Read the audience profile closely — tone, register, how much explanatory latitude is allowed, the priority order between understanding, accuracy, readability and consistency.
2. Translate the source into the target language, applying the audience profile directly. Since there is no termbase, use your own best judgment for terminology, staying consistent within the piece even without an external reference locking word choices in advance.
3. **Translate verse by verse, pāda-aligned to the source — required, not optional, even without a termbase.** Each segment's translation must mirror its source's exact line count, with each target-language line carrying its source line's content, not collapsed into flowing prose and not mechanically word-wrapped. Preserve every block ID exactly, in the same position as the source (the end of the last line of its block). Skipping the termbase does not mean skipping structural fidelity — the two are independent, and the whole point of this draft is that it stays block-aligned.
4. Work through a long text in natural chunks — chapter by chapter — with the user, rather than producing the whole thing in one uninterrupted pass.
5. **Translate chapters one at a time, in sequence, never in parallel.** Finish and present one chapter, then wait for the user's go-ahead before starting the next — do not dispatch several chapters at once via parallel subagents. A register or structural problem caught after one chapter is cheap to fix; the same problem found after several parallel chapters is not, and parallel work burns a large number of tokens on material nobody has reviewed.

### Where the output goes

```
0-INBOX/temp/zeroshot/<text-id>-<lang>/
    Chapter-NN.md        one file per chapter
```

- `<text-id>` is the short identifier for the source text — take it from the root text's frontmatter or from the vault's existing filenames; ask if it is genuinely unclear.
- `<lang>` is the target language tag.
- Each chapter file is plain markdown: one block per source block, block ID at the end of the block's last line. No track frontmatter — a `status: draft` line and the source path are enough.
- A merged single file is optional and only produced if the user asks. `scripts/merge_chapters.py` will do it.

### Notes

- Because there is no locked termbase, re-running Mode 2 (or running it for a different audience profile) can legitimately produce different word choices each time — that is expected, not an inconsistency to chase down.
- When the user later wants a real translation, this draft is a reasonable place to start the keyword extraction and glossary from: its terminology choices, even unlocked, reflect real translation decisions rather than nothing. That is the whole purpose. Hand it to `keyword-extract`, then to `graded-translate` Phase 1 as the pivot, and let the graded track be the citable output.

### Completion check — Mode 2

- [ ] Output is under `0-INBOX/temp/zeroshot/<text-id>-<lang>/` and nowhere else.
- [ ] Every source block ID appears exactly once in the draft, at the end of its block's last line.
- [ ] Line counts mirror the source's pāda structure.
- [ ] Chapters produced one at a time, in sequence.
- [ ] The user was told this is an extraction input, not a citable translation, and what to run next.
