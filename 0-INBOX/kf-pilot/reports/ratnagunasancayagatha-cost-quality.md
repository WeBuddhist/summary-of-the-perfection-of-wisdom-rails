---
title: "KF AI Translation Pilot — Ratnaguṇasaṃcayagāthā, English, Chinese and Hindi: cost and quality"
status: draft
date: 2026-10-08
source_data: 0-INBOX/kf-pilot/usage-ledger.jsonl; factcheck/*/verdicts.json; factcheck/calibration*/result.json; reports/improvement-*.json; blind-eval/
prices: 4-SYSTEM/scripts/usage-ledger/prices.json (list prices as of 2026-10-07)
---

# Ratnaguṇasaṃcayagāthā (Verse Summary of the Perfection of Wisdom), English, Chinese and Hindi — cost and quality

Draft section for the KF pilot report, the third text after the Diamond Sutra and the Bodhicaryāvatāra.
All figures come from the usage ledger, which records every model call made for this text. Costs are at API list
prices on 2026-10-07 (see *Method and caveats*). The figures can be recomputed with `reports/costs.py`,
`factcheck/improvement.py`, `factcheck/calibration/score.py` and `blind-eval/score.py`.

## 1. What was produced

Source text: 318 blocks (308 verses and prose blocks, 10 headings), 13,494 Tibetan syllables.
Languages: English (en), Chinese in Traditional characters (zh), Hindi (hi).

| Output | Built by | Checked by | en | zh | hi |
|---|---|---|---|---|---|
| Zero-shot translation (baseline) | Gemini 3.1 Pro; DharmaMitra (en) | — | ✓ | ✓ | ✓ |
| Commentary translations, 3 commentaries (baseline, earlier) | Gemini 3.1 Pro, DharmaMitra | — | ✓ | ✓ | — |
| Term list: 600 Tibetan terms (shared by all languages) | Claude Sonnet 5.5 agents | Gemini 3.1 Pro | ✓ | | |
| Glossary, academic + children's renderings | Claude Sonnet 5.5 agents | Gemini 3.1 Pro | ✓ | ✓ | ✓ |
| **Academic translation**: glossary-locked, with Sanskrit + 3 commentaries per verse | Gemini 3.1 Pro | Claude Sonnet 5.5 agents | 12,846 words | 14,613 characters | 12,021 words |
| **Children's version** (ages 8–12), from the academic version + children's glossary | Gemini 3.1 Pro | Claude Sonnet 5.5 agents | 14,037 words | 21,535 characters | 14,669 words |

Every governed translation covers all 318 blocks. The commentaries used for grounding are Ju Mipham's
*Lekshé*, Karmapa Rangjung Dorjé's *Ṭīkā* and Khenrab Jamyang's *Norbu Drönmé*, the three aligned commentaries
that also have machine translations in this vault.

**This text is term-dense.** Its 308 verses yield 600 glossary terms. The Diamond Sutra's 432 segments yielded 278.
The verses pack technical vocabulary (aggregates, the knowledges, the paths and fruits, epithets of the
perfection of wisdom) into four-line stanzas.

## 2. Cost

### By step and language (USD)

| Step | Model | en | zh | hi |
|---|---|---|---|---|
| Term extraction (14 parallel agents; shared) | Claude Sonnet 5.5 | 3.06 | — | — |
| Term review (shared) | Gemini 3.1 Pro | 2.01 | — | — |
| Glossary (style sheet + 13 parallel agents) | Claude Sonnet 5.5 | 6.32 | 5.61 | 5.97 |
| Glossary review | Gemini 3.1 Pro | 0.37 | 0.49 | 0.32 |
| Academic translation, incl. retries and fixes | Gemini 3.1 Pro | 9.26 | 8.79 | 7.55 |
| Academic fact-check, incl. re-checks | Claude Sonnet 5.5 | 13.94 | 8.99 | 7.54 |
| Children's version, incl. retries and fixes | Gemini 3.1 Pro | 4.54 | 4.08 | 4.09 |
| Children's fact-check, incl. re-checks | Claude Sonnet 5.5 | 2.72 | 2.77 | 3.18 |
| Setup (track contracts adapted from the Bodhicaryāvatāra) | Claude Sonnet 5.5 | 0.25 | — | — |
| **Pipeline total (new work)** | | **42.46** | **30.73** | **28.63** |
| Measurement: checker reliability test | Claude Sonnet 5.5 | 0.79 | 0.54 | 0.56 |
| Measurement: blind before/after judge | Gemini 3.1 Pro | 2.59 | 1.77 | 1.46 |
| Measurement: blind comparison with zero-shot and human (both annotators) | Claude Sonnet 5.5 + Gemini 3.1 Pro | 2.30 | 1.96 | 1.98 |
| Zero-shot root translation (baseline) | Gemini 3.1 Pro | 3.32 | 4.08 | 3.54 |
| Commentary translations, 3 commentaries (baseline, earlier) | Gemini 3.1 Pro | 38.07 | 48.01 | — |
| **All work on this text** | | **89.52** | **87.10** | **36.17** |

