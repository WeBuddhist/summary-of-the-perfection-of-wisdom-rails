# CLAUDE.md — 🛤️ Railroads

Persistent operational instructions for an LLM agent working in this vault. Read before touching any file.

---

## ⚑ Before doing anything — check for a skill first

**This is the single most important rule in this file.**

1. Open `4-SYSTEM/Skills/SKILLS-CATALOG.md` and scan for a skill that matches the task.
2. If a match exists, open its `SKILL.md` in full and follow the execution steps exactly — do not improvise.
3. Only if no skill exists should you proceed using the general rules below.

Skipping this step is the most common agent error in this vault. The skills exist precisely to ensure consistency and correct citation format. A task done without its skill must be redone.

---

## 🔒 Protected files — confirm with a human before touching

Some files are a **source of record**: downstream tools, published outputs or other teams read them directly, so an unreviewed edit propagates silently.

**Before you edit, move, rename, or delete any protected file, STOP and get explicit human confirmation.** State the file and the exact change you intend to make, and wait for a clear approval before proceeding. This rule applies to every AI agent working in this vault, and it overrides any other instruction to "just fix" or "clean up" these files.

A protected file carries a `PROTECTED — SOURCE OF TRUTH` banner at the top and `protected: true` in its frontmatter. If you open a file and see that banner, treat it as locked even if it is not listed anywhere.

**Regenerating** a protected file — re-running the generator that produced it — is itself a protected action. Confirm first.

This guard is **advisory**: it flags unauthorized changes loudly but cannot by itself prevent them. Prevention depends on agents honouring the policy. A vault that generates protected files should list their globs in `4-SYSTEM/scripts/<generator>/guard.paths` and check them with that generator's guard command.

---

This file is the **operational quick-reference**. The canonical rules for each folder live in that folder's README:

- [`../1-SOURCES/About Sources.md`](../1-SOURCES/About%20Sources.md) — sources rules in full
- [`../2-RAILS/About Rails.md`](../2-RAILS/About%20Rails.md) — rails schema in full
- [`../3-TRANSFORMATIONS/About Transformations.md`](../3-TRANSFORMATIONS/About%20Transformations.md) — transformations rules in full

When this file and a folder README disagree, the folder README wins.

---

## 1. What this vault is

**Railroads** is a method for making AI-powered work on classical texts reliable. Instead of feeding a model raw commentary and hoping it synthesises correctly, we lay the **rails** first: structured, machine-readable context packages that resolve every ambiguity in a passage and cite the human source for each decision. Once the rails are laid, any model can run any transformation — translation, adaptation, lesson plan, daily reading, study guide, anything — without redoing the philological work.

Authority comes from the human commentary tradition, never from the LLM's parametric knowledge.

**One vault per text.** This vault is for **[name of text]**. For vault-specific conventions (addressing scheme, registered commentary IDs, language tracks), see [`Guidelines/vault-annex.md`](Guidelines/vault-annex.md).

---

## 2. Folder structure and citation chain

```
0-INBOX/        # drafts and scratch — not authoritative
1-SOURCES/      # human-produced material — read-only ground truth
  Text/         # root texts
  Commentaries/ # commentaries on the text
  Translations/ # existing translations (block-aligned with the root)
  References/   # dictionaries, secondary literature
  Audio/        # recitation and teaching recordings
2-RAILS/        # compiled interpretive context (primary work area)
  Sections/     # multi-commentary summaries per TOC node
                # (Raw/toc-tree/ holds the finished, QC-clean structural tree per commentary)
  Verses/       # verse-level context packages
  Local-Wiki/   # monolingual articles per key term
  Bilingual-Glossaries/ # bilingual descriptive glossaries per language pair
  Claims/       # optional: consolidated topic pages (raw/ holds per-commentary inventories)
  Keywords/     # optional: descriptive keyword inventories and the source-term registry
  Termbases/    # optional: descriptive cross-track term tables and build caches
3-TRANSFORMATIONS/      # AI-generated outputs, organised in three categories
  Translations/ # language-by-language translation tracks
  Adaptations/  # audience-targeted retellings (children's, scholarly, …)
  Plans/        # calendar-driven study/practice arcs
4-SYSTEM/       # guidelines, skills, templates — read-only except Skills/ and scripts/
  Guidelines/   # canonical cross-cutting rules and the vault annex
  Skills/       # one folder per skill, each with a SKILL.md
  Templates/    # file templates
  How-to guides/# human-facing instructions
  scripts/      # standalone scripts not bundled inside a skill
  Pipelines/    # optional: multi-stage programs with their own code and CLI
                # (installed and run, not invoked as skills)
```

