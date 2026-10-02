---
name: bilingual-glossary
description: >
  Build and maintain a project's bilingual glossary end to end: extract every
  source-language keyword and its attested renderings from each (source, translation)
  pair, merge the per-source files into one consolidated glossary per language pair,
  flag the terms whose renderings genuinely disagree, and select the preferred
  rendering for a particular translation track.

  Trigger this skill for any glossary or termbase work: "extract the glossary",
  "build the bilingual glossary", "combine the glossaries", "which terms are
  contested", "pick the termbase renderings", "make the working glossary for this
  track", "consolidate the keyword renderings".

  Phases are separately addressable — run only the one the user needs.
---

# Bilingual glossary — extract, consolidate, contest, select

A glossary is built in four passes, each with a different job and a different
output. They were four separate skills; they are one skill because each phase reads
only what the previous one wrote, and running them out of order silently produces a
glossary that looks complete and is not.

| Phase | Does | Input → Output |
|---|---|---|
| 1 — Extract | Every keyword and the rendering(s) it actually receives, per source | one (root, translation) pair → `2-RAILS/Bilingual-Glossaries/Raw/<pair>.md` |
| 2 — Combine | Merge every raw file sharing a language pair | all `2-RAILS/Bilingual-Glossaries/Raw/<pair>*` → `2-RAILS/Bilingual-Glossaries/<pair>.md` |
| 3 — Contest | Rank the terms whose renderings genuinely disagree | `2-RAILS/Bilingual-Glossaries/<pair>.md` → contested shortlist |
| 4 — Select | Choose one preferred rendering per term, for one track | consolidated + shortlist → `3-TRANSFORMATIONS/Translation/<track>/bilingual glossary.md` |

**Run only what is asked for.** "Extract the glossary for this commentary" is Phase 1
alone. "What terms are contested?" is Phase 3 alone, and needs Phase 2 to have run.
Phase 4 is per translation track and is re-run whenever the track's requirements
change — it never edits the consolidated glossary it reads from.

**Two extraction inputs exist.** Phase 1 normally reads a (root text, translation)
pair directly. The Abhidhamma vault instead extracts from an already-built
**interlinear gloss file** (`interlinear-gloss`), in both horizontal (`\gla`/`\glb`)
and vertical formats — same output, different input. If an interlinear gloss already
exists, prefer it: its alignment is already reviewed.

---

## Phase 1 — Extract — raw per-source glossary

Run once per (source, translation) pair. Output is raw evidence: every attested rendering, nothing chosen yet.

This skill turns one **interlinear gloss file** in `2-RAILS/Bilingual-Glossaries/Raw/` into a **raw bilingual glossary** — a per-source record of every keyword in the original language and every distinct rendering it receives in this translation. The raw bilingual glossaries are the input for `glossary-combine`.

The gloss file is the primary input. It must exist before this skill runs. Run `interlinear-gloss` first to produce it.

The skill has two passes:

1. **Token-pair extraction** (helper script) — walk every ```` ```gloss ```` block in the gloss file, pair each `\gla` token with the `\glb` token at the same column position, and tally distinct (source-token, target-rendering) pairs across verses.
2. **Sense disambiguation and curation** (LLM) — group the raw tallies by source lemma, merge inflectional variants, separate clearly distinct senses, pick sample pairings, and write the final raw bilingual glossary.

---

### Inputs

- **Interlinear gloss file** — `2-RAILS/Bilingual-Glossaries/Raw/<source-lang>-<target-lang-tag>-gloss.md`. Produced by the `interlinear-gloss` skill. Must validate clean (run `scaffold_gloss.py --validate` first).
- **Keyword list (optional)** — if a controlled keyword list exists (extracted from the mātikā, or pulled from existing Local-Wiki articles), pass it in to constrain extraction. If omitted, extract every source token that recurs at least three times across the gloss file.

### Output

One file at:

```
2-RAILS/Bilingual-Glossaries/Raw/<source-lang>-<target-lang-tag>.md
```

The filename mirrors the gloss file but without the `-gloss` suffix. For example, `pi-en-rd-gloss.md` → `pi-en-rd.md`. Both files live side by side under `Bilingual-Glossaries/Raw/`.

---

### Output file format

```markdown
---
gloss_file: 2-RAILS/Bilingual-Glossaries/Raw/<source-lang>-<target-lang-tag>-gloss.md
source_file: 1-SOURCES/Text/<root-text>.md
target_file: 1-SOURCES/Translations/<translation>.md
source_language: <pi | sa | bo | zh>
target_language: <en | bn | sin | ...>
language_pair: <pi-en | pi-bn | ...>
target_lang_tag: <en-rd | en | bn | sin | ...>
translator: <name from translation frontmatter, if present>
total_keywords: <count>
status: draft
---