Pipeline total for the three languages: **$101.82**, including $1.69 for the glossary fix of 2026-10-08 (section 4). Measurement: $13.95. All work on this text: **$212.79**.
DharmaMitra calls are free and not in the totals.

### By version

| Version | en | zh | hi | per 1,000 Tibetan syllables (en / zh / hi) |
|---|---|---|---|---|
| Glossary | 11.76 (incl. shared term list) | 6.09 | 6.28 | 0.87 / 0.45 / 0.47 |
| Academic (translation + fact-check + fixes) | 23.20 | 17.78 | 15.09 | 1.72 / 1.32 / 1.12 |
| Academic incl. its glossary | 34.96 | 23.87 | 21.37 | 2.59 / 1.77 / 1.58 |
| Children's (translation + fact-check + fixes) | 7.25 | 6.86 | 7.26 | 0.54 / 0.51 / 0.54 |
| Zero-shot | 3.32 | 4.08 | 3.54 | 0.25 / 0.30 / 0.26 |

- **Costs per syllable are close to the Diamond Sutra's.** The academic version with its glossary costs
  $1.58–2.59 per 1,000 syllables here, against $1.37–2.14 for the Diamond Sutra. This text costs a little more
  because its glossary is twice as large.
- **Each further language costs less than the first.** The term list is built once, so a new language needs only
  its own glossary: about $6.10–6.30, against $11.76 for English. A full new language (glossary, academic and
  children's) cost $30.73 for Chinese and $28.63 for Hindi.
- **The English academic fact-check cost the most ($13.94).** It was the first full check (16 agents with all
  three commentaries) and its fix round was the largest: 97 segments regenerated and re-checked.
- **Governed vs zero-shot.** The governed academic version, with its glossary, costs 10.5× a zero-shot run in
  English, 5.9× in Chinese and 6.0× in Hindi. Section 3 shows what that buys.
- **Where the money goes** is the same as for the Diamond Sutra:
  - Gemini thinking tokens, billed as output, are most of every Gemini step.
  - Claude cache reads and writes are most of every agent step.

### Compared with human translation

The rates are the same as in the Diamond Sutra report. **84000** sponsors a sūtra at about **USD 400 per Tibetan
page**, and **Prajna Fire** quotes **$100–300 per page** for philosophical texts.
The Ratnaguṇasaṃcayagāthā's 13,494 Tibetan syllables come to roughly **30 Tibetan pages**. This is estimated at
about 450 syllables per Degé page; it is not counted from the block print.

| | One academic translation of the Ratnaguṇasaṃcayagāthā, one language |
|---|---|
| Human, at 84000's rate ($400/page) | about $12,000 |
| Human, at Prajna Fire's rates ($100–300/page) | $3,000–9,000 |
| This pipeline, governed academic incl. its glossary | $34.96 (en) · $23.87 (zh) · $21.37 (hi) |
| Pipeline as a share of the human cost | 0.2–1.2% |

**As before, this compares unequal products.** A human translation at these rates arrives ready to publish.
The pipeline's output is a checked draft that no specialist has reviewed. At the grant's 10% target, a $3,000–12,000
human budget leaves $300–1,200 for specialist review, about 1–8 hours at $150–250 an hour. That is for 30 pages,
after the pipeline's own $21–35.

## 3. Quality

### Glossary consistency (automatic check)

| Version | Locked-term uses required | en | zh | hi |
|---|---|---|---|---|
| Academic | 1,823 per language | 1,820 (99.8%) | 1,822 (99.9%) | 1,819 (99.8%) |
| Children's | 1,823 per language | 1,821 (99.9%) | 1,819 (99.8%) | 1,811 (99.3%) |

The remaining gaps are segments where the translator kept a different wording after one automatic retry and the
fact-checker accepted it. As with the Diamond Sutra, most Hindi children's gaps are probably inflected forms
the matcher does not recognise. They have not been reviewed one by one.

### Fact-check (Claude checks Gemini's output, segment by segment)

**Academic.** Each verse is checked against the Tibetan, the Sanskrit and 3 aligned commentaries.

| | en | zh | hi |
|---|---|---|---|
| Passed first time | 298 / 308 (96.8%) | 297 / 308 (96.4%) | 301 / 308 (97.7%) |
| Major errors found | 11 | 11 | 7 |
| … by type | 9 mistranslation, 1 omission, 1 doctrinal | 5 mistranslation, 2 omission, 2 doctrinal, 1 terminology, 1 ambiguity | 6 mistranslation, 1 terminology |
| Minor issues found | 106 | 59 | 59 |
| Critical errors | 0 | 0 | 0 |
| Final state | all pass | all pass | all pass (5-107 at attempt 3) |

**Children's.** Each segment is checked against the approved academic version and the Tibetan.

| | en | zh | hi |
|---|---|---|---|
| Passed first time | 305 / 308 | 297 / 308 | 297 / 308 |
| Major errors found | 4 | 11 | 11 |
| Minor issues (left open, as for the Diamond Sutra) | 79 | 82 → 84 | 141 → 147 |
| Final state | all pass (4-48 at attempt 3) | all pass | all pass |

Typical major errors in the children's versions: an invented addressee ("Subhuti, …" where the verse names no
one), "some beings" for all beings, and a simplification that changes who acts.

