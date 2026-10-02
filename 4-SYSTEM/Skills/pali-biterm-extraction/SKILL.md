---
name: pali-biterm-extraction
description: For a block-aligned Pāli source file and an English translation file, extract every attested English rendering for each Pāli token's morphological family and write one file per term to bilingual-glossary/. The script (Pass 2) produces a flat draft with per-declension English frequency counts and example phrases; Claude applies semantic grouping to produce the final benchmark format.
---

# pali-biterm-extraction

Extracts bilingual term data from block-aligned Pāli/English markdown files and writes **one file per term** to `bilingual-glossary/`.

Each output file matches the benchmark format in `4-SYSTEM/Benchmarks/bi-term-extraction/output/`:

```markdown
# {term}

## Senses in text:

1. {Sense label}: {pāli example phrase} — "{English translation}"

### 1. {Sense label}
english-rendering1: N
english-rendering2: N

## Declensions in the text:
pali-form1: {pāli example phrase} — "{English translation}"
pali-form2: {pāli example phrase} — "{English translation}"
```

**No Pāli stemming.** Exact token forms are preserved. Morphological merging is done by the human contributor during semantic grouping (Step 3).

---

## Inputs

| Input | Description | Path pattern |
|---|---|---|
| Source file | Pāli root-text markdown with Obsidian block IDs | `1-SOURCES/Text/<lang-tag>-<text>.md` |
| Target file | English translation markdown with matching block IDs | `3-TRANSFORMATIONS/Translations/<track>/<lang-tag>-<text>-<translator>.md` |
| Focus term | Pāli root form to focus on (e.g. `āsava`, `dhamma`) | — |
| Output directory | Folder for the term file | `bilingual-glossary/` |

---

## Output — benchmark format

### `bilingual-glossary/{term}.md`

```markdown
# āsava

## Senses in text:

1. Defilement / outflow: āsavā dhammā — "Phenomena that are taints"

### 1. Defilement / outflow
taint: 29
canker: 24
influx: 14

## Declensions in the text:
āsava: cattāro āsavā — "four cankers"
sāsava: sāsavā dhammā — "tainted phenomena"
anāsava: anāsavā dhammā — "untouched by taints phenomena"
kāmāsava: kāmāsavo — "the canker of sensual desire"
bhavāsava: bhavāsavo — "the canker of existence"
diṭṭhāsava: diṭṭhāsavo — "the canker of views"
avijjāsava: avijjāsavo — "the canker of ignorance"
āsavasampayutta: āsavasampayuttā dhammā — "states concomitant with cankers"
āsavavippayutta: āsavavippayuttā dhammā — "phenomena disjoined from influxes"
āsavānaṃ: āsavānaṃ khaye ñāṇaṃ — "knowledge of the destruction of the taints"
```

---

## Rules

1. **Never modify source files.** Reads `1-SOURCES/` and `3-TRANSFORMATIONS/`; writes only to `bilingual-glossary/`.
2. **Run from the vault root.** All paths in the command are relative to the vault root.
3. **Both files must have matching block IDs.** If the aligned count is zero, stop and report the mismatch.
4. **This skill is descriptive, not prescriptive.** It records what the translation *did*; prescriptive choices belong in `termbase.md`.
5. **Inflected forms are separate keys.** Merge only during the semantic grouping step (Step 3).
6. **Senses reflect genuine lexical polysemy**, not morphological variation. A single-sense term (e.g. āsava) gets one sense block; a polysemous term (e.g. dhamma) gets one block per distinct meaning.

---

## Procedure

### Step 1 — Confirm inputs

```bash
grep -c '\^' 1-SOURCES/Text/pi-dhammasangani.md
grep -c '\^' 3-TRANSFORMATIONS/Translations/en-Contemporary-English-Abhidhamma/en-dhammasangani-ai.md
```

Both counts must match (or be very close).

### Step 2 — Run extraction (produces flat draft)

