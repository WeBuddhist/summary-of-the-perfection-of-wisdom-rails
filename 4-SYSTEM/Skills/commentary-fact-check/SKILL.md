---
name: commentary-fact-check
description: >
  Check a translation verse by verse against the commentary tradition that
  grounds it, producing a graded report of every place the translation departs from
  what the commentaries support — then apply the mechanical fixes from that report and
  log what was applied, what was skipped for human judgment, and what re-verification
  found.

  Trigger on "fact-check this translation", "check this against the commentaries",
  "verify the translation", "apply the fact-check fixes", "work through the fact-check
  report".

  Two phases: the check never edits the translation; the fix phase never invents a
  correction the report did not support.
---

# Fact-check a translation against its commentaries, then apply the fixes

| Phase | Does | Touches the translation? |
|---|---|---|
| 1 — Check | Grounds each verse in its commentaries and grades the translation against them | No — report only |
| 2 — Apply | Triages the report into mechanical vs judgment-call, applies the mechanical ones, logs everything | Yes |

**The split is load-bearing.** Phase 1 must be free to report a problem without
having to solve it, and Phase 2 must not be free to invent a fix the report did not
support. An agent doing both at once will quietly soften findings it cannot fix.

Phase 2 triages every flagged verse into **MECHANICAL** (the report states the
correct reading and it is unambiguous) and **JUDGMENT-CALL** (the report flags a
problem but the right rendering is a translator's decision). Only mechanical fixes
are applied. Judgment calls go to the human, in the log, with the grounding
attached — never silently applied and never silently dropped.

---

## Phase 1 — Fact-check — grade the translation against its commentaries

Report only. Never edits the translation file.

Confirms that an already-written English translation says what the Tibetan
**commentary** says each verse means, checked **at the word level, not the gist
level**. This is the key design decision: a comprehension check ("does the English
convey roughly what the verse means?") silently passes errors like *chos kyi sku*
(dharmakāya, a buddha-**body**) rendered as "the dharma", because the three-jewels
gist survives even though the referent is wrong. To catch that class of error the
audit forces a term-by-term alignment against the commentary's own glosses and
withholds any verdict until every anchored term has been checked.

This skill **reports**; it never edits the translation file. Real discrepancies go
in the report (and to the user) for a separate editing pass to fix.

Companion to `translation-qa` (which scores wording/register against `2-RAILS/`
rails and `termbase.md`). This skill's ground truth is the **commentary**, because
it transcludes the whole root text and settles content questions — sutra
citations, similes, named entities, classification schemes, kāya distinctions —
that a bare verse line can't.

---

### Inputs

| Input | Required | Description |
|---|---|---|
| **`<commentary>`** | ✓ | Path to one commentary under `1-SOURCES/Commentaries/` that transcludes the root via `![[…#^verse-id]]` markers. **One commentary per run** — do not silently mix commentaries; if a verse is unclear from this one, say so rather than reaching for another. |
| **`<translation>`** | ✓ | Path to the translation file to audit, under `3-TRANSFORMATIONS/Translations/<track>/`. |
| **`<track>`** | ✓ | The translation track's folder name. Everything this skill writes lives under `3-TRANSFORMATIONS/Translations/<track>/`. |
| **`<report>`** | derived | `3-TRANSFORMATIONS/Translations/<track>/commentary-fact-check-report.md`, unless the caller names another path. |
| **Scope** | ✓ | A chapter number, `colophon`, or an explicit verse range (e.g. `1-1 to 1-5`). Never default to "the whole text" — pick a bounded scope so each verse gets a full term-alignment pass. |

Report file: `<translation-dir>/commentary-fact-check-report-<commentary-id>-<translation-name>.md`
(one file per commentary×translation pair, so audits of the same text against
different commentaries never overwrite each other). Create on first use.

---

### Procedure

#### Step 1 — Extract the commentary passages

```bash
python3 4-SYSTEM/Skills/commentary-fact-check/scripts/extract_commentary.py \
    <commentary-path> --json 0-INBOX/temp/commentary.json
```

Splits the file on its transclusion markers, attributing the Tibetan prose (and
block-quoted sutra citations — they are the commentary's own support and are worth
checking) between one marker and the next to that marker's verse. Read the coverage
summary. An empty bucket means its content was absorbed into the **next** verse's
bucket (a heading or citation sat flush against the marker) — recover it from the
following verse; do not report it as a translation defect. Watch for a **cascading
shift** where every bucket quietly holds the *next* verse's prose: if a bucket's
content plainly describes a different verse than its label, check the neighbor
before concluding the English is wrong, and note any confirmed shift in the report.

#### Step 2 — Extract the target translation

```bash
python3 4-SYSTEM/Skills/commentary-fact-check/scripts/extract_translation.py \
    <translation-path> --chapter <N> --json 0-INBOX/temp/translation.json
```

#### Step 3 — Term-by-term audit (the core method)

**Stance: assume the translation CONTAINS errors; your job is to find them, not to
confirm it reads well. A verse is not cleared until every anchored term is checked.**

For **each** verse in scope, build an alignment table before assigning any verdict:

1. **List the anchors.** From the commentary's prose for that verse, list every
   content word/phrase the commentary explicitly glosses, defines, etymologizes,
   names, counts, or illustrates (e.g. it spells out *chos kyi sku*, *sdom*,
   *bodhi = byang chub*; names a sutra/person; gives a number; states a simile).
   These glossed terms — not your own sense of what matters — are the mandatory
   checklist.
2. **One row per anchor:** `Tibetan (+Wylie) | commentary's gloss | English word used | MATCH / MISMATCH | one-line reason`.
3. **Verdict only after the table.** No verdict without the table.

**Flag as an ERROR (not a style note) any row where the English NAMES THE WRONG
THING, even if it reads fluently.** Scan specifically for:

- **kāya vs dharma vs mind:** *sku / chos sku / longs sku / sprul sku* must stay a
  "body/kāya" — never collapse to "dharma" (the teaching) or "mind".
- **precise term → vague near-synonym:** *dge ba* = virtue/goodness, not "kindness";
  *sdom* = vow/discipline, not "way of life"; *theg dman* = lesser vehicle, not
  merely "lower".
- **named entities:** sutras, teachers, bodhisattvas (Subāhu, Sudhana, Maitreya,
  Maitrībala…) — right name, right person.
- **number & scope:** singular/plural, one vs a few vs countless; *only / all /
  each / even / alone*.
- **simile tenor:** what illustrates what (lightning reveals **forms**, not "the
  sky"; *chu shing* = plantain).
- **grammatical role / agent:** who acts on whom; subject, object, case relations.
- **enumerations and their ORDER** (e.g. the three: virtue / friend / merit).

**Do NOT flag** elaboration the commentary adds that the verse needn't carry
(etymologies, sutra citations, sub-classifications, narrative illustrations).
Dropping supplementary detail is fine; renaming the referent is not. Keep a "style
/ softening" note separate from a hard ERROR so the editor can triage.

#### Step 3a — Second pass on the highest-miss classes

After the first pass over the whole scope, do a **dedicated second sweep looking
ONLY for doctrinal-category swaps** — kāya↔dharma↔mind, wrong named entity, wrong
number/scope. A general pass averages over exactly these; a scoped pass catches
them. Report anything the second pass adds.

#### Step 4 — Write the report

Create the report file if absent with a header and an empty progress table:

```markdown
# <Track> Translation — Commentary Fact-Check

- **Commentary (ground truth):** `<commentary-path>`
- **Translation audited:** `<translation-path>`

Method: strict term-by-term alignment against the commentary's own glosses
(kāya/entity/number/simile/agent/order sensitive), not a gist check. Preliminary
self-check, not a scholarly sign-off — a domain specialist reviews before this is
treated as final (an LLM never marks its own output complete).

## Progress

| Scope checked |
|---|
```

Append a `## Chapter <N>` (or range) subsection. Include, per verse, the ERROR and
MISMATCH rows (not the full alignment table — keep the report readable), then:

```markdown
### Chapter <N> — verses <a>–<b>

| Verse | Verdict | Tibetan (Wylie) | Commentary gloss | English | Fix |
|---|---|---|---|---|---|
| 1-1 | ⚠ ERROR | ཆོས་ཀྱི་སྐུ (chos kyi sku) | dharmakāya, a buddha-body | "the dharma they embody" | dharmakāya / truth-body, not "dharma" |

**Result: <k>/<total> clean, <e> errors, <m> softening notes.**
```

Never overwrite an earlier subsection; append and extend the progress row.

#### Step 4a — Verify the write landed

Re-read the report back (a fresh read) and confirm the new subsection is present as
written; if
the re-read is missing or stale, redo the write once, then tell the user plainly if
it still doesn't stick (suggest the file may be open in Obsidian or under a sync
conflict).

#### Step 5 — Report back

Tell the user: which commentary/translation/scope was checked, the clean/error
counts, and the full text of every ERROR row (with its Tibetan + commentary gloss)
so they can act without opening the file. Offer to apply the fixes.

---

### Completion check

- [ ] Commentary, translation file, and bounded scope all established before starting.
- [ ] Commentary extracted; empty-bucket / cascading-shift artifacts resolved, not mis-reported.
- [ ] Every verse got a term-alignment table anchored on the commentary's own glosses, before any verdict.
- [ ] Second pass on kāya/entity/number swaps completed.
- [ ] ERRORs (wrong referent) kept distinct from softening/style notes.
- [ ] Report appended (never overwritten) to the commentary×translation report file; write re-read and confirmed.
- [ ] Every ERROR surfaced to the user in chat with its Tibetan + commentary citation.

---

## Phase 2 — Apply fixes — mechanical only, everything logged

Re-assembles the grounding for each flagged verse before touching it, applies only unambiguous corrections, and re-verifies afterwards.

Turns a commentary-fact-check report's ⚠ rows into actual edits in
`<translation>`, then re-verifies the fix by re-running `commentary-fact-check`
on the same range. This exists because `commentary-fact-check` deliberately never
edits the translation — "let the user or a follow-up editing pass fix the
translation file itself" — and doing that follow-up pass by hand, verse by verse,
does not scale. Failure mode this prevents: silently "fixing" a translation with an
interpretive rewrite that isn't actually grounded in the commentary, or fixing a
verse and never confirming the fix actually resolved the flagged discrepancy.

This skill **reports and edits only what is mechanical**. It does not resolve
genuine judgment calls (e.g. choosing between two equally valid English names for
a figure with no commentary-stated preference) — those are surfaced to the human,
not decided by the LLM.

---

### Inputs

| Input | Required | Description |
|---|---|---|
| **`<track>`** | ✓ | The translation track to fix. It must already have a `<report>` with at least one ⚠ row in scope. A track that publishes several graded variants (`beginner`, `general`, `advanced`, …) is several tracks for this skill's purposes: one run per variant, each with its own report and its own fix log. |
| **Scope** | recommended | A chapter number, `colophon`, or explicit verse range (e.g. `2-1 to 2-20`). If omitted, use every ⚠ row in the track's report that hasn't yet been resolved (see the Fix Log in Output). |
| **Report file** | derived | `3-TRANSFORMATIONS/Translations/<track>/<report>` — the source of every ⚠ row this skill acts on. If it doesn't exist, stop: nothing to fix. |
| **Commentary source** | ✓ | `<commentary>` — re-read (or reuse the cached `0-INBOX/temp/commentary.json` from the parent skill) to ground each fix. Same restriction as the parent skill: this file only, no other commentary. |
| **Target translation** | ✓ | `3-TRANSFORMATIONS/Translations/<track>/<translation>` — the file this skill edits. |

---

### Output

| Location | Action |
|---|---|
| `3-TRANSFORMATIONS/Translations/<track>/<translation>` | Edited in place — only the specific flagged line(s) for each MECHANICAL fix. Nothing else in the file changes. |
| `3-TRANSFORMATIONS/Translations/<track>/commentary-fact-check-fixes-log.md` | Created (first run) or appended (later runs) — a dated changelog of every fix applied and every fix skipped. |
| `3-TRANSFORMATIONS/Translations/<track>/<report>` | Updated by re-invoking `commentary-fact-check` on the same range (that skill's own re-check-replaces-subsection behavior applies here, not a separate write path owned by this skill). |

---

### Output file format

`commentary-fact-check-fixes-log.md`:

```markdown
# <Track> Translation — Fact-Check Fix Log

Method: mechanical fixes only, applied from ⚠ rows in
<report> and grounded in <commentary>. Judgment
calls are listed but never auto-applied. This is a draft editing pass, not a
scholarly sign-off — a domain specialist should review before treating any track
as final, per this vault's standing rule that an LLM never marks its own
translation output complete.

## Run — <date> — Chapter <N> (or range)

#### Applied

| Verse | Before | After | Grounds |
|---|---|---|---|
| 2-13 | ...Manjushri... | ...Manjughosha... | Locked rendering used at 2-49; report flagged inconsistency |

#### Skipped — needs human judgment

| Verse | Discrepancy | Why not auto-applied |
|---|---|---|
| <id> | <what the report's ⚠ said> | <e.g. two valid renderings, no commentary-stated preference; style choice not factual error> |

**Result: <k> applied, <m> skipped for human review.**

#### Re-verification

Ran `commentary-fact-check` on <track> / Chapter <N> after applying fixes.
Result: <pass count>/<total>, <remaining ⚠ count> — see
`<report>#chapter-<n>` for the fresh verdict table.
```

---

### Rules

1. **Source of truth is the report, not a fresh re-read of the commentary from scratch.** Only act on rows already marked ⚠ in `<report>` for the requested scope. Do not go looking for new discrepancies — that's the parent skill's job.
2. **Minimal edit only.** Change only the span the report's note identifies as wrong (a name, a number, a dropped clause, an inconsistent rendering). Never rewrite a verse's phrasing, meter, or register beyond what the discrepancy requires. This is an edit, not a retranslation.
3. **Every edit is grounded in `<commentary>`**, via the specific commentary passage the report already cited, or a fresh read of that verse's passage if the report's note doesn't quote enough to act on directly. Never invent a fix from parametric knowledge.
4. **MECHANICAL vs JUDGMENT-CALL triage is mandatory before editing anything.** A row is MECHANICAL only if the commentary unambiguously supports exactly one correction (wrong/omitted named entity, wrong number or enumeration, dropped content the commentary marks essential, a locked term rendered inconsistently with its own established usage elsewhere in the file). A row is JUDGMENT-CALL if the "fix" requires picking between two defensible options the commentary doesn't itself adjudicate (e.g. two acceptable English names, a register preference). JUDGMENT-CALL rows are never edited — log them for the human.
5. **One verse, one targeted edit.** Match the exact existing line (text + `^verse-id`) before replacing it, the same way `extract_translation.py` parses it. If the line can't be matched exactly (file has drifted since the report was written), stop and flag that verse as skipped — do not guess which line it is.
6. **Never touch a verse the report didn't flag ⚠ for the requested scope**, even if something looks off while reading past it. Report it to the human instead; that's a new finding for `commentary-fact-check`, not this skill's job.
7. **Always re-verify after editing.** Once all applicable fixes in scope are applied, re-run `commentary-fact-check` for that same track/scope before reporting success. A fix that doesn't clear the discrepancy on re-check is not done — log it and say so.
8. **Never set `status: complete` on anything.** This skill produces drafts for human review, same as its parent skill and `translation-qa`.
9. **Do not modify any file in `1-SOURCES/`.** Only `<translation>`, the fixes log, and (via re-invoking `commentary-fact-check`) that track's report file are ever written.
10. **Append, dated. Never overwrite** an earlier run's section in the fixes log.

---

### Procedure

#### Step 1 — Load the report and select scope

Open `<report>`. Collect every ⚠ row within the
requested scope (or every unresolved ⚠ row in the whole file if scope was
omitted — cross-check against the fixes log's "Applied" tables from prior runs to
know what's already resolved). If there are zero ⚠ rows in scope, stop and tell
the user there is nothing to fix.

#### Step 2 — Re-assemble grounding for each flagged verse

For each ⚠ verse: get the commentary passage (reuse cached
`0-INBOX/temp/commentary.json` from a prior `commentary-fact-check` run in this session
if present and still valid, otherwise regenerate it with
`4-SYSTEM/Skills/commentary-fact-check/scripts/extract_commentary.py`), and get
the current English line via
`4-SYSTEM/Skills/commentary-fact-check/scripts/extract_translation.py` scoped to
that verse's chapter.

#### Step 3 — Triage: MECHANICAL vs JUDGMENT-CALL

Apply Rule 4 to every flagged verse. Write the triage decision down before editing
anything — this becomes the Applied/Skipped split in the fixes log.

#### Step 4 — Apply MECHANICAL fixes

For each MECHANICAL verse, construct the corrected line (minimal edit per Rule 2)
and replace the exact existing `<text> ^<verse-id>` line in `<translation>`
with it. Do this one verse at a time; do not batch-replace across the file with a
find-and-replace that could match unintended text (e.g. a name that also appears
correctly elsewhere).

#### Step 5 — Write the fixes log

Create `commentary-fact-check-fixes-log.md` if it doesn't exist yet (header
from the Output file format above). Append a new `## Run — <date> — <scope>`
section with the Applied table, the Skipped table, and a result line, per Rule 10.

#### Step 6 — Re-verify

Invoke `commentary-fact-check` (read and follow
`4-SYSTEM/Skills/commentary-fact-check/SKILL.md`) for the same track and scope.
This appends a fresh verdict subsection to `<report>`
per that skill's own re-check-replaces-subsection rule. Record the outcome (pass
count, any ⚠ that persisted) in this run's fixes-log entry under
"Re-verification."

#### Step 7 — Report back

Tell the user: how many fixes were applied, how many were skipped as judgment
calls (list them briefly so the user can decide), and the re-verification result.
If any applied fix still shows ⚠ after re-check, say so plainly and do not claim
the discrepancy is resolved.

---

### Completion check

- [ ] Grade and scope established; report file confirmed to have ⚠ rows in scope.
- [ ] Every flagged verse triaged MECHANICAL or JUDGMENT-CALL before any edit was made.
- [ ] Only MECHANICAL verses edited; each edit minimal and grounded in the cited commentary passage.
- [ ] Each edit matched the exact existing line before replacing it; no guessed line matches.
- [ ] No verse outside the requested ⚠ scope was touched.
- [ ] Fixes log created/appended (never overwritten) with Applied + Skipped tables.
- [ ] `commentary-fact-check` re-run on the same track/scope after edits; result recorded.
- [ ] No `status: complete` set anywhere; no file outside `<translation>`, the fixes log, and that track's report file was modified.
- [ ] User told: fixes applied, judgment calls skipped (with brief reasons), and the re-verification outcome.

---

## After this skill

Re-run `translation-qa` after a fix round: the MQM score is computed against the
translation as it now stands, and a stale QA report is worse than none.