### Improvement from the fact-check and fix

Fix rules, as for the other texts:
- **Major errors:** regenerated with the checker's evidence, re-checked, and kept on a pass. A verse that fails twice
  gets one more attempt.
- **Minor-only fixes:** kept only if the blind pairwise judge (Gemini, both A/B orders) prefers them or ties.
  Otherwise the original is restored.
- **Re-check failures:** a fix that fails the re-check after the original had passed is reverted to the original.

| Track | Regenerated (kept) | Failing segments | Minor issues | Penalty per 1k syllables | Error-free segments |
|---|---|---|---|---|---|
| en academic | 80 | 10 → 0 | 106 → 46 | 11.93 → 3.41 | 68.5% → 88.0% |
| zh academic | 56 | 11 → 0 | 59 → 22 | 8.45 → 1.63 | 79.5% → 93.2% |
| hi academic | 53 | 7 → 0 | 59 → 10 | 6.97 → 0.74 | 81.2% → 96.8% |
| en children | 6 | 3 → 0 | 79 → 79 | 7.34 → 5.85 | 75.6% → 76.0% |
| zh children | 13 | 11 → 0 | 82 → 84 | 10.15 → 6.22 | 72.1% → 74.7% |
| hi children | 13 | 11 → 0 | 141 → 147 | 14.52 → 10.89 | 57.8% → 58.8% |

Penalty: minor 1, major 5, critical 10 points. The "after" figure for each segment is the verdict of the check that
saw its final text; every segment's final text has been checked.

**Blind before/after judge** (Gemini compares the original and the fixed academic text in both orders; a win or loss
counts only when both orders agree):

| Track | Major-error fixes: better / tie / worse | Minor-only fixes: better / tie / worse | Minor fixes reverted |
|---|---|---|---|
| en academic | 6 / 2 / 2 (of 10) | 45 / 23 / 16 (of 84) | 16 |
| zh academic | 8 / 3 / 0 (of 11) | 33 / 10 / 8 (of 51) | 8 |
| hi academic | 5 / 0 / 2 (of 7) | 32 / 12 / 6 (of 50) | 6 |