## Raw bilingual glossary — <translator / translation short name>

### <source-lang keyword>

**Renderings attested in this source:**

| Rendering | Frequency | First seen | Notes |
|-----------|-----------|------------|-------|
| <target-language rendering> | <n> | ^<block-id> | <inflection / context note> |
| <alternative rendering> | <n> | ^<block-id> | <when this rendering is used> |

**Sample pairings:**

> **^<block-id>** — *<source snippet containing the keyword>*
> → "<corresponding target rendering>"

---

### <next keyword>

...
```

One `##` heading per keyword. Keywords are sorted alphabetically (by source-language form). Diacritics are preserved.

The output schema is **unchanged** from earlier versions of this skill — what changed is the input: the source/target alignment is no longer extracted from the block level (whole-paragraph pairs) but from the token level (one `\gla` token paired with one `\glb` cell), giving cleaner and finer-grained rendering data.

---

### Rules

1. **One raw bilingual glossary per gloss file.** A `pi-en-rd-gloss.md` becomes `pi-en-rd.md`. Never merge two translations into one raw file — that's what `glossary-combine` is for.
2. **Tokens come from `\gla`; renderings come from `\glb`.** The free translation on `\ex` is not used for rendering extraction (it's full-sentence English; `\glb` is the per-token gloss).
3. **Inflectional variants are merged.** *dhammā*, *dhammānaṃ*, *dhammehi* all map to lemma *dhamma*. Normalise manually during the curation pass.
4. **Distinct renderings stay distinct.** `states` and `mental-states` are two renderings of the same keyword, not one. They each get a row with their own frequency.
5. **Sample pairings show context.** Two to four pairings per keyword, chosen to cover the range of renderings and inflectional contexts. Quote the source token in context (a few words on each side) and the rendering verbatim.
6. **No interpretive judgments.** This file is descriptive: what the translation actually does. Whether a rendering is good belongs in `glossary-select`, not here.

---

### Procedure

1. **Validate the gloss file.** Run:

   ```bash
   python3 4-SYSTEM/Skills/interlinear-gloss/scripts/scaffold_gloss.py \
       --validate 2-RAILS/Bilingual-Glossaries/Raw/pi-en-rd-gloss.md
   ```

   The gloss file must validate clean — every `\glb` line has the same token count as its `\gla` line.

2. **Run the token-pair extractor:**

   ```bash
   python3 4-SYSTEM/Skills/bilingual-glossary/scripts/extract_pairs.py \
       2-RAILS/Bilingual-Glossaries/Raw/pi-en-rd-gloss.md \
       0-INBOX/temp/pi-en-rd-pairs.csv
   ```

   The script reads every `gloss` block, pairs `\gla[i]` with `\glb[i]` for each column `i`, and emits a CSV with columns: `source_token, source_lemma, target_rendering, block_id, frequency_within_block`.

3. **Tally by lemma.** Open the CSV and group rows by `source_lemma`. For each lemma, count how many distinct blocks contain each `target_rendering`. Discard rows where the rendering is `--` (unfilled placeholder).

4. **Filter to keywords.** Keep lemmas that recur at least three times. Discard function words and inflectional particles unless they carry interpretive weight (e.g. *iti*). If a controlled keyword list was supplied, intersect with it.

5. **Pick sample pairings.** For each retained lemma, pick two to four blocks that illustrate the range of renderings. The CSV contains the block IDs; cross-reference the gloss file to extract the surrounding tokens for the snippet.

6. **Write the raw bilingual glossary file** to `2-RAILS/Bilingual-Glossaries/Raw/<source-lang>-<target-lang-tag>.md` with the frontmatter populated. Sort `##` headings alphabetically.

7. **Set `status: draft`.** A domain specialist marks the file `complete` after spot-checking.

---

### Helper scripts

- **`scripts/extract_pairs.py`** — walks one gloss file and emits a CSV of `(source_token, source_lemma, target_rendering, block_id)` rows.
- **`scripts/align_blocks.py`** — legacy fallback for cases where no gloss file exists (e.g. for sources where token-level glossing was skipped). Pairs root-text and translation by block ID into a CSV. Use this only if the gloss workflow is not yet available for the language pair in question; the gloss-based extraction is otherwise the canonical input.

---

### Completion check

- [ ] Every keyword appears as its own `##` heading
- [ ] Every keyword has at least one rendering row and one sample pairing
- [ ] Sample pairings show the block ID and quote both source token (in context) and target rendering
- [ ] Frequencies count distinct blocks, not raw token-pair occurrences
- [ ] `total_keywords` in frontmatter matches the number of `##` headings
- [ ] `--` placeholder renderings have not generated rows
- [ ] File is sorted alphabetically by source-language keyword
- [ ] `gloss_file` frontmatter field points at the gloss file that was the input
                                                                                                                                        

---

## Phase 2 — Combine — one consolidated glossary per language pair

Run after every relevant raw file exists. Purely a merge — it never invents or drops a rendering.

This skill takes the raw bilingual glossaries that `glossary-extract-raw` produced — one per translation source — and merges them into a single **consolidated bilingual glossary** per language pair. The consolidated file is descriptive: it tells you, for each source-language keyword, every distinct rendering attested across the corpus and which sources use which rendering.

The consolidated bilingual glossary is the menu that `glossary-select` chooses from when building a per-track bilingual glossary.

---

### Inputs

- **Language pair** — e.g. `pi-en`, `pi-bn`, `pi-sin`. Determines which raw files to merge.
- **Raw bilingual glossaries** — all files under `2-RAILS/Bilingual-Glossaries/Raw/` whose `language_pair` frontmatter field matches the requested pair.

### Output

One file at:

```
2-RAILS/Bilingual-Glossaries/<source-lang>-<target-lang>.md
```

(e.g. `2-RAILS/Bilingual-Glossaries/pi-en.md`). If the file exists, regenerate it from the current raw inputs — manual edits to the consolidated file are discouraged; consolidate from raw instead.

---

### Output file format

```markdown
---
language_pair: <pi-en | pi-bn | ...>
source_language: <pi | sa | bo | zh>
target_language: <en | bn | sin | ...>
raw_sources:
  - 2-RAILS/Bilingual-Glossaries/Raw/<source-name>.md
  - 2-RAILS/Bilingual-Glossaries/Raw/<source-name>.md
total_keywords: <count>
total_distinct_renderings: <count>
generated: <ISO date>
status: draft
---

## Consolidated bilingual glossary — <source-language> → <target-language>

### <source-lang keyword>

| Rendering | Sources | Total frequency | Local-Wiki |
|-----------|---------|-----------------|------------|
| <rendering A> | <src-1> (n), <src-2> (n) | <sum> | [[<term>]] |
| <rendering B> | <src-3> (n) | <n> | [[<term>]] |

---

### <next keyword>

...
```

One `##` heading per keyword. Renderings within a keyword are sorted by total frequency descending — the most widely attested rendering at the top. Keywords are sorted alphabetically (by source-language form, diacritics preserved).

The **Local-Wiki** column links to the Local-Wiki article for the term, if one exists. The link is the same for every row of the keyword's table (it's a property of the keyword, not the rendering). If no Local-Wiki article exists, leave the cell as `—`.

