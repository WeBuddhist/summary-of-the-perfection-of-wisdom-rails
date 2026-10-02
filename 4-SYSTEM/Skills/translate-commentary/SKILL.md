---
name: translate-commentary
description: Translate a commentary into a target language against a translation track's requirements, termbase and section rails, preserving every block ID and heading so the output stays block-aligned with the source. Output goes to the track folder under 3-TRANSFORMATIONS/Translations/, never to 1-SOURCES/.
---

# translate-commentary

This skill translates a classical commentary from its source language into a target language using a rigorous translation framework. It ensures high fidelity, consistency, and alignment with the track's established terminology and style by actively consulting the track's translation requirements, its termbase, and the section rails that cover the commentary — and it keeps the translation **block-aligned** with the source commentary, so every citation that points into the original still resolves in the translation.

**Where the output goes.** A commentary translation is an AI-generated transformation. It goes to `3-TRANSFORMATIONS/Translations/<track>/`. It is **never** written into `1-SOURCES/` — `1-SOURCES/` is human-produced ground truth and an LLM may not add a file to it. An AI translation placed there would be cited as a source by every downstream skill, which is exactly the corruption the citation chain exists to prevent.

---

## Inputs

1. **Source commentary**
   - The commentary file under `1-SOURCES/Commentaries/`, named by the user. Note its registered short ID (frontmatter `id:` / `short_id:`), its `root_text:`, and its `covers_verses:` range.
2. **Track folder** — `3-TRANSFORMATIONS/Translations/<track>/`
   - The track is an **input**, named by the user (e.g. `<lang>-<audience>`). It is not fixed by this skill. The track must already carry its three contract files; if any is missing, stop and say which.
   - **`requirements.md`** — style constraints, target audience, register, tone, and cultural-adaptation rules, written in the target language.
   - **`termbase.md`** — the locked, prescriptive vocabulary contract: one rendering per source lemma, with rationale.
   - **`audience.md`** — the audience profile the requirements were written for.
3. **Section rails** — `2-RAILS/Sections/<node-id>.md`
   - **Every** TOC node the commentary covers, not one fixed node. Determine the node range from the commentary's own headings and its `covers_verses:`, then load each corresponding section file. Each contains the original-language synthesis, the divergences among commentators, and an English translation — crucial contextual and semantic anchoring.
4. **Verse rails** (where they exist) — `2-RAILS/Verses/<verse-id>.md` for the verses the commentary comments on. Their Disambiguated Restatement resolves ambiguities the section rail leaves open.

---

## Output

- A new translation file inside the track folder:
  ```
  3-TRANSFORMATIONS/Translations/<track>/<commentary-id>-<lang>.md
  ```
  where `<commentary-id>` is the commentary's registered short ID and `<lang>` is the target language tag.
- **Format:** standard markdown, structurally identical to the source commentary — same heading tree, same block boundaries, same block IDs — with complete YAML frontmatter.

```yaml
---
title: "<Commentary name> — <target language> translation"
transformation_type: translation
track: <track>
source_commentary: 1-SOURCES/Commentaries/<file>.md
source_language: <src-lang-tag>
target_language: <tgt-lang-tag>
covers_verses: <first>–<last>
context_packages:
  - 3-TRANSFORMATIONS/Translations/<track>/requirements.md
  - 3-TRANSFORMATIONS/Translations/<track>/termbase.md
  - 3-TRANSFORMATIONS/Translations/<track>/audience.md
  - 2-RAILS/Sections/<node-id>.md          # one line per node loaded
  - 2-RAILS/Verses/<verse-id>.md           # one line per verse rail loaded
generation_date: <YYYY-MM-DD>
status: draft
---
```

`status:` is `draft`. The vault's status values are `draft | partial | complete`; there is no `ai-generated` status. Only a domain specialist promotes a file to `complete`, and only after `translation-qa` reports no Critical or Major errors.

---

## Rules

1. **Strict terminology alignment.** Every key term in the source that exists in `termbase.md` MUST be translated exactly as the termbase specifies. No unauthorised synonyms or variations. Where the source uses a term the termbase does not cover, choose a rendering, use it consistently, and list it in the end report as a candidate addition to the termbase — do not silently extend the termbase yourself.
2. **Adherence to requirements.** The translation must strictly conform to the constraints in `requirements.md`: target register, tone, and the treatment of the source tradition's figurative language. `requirements.md` is the authority on all three; do not substitute your own judgement for it.
3. **Contextual anchoring via the rails.** Use the synthesis, divergences and translation in each `2-RAILS/Sections/<node-id>.md` the commentary covers — and the Disambiguated Restatement in `2-RAILS/Verses/<verse-id>.md` where one exists — to resolve semantic ambiguities in the source commentary, so the translation aligns with the commentarial consensus the rails record. Where a rail flags a divergence ⚑, do not resolve it in the translation; render the commentary's own wording and let the ambiguity stand.
4. **Preserve every block ID and every heading.** This is what makes the output usable.
   - Every heading in the source appears in the output at the **same level**, carrying the **same heading anchor** (`^N-0`, `^N-N-0`, …).
   - Every content block in the source appears in the output as one block carrying the **same block ID**. One source block in, one target block out — never merge two blocks, never split one, never renumber.
   - Transclusion lines (`![[…#^…]]`) are structural, not content. Copy them through unchanged; do not translate them and do not give them IDs.
   - A commentary translation that loses its block IDs cannot be cited, cannot be compared against its source, and cannot be QA'd. Treat a missing or altered ID as a Critical defect.