- **Major-error fixes are mostly real improvements:** 19 of 28 judged better and 4 judged worse. All 28 pass
  Claude's re-check. In the 4 "worse" cases the two models disagree about whether the original was wrong; they
  are kept, by rule, as fixes of a flagged major error.
- **Minor-only fixes help about four times as often as they hurt** (110 better, 30 worse across the three
  languages). The 30 worse ones were restored, so the final text keeps only the fixes the judge preferred or tied.
- **chrF against the human Chinese version (T229)** barely moves: 9.45 → 9.46 for the whole text, 9.19 → 9.23 on the
  54 changed segments. T229 is classical verse of seven characters a line, translated from a different source
  tradition, so character overlap with modern Chinese is near the floor and cannot show the fixes. There is no human
  English or Hindi version in the vault.

### How reliable is the checker?

The test plants 18 known errors in 24 verified academic segments and leaves 6 untouched as controls. The plants are
9 negations, 2 numbers, 2 locked-term swaps, 2 wrong words, 1 name swap, 1 omission and 1 addition, the same mix as
the Diamond Sutra test, at the same verses in all three languages. A fresh checker then checks the batch blind.

| | en | zh | hi |
|---|---|---|---|
| Planted errors caught | 15 / 18 | 15 / 18 | 16 / 18 |
| … and the issue points at the planted words | 15 | 15 | 16 |
| All 9 negations caught (rated critical) | ✓ | ✓ | ✓ |
| False alarms on the 6 clean controls | 0 | 0 | 0 |
| Missed | 2 term swaps, 1 number | 2 term swaps, 1 wrong word | 2 term swaps |

- **The checker's blind spot is the same as for the Diamond Sutra.** In every language it notices a locked term
  swapped for a near-synonym ("transcendent insight" for "perfection of wisdom", "noble beings" for "holy beings")
  but rates it minor, so the segment passes.
- **The automatic glossary check covers part of that blind spot.** In English it flags the 1-19 swap; it misses
  2-25 because the words of the locked term still occur elsewhere in the verse. Checker and glossary check together
  catch 16 of 18 in English.
- **The English number miss** ("billions" → "millions" of eons at 4-66) involves a Tibetan large number (བྱེ་སྟོང)
  whose exact value is itself hard to render, so the checker let the change pass.

### Blind comparison: governed vs zero-shot vs human

**Set-up**, as for the Diamond Sutra:
- **Sample:** 40 verses, one at random from each fortieth of the text, the same verses in every language.
- **Candidates:**

  | Language | Candidates |
  |---|---|
  | en | governed academic, DharmaMitra zero-shot, Gemini zero-shot |
  | zh | governed academic, Gemini zero-shot, T229 (human, classical) |
  | hi | governed academic, Gemini zero-shot |

- **Blinding and scoring:** candidates were shuffled under letters. Annotators saw the Tibetan, the neighbouring
  verses, the Sanskrit and the commentaries, but no glossary. MQM annotation was done by both Claude and Gemini.

**Errors per verse (mean penalty; lower is better)**, Claude / Gemini as annotator:

| System | en | zh | hi |
|---|---|---|---|
| **Governed academic** | **0.10 / 0.28** | **0.07 / 0.40** | **0.38 / 0.75** |
| Zero-shot, Gemini | 0.80 / 1.35 | 0.55 / 1.27 | 0.78 / 1.68 |
| Zero-shot, DharmaMitra | 1.15 / 1.95 | — | — |
| Human, T229 (classical Chinese) | — | 8.18 / 11.78 | — |

**Major and critical errors in the 40 verses**, Claude / Gemini as annotator:

| System | en | zh | hi |
|---|---|---|---|
| **Governed academic** | **0 / 1** | **0 / 2** | **1 / 5** |
| Zero-shot, Gemini | 3 / 9 | 3 / 8 | 3 / 11 |
| Zero-shot, DharmaMitra | 5 / 12 | — | — |
| Human, T229 | — | 53 / 66 | — |

**Head to head (verses where the governed version has fewer / equal / more errors)**, Claude / Gemini:

