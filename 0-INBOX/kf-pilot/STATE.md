# KF pilot — Ratnaguṇasaṃcayagāthā pipeline state

Third text of the KF AI-translation pilot. Same method as the Diamond Sutra and the Bodhicaryāvatāra
(`daimond-sutra-rails/0-INBOX/kf-pilot/STATE.md` has the decisions and the keep-best rule;
`bodhisattvacharyavatara-rails/0-INBOX/kf-pilot/STATE.md` the verse-text adaptations).
Scripts copied from the Bodhicaryāvatāra pipeline on 2026-10-07 and adapted; text id `ratnagunasancayagatha`.

## Decisions
- User (2026-10-07): same pipeline as the other two texts. Gemini translates, Claude checks, the cross-model review approves; academic + children's; en, zh (Traditional), hi; measure the improvement of every fact-check + fix round; keep-best rule for minor fixes.
- Made in this session, following the Bodhicaryāvatāra precedent (revisit if the user disagrees):
  - Term-extraction baselines: the existing DharmaMitra en + Gemini en zero-shots (2026-10-06).
  - The human Chinese version (`1-SOURCES/Translations/zh-ratnagunasancayagatha.md`, T229 佛母寶德藏般若波羅蜜經, classical, translator not recorded upstream) stays OUT of the pipeline, so it can be the independent chrF reference. No human English or Hindi version is in the vault: chrF for zh only.
  - Commentaries for segment context: Ju Mipham (`bo-mipham`), Karmapa Rangjung Dorjé (`bo-rangjung`), Khenrab Jamyang (`bo-khenrab`). These are the three that have machine translations in this vault. Shāsana's Dībam Bedön Drönmé is aligned too but is not used; Cone and Senge Zangpo are not aligned.

## Source map
| What | File |
|---|---|
| Tibetan root (318 blocks: 308 segments + 10 headings; ids `<topic>-<n>`, topics 0–8) | `1-SOURCES/Translations/bo-ratnagunasancayagatha.md` |
| Sanskrit (aligned by `![[…sa-ratnagunasancayagatha.md#^id]]` above each Tibetan block) | `1-SOURCES/Text/sa-ratnagunasancayagatha.md` |
| Commentaries (aligned by `![[…bo-ratnagunasancayagatha.md#^id]]`) | `1-SOURCES/Commentaries/bo-{mipham-lekshe,rangjung-dorje-tika,khenrab-jamyang-norbu-dronme}.md` |
| Human zh reference (aligned by transclusion; zh ids ≠ bo ids) | `1-SOURCES/Translations/zh-ratnagunasancayagatha.md` |

## Pipeline status
| Step | Status | Where |
|---|---|---|
| 0 Setup: kf-pilot scripts and prompts copied from the BCA and adapted; usage-ledger copied; track contracts (requirements + audience) for en/zh/hi × academic/children | done | `0-INBOX/kf-pilot/`, `4-SYSTEM/scripts/usage-ledger/`, `3-TRANSFORMATIONS/Translations/{en,zh,hi}-{academic,children}/` |
| 0b Zero-shot baselines: DharmaMitra en, Gemini en, Gemini zh | existed (2026-10-06), 308/308 | `3-TRANSFORMATIONS/Translations/{Dharmamitra,Gemini}/` |
| 0c Gemini hi zero-shot | done — 308/308, 0 line-parity failures; en/zh/hi baseline costs backfilled to the ledger | `Gemini/hi/` |
| 1 Term extraction (14 Sonnet agents) | done — 603 terms, 1,674 occurrences | `term-extract/ratnagunasancayagatha-en/` |
| 1b Recall check + Gemini review | done — review dropped 39, fixed 30 spans, added 201 occurrences → 600 terms, 1,834 occurrences | `term-list.md`, `registry-reviewed.json` |
| 2 Termbase en (style sheet + 13 agents + sense pass + Gemini review) | done — 600 terms; Gemini: 15 objections, 11 applied | `termbase/ratnagunasancayagatha-en/`; installed as `en-{academic,children}/termbase.md` |
| 2b Termbase zh, hi (pivot on en; style sheet + 13 agents each + Gemini review) | done — zh 21 applied, hi 15 applied | `termbase/ratnagunasancayagatha-{zh,hi}/`; installed in the tracks |
| 3 Segment context | done — 308 segments; Sanskrit 307; Mipham 306, Rangjung 305, Khenrab 305 | `context/ratnagunasancayagatha-context.json` |
| 4 Academic translation en | done — 318/318; 3 segments still miss a locked term | `3-TRANSFORMATIONS/Translations/en-academic/` |
| 5 Fact-check en academic a1 (16 Sonnet agents) | done — 298/308 pass; 11 major (9 mistranslation, 1 omission, 1 doctrinal), 106 minor | `factcheck/academic-a1/verdicts.json` |
| 5b Fix round en: 10 major regenerated (attempt 2); 87 minor-only regenerated | major done; minor running | `factcheck/academic-a1/feedback{,-minor}.json`; next: re-check `academic-a2`, `loop.py keep-best`, pairwise judge `--revert-losses` |
| 4 zh / hi academic | running | `translate/{zh,hi}-academic-run.log` |