---

### Rules

1. **One file per language pair.** Never mix pairs. `pi-en` is its own file, separate from `pi-bn`.
2. **Regenerate, don't edit.** The consolidated file is a derived artefact. If the data is wrong, fix the raw bilingual glossary, then re-run this skill. Manual edits get overwritten.
3. **Frequencies are summed across sources.** If three sources each use the rendering "states" five times, the total is 15. The `Sources` column makes the per-source breakdown visible.
4. **Renderings that differ only in capitalisation are merged.** `"states"` and `"States"` become one row. Renderings that differ in punctuation or footnote markers are also merged.
5. **Renderings that differ in glossing strategy are not merged.** `"states"` and `"phenomena (dhammā)"` are two distinct renderings — the second carries a transliteration the first does not.
6. **Local-Wiki link is populated automatically.** If `2-RAILS/Local-Wiki/<keyword>.md` exists, link to it. If not, leave `—`. Do not create the Local-Wiki article from this skill — that's the `local-wiki-article` skill's job.

---

### Procedure

The recommended path uses the helper script under `scripts/` followed by an LLM pass for sense-disambiguation edge cases.

1. **Run the merge script:**

   ```bash
   python3 4-SYSTEM/Skills/bilingual-glossary/scripts/combine_glossaries.py \
       pi-en \
       2-RAILS/Bilingual-Glossaries/Raw/ \
       2-RAILS/Bilingual-Glossaries/pi-en.md
   ```

   The script reads every raw bilingual glossary with `language_pair: pi-en`, merges renderings by keyword, sums frequencies, sorts, and writes the consolidated file with frontmatter.