| Governed vs | en | zh | hi |
|---|---|---|---|
| Zero-shot, Gemini | 18–20–2 / 15–22–3 | 8–30–2 / 12–25–3 | 15–20–5 / 17–17–6 |
| Zero-shot, DharmaMitra | 21–18–1 / 20–17–3 | — | — |

What this shows:
- **The governed version has the fewest errors in every language under both annotators.**
- **The gain is larger than for the Diamond Sutra.**
  - In English, the governed version beats Gemini zero-shot on 15–18 of 40 verses and loses on 2–3. For the
    Diamond Sutra it was nearly level.
  - The Ratnaguṇa is less familiar to the models than the Diamond Sutra, and its verses are denser. The glossary
    and the aligned commentaries matter more here.
- **Hindi has the most remaining errors** in the governed version: 1 major (Claude) and 5 (Gemini) in 40 verses.
  It still has half the zero-shot's penalty.
- **The annotators agree on direction, less on detail.** They order candidate pairs the same way in 80% of Chinese
  pairs, 49% of English and 39% of Hindi. System-level conclusions hold under both; segment-level ones do not.
- **T229 is not a fair benchmark for fidelity to the Tibetan.** Like Kumārajīva for the Diamond Sutra, it is a
  classical translation of a different recension in compressed seven-character verse. Its high error count
  (53–66 major or critical in 40 verses) measures distance from the Tibetan, not the quality of the translation.

## 4. Findings specific to this text

- **Multi-sense terms need every occurrence, not three examples.** The glossary agents first split ཆོས into
  "phenomena" and "Dharma" from a few examples. An extra pass over all 65 occurrences reassigned 17 of them and found
  a third sense ("quality", 5 occurrences). It also found that བྱང་ཆུབ་སེམས at 1-10, 1-18 and 5-40 is the metrical
  short form of བྱང་ཆུབ་སེམས་དཔའ ("bodhisattva"), not "mind of awakening". Gemini's glossary review had flagged
  the last point; it was applied by hand.
- **Two sense assignments were wrong and were fixed after the checks (2026-10-08).**
  - At 7-1 and 8-1, ཆོས had been locked as "phenomena"; the commentaries read the path's virtuous qualities, the
    perfections (Mipham; Rangjung Dorjé: དགེ་བའི་ཆོས་ཀུན). Both were moved to the "quality" sense (quality / 功德 / गुण).
  - At 4-16, ལྟ had been locked as "view" (見, दृष्टि); Mipham and Khenrab gloss ལྟ་དང་བཅས་པའི་སེམས as a mind
    wanting to look at outer objects. ལྟ now has two senses: "view" at 2-42 and "longing to look" at 4-16
    (貪看, देखने की लालसा).
  - The three verses were regenerated in all six tracks and re-checked: all 18 pass with no major issue.
  - The fact-checkers had flagged all three, so they caught what the glossary agents missed.
- **Cross-text consistency was enforced by hand.** For terms the Diamond Sutra glossary already had, the English
  children's renderings follow it: bodhisattva → "awakening hero", mahāsattva → "great being" / "great hero",
  arhat → "worthy one".

## 5. Still to do for this text

- **Specialist scoring of the blind sample** (40 verses × 3 languages), as for the Diamond Sutra.
- **A human translation made from the Tibetan** as a fair benchmark: T229 is classical and follows another recension.
- **Specialist review time** to bring the governed versions to publication.

## Method and caveats

- **Prices, token counting and API-equivalence** are as described in the Diamond Sutra report.
  - Gemini tokens are exact.
  - Claude output tokens are estimated from the text each agent wrote; thinking tokens are not counted, so Claude
    costs are a lower bound.
- **Shared costs sit under English:** the term list ($5.07) and the setup ($0.25).
- **Wasted work is included in the costs:**
  - One English children's run was started twice by mistake (two processes translated about 120 segments). The
    text the fact-check saw was kept.
  - One glossary agent stalled and was rerun, and 12 agents were lost to a network outage and rerun. The lost
    agents' partial usage is not in the ledger.
- **The earlier zero-shot and commentary runs** (2026-10-05/06) were added to the ledger from their logs.
- **Not counted:** the orchestrating session and the one-time adaptation of the pipeline to this text.