```bash
python3 4-SYSTEM/Skills/pali-biterm-extraction/scripts/pali_biterm_extraction.py \
    <pali_file> \
    <en_file> \
    bilingual-glossary/ \
    --focus <term>
```

Example for āsava:

```bash
python3 4-SYSTEM/Skills/pali-biterm-extraction/scripts/pali_biterm_extraction.py \
    1-SOURCES/Text/pi-dhammasangani.md \
    3-TRANSFORMATIONS/Translations/en-Contemporary-English-Abhidhamma/en-dhammasangani-ai.md \
    bilingual-glossary/ \
    --focus āsava
```

The script writes `bilingual-glossary/āsava-draft.md` — one section per Pāli declension form with English frequency counts and a representative example phrase. Progress summary:

```
source : …
target : …
focus  : āsava
format : term-file
blocks : N src / N tgt
aligned: N block pairs
Pass 1 : TF-IDF keyword extraction …
         N keywords selected
Building sub-block pairs …
Pass 2 : weighted co-occurrence …
terms  : N English terms in output
output : bilingual-glossary/āsava-draft.md
focus  : N English keywords matched — [taint, canker, influx, ...]
```

Optional flags:

| Flag | Default | Effect |
|---|---|---|
| `--top N` | 600 | English keywords to consider |
| `--min-co N` | 2 | Minimum raw co-occurrence count |
| `--min-score F` | 0.25 | Minimum weighted alignment score |
| `--max-pi-df F` | 0.99 | Max Pāli doc-freq fraction |
| `--max-pi-per-kw N` | 20 | Max Pāli tokens linked to one English keyword |
| `--max-phrase N` | 4 | Maximum phrase length in words |

### Step 3 — Apply semantic grouping (Claude step)

Read `bilingual-glossary/{term}-draft.md`. Then:

1. **Identify semantic senses** — genuine lexical polysemy among the declension forms:
   - Declensions whose English keywords overlap → same sense (one cluster)
   - Declensions mapping to distinct English families → separate senses
   - Flag English words that appear in two distinct senses for disambiguation

2. **Write a sense label** for each cluster:
   - `Defilement / outflow` (āsava family)
   - `The teaching / doctrine` vs. `Phenomenon / mental state` (dhamma polysemy)

3. **Choose a representative example phrase** for each sense from the draft's per-declension examples — the clearest, most concise phrase that illustrates that sense.

4. **Aggregate English counts** across all declensions in the same sense cluster (sum per English rendering).

5. **List all declensions** in the `## Declensions in the text:` section — one line per form, using the example phrase from the draft.

6. **Write the final file** `bilingual-glossary/{term}.md` in the benchmark format. Sort senses by total count descending; sort English renderings within each sense by count descending.

### Step 4 — Spot-check the output

Verify expected English keywords appear and map to plausible Pāli equivalents. Reference the benchmark files in `4-SYSTEM/Benchmarks/bi-term-extraction/output/` for comparison.

Key terms to check:

| Expected Pāli term | Expected top English renderings |
|---|---|
| āsava | taint, canker, influx |
| dhamma (sense 1) | dhamma, truth, doctrine |
| dhamma (sense 2) | phenomena, states, factor |
| phassa | contact |
| vedanā | feeling |
| saññā | perception |
| cetanā | volition |
| vitakka | initial application |
| vicāra | sustained application |
| jhāna | jhāna |

---

## Completion check

- [ ] Both source and target files confirmed present with matching block IDs
- [ ] Script ran without errors and reported > 0 aligned block pairs
- [ ] Draft file written to `bilingual-glossary/{term}-draft.md`
- [ ] Semantic grouping applied — senses identified and sense labels written
- [ ] Final file written to `bilingual-glossary/{term}.md` in benchmark format
- [ ] Output spot-checked against expected renderings table
- [ ] Draft file (`{term}-draft.md`) removed after final file is confirmed