2. **Spot-check sense splits.** Some source keywords have multiple senses in the commentary tradition, and renderings cluster by sense. For example, *kusala* (wholesome) and *kusala* (skill) may both appear; the renderings "wholesome / skilful" partly map to one sense and "good / virtuous" to the other. Where this matters and a sense-split Local-Wiki article exists, split the consolidated keyword heading into two: `## kusala (wholesome)` and `## kusala (skill)`, assigning each rendering row to the right one. The script will not do this automatically — the disambiguator is in the Local-Wiki, not the raw bilingual glossaries.

3. **Verify Local-Wiki links.** For each keyword, confirm that the linked Local-Wiki article (if any) actually documents the senses present in the rendering table. If not, either add a stub or split the keyword.

4. **Set `status: draft`.** A domain specialist marks the file `complete` after review.

---

### Combiner script

`scripts/combine_glossaries.py` reads the raw bilingual glossaries with the requested `language_pair`, walks each `##` heading (one per keyword) and its rendering table, merges them, and writes the consolidated output. It does not invent renderings, it does not invent sense splits, and it does not invent Local-Wiki links — those come from existing files.

Run with `--check` to dry-run: the script reports the keyword count and the distinct-rendering count without writing.

```bash
python3 4-SYSTEM/Skills/bilingual-glossary/scripts/combine_glossaries.py \
    pi-en \
    2-RAILS/Bilingual-Glossaries/Raw/ \
    /tmp/pi-en.md --check
```

---

### Completion check

- [ ] Frontmatter lists every raw file consumed in `raw_sources`
- [ ] `total_keywords` matches the number of `##` headings
- [ ] Renderings within each keyword are sorted by total frequency descending
- [ ] Keywords are sorted alphabetically with diacritics preserved
- [ ] Capitalisation-only duplicates have been merged
- [ ] Sense splits (where they matter) are reflected in separate `##` headings, with the Local-Wiki article for each sense linked
- [ ] Local-Wiki column is `—` for keywords with no article — not blank, not an empty link

---

## Phase 3 — Contest — rank the terms that need a decision

Optional but strongly recommended before Phase 4: it tells you which terms actually need a human termbase decision, instead of reviewing all of them.

This skill reads the consolidated bilingual glossary produced by `glossary-combine` and surfaces the terms most likely to be rendered inconsistently by a zero-shot LLM translation. A term is contested when it has multiple attested renderings and no single rendering dominates strongly enough to be assumed safe. The output is the prioritised input to `glossary-select` for termbase curation.

