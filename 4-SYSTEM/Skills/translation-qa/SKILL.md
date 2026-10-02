---
name: translation-qa
description: MQM-based quality check of a translation file or track in any target language, against the source text, the 2-RAILS/ verse packages, and the track's requirements + termbase. Use whenever asked to QA, check, evaluate, grade, score, review, or "rate" a translation in 3-TRANSFORMATIONS/Translations/ (or a draft translated_*.md), to compare two candidate translations of the same verses, or to decide whether a translation is ready to move from status:draft to status:complete. Produces a qa-report.md with per-verse MQM error annotations (dimension + severity + suggested fix) and an aggregate scorecard with a pass/fail gate. Especially suited to zero-shot output, which reads fluently but hides omissions, mistranslations, and broken verse IDs.
---

# translation-qa — MQM quality check for translation output

This skill grades an already-written translation against its sources. It does **not** rewrite the translation; it reports what passes, what fails, exactly where, and how to fix it, so a reviewer can act and a domain specialist can sign off. It is the QA companion to every generator skill in the repo — `zeroshot-translate`, `graded-translate`, `verse-translate`, `translate-commentary`, `plan-day-generate` — and to any future generator.

The method is **MQM (Multidimensional Quality Metrics)**: instead of a holistic "rate it out of 5", every problem is located, classified by dimension, and assigned a severity. The score is the sum of weighted penalties — but the **error list is the real product**; the number is just its total.

Because authority in this vault comes from the human tradition and never from the model's parametric knowledge, **every accuracy judgement is made against the rails / source, never from memory.** A claim that "this reads wrong" must point to the specific source or rail line it contradicts.

---

## When to use

- The user asks to QA, check, evaluate, grade, score, review, or rate a translation file or track.
- Two candidate translations of the same verses must be compared (pick the better; say why).
- A translation is being considered for promotion from `status: draft` to `status: complete`.
- After generating translation output, as a self-check before saving.

The LLM never sets `status: complete` on its own output — it reports; a domain specialist decides.

---

## Inputs

| Input | Required? | Where to get it |
|---|---|---|
| **Translation file(s)** | Yes | The file under test, e.g. `3-TRANSFORMATIONS/Translations/<lang>-<audience>/Chapter-02.md`, or a draft `translated_*.md`. For comparison, two files. |
| **Source text** | Yes | The root text named in the translation's own `root_text:` frontmatter, plus any pivot or basis file named in its `context_packages:`. Resolve those names against `1-SOURCES/Text/` and `1-SOURCES/Translations/`; if the translation names none, stop and ask which source it was made from rather than guessing. |
| **Verse rails** | Preferred | `2-RAILS/Verses/<verse-id>.md` — the disambiguated restatement is the authority for accuracy. If a verse rail is not `status: complete`, fall back to the source and say so in the report. |
| **Track requirements** | Yes | `3-TRANSFORMATIONS/Translations/<track>/requirements.md` — the register/style contract. |
| **Track termbase** | Yes | `3-TRANSFORMATIONS/Translations/<track>/termbase.md` — the one-rendering-per-keyword contract. |

Read the translation and every relevant source before scoring. Do not score accuracy or terminology from memory.

---

## The MQM rubric (this vault)

### Dimensions

| Dimension | What it catches |
|---|---|
| **Accuracy/Mistranslation** | meaning changed, sense reversed, wrong referent |
| **Accuracy/Omission** | a word, pāda, clause, or whole verse dropped |
| **Accuracy/Addition** | content invented / not in source (hallucination, over-explanation) |
| **Accuracy/Untranslated** | source left untranslated, or an `UNTRANSLATED` placeholder remains |
| **Terminology** | rendering disagrees with `termbase.md`, or a keyword is rendered inconsistently across the file |
| **Fluency** | grammar, agreement, spelling, punctuation, garbled syntax in the target language |
| **Style/Register** | violates `requirements.md` (e.g. colloquial where scholarly is required, or vice-versa) |
| **Audience** | wrong reading level for the track (a plain-track verse that stays technical; a scholarly-track verse that loses precision) |
| **LocaleConvention** | script/number/transliteration conventions; stray foreign-script characters |
| **Markup/BlockID** | broken or mislabeled `^chapter-verse` block ID, duplicate ID, transclusion pointing at the wrong verse, heading-level or danda errors |

`Markup/BlockID` matters as much as meaning here: block IDs are the sole verse-level link across the vault (CLAUDE.md §5), so a mislabeled ID silently breaks every downstream transformation keyed to that verse.

### Severities and weights

| Severity | Weight | Meaning |
|---|---|---|
| **Critical** | 10 | doctrinal meaning reversed/lost; a whole verse or pāda dropped; broken citation link; untranslated content |
| **Major** | 5 | meaning distorted, term contradicts the termbase, clear register violation a reader would notice, duplicate/again-wrong block ID |
| **Minor** | 1 | awkward but meaning intact; punctuation; light register slip; CRLF/formatting |
| **Neutral** | 0 | a preference, logged but not penalised |

### Score and gate

```
MQM score = 100 − (Σ weighted penalties / word_count) × 100
```

**Gate: a file with any Critical or any Major error cannot be marked `complete`** — regardless of its score or how fluent it reads. (A high score with one Critical is still a FAIL.)