5. **Batch in runs of 30–50 blocks.** Work through the commentary in order, 30–50 blocks at a time. For each batch, inject into the prompt **only the termbase entries whose source lemma actually occurs in that batch** — a full termbase dilutes the instruction and degrades adherence. After each batch, check the output block count and IDs against the input batch before moving on.
6. **Never translate more blocks than exist.** If a batch comes back with IDs that were not in the input, or is missing IDs that were, stop and report the missing or invented IDs. Do not paper over the gap by generating the missing blocks from the surrounding context.
7. **No style drift.** Maintain a consistent register and style throughout the whole file, not just within a batch. Re-read the end of the previous batch before starting the next.
8. **Transparency.** The frontmatter records the track, the source commentary, every rail consumed in `context_packages:`, and `status: draft`. A reader must be able to tell at a glance that this is a generated translation and exactly what it was generated from.
9. **Never write to `1-SOURCES/`.** Not the translation, not a copy, not a stub.

## Procedure

1. **Information gathering**
   - Read the source commentary in full. Record its registered short ID, its heading tree, its block IDs in order, and its `covers_verses:` range.
   - Read `requirements.md` and `audience.md` from the track folder to internalise the style and register guidelines.
   - Read `termbase.md` and build a lookup map of locked renderings.
   - Determine every TOC node the commentary covers and read each `2-RAILS/Sections/<node-id>.md`. Read the `2-RAILS/Verses/` packages for the verses in range.
   - If the track folder, any contract file, or the section rails are missing, stop and say which — do not improvise a track or translate without the contract.

2. **Drafting the translation**
   - Translate in batches of 30–50 blocks, in document order.
   - For each batch, filter the termbase to the lemmas present and inject only those.
   - For every sentence, identify key terms and cross-reference them against the filtered termbase map.
   - Mirror the source's structure exactly: same headings, same levels, same anchors, same block boundaries, same block IDs on the same blocks.
   - Render the source tradition's figurative language as `requirements.md` directs — some tracks keep an image literal and gloss it, others naturalise it. Follow the contract, not habit.

3. **Validation**
   - Check every locked term is rendered as the termbase dictates, consistently, across the whole file.
   - Check the output's block-ID sequence against the source's, one by one. Same count, same IDs, same order.
   - Check the heading tree matches the source's levels and anchors.
   - Verify the register matches `requirements.md` and that no unauthorised modernisation has crept in.

4. **Writing the output file**
   - Save to `3-TRANSFORMATIONS/Translations/<track>/<commentary-id>-<lang>.md` with the frontmatter above.

5. **Quality assurance — run `translation-qa`**
   - Run the `translation-qa` skill on the output, passing the source commentary as `--source`. Its Stage 0 mechanical checks are what catch a dropped or mislabelled block ID.
   - Iterate until no Critical and no Major errors remain. The file stays `status: draft` until a domain specialist promotes it.

6. **Report**
   - Blocks translated, batches run, terms rendered from the termbase, terms not in the termbase (candidates for addition), any node whose section rail was missing, and the `translation-qa` gate result.

---

## Completion check

- [ ] Output is at `3-TRANSFORMATIONS/Translations/<track>/<commentary-id>-<lang>.md` — and nothing was written to `1-SOURCES/`
- [ ] Frontmatter carries `transformation_type: translation`, `track:`, `source_commentary:`, `covers_verses:`, `context_packages:` listing every contract file and every rail used, `generation_date:`, and `status: draft`
- [ ] Every block ID in the source appears exactly once in the output, on the corresponding block, unchanged
- [ ] Every heading appears at the same level with the same `-0` anchor
- [ ] Transclusion lines are copied through untranslated and un-ID'd
- [ ] Every key term matches the prescriptive rendering in `termbase.md`; terms outside the termbase are listed in the report, not silently added
- [ ] Register and tone conform to `requirements.md` throughout
- [ ] Section rails for **every** covered node were loaded, not just one
- [ ] `translation-qa` has been run and reports no Critical and no Major errors