### Decisions made while running (this session)
- English style sheet aligned with the Diamond Sutra termbase for shared terms: bodhisattva → children "awakening hero"; སེམས་དཔའ་ཆེན་པོ → "great being" / "great hero"; arhat → children "worthy one".
- Sense pass: the termbase agents saw only 3 examples per term, so an extra agent assigned senses from every occurrence for ཆོས (34 phenomena / 26 Dharma / 5 quality), ཁམས, སྟོང, སྟོང་པ, ས (stage / birthplace at 4-13). བྱང་ཆུབ་སེམས at 1-10, 1-18, 5-40 is the metrical short form of བྱང་ཆུབ་སེམས་དཔའ → its own sense "bodhisattva" (Gemini flagged it; applied by hand).
- New helpers: `termbase/render_prompts_lang.py`, `factcheck/render_prompts.py`, `harvest.py` (agent usage from an agents-map.json); `factcheck/loop.py` copied from the BCA; `pairwise_judge.py --revert-losses` ported from the Diamond Sutra.

### Findings to carry into the report
- Ratnaguṇa is term-dense: 600 terms for 308 verses (Diamond 278 for 446 segments).
- Checker note: ཆོས at 7-1 and 8-1 is locked as "phenomena", but the commentaries read virtuous dharmas / perfections there — a sense-assignment question for the termbase.
- One Hindi termbase agent stalled (watchdog, no output); rerun. Its ledger row shows model `<synthetic>` and $0 (partial cost not priced).
- A Gemini batch (5-69..5-74) hung >20 min in the en academic run; it completed when the run was restarted.

## Commands (from the vault root; Gemini scripts through `zsh -ic` so the key is read)
PY=/Users/tashitsering/Desktop/work/Obsidian/KF-project/.venv/bin/python
- Term review: `$PY 0-INBOX/kf-pilot/term-extract/gemini_review.py 0-INBOX/kf-pilot/term-extract/ratnagunasancayagatha-en`, then `verify.py consolidate <run> --review <run>/review.json`, `term_list_md.py`.
- Hindi baseline (resumes from its ledger): `gm_translate.py --source 1-SOURCES/Translations/bo-ratnagunasancayagatha.md --lang hindi --lang-tag hi --out 3-TRANSFORMATIONS/Translations/Gemini/hi --style-file …/Gemini/hi/style.md --context-header …/Gemini/hi/context-header.md --extra-fm …/Gemini/hi/work/extra-fm-bo-ratnagunasancayagatha.json`, then the same with `--headings --style-file …/heading-style.md`.

## Status (2026-10-08): ALL SIX TRACKS FINAL — report drafted
**Published (2026-10-08):** Claude Docs doc "KF Pilot — Ratnaguṇasaṃcayagāthā: Cost and Quality", https://claude.ai/artifact/GqTDoMqboGVvxoZjC81U5R (edit through the Docs connector). Source: `reports/ratnagunasancayagatha-cost-quality.md` (costs via `reports/costs.py`; metrics `reports/improvement-ratnagunasancayagatha.json`; judge `reports/improvement-judged-ratnagunasancayagatha.json`; blind eval `blind-eval/score.py`).
- Academic (en/zh/hi): first check 298/297/301 of 308 pass → 0 failing; minor 106→46 / 59→21 / 59→10; error-free 68.5→88.0 / 79.5→93.5 / 81.2→96.8%.
- Children's (en/zh/hi): first check 305/297/297 → 0 failing (en 4-48 at attempt 3); minors left open.
- Judge: major fixes 19/28 better, 4 worse (kept by rule); minor fixes 110 better / 45 tie / 30 worse → 30 reverted.
- Calibration: en 15/18, zh 15/18, hi 16/18 caught, 0 false alarms; misses = locked-term swaps rated minor.
- Blind MQM (40 verses): governed has the fewest errors in all languages under both annotators; T229 not a fair benchmark.
- Cost: pipeline $101.82 (en 42.46 / zh 30.73 / hi 28.63, incl. $1.69 glossary fix); measurement $13.95; all work $212.79.
Open:
1. ~~Glossary corrections~~ — done 2026-10-08: T002 ཆོས at 7-1, 8-1 → "quality" sense; T172 ལྟ split into "view" (2-42) and "longing to look" (4-16), en/zh/hi (edited in agents/batch-02/03.json, zh/hi packets rebuilt with prep_lang.py, `gemini_review.py --apply-only`, termbases re-installed). The 3 verses were regenerated in all 6 tracks (attempt 4) and re-checked in `*-a4`: 18/18 pass.
2. Specialist scoring of the blind sample; specialist review time.
3. Register the pipeline scripts as skills (`create-skill`) once the three texts agree on one version (this vault adds render_prompts_lang.py, factcheck/render_prompts.py, harvest.py, translate/run.sh, translate/regen.sh, factcheck/judge.sh, loop.py feedback guard).
Notes: a network outage killed 12 agents (rerun); an English children's run was started twice by mistake (checked text restored for 116 segments); `loop.py feedback` now skips segments whose text changed since the check.