---

## How to run

### Stage 0 — mechanical checks (script, deterministic)

Run the bundled script first. It decides the things that need no judgement — verse coverage, mislabeled/duplicate/missing block IDs, leftover `UNTRANSLATED`, stray Latin characters, CRLF — and maps each to an MQM dimension + severity.

```bash
python3 4-SYSTEM/Skills/translation-qa/scripts/mqm_mechanical_checks.py \
    <translation.md> \
    --source <the root text named in the translation's root_text:> \
    --json 0-INBOX/temp/qa-stage0-<name>.json
```

The script's block-ID pattern accepts every ID shape the vaults use: one
segment (`^583`), two (`^1-1`), three or more (`^1-2-3`), letter zones (`^I-4`,
`^a-2`) and letter sub-namespaces (`^1-0a-1`). An ID whose last segment is `0`
is treated as a heading anchor and never counted as a verse.

Always pass `--source` (omission detection depends on it, especially for files that inline verses rather than transclude them). Carry every Stage-0 finding into the report verbatim — these are facts, not opinions.

### Stage 1 — semantic checks (LLM, per verse, against the rails)

For each verse, assemble the bundle — source verse + rail restatement (or source if no complete rail) + `termbase.md` + `requirements.md` + the candidate translation — and emit zero or more error annotations. Judge only against what is in those inputs. Cover, per verse:

1. **Accuracy** — does the candidate say what the rail/source says? Nothing dropped (every pāda), nothing added.
2. **Terminology** — each keyword rendered as `termbase.md` dictates, and consistently throughout.
3. **Style/Register & Audience** — matches `requirements.md` for this track.
4. **Fluency** — reads as correct, natural target-language.
5. **Proper nouns and titles** — every personal name, place name, epithet and title appears in its formal target-language form, not an ad-hoc transliteration or a casual short form; the same name is spelled identically at every occurrence in the file; cited scripture titles are given in full, not truncated, and carry the target language's own title punctuation consistently throughout; and every name or title that the track's `termbase.md` fixes is rendered as the termbase fixes it. A name that drifts between two spellings in one file is `Terminology`, Major; a name or title given in a form no source supports is `Accuracy/Addition`, Major; inconsistent or missing title punctuation is `LocaleConvention`, Minor.

Each annotation: `{verse_id, span, dimension, severity, note, suggested_fix, cite}` where `cite` is the source/rail line the judgement rests on. A verse with no problems produces no annotation.

### Stage 2 — aggregate and write the report

Combine Stage 0 + Stage 1, compute counts and score, apply the gate, and **append** to `3-TRANSFORMATIONS/Translations/<track>/qa-report.md` (create if absent). Never overwrite prior runs — append, dated.

---

## Output — `qa-report.md`

```markdown
## QA run — <file> — <date>

**Score:** 96.1 / 100   **Gate:** FAIL (1 critical, 1 major present)
**Profile:** Accuracy/Omission 2 · Markup/BlockID 1 · Fluency 9 · Terminology 1
**Rails basis:** 2-RAILS/Verses complete for ch.1–2; ch.8 scored against source (rails draft).

### Errors

| Verse | Dimension | Severity | Note | Suggested fix | Cite |
|---|---|---|---|---|---|
| 8-72 | Accuracy/Omission | Critical | verse absent from translation | translate ^8-72 | <root-text>.md#^8-72 |
| 5-78 | Markup/BlockID | Major | body tagged ^5-77 (duplicate); ^5-78 missing | retag → ^5-78 | — |
| 3-19 | Accuracy/Omission | Major | a named image in the source is dropped and generalised | restore the image | 2-RAILS/Verses/3-19.md |
| 8-129 | Fluency | Minor | stray comma, choppy clause | smooth the clause | — |

### Top fixes
1. Translate the omitted verse ^8-72.
2. Retag the mislabeled ^5-78 block.
3. Restore कामधेनु at 3-19.
```

Optionally also write the machine JSON to `0-INBOX/temp/` for tooling.

---

## Comparison mode (two candidates)

Run Stages 0–2 on each file, then present the two scorecards side by side and recommend one. **Decide on the error profile, not the single number** — e.g. a candidate with one Critical (a dropped verse or broken ID) loses to a slightly less fluent candidate that is complete and correctly linked. State the deciding errors explicitly.

---

## Rules

- **No parametric knowledge.** Every accuracy/terminology judgement cites a `1-SOURCES/` or `2-RAILS/` line. If you cannot cite it, do not raise it.
- **Rails first, source as fallback.** Prefer the disambiguated restatement in `2-RAILS/Verses/`; if a rail is not `status: complete`, score against the source and record that in the report's `Rails basis` line.
- **Report, don't rewrite.** Suggest fixes; do not edit the translation.
- **Gate is hard.** Any Critical or Major ⇒ stays `draft`. Only a domain specialist sets `complete`.
- **Append, dated.** Never overwrite earlier QA runs in `qa-report.md`.
- When **any generator skill** changes its rules — `zeroshot-translate`, `graded-translate`, `verse-translate`, `translate-commentary`, `plan-day-generate` — update this skill's Style/Register and Terminology checks to match.