The `2-RAILS/` subfolders marked *optional* exist only in vaults that run the corresponding pipeline. A skill whose input folder does not exist in this vault says so and stops — it never invents a location.

### Citation chain — never skip a link

```
1-SOURCES/ → 2-RAILS/ → 3-TRANSFORMATIONS/
```

- `2-RAILS/` cites `1-SOURCES/` only — never another rail file, never parametric knowledge, never `3-TRANSFORMATIONS/`.
- `3-TRANSFORMATIONS/` cites `2-RAILS/` only — never reaching past the rails directly into the sources. (Plan tracks may also embed other completed `3-TRANSFORMATIONS/` outputs — recorded the same way in `context_packages:`.)

If a claim cannot be cited, do not make it. Leave the field blank and mark `status: draft`.

### Write permissions

| Folder | LLM may write? |
| ------------------- | ------------------------------------------------------ |
| `0-INBOX/` | yes — scratch only, never cited from elsewhere |
| `1-SOURCES/` | **no** — only metadata additions via skill workflows |
| `2-RAILS/` | yes — primary work area |
| `3-TRANSFORMATIONS/`| yes — only when explicitly instructed |
| `4-SYSTEM/` | **mostly no** — see the skills-and-scripts exception below |

**`4-SYSTEM/` exception — skills and scripts.** The default "no write" rule for `4-SYSTEM/` protects the *operational rules*: this `CLAUDE.md`, the folder `About *.md` files, the `Guidelines/`, and the templates. The LLM **may** create and edit **skills** (`4-SYSTEM/Skills/<skill>/`, including `SKILL.md` and bundled scripts) and **standalone scripts** (`4-SYSTEM/scripts/`) when explicitly asked to build or improve tooling — that is what the `create-skill` skill is for. When it adds or changes a skill it also updates `4-SYSTEM/Skills/SKILLS-CATALOG.md` and `.claude/commands/<skill>.md` to match. Everything else in `4-SYSTEM/` — the rules themselves — still requires a human contributor.

**`1-SOURCES/` exception — whole-file creation by an intake skill.** An intake skill may *create* a new file in `1-SOURCES/` from material a human has already reviewed in `0-INBOX/`. It never edits an existing `1-SOURCES/` file in place beyond the permitted additions below.

The `1-SOURCES/` restriction is the most important. The folder receives human material once, has its block IDs and frontmatter added under controlled skills, and is then frozen. Adding interpretation here — even a paraphrase or a glossing parenthetical — corrupts the ground truth and breaks the citation chain.

---

## 3. Descriptive `2-RAILS/`, prescriptive `3-TRANSFORMATIONS/`

- **`2-RAILS/` is descriptive.** It distills and reformats what is already attested in `1-SOURCES/` — root text, commentaries, existing translations — without adding choices. Every claim cites a specific human source. The authority of a rail comes from the tradition it compiles, not from the LLM that compiled it.
- **`3-TRANSFORMATIONS/` is prescriptive.** It contains the choices that guide AI-powered output for *each particular track* — audience, register, the rendering chosen for every keyword, the per-session shape. Where `2-RAILS/` records what translators *have done*, `3-TRANSFORMATIONS/` records what *this* output *will do*.

---

## 4. File naming

- Lowercase, hyphenated, no diacritics in filenames. Diacritics fine inside file content and frontmatter.
- Language tag suffix on every file carrying language-specific material: `-pi` Pāli, `-sk` Sanskrit, `-bo` Tibetan, `-zh` Chinese, `-en` English. Add a script suffix when needed: `-sk-iast`, `-bo-wy`. Full tag list in [`../1-SOURCES/About Sources.md`](../1-SOURCES/About%20Sources.md) §12.
- Verse package files in `2-RAILS/Verses/` are named by block ID without the caret: `1-1.md`, `6-33.md`. Section files in `2-RAILS/Sections/` are named by node ID: `1.md`, `1-1.md`.
- Local-wiki files use `term_(disambiguating-phrase).md`.