Without this filter, `glossary-select` must work through hundreds of terms; most have one clear rendering and need no decision. This skill collapses the problem to the ~20–60 terms that actually matter.

---

### Inputs

- **Consolidated bilingual glossary** — `2-RAILS/Bilingual-Glossaries/<source-lang>-<target-lang>.md` (output of `glossary-combine`). Must exist before this skill runs.

### Output

```
0-INBOX/temp/<pair>-contested.md
```

e.g. `0-INBOX/temp/pi-en-contested.md`

---

### Output file format

```markdown
---
source: 2-RAILS/Bilingual-Glossaries/pi-en.md
total_contested: <N>
---

## Contested terms — termbase candidates

Terms are ranked by variation score (1 − max_freq / total_freq).
A score of 0 means one rendering dominates; 1 means renderings are equally split.
These are the terms most likely to be rendered inconsistently in zero-shot translation.

| Term | Top rendering | Alternatives | Total | Score |
|------|---------------|--------------|-------|-------|
| āsava | taint (29) | canker (24), influx (14) | 67 | 0.57 |
| dhamma | phenomena (608) | states (374), factor (57) | ... | 0.40 |

---

### Term details

#### āsava

**Variation score:** 0.57  **Total attestations:** 67  **Distinct renderings:** 3
**Local-Wiki:** [[āsava]]

| Rendering | Frequency | Share |
|-----------|-----------|-------|
| taint | 29 | 43% |
| canker | 24 | 36% |
| influx | 14 | 21% |
```

---

### Rules

1. **Never modify source files.** Reads only from `2-RAILS/Bilingual-Glossaries/`; writes only to `0-INBOX/temp/`.
2. **Three thresholds must all be met** for a term to appear in the output: `min_total` (default 5) total attestations, `min_second` (default 2) attestations for the second-most-frequent rendering, and `min_variation` (default 0.15) variation score.
3. **Capitalisation-only variants are not separate renderings.** `glossary-combine` should have merged these; flag any that slipped through rather than counting them as genuine variation.
4. **Sense-split keywords are evaluated independently.** `dhamma (phenomenon)` and `dhamma (teaching)` are separate keywords — each is assessed on its own rendering table.
5. **The output is descriptive, not prescriptive.** It records observed variation; the choice of which rendering to standardise on is made by `glossary-select`.

---

### Procedure

#### Step 1 — Confirm input

```bash
wc -l 2-RAILS/Bilingual-Glossaries/<pair>.md
```

Confirm the file exists and has content.

#### Step 2 — Run the analysis script

```bash
python3 4-SYSTEM/Skills/bilingual-glossary/scripts/find_contested.py \
    2-RAILS/Bilingual-Glossaries/<pair>.md \
    0-INBOX/temp/<pair>-contested.md
```

The script prints a summary:
```
Reading: 2-RAILS/Bilingual-Glossaries/pi-en.md
Keywords: 312
Contested: 47
Output: 0-INBOX/temp/pi-en-contested.md
```

Optional flags:

| Flag | Default | Effect |
|------|---------|--------|
| `--min-total N` | 5 | Minimum total attestations |
| `--min-second N` | 2 | Minimum second-rendering count |
| `--min-variation F` | 0.15 | Minimum variation score |
| `--top N` | all | Only output top N terms |

#### Step 3 — Review for noise

Scan the term details section. Flag any terms where the variation is artefactual:
- Capitalisation variants not caught by `glossary-combine` (fix upstream)
- Renderings that differ only by a trailing footnote marker or parenthetical gloss (merge upstream)
- Terms where one "rendering" is a phrase fragment from a mis-parsed block (discard)

#### Step 4 — Move after review

```bash
cp 0-INBOX/temp/<pair>-contested.md 2-RAILS/Bilingual-Glossaries/<pair>-contested.md
```

The `glossary-select` skill reads from `2-RAILS/Bilingual-Glossaries/<pair>-contested.md` as its prioritisation guide.

---

### Completion check