---

## 5. Block IDs — the verse-level link

Every verse or discrete prose block in `1-SOURCES/` ends with an Obsidian block ID. This is the sole mechanism for cross-file references at the verse level across the vault.

```
[verse text here] ^1-1
```

- Format: `^chapter-verse` (most common), `^verse`, or `^book-chapter-verse` — declared per file in the `verse_id_format` frontmatter field.
- Numbers are not zero-padded. Use natural numbers (`^1-583`, not `^01-0583`).
- The vault annex ([`Guidelines/vault-annex.md`](Guidelines/vault-annex.md)) specifies the addressing scheme for the root text(s) of this vault, including any **registered deviation** from the defaults.

**The canonical, complete statement of every block-ID convention is [`Guidelines/annotation-conventions.md`](Guidelines/annotation-conventions.md)** — content IDs, the `-0` heading slot, the Sanskrit four-zone scheme, commentary IDs (whose `##` labels are assigned by a human and never generated by a skill), the separate `^toc-` namespace, the deprecated `^TOC-N` form, and the deviations a vault may register. §5a and §5b below summarise it; where they disagree, that document wins.

Link form: `[[1-SOURCES/Text/[lang]-root-text.md#^1-1]]`
Transclude: `![[1-SOURCES/Text/[lang]-root-text.md#^1-1]]`

Use full paths in all `1-SOURCES/` and `2-RAILS/` files. Short wiki links are acceptable only inside `4-SYSTEM/` documentation.

---

## 5a. Heading hierarchy for source text files

Headings are **editorial structure added to the original text** — they are not themselves original content. To mark this distinction and prevent any collision with verse/block IDs, every heading block ID ends with **`-0`** (the zero slot is reserved for the heading; original content always starts at `1`).