- [ ] Consolidated glossary confirmed present at `2-RAILS/Bilingual-Glossaries/<pair>.md`
- [ ] Script ran without errors and reported > 0 contested terms
- [ ] Output written to `0-INBOX/temp/<pair>-contested.md`
- [ ] Term details section reviewed for artefactual variation
- [ ] Output moved to `2-RAILS/Bilingual-Glossaries/<pair>-contested.md` after review

---

## Phase 4 — Select — the per-track working glossary

Run once per translation track. Reads the consolidated glossary (and the contested shortlist, if built) and commits to one rendering per term.

This skill builds the **per-track bilingual glossary** that the translation skill reads on every run. It selects, for each keyword, one preferred rendering for the track from the menu of attested options in the consolidated bilingual glossary — using the track's `requirements.md` as the selection rubric. Where no attested rendering meets the requirements, it derives a new rendering from the keyword's Local-Wiki article and records the new rendering both in this per-track bilingual glossary and back into the consolidated bilingual glossary under `2-RAILS/Bilingual-Glossaries/`.

This is the only skill in the rails workflow that introduces target-language vocabulary into the project. Every other skill catalogues what already exists; this one chooses.

---

### Inputs

- **Track folder** — `3-TRANSFORMATIONS/Translation/<track-name>/`. The folder must already contain `requirements.md`. If it doesn't, run the `requirements-author` skill first (or write it manually) — selection cannot proceed without a rubric.
- **Consolidated bilingual glossary** — `2-RAILS/Bilingual-Glossaries/<source-lang>-<target-lang>.md` for the track's language pair.
- **Local-Wiki articles** — `2-RAILS/Local-Wiki/*.md`, consulted whenever no attested rendering satisfies the requirements.

### Output

Two artefacts:

1. **Per-track bilingual glossary** at:

   ```
   3-TRANSFORMATIONS/Translation/<track-name>/bilingual glossary.md
   ```

   One row per keyword, one chosen rendering per row, with the rationale recorded.

2. **Updates to the consolidated bilingual glossary** at `2-RAILS/Bilingual-Glossaries/<source-lang>-<target-lang>.md` for any new renderings this skill introduces — added as a new row in the keyword's rendering table with source `<track-name>` and frequency `0` (until the translation actually attests it).

If the per-track bilingual glossary already exists, update in place — preserve manually adjusted rationales unless the underlying consolidated bilingual glossary has changed.

---

### Output file format (per-track bilingual glossary)

```markdown
---
track: <track-name>
language_pair: <pi-en | pi-bn | ...>
source_language: <pi | sa | bo | zh>
target_language: <en | bn | sin | ...>
requirements: 3-TRANSFORMATIONS/Translation/<track-name>/requirements.md
consolidated_glossary: 2-RAILS/Bilingual-Glossaries/<source-lang>-<target-lang>.md
total_keywords: <count>
last_updated: <ISO date>
status: draft
---

## Translation bilingual glossary — <track-name>

| <source-lang keyword> | Chosen rendering | Origin | Rationale |
|-----------------------|------------------|--------|-----------|
| <keyword> | <rendering> | attested / derived | <one-line note pointing to the requirements clause or Local-Wiki article that decided it> |

### Notes on derivations

#### <keyword>

<paragraph explaining why no attested rendering satisfied the requirements
and how the new rendering was derived from the Local-Wiki article. Cite
the Local-Wiki article and the requirements clause that drove the choice.>

(2-RAILS/Local-Wiki/<keyword>.md)
(3-TRANSFORMATIONS/Translation/<track-name>/requirements.md)
```

The main artefact is the table. The **Notes on derivations** section only contains entries for keywords with `Origin: derived` — attested selections need no extra prose.

---

### Rules