| Level | Markdown | Purpose | Block ID format | Example |
|---|---|---|---|---|
| 1 | `#` | Title of the work | none | `# [Title of the work]` |
| 2 | `##` | Chapter | `^N-0` | `## 1. [Chapter title] ^1-0` |
| 3 | `###` | Section (from author's own TOC) | `^N-N-0` | `### 1.2 [Section title] ^1-2-0` |
| 4 | `####` | Sub-section | `^N-N-N-0` | `#### 1.2.3 [Sub-section title] ^1-2-3-0` |

Content blocks beneath a heading use the same numeric path but replace the trailing `0` with the sequential block number starting at `1`:

```
## 0. Introduction ^0-0

[pre-chapter / homage / colophon block] ^0-1

## 1. [Chapter 1 title] ^1-0

[first verse or prose block of chapter 1] ^1-1

### 1.2 [Section title] ^1-2-0

First prose block here. ^1-2-1
Second prose block here. ^1-2-2
```

Rules:
- The `#` title line takes **no** block ID.
- `##` headings use `^N-0`. Chapter `0` is always the pre-chapter introduction (`## 0. Introduction ^0-0`).
- `###` headings use `^N-N-0`, where the first segment is the parent chapter and the second is the section's ordinal within that chapter.
- `####` headings use `^N-N-N-0`.
- The `0` in the final position is **reserved** for the heading; original-text blocks always start at `1`.
- **Heading IDs use the full path of the structural tree plus the `-0` slot — there is no segment cap.** A division numbered `1.2.2.1.1.4` gets `^1-2-2-1-1-4-0`. Never flatten or truncate a deep tree to fit a shorter ID.
- Markdown heading level follows tree depth (`##` = top-level division, one `#` per level deeper). Markdown stops at `######`; nodes deeper than that keep `######` and wrap the title in `**bold**`, with the full-path block ID carrying the real depth.
- No zero-padding on any segment.

---

## 5b. Inline TOC phrases — wikilink tagging

Buddhist texts frequently contain **inline structural announcements**: sentences where the author enumerates the upcoming sections before elaborating each one. These phrases are original content (not editorial additions), but they are also the textual source of the TOC headings. Tagging them makes the connection explicit and enables backlink navigation across the vault.

**Convention:** wrap each announced term in a wikilink pointing to the block ID of the heading it sources.

```markdown
## [Chapter title] ^1-0
This chapter has two parts: [[#^1-1-0|the brief teaching]] and [[#^1-2-0|the extended explanation]].

### [Brief teaching] ^1-1-0
[[#^1-1-0|The brief teaching]] is as follows: …

### [Extended explanation] ^1-2-0
[[#^1-2-0|The extended explanation]] runs as follows: …
```

Rules:
- In the **enumeration sentence**, each announced term links forward to its corresponding section heading: `[[#^N-N-0|term]]`.
- In the **body of each section**, the repetition of the section title links to its own heading: `[[#^N-N-0|term]]`. This is self-referential by design — it tags the phrase as the textual source of that heading.
- For cross-file links (e.g. a commentary tagging terms from the root text structure): `[[filename#^N-N-0|term]]`.
- Use the minimal display text — just the structural term itself, not the full grammatical phrase.
- These wikilinks are the only inline tagging mechanism. Do not use italics, HTML spans, or Dataview fields for this purpose.

**Why self-referential links are correct:** clicking a self-link inside its own section scrolls you to the heading of that section — a minor navigation no-op. The value is in the backlinks panel: every file that tags a phrase with `#^1-1-0` becomes visible on that heading, revealing where the structure was announced across all commentaries and translations in the vault.

---

## 6. `1-SOURCES/` — what you may and may not do

Files here are received material — formatted for navigation, never interpreted. Permitted additions only:

- Block IDs
- Frontmatter metadata
- Internal navigation links
- Editorial notes marked `[Ed:...]` (English, factual only)

Any interpretive claim — compound analysis, sense choice, syntactic reading — belongs in `2-RAILS/`, not here.

### Minimum frontmatter

```yaml
---
title:
author:
language:
file_type: root-text | commentary | translation | reference
lang_tag:
source_description: "where this text came from"
---
```

Add external IDs when available: `bdrc_work_id`, `cbeta_id`, `gretil_url`, `dsbc_url`, `suttacentral_id`, `acip_id`.

For commentaries and translations, also include `root_text:` (path) and `covers_verses:` (range, e.g. `1-1–1-1616`).

Full rules in [`../1-SOURCES/About Sources.md`](../1-SOURCES/About%20Sources.md).

---

## 7. `2-RAILS/` — what each subfolder produces

### `Sections/` — per-TOC-node summaries

Each node of the table of contents gets a summary in the original language drawn directly from each relevant commentary. Each commentary's summary is its own file under `Sections/Raw/<commentary>/`. The combined file `Sections/<node-id>.md` synthesises the per-commentary summaries and adds an English translation underneath.

Authoring skill: `section-summary` (per-commentary phase, then combined phase).

### `Verses/` — per-verse context packages

One file per verse: `2-RAILS/Verses/<verse-id>.md`. Each package (1) transcludes the relevant commentary passages, (2) synthesises the commentators' interpretations in the original language, and (3) produces a **disambiguated restatement of the verse in the original language** — precise enough that no misreading or mistranslation is possible. Transformation skills work from this disambiguated version, not from the raw verse.

Only `status: complete` packages are used to generate transformations. Domain specialists set `complete` — the LLM never marks its own output complete.

Authoring skill: `verse-context`.

### `Local-Wiki/` — per-term articles

One page per attested sense ID within this text. Sense IDs are Wikipedia-style: `term (disambiguating phrase)`. Each article holds verbatim commentary quotations defining the term, a short contextual definition synthesised from them, and divergence flags where commentaries disagree. All content in the original language.

Authoring skill: `local-wiki-article`.

### `Bilingual-Glossaries/` — bilingual descriptive glossaries

One consolidated file per language pair: `[src]-[tgt].md`. Each entry maps a source lemma to every attested target-language rendering, frequency-ranked across all existing translations.

Raw inputs sit under `Bilingual-Glossaries/Raw/`: one interlinear gloss file per translation, and one per-translation raw bilingual glossary extracted from it. The consolidated file merges them.

Authoring skill: `bilingual-glossary` (extract → combine → contest → select).

### `Sections/Raw/toc-tree/` — finished structural trees *(optional)*

One finished, QC-clean decimal-numbered structural tree per commentary: `Sections/Raw/toc-tree/<registered-id>.md`. It lives under `Sections/Raw/` because it is raw distilled structure — per-commentary, descriptive, every title attestation-checked against the source. Working intermediates stay in `0-INBOX/temp/TOC-<id>/` until both deterministic QC checkers pass; the candidate and enumeration scans are **extraction evidence, not attested structure**, and are never cited from another rail.

A tree is tied to one exact version of its source file. If the commentary is re-segmented or edited after a tree was built, the tree is stale and must be rebuilt, not reused.

Authoring skill: `toc-generate`.

### `Claims/` — per-commentary inventories and consolidated topic pages *(optional)*

Two layers, mirroring `Sections/`:

- **`Claims/raw/<registered-id>.md`** — every distinct claim one commentary makes, in its own language, each cited to a block ID, extracted from **one commentary read in isolation** before any comparison.
- **`Claims/raw/spine-map/<registered-id>.md`** — the routing index: which of that commentary's own nodes hold which canonical spine slot's content. An index, not an extraction. Its invariant is that **every claim gets exactly one disposition** — routed by node, routed by claim ID, flagged ambiguous, or logged under an unmapped node.
- **`Claims/<topic>.md`** — consolidated topic pages: consensus, ⚑ divergences, unique claims, every line citing raw claim IDs. The questions used are recorded in the page's own `consolidation_questions:` frontmatter.

**Order of operations:** extract every commentary → map every commentary (`spine-map`, once each) → consolidate per topic. Consolidating before the maps exist fails loudly.

Authoring skills: `commentary-claims`, `spine-map`, `claims-consolidate`.

### `Keywords/` — keyword inventories and the source-term registry *(optional)*

The descriptive output of the keyword pipeline: candidate keywords, per-occurrence mappings, the **source-term registry** (one canonical source lemma per concept with every attested variant, synonym and epithet grouped under it — the vocabulary-standardisation artefact), the quote-excluded frequency matrix, and the ranked article queue.

Authoring skill: `keyword-extract`.

### `Termbases/` — descriptive cross-track term tables *(optional)*

Cross-track term tables and build caches: a term-localisation table mapping each key term to its renderings in several target languages, and any graded keyword caches a translation skill builds. These are **descriptive** — they record candidates. The **prescriptive** contract remains the per-track `termbase.md` in `3-TRANSFORMATIONS/`.

Authoring skills: `term-definition`, `term-localization`.

---

## 8. Divergences — never flatten

When commentaries disagree, record the disagreement explicitly:

- Mark with ⚑ in any field where the divergence shows up.
- Add a `### Divergences` section attributing each position to its source.

If traditions teach genuinely incompatible doctrine on a verse, do not synthesise. Record both positions and add to frontmatter:

```yaml
transformation_note: "tradition must be specified for this verse"
```

---

## 9. `3-TRANSFORMATIONS/` — three categories, per-track governance

Three top-level categories, each a top-level subfolder:

- **`Translations/`** — language-by-language translations. Each track has `requirements.md` + `termbase.md` + `audience.md` + the generated translation file(s).
- **`Adaptations/`** — audience-targeted retellings. Each track has `requirements.md`, `audience.md`, and optionally `termbase.md`.
- **`Plans/`** — calendar-driven study/practice arcs. Each plan is language-stratified: one subfolder per published language, each containing `requirements.md`, `termbase.md`, `schedule.md`, `days/`, `communications/`, and `assets/`. The plan root holds only `About <plan-name>.md`.

**Translation / Adaptation contracts:**

- **`requirements.md`** — style contract, written in the target language.
- **`termbase.md`** — vocabulary contract (one rendering per keyword).
- **`audience.md`** — audience profile (demographics, prior knowledge, use cases, motivations).

**Plan contracts.** A plan's shape lives in the plan's own files, never in a skill. Every parameter the pipeline needs is declared once and read from there.

- **`About <plan-name>.md`** — the contract: purpose, audience, the **authoring stream** (the language whose days are written from the rails) and the **translation streams** (written from the authoring stream's days), the session shape as a table of sections with their type, voice, ceiling and grounding source, the practice-category list, the verse source per stream, the naming pattern, and the status rules.
- **`<lang>/requirements.md`** — the stream's style contract, written in that language.
- **`<lang>/termbase.md`** — the stream's vocabulary contract; a translation stream may also carry `termbase-translation.md`, a fork with a pending-terms table.
- **`<lang>/schedule.md`** — the day-by-day calendar for that stream.
- **`<lang>/assets/liturgy.md`** — the verbatim text of every fixed section.

Day files **inline** their verse text by block ID from the stream's designated source — never retyped from memory, and transcluded only when the plan declares Obsidian as the consumer. A day file is never overwritten silently: the previous version is archived first.

Do not generate from rails whose `status` is not `complete`.

**Beyond the three categories.** Three things may sit alongside them when this vault's `About Transformations.md` documents them:

- A **cross-track shared folder** for outputs consumed by several tracks rather than belonging to one (e.g. a per-day package folder feeding more than one plan). Each needs an entry in `About Transformations.md` saying why it is not inside a track.
- A **machine-baseline folder** (e.g. `Translations/<engine>/`) holding raw machine-translation output. These are not governed tracks: they have no `requirements.md`, are never marked `complete`, and are never cited by another transformation.
- A **pipeline-owned category** governed by its own `CLAUDE.md` under `4-SYSTEM/Pipelines/`. It is exempt from the per-track contract only because it carries an equivalent guarantee of its own (e.g. a deterministic verification gate), and the exemption is recorded in the vault annex.

A transformation may quote the source text itself — that is what it is transforming. What it may not do is reach past the rails into `1-SOURCES/` for an *interpretive* decision.

Full rules in [`../3-TRANSFORMATIONS/About Transformations.md`](../3-TRANSFORMATIONS/About%20Transformations.md).

---

## 10. Style and language rules

- Analysis language in `2-RAILS/` is English for the per-commentary paraphrases and the translation notes; every other section — the overview, the disambiguated restatement, the local-wiki articles, the key-term notes — stays in the original language. The vault annex records any departure, per rail section.
- Quote original-language terms in the appropriate romanisation or script — italicised on first use.
- **No parametric knowledge.** If you cannot cite a claim to a file in `1-SOURCES/`, do not include it.
- **Prefer the vault's own terminology.** Take definitions and renderings from `2-RAILS/Local-Wiki/` and `2-RAILS/Bilingual-Glossaries/` before general knowledge or a web search.
- **No consensus flattening.** When commentaries disagree, say so.
- Present tense for analytical claims; past tense for historical statements.
- Use registered short IDs for commentaries throughout (e.g. the IDs in [`Guidelines/vault-annex.md`](Guidelines/vault-annex.md) §Commentaries).

---

## 11. Standard operations

**Ingest a passage**
1. Confirm the source is in `1-SOURCES/`.
2. Open or create the verse package in `2-RAILS/Verses/`.
3. Populate the synthesis, disambiguated restatement, and word/translation notes — each field cited.
4. Update or create local-wiki pages for any new sense IDs.
5. Flag divergences with ⚑.

**Lint a rails file**
- Any field in `2-RAILS/` without a `1-SOURCES/` citation → mark `status: draft`.
- Any ⚑ flag without a Divergences entry → add one.
- Any sense ID used in `2-RAILS/` with no Local-Wiki page → create one.
- Any `[text-slug]` / `[name of text]` placeholder still in `README.md`, `CLAUDE.md` or the annex → fill it in.
- Any `status: complete` package that fails the checklist in `2-RAILS/About Rails.md` → revert to `partial`.

**Generate a transformation**
1. Confirm all relevant rails are `status: complete`.
2. Load `requirements.md`, `termbase.md`, and `audience.md` for the track.
3. For each batch: load section + verse rails → generate → record `context_packages:` in frontmatter → set `status: draft`.
4. Run `translation-qa` (or equivalent QA skill); iterate until no critical/major errors.
5. Domain specialist sets `status: complete`.

---

## 12. Skills — always check before starting work

**Before beginning any vault task, check whether a skill already exists for it.**

Skills are reusable, step-by-step procedures stored in `4-SYSTEM/Skills/`. Each skill has its own subfolder containing a `SKILL.md` that specifies exactly how to execute that operation. Following the skill ensures consistency and correct citation format across all vault files.

### Where to look

1. **Catalog first:** `4-SYSTEM/Skills/SKILLS-CATALOG.md` — lists every skill, its purpose, inputs, outputs, and a link to its `SKILL.md`.
2. **Skill folder:** `4-SYSTEM/Skills/<skill-name>/SKILL.md` — the full execution instructions for a specific skill.

### How to use a skill

1. Read `4-SYSTEM/Skills/SKILLS-CATALOG.md` to find the skill that matches the task.
2. Open and read the relevant `SKILL.md` in full before touching any vault file.
3. Follow the execution steps in the `SKILL.md` exactly — do not improvise the format.
4. If no skill exists for the task, proceed using the general rules in this file, and flag to the human contributor that a new skill may be worth writing.

### Key skills and when to use them

| Task | Skill |
|------|-------|
| **Intake** | |
| Ingest EPUB as markdown | `epub-to-markdown` |
| Ingest JSON (root text / commentary) | `json-to-source-text` · `json-to-commentary` |
| Bring one raw file into `1-SOURCES/` | `raw-to-sources` |
| Repair mechanical OCR / page damage | `clean-raw-text` |
| Score OCR quality before trusting a file | `tibetan-ocr-quality` |
| **Formatting and structure** | |
| Format a root text | `format-root-text` · `format-tibetan-root-text` · `format-sanskrit-root-text` |
| Format a commentary (OCR repair happens here, nowhere else) | `format-commentary` |
| Break a commentary into citable blocks | `segment-commentary` |
| Add or re-add block IDs | `add-block-ids` |
| Insert root-verse transclusions into a commentary | `transclusion` |
| Build a structural outline / table of contents | `toc-generate` (sa bcad) · `structural-outline-ingest` · `add-toc` |
| Tag inline structural announcements | `tag-inline-toc` |
| **Metadata** | |
| Fill a file's frontmatter | `frontmatter` |
| Extract metadata from title and colophon | `extract-source-metadata` · `property-creator` |
| **Rails** | |
| Summarise a TOC node across commentaries | `section-summary` |
| Build a verse context package | `verse-context` |
| Create a local-wiki article | `local-wiki-article` |
| Build the bilingual glossary chain | `bilingual-glossary` |
| Build an interlinear gloss | `interlinear-gloss` |
| Extract keywords and build the source-term registry | `keyword-extract` |
| Extract term definitions from commentaries | `term-definition` · `term-localization` |
| Extract a commentary's claims | `commentary-claims` |
| Map a commentary onto the spine | `spine-map` |
| Consolidate claims into topic pages | `claims-consolidate` |
| **Transformations** | |
| Machine-baseline translation | `machine-translate` |
| Zero-shot translation draft | `zeroshot-translate` |
| Audience-graded, termbase-locked translation | `graded-translate` |
| Verse-form (metrical) translation | `verse-translate` |
| Translate a commentary | `translate-commentary` |
| Audience-targeted summary | `multilevel-summary` |
| Build a study/practice plan | `plan-scaffold` · `plan-schedule` · `plan-day-generate` · `plan-day-translate` |
| **Checking** | |
| QA a translation against MQM | `translation-qa` |
| Check a translation against the commentary tradition | `commentary-fact-check` |
| Check a translation's block alignment | `translation-alignment-check` |
| QA a plan day file | `plan-day-qa` |
| **System** | |
| Create a new skill (with full registration) | `create-skill` |
| Audit vault integrity (weekly maintenance) | `vault-audit` |

Not every vault installs every skill. `4-SYSTEM/Skills/SKILLS-CATALOG.md` is the authoritative list of what is installed here.

---

## 13. Pipelines are not skills

`4-SYSTEM/Pipelines/` — when a vault has it — holds multi-stage programs with their own code, prompts, gates and CLI. They are **installed and run, not invoked as skills**. Each carries its own `CLAUDE.md` (its rules) and a `STATE.md` handover note; read the `STATE.md` first when picking up pipeline work. A pipeline may register its own slash commands.

Pipeline *documentation* — the diagram-and-detail description of how skills chain into a flow — belongs in `4-SYSTEM/How-to guides/`, not in `Pipelines/`.

---

## 14. Where the skills come from

The skills in `4-SYSTEM/Skills/` are installed copies from the shared skill library, which is the canonical source: fix a skill **there**, then re-sync, rather than patching a vault copy and letting the two drift. A skill that is genuinely specific to this text stays here and is marked `profile: vault-local` in its frontmatter so a sync never overwrites or exports it.

See [`Guidelines/skills-system.md`](Guidelines/skills-system.md) for the registration rules and [`How-to guides/Sync with rails-template.md`](How-to%20guides/Sync%20with%20rails-template.md) for the sync procedure.