1. **Attested first, derived only when forced.** If any attested rendering in the consolidated bilingual glossary meets the requirements, prefer it. Derive a new rendering only when none does.
2. **One rendering per keyword.** This is a working bilingual glossary, not a thesaurus. If the track requires different renderings for different senses of one source keyword, treat them as two keywords with sense disambiguators (`kusala (wholesome)`, `kusala (skill)`) — matching the sense splits in the consolidated bilingual glossary.
3. **The rationale column is mandatory.** Every chosen rendering carries a one-line note that points to the part of `requirements.md` (or the Local-Wiki article, for derivations) that justifies the choice. The translation skill reads the rationale to decide edge cases.
4. **Derivations write back to the rails.** Any new rendering introduced by this skill is added to the consolidated bilingual glossary as a new row, source `<track-name>`, frequency `0`. This keeps the consolidated bilingual glossary a complete record of every rendering ever used or proposed for the language pair.
5. **No silent overrides.** If the requirements demand a rendering that the Local-Wiki article would not support (because the article documents the term differently), flag the conflict in the **Notes on derivations** section rather than silently overriding either source.
6. **Diacritics and script preserved.** Source-language keywords in the table use the same form as the consolidated bilingual glossary; target-language renderings use the script declared in `requirements.md`.

---

### Procedure

1. **Read `requirements.md`.** Note: the target register, the preferred-rendering directives, the style constraints, and any explicit term mappings. Treat directives as hard constraints; treat the rest as soft preferences.
2. **Read the consolidated bilingual glossary** for the track's language pair. The list of `##` headings is the working keyword set.
3. **For each keyword:**
   - Look at the rendering table. Sorted by total frequency descending, the top row is the default candidate.
   - Apply the requirements: does the top row satisfy register, the style constraints, and any explicit directives? If yes, select it.
   - If not, walk down the table to the next rendering that does. Select it. Note in the rationale why the more frequent rendering was rejected.
   - If no row satisfies the requirements, open the Local-Wiki article (`2-RAILS/Local-Wiki/<keyword>.md`). Read the Contextual definition and the Attestations. Derive a target-language rendering that captures the term's sense as documented and that meets the requirements. Mark the row `Origin: derived` and add a paragraph to **Notes on derivations**.
4. **Write back the new renderings** to the consolidated bilingual glossary as new rows (source = track name, frequency = 0). This step requires editing `2-RAILS/Bilingual-Glossaries/<pair>.md`. Set the per-keyword row order on re-sort by total frequency descending; the new row with frequency 0 lands at the bottom of its keyword's table.
5. **Write the per-track bilingual glossary** to `3-TRANSFORMATIONS/Translation/<track-name>/bilingual glossary.md`. Set `total_keywords` and `last_updated`. Set `status: draft`.

---

### Re-running this skill

The per-track bilingual glossary is regenerated whenever:

- `requirements.md` changes (e.g. register adjusted, new explicit term mapping added).
- The consolidated bilingual glossary gains new sources (e.g. a fresh `glossary-extract-raw` run added more attested renderings).
- A translation pass introduces a new rendering on the fly (the translation skill records it in the per-track bilingual glossary; the next `glossary-select` run promotes it back to the consolidated bilingual glossary).

In each case the existing per-track bilingual glossary is read first so manually edited rationales are preserved where the underlying selection still holds.

---

### Completion check

- [ ] Every keyword in the consolidated bilingual glossary appears as a row, or has a documented reason for exclusion in **Notes**
- [ ] Every row has an `Origin` (attested / derived) and a rationale
- [ ] Every `derived` row has a paragraph in **Notes on derivations** citing the Local-Wiki article and the requirements clause
- [ ] Every new derived rendering is written back to `2-RAILS/Bilingual-Glossaries/<pair>.md`
- [ ] Sense splits in the consolidated bilingual glossary are preserved in the per-track bilingual glossary
- [ ] Target-language renderings use the script declared in `requirements.md`
- [ ] Frontmatter `requirements` and `consolidated_glossary` paths resolve

---

## After this skill

The per-track glossary from Phase 4 is a **hard constraint** for the translation
skills — `zeroshot-translate` and `translate-commentary` both load it and must not
depart from a locked rendering without saying so. `translation-qa` checks compliance
against it.

If a translation forces a term's rendering to change, change it here in Phase 4 and
re-run the translation — never let the two drift apart.
