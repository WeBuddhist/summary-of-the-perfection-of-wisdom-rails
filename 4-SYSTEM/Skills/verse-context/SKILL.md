---
name: verse-context
description: >
  Build the context package for a verse: transclude the root verse and the
  relevant commentary passages, paraphrase or synthesise how each commentator reads it,
  and write a disambiguated restatement of the verse in the original language — the
  package a translator works from instead of the bare verse line.

  Trigger on "build the verse context", "make the verse package", "what do the
  commentaries say about this verse", "build the context for chapter N", "verse
  context for the whole chapter", "contextual summary for these verses",
  "regenerate the AI overview".

  One verse, a whole chapter in bulk, a group of verses under one outline node,
  or a regeneration of the AI Overview alone.
---

# Build a verse's context package

**One verse, one file, one schema.** A verse package is
`2-RAILS/Verses/<verse-id>.md`. There is no second `-summary.md` file; every
downstream skill reads `<verse-id>.md`.

**The schema is defined in `2-RAILS/About Rails.md` §5, and About Rails is the
authority.** When this skill and About Rails disagree, About Rails wins — fix
the skill. A blank copy-me skeleton in exactly that format ships with this
skill at [`templates/verse-package.md`](templates/verse-package.md), mirroring
the vault's own `2-RAILS/Verses/_TEMPLATE.md`.

| Mode | Scope | Use |
|---|---|---|
| 1 — Single verse | One verse | Default; also the one to use while the format is still being tuned |
| 2 — Chapter batch | Every verse in a chapter | After mode 1 has been validated on a few verses of that text |
| 3 — Structural position | A group of verses under one outline node | To produce the `## Structural Position` layer of those verses' packages |
| 4 — AI Overview only | One existing package | Regenerate just the `## AI Overview` section from the package's own cited paraphrases |

**Run mode 1 on two or three verses before starting a batch.** Mode 2 builds a
complete block-ID mapping across every commentary and then generates one file per
verse — an error in the package format is an error in every file, and finding it
after 90 verses is expensive.

Mode 3 exists because commentaries frequently do not comment verse by verse: they
take a group of verses under one outline node and treat it as a single topic. Forcing
that into per-verse packages invents distinctions the commentary did not make. When
the outline groups verses, follow it — record the grouping in
`coarser_groupings:` and write the shared reading once, into each affected
package's `## Structural Position` section.

Every mode's output cites block IDs — into the root text for the verse, into each
commentary for its reading.

---

## The schema, in brief

Full definition: About Rails §5. Repeated here only so a run does not have to
guess.

**Frontmatter:** `ref`, `unit_type`, `unit_verses`, `coarser_groupings`,
`template_ref`, `commentary_coverage`, `tradition_coverage`,
`concepts_in_verse`, `concepts_in_commentary`, `stories`, `layer_order`,
`note`, `status`.

`concepts_in_verse:` and `concepts_in_commentary:` are what a termbase or
keyword build reads to know which terms a verse actually turns on — fill them
even when the Key Concepts section itself is omitted.

**Section headings are the English name first, with an optional
original-language label in parentheses:** `## AI Overview (བསྡུས་དོན།)`. The
English name comes first so a script can match on it; the parenthetical is for
the human reader. Never invert that order and never drop the English name.

**Required sections, never deleted:**

| Heading | Contents |
|---|---|
| `## Source Text` | One `###` per source language the vault has, each transcluding the verse block. Plus `**Variants**` where a cross-edition reading exists. |
| `## Traditional Interpretation` | One `###` per commentary, **in the annex's tier order**, English paraphrase, every claim cited. Then `### Synthesis` and `### Divergences`. |
| `## AI Overview` | The reader-facing compression of Traditional Interpretation, in the original language. |
| `## Disambiguated Restatement` | The verse rewritten in the original language with every ambiguity resolved. |
| `## Concept Links` | Local-Wiki links for the verse's terms. |

**Optional sections, ordered by `layer_order:`, each omitted outright when no cited material exists:** `## Word Commentary`, `## Word-by-word Disambiguation`, `## Key Concepts`, `## Stories`, `## Metaphors`, `## Quotations`, `## Translation Notes`, `## Practical Application`, `## Structural Position`, `## Morphology`, `## Syntax`, `## Semantic Gloss`.

---

## Rules that apply in every mode

1. **Required sections always present:** Source Text, Traditional Interpretation (with Synthesis, and Divergences where they exist), AI Overview, Disambiguated Restatement, Concept Links. The optional layers are populated where the commentaries supply material and **omitted otherwise** — a verse with no attached story drops the Stories section; do not write an empty heading.
2. **Every source language in Source Text.** Transclude the root block from each root text the annex declares; never copy the verse in. If a block ID is missing from a root-text file, fix the root text first — pasting the verse into the rail instead is how a rail stops being a rail.
3. **Traditional Interpretation is the cited anchor.** The AI Overview is its compression — every claim in the Overview must trace to a paraphrase that is itself cited. Do not introduce a claim in the Overview that is not in Traditional Interpretation.
4. **Commentary roles and tier order come from the annex, not from this skill.** The annex says which commentary is the word-commentary / annotation source (feeding Word Commentary and Word-by-word Disambiguation), which are story commentaries (feeding Stories), which are scholarly (feeding the paraphrase and concepts), and in what order they are listed. Attribute every claim by the annex's `registered_id`.
5. **Word Commentary uses a word-commentary source.** It is not your own gloss — it re-presents an attested annotation reading as running word-commentary, cited to its blocks, woven so the verse reads continuously with the annotation inline.
6. **Word-by-word disambiguation only for non-obvious choices** — sense selection, compound parsing, referent. Skip obvious tokens.
7. **A key term is a word or a short phrase, never a whole verse line.** A "term" that is a line of the verse is not a term; it is the verse. Break it down or drop it. **Where the commentaries gloss a term differently, give both glosses and flag ⚑** — a second gloss is not a correction of the first.
8. **Stories are précis, not invention.** Only narratives a commentary actually attaches to the verse; name the story and cite the block. Record each in the frontmatter `stories:` list.
9. **Extended information belongs in the package.** Where a commentary adds material that expands the verse without glossing it — an enumeration, a reasoning structure laid out step by step, a concluding piece of advice — that is *extended information*. Put an enumeration or a reasoning structure under Key Concepts or Word Commentary, concluding advice under Practical Application. Do not discard it as "not a gloss", and do not smuggle it into the Disambiguated Restatement, which restates the verse and nothing more.
10. **Quotations are verbatim and attributed.** Reproduce the original-language quotation as the commentary gives it; name the scripture the commentary names; cite the commentary block that adduces it.
11. **Every claim cites a `1-SOURCES/` block.** No parametric knowledge. Uncited field → leave blank, `status: draft`.
12. **Divergences are never flattened.** ⚑ each position; the Disambiguated Restatement follows the best-attested reading and footnotes the alternatives.
13. **`status: draft` always.** The LLM never sets `complete`; a domain specialist does.
14. **Never write to `1-SOURCES/`** beyond the structural additions the vault permits (block IDs, frontmatter, navigation links, `[Ed: …]` notes).

### Two edge cases every builder hits

**Grouped transclusions.** Some commentaries place several consecutive verse transclusions together and comment on the whole group after the last one. **Scan forward through *all* consecutive transclusion lines to the first line of prose**; that prose belongs to every verse in the run. Reading only "up to the next transclusion" finds nothing for the earlier verses of the group and silently drops the commentary. Record the run in the frontmatter `coarser_groupings:` of every verse in it.

**A commentary with no block IDs of its own.** Some segmented commentaries carry IDs only on their transclusion anchors, so the prose you want to cite has no ID to cite to. The vault rule is to fix the source first — but a raw or segmented commentary is not always yours to stamp. In that case, **cite the material to the verse-transclusion anchor** (`[[1-SOURCES/Commentaries/<file>.md#^<verse-id>]]`) and **record the fallback in the package's frontmatter `note:` field**, so a later reader knows the citation is anchor-level rather than block-level. Never invent a block ID that does not exist in the file.

### After an LLM writes a synthesis, verify its citations

Any section compiled by a model from material above it — the AI Overview above all — is a second-pass compression. **Every citation it carries must exist in the material it was compiled from.** Check them one by one before saving. A synthesis that cites a block nobody paraphrased is a fabrication, however plausible it reads.

### Second-model tools are optional

If a second-model tool is available, use it for the synthesis pass: a different
model compressing the paraphrases is a useful check on the first model's
reading. If none is available, compose and verify the same way — the prompt in
[`references/ai-overview-prompt.md`](references/ai-overview-prompt.md) is the
same either way, and so is the citation-verification step. A missing tool is
never a reason to stop, and never a reason to skip verification.

---

## Mode 1 — Single verse

Transcludes the root verse (every source language the vault has), paraphrases each commentary's reading, then compiles the descriptive layers.

Produces the **verse-level descriptive context** that every downstream transformation (translation, adaptation, study plan) works from. The translator never sees the bare verse: it sees the disambiguated restatement plus the word commentary, the concepts, the stories, and the cited synthesis. This is the rail that defuses hallucination — every interpretive decision is made and cited here, once, before any output is generated.

### Language rule

- **Traditional Interpretation** — English paraphrase, one subsection per commentary. **Translation Notes** are English too.
- **Every other section is in the original language**: AI Overview, Word Commentary, Word-by-word Disambiguation, Key Concepts, Stories, Metaphors, Quotations, Practical Application, Structural Position, and the Disambiguated Restatement. Which language that is, is declared in the vault annex.
- Quotations are verbatim in the original language. Never translate scripture in the rail — that is a transformation's job.

This follows the vault-annex convention: the primary analysis language for `2-RAILS/` is the text's own language; only the cross-tradition paraphrase is held in English so coverage is legible at a glance.

### Inputs

- **Verse ID** — block ID of the verse, no caret (e.g. `1-1`, `6-33`), in the root text's declared `verse_id_format`.
- **Root text(s)** — every root text the vault annex declares, under `1-SOURCES/Text/`. A vault may have one source language or two; transclude the verse block from each. If a root-text file does not yet carry this block, the verse must be added to a root text under `1-SOURCES/Text/` first — do not paste the verse into the rail.
- **Commentary files** — every relevant file under `1-SOURCES/Commentaries/`, whether or not the vault also keeps a transcluded copy of them. Use each commentary in the role the annex assigns it:
  - the **word-commentary / annotation** source for Word Commentary and Word-by-word Disambiguation;
  - the **story commentaries** for Stories;
  - the **scholarly commentaries** for the paraphrase and the concepts.
  Use the `registered_id` from the annex to attribute every claim, and list them in the annex's tier order.

### Output

One file at `2-RAILS/Verses/<verse-id>.md`. Update in place if it exists; never overwrite a hand-edited section without confirming the edit is still supported by the cited blocks.

### Output file format

Copy [`templates/verse-package.md`](templates/verse-package.md) and fill it in. Its shape, in full:

```markdown
---
ref: <verse-id>
unit_type: single          # single | group | template | instance
unit_verses: [<verse-id>]
coarser_groupings: {}      # commentary-id: [verses it reads as one unit]
template_ref:              # for unit_type: instance only
commentary_coverage: []    # registered_ids, in the annex's tier order
tradition_coverage: []     # traditions represented in Traditional Interpretation
concepts_in_verse: []      # term (disambiguating-phrase)
concepts_in_commentary: [] # term (disambiguating-phrase)
stories: []                # names of narratives attached to this verse
layer_order: []            # which optional layers this package carries, in order
note:                      # e.g. citation fallback used, see About Rails §5
status: draft
---

## Source Text

### <Source language>
![[1-SOURCES/Text/<lang>-root-text.md#^<verse-id>]]

### <Second source language, if the vault has one>
![[1-SOURCES/Text/<lang2>-root-text.md#^<verse-id>]]

**Variants**
[Ed: <cross-edition or cross-language variant, with citation>]

## Traditional Interpretation

### <commentary-id> — <Commentary full name> (<language>)
<English paraphrase of this commentary's reading; every claim cited.>
(1-SOURCES/Commentaries/<file>.md#^<block>)

<!-- one ### per commentary, in the annex's tier order -->

### Synthesis
<What the sources agree on. Do not flatten disagreement here.>

### Divergences
<Only where commentaries genuinely disagree. Attribute each position, flag ⚑. Delete if none.>

## AI Overview (<original-language label>)

**<Headline reading: one or two sentences answering what the verse says.>**
(1-SOURCES/Commentaries/<file>.md#^<block>)

**Key points**
- <key point> (1-SOURCES/Commentaries/<file>.md#^<block>)
- <key point> (1-SOURCES/Commentaries/<file>.md#^<block>)

## Disambiguated Restatement

<Short rewrite of the verse in the original language with every ambiguity the
synthesis resolved made explicit: referents fixed, senses chosen, compounds
parsed. Cite the blocks that authorise each choice.>
(1-SOURCES/Commentaries/<file>.md#^<block>)

<!-- ===== OPTIONAL LAYERS, in `layer_order:` — delete any with no cited material ===== -->

## Word Commentary
<Running word-commentary in the original language: each phrase of the root verse
with its gloss woven inline, annotation style.>
(1-SOURCES/Commentaries/<file>.md#^<block>)

## Word-by-word Disambiguation
- **<root word/phrase>** — <disambiguating gloss in the original language.>
  (1-SOURCES/Commentaries/<file>.md#^<block>)

## Key Concepts

### Concepts the verse introduces
- **<term>** (<disambiguating phrase>) — <one-line note.>
  (1-SOURCES/Commentaries/<file>.md#^<block>) · [[2-RAILS/Local-Wiki/<term>_(<disambiguator>).md]]

### Further concepts the commentaries raise
- **<term>** (<disambiguating phrase>) — <one-line note.>
  (1-SOURCES/Commentaries/<file>.md#^<block>) · [[2-RAILS/Local-Wiki/<term>_(<disambiguator>).md]]

## Stories
- **<story name>** — <précis; which phrase of the verse it illustrates.>
  (1-SOURCES/Commentaries/<file>.md#^<block>)

## Metaphors
- **<image>** → <what it stands for.> <how the commentaries unpack it.>
  (1-SOURCES/Commentaries/<file>.md#^<block>)

## Quotations
> <verbatim quotation in the original language>
> — <scripture as the commentary names it>
> (1-SOURCES/Commentaries/<file>.md#^<block>)

## Translation Notes
- **<figure or idiom>** — <the difficulty>; <rendering strategy A, for audience X>;
  <rendering strategy B, for audience Y>. (1-SOURCES/Commentaries/<file>.md#^<block>)

## Practical Application
<What the commentaries say the verse asks of a practitioner.>
(1-SOURCES/Commentaries/<file>.md#^<block>)

## Structural Position
<Where the verse sits in the commentary's own outline, in prose, tracing the
full path. Produced by Mode 3.> (1-SOURCES/Commentaries/<file>.md#^<block>)

## Concept Links
- [[2-RAILS/Local-Wiki/<term>_(<disambiguator>).md]]
```

### Optional — scaffold the file first

`scripts/scaffold_verse_context.py` writes the skeleton above with the commentary blocks already located, so the fill step only has to write prose. The root text(s) and commentaries are arguments; there are no defaults.

```bash
python3 4-SYSTEM/Skills/verse-context/scripts/scaffold_verse_context.py <verse-id> \
    --vault-root <vault root> \
    --root-text "<Language label>=1-SOURCES/Text/<lang>-root-text.md" \
    [--root-text "<Second language>=1-SOURCES/Text/<lang2>-root-text.md"] \
    --commentary "<registered-id>=1-SOURCES/Commentaries/<file>.md" \
    [--commentary ... ] \
    [--language "<original language label>"] \
    [--layer concepts --layer stories ...] \
    [--dry-run | --overwrite]

# check an existing package against the required schema
python3 4-SYSTEM/Skills/verse-context/scripts/scaffold_verse_context.py <verse-id> --validate
```

It applies the grouped-transclusion rule when locating blocks, records the run in `coarser_groupings:`, and flags a commentary that has a transclusion anchor but no block IDs of its own so the `note:` fallback can be filled in.

`scripts/extract_block.py` reads just the blocks you need out of a large commentary, so a sub-agent does not have to load the whole file:

```bash
python3 4-SYSTEM/Skills/verse-context/scripts/extract_block.py <commentary file> <block-id> [<block-id> ...]
```

### Procedure

1. Read the vault annex: root text(s), registered commentary IDs, their roles, the tier order, the analysis language.
2. Read the root block in each root text. Confirm every block ID exists; if a root file lacks the block, stop and fix the root text.
3. **Locate this verse's commentary in each commentary file** — do not read the whole file. Root-text verses are transcluded into the commentary files with `![[…#^<verse-id>]]`. Search each file in `1-SOURCES/Commentaries/` for the transclusion of the target verse's block ID; all text from there to the next transclusion is commentary on that verse. **Apply the grouped-transclusion rule**: scan forward through all consecutive transclusion lines to the first line of prose. Read only that span and record the block IDs and the `registered_id`. Where a commentary has no transclusion anchors at all, locate the passage by content and cite its own block IDs.
4. Write **Traditional Interpretation** — one English subsection per commentary, in the annex's tier order, each claim cited. Add **Synthesis**, and **Divergences** if any. Where a commentary's prose carries no block IDs, apply the un-stamped-prose fallback and fill `note:`.
5. Write the **AI Overview** in the original language from the paraphrases — Mode 4's procedure and prompt, run inline.
6. Build the **Word Commentary** from the annotation source; **Word-by-word Disambiguation** for non-obvious tokens.
7. Fill **Key Concepts** (in-verse / from-commentary), **Stories**, **Metaphors**, **Quotations**, **Translation Notes**, **Practical Application** — each from a cited block; omit any section with no material. Capture extended information per rule 9.
8. Write the **Disambiguated Restatement** in the original language.
9. Fill the frontmatter — including `concepts_in_verse:`, `concepts_in_commentary:`, `stories:`, `layer_order:` in the order the sections actually appear, and `note:` if a fallback was used. Set `status: draft`. Add **Concept Links**.
10. **Verify the citations** in every synthesised section against the Traditional Interpretation above it.
11. Write to `2-RAILS/Verses/<verse-id>.md`.

### Completion check — Mode 1

- [ ] Frontmatter complete — `ref`, `unit_type`, `unit_verses`, `coarser_groupings`, `commentary_coverage`, `tradition_coverage`, `concepts_in_verse`, `concepts_in_commentary`, `stories`, `layer_order`, `note` where used; `status: draft`.
- [ ] Source Text transcludes every source language (not copied).
- [ ] Traditional Interpretation: one English subsection per commentary in the annex's tier order, every sentence cited; Synthesis present; Divergences ⚑ where they exist.
- [ ] AI Overview in the original language: headline reading + key points, every line cited, ⚑ on splits, nothing beyond the paraphrases above.
- [ ] Every citation in the AI Overview verified to exist in Traditional Interpretation.
- [ ] Word Commentary drawn from a cited word-commentary source (or section omitted).
- [ ] Word-by-word disambiguation only for non-obvious tokens, each cited.
- [ ] Key Concepts: in-verse and from-commentary, cited and Local-Wiki-linked; no "term" is a whole verse line; ⚑ where a second gloss is attested.
- [ ] Stories / Metaphors / Quotations / Translation Notes / Practical Application populated from cited blocks, omitted where absent; quotations verbatim in the original language.
- [ ] Disambiguated Restatement in the original language, each choice cited.
- [ ] Concept Links present for every key term.
- [ ] Section headings are the English name first, with any original-language label in parentheses.

---

## Mode 2 — Chapter batch

Scans every commentary once to produce a complete block-ID mapping, then generates one file per verse in the chapter.

This mode produces a complete set of verse-level context packages for an entire chapter, using a Python script to generate all files in one pass after the source-scanning phase is complete. It exists because building 30+ verse packages one at a time is slow and prone to mapping inconsistencies between files — a single mapping table that every package in the chapter is generated from removes that class of error.

The output is the same schema Mode 1 produces, generated with the prose sections left as placeholders for a per-verse fill pass. Status is always `draft` on generation; a domain specialist marks files `complete` after review.

### Inputs

- **Chapter number** — e.g. `1`.
- **Verse range** — first and last verse in the chapter (verses that already have manually authored files may be skipped).
- **Commentary files** — every file under `1-SOURCES/Commentaries/` that covers this chapter, taken from the vault annex's registered list, in its tier order.
- **Root text(s)** — per the vault annex, for the verse transclusions.
- **All commentary files must already have block IDs.** Run `format-commentary` on any commentary that lacks them before proceeding.

### Output

One file per verse at `2-RAILS/Verses/<chapter>-<verse>.md`. Files that already exist are skipped, not overwritten.

A Python generation script is saved to `0-INBOX/temp/verse-context-batch-ch<N>.py` for audit and re-use.

### Rules

1. **Read before mapping.** Never guess block ranges. Read each commentary section in full before assigning block IDs to verses. Commentary structure frequently does not align one-to-one with root-text verses.
2. **A commentary's section numbers are not verse numbers.** When a commentary numbers its own structural sections (`### 1.7`), that is *its* seventh section of chapter 1 — it may cover several root-text verses, or part of one. Map its sections to root-text verses **by reading the content**, never by matching the numbers. Conflating the two is the single most common batch error and it corrupts every file it touches.
3. **A block may straddle two verses: include it in both.** Prose commentaries do not respect verse boundaries — one block frequently finishes discussing verse N and begins verse N+1. Put that block in both verse packages rather than choosing one.
4. **Some commentaries carry exactly one block per verse — verify by grep, do not assume.** A commentary whose block IDs are derived from the root's (`^<chapter>-<verse>-1`) can be mapped mechanically, which makes it tempting to skip the check. Grep for every block in the range first and confirm each exists; a single missing block produces a package that silently cites nothing.
5. **Apply the grouped-transclusion rule** (see § Two edge cases) when building the mapping. A verse whose transclusion sits in the middle of a run maps to the prose after the run, not to nothing.
6. **Do not overwrite existing files.** If `2-RAILS/Verses/<verse-id>.md` already exists, skip it silently.
7. **Status is always `draft` on generation.** Never set `status: complete` — that is a human domain-specialist decision.
8. **Prose sections are in the original language** (except Traditional Interpretation and Translation Notes, which are English) — per the Mode 1 language rule.
9. **Every synthesis claim must cite a source block.** Format: `(1-SOURCES/Commentaries/<file>.md#^<block-id>)` inline at the end of the claim.
10. **Save the generation script to `0-INBOX/temp/`.** This preserves the mapping table for audit and re-runs.

### Procedure

#### Phase 1 — Verify prerequisites

1. Confirm every commentary file in scope has block IDs throughout. If any lacks them, run `format-commentary` on it first and do not proceed until that is complete.
2. Confirm each root text has block IDs for every verse in the target chapter.
3. Note which verse files in `2-RAILS/Verses/` already exist and will be skipped.

#### Phase 2 — Build the block mapping table

For each commentary, read the relevant chapter section(s) and record the block ID range that covers each root-text verse. Produce a mapping table of this shape:

| Verse | \<commentary-a\> blocks | \<commentary-b\> blocks | \<commentary-c\> |
|-------|-------------------------|-------------------------|------------------|
| 1-4   | ^0-176 to ^0-187        | ^1-3-1 to ^1-3-16       | ^1-4-1           |
| …     | …                       | …                       | …                |

How to read each commentary depends on how it is organised, and you determine that by reading it, not by assumption:

- **Sequential prose with verse-heading markers** — scan the chapter body in order and use the commentary's own verse-heading phrases to delimit each verse's block range.
- **Numbered structural sections** — read each section heading, then read the section body to determine which root-text verses it covers. Multiple verses may fall in one section, and multiple sections may be needed for one verse (rule 2).
- **Large undivided prose sections** — read the section in full and map each block to the verse whose content it discusses. Where a block straddles two verses, include it in both (rule 3).
- **One block per root verse, ID derived from the root's** — grep the whole range to confirm every block exists before generating (rule 4).

#### Phase 3 — Draft synthesis descriptions

For each verse, note (in one sentence per commentary) the structural context and main interpretive point. These become the starting prose in the generated files. Cite the first key block per commentary.

#### Phase 4 — Write the generation script

Write a Python script to `0-INBOX/temp/verse-context-batch-ch<N>.py` that:

1. Defines the block mapping table as a Python dict keyed by verse number.
2. For each verse in the range:
   a. Skips if the output file already exists.
   b. Generates the markdown content — the About Rails §5 schema — using the mapping and the synthesis descriptions.
   c. Writes to `2-RAILS/Verses/<chapter>-<verse>.md`.
3. Prints a summary of files created vs. skipped.

The script must be self-contained (no external dependencies beyond the Python standard library) and use absolute paths.

#### Phase 5 — Run the script

Execute the script. Verify the printed summary matches the expected count of new files.

#### Phase 6 — Spot-check output

Read three generated files — one from the beginning, middle, and end of the chapter — and verify:
- Frontmatter fields are correct and complete for the schema.
- Every commentary section is present and non-empty.
- Block IDs in transclusion links match the mapping table.
- Prose is in the right language and has at least one inline citation per commentary subsection.
- The Disambiguated Restatement carries citations.

`scripts/scaffold_verse_context.py … --validate` checks the required headings and frontmatter fields of an existing file; run it across the chapter as a cheap first pass.

#### Phase 7 — Save and report

Confirm the generation script is saved to `0-INBOX/temp/`. Report: total files generated, any files skipped (already existed), and any anomalies found in spot-check.

### Completion check — Mode 2

- [ ] Every commentary file confirmed to have block IDs before mapping begins
- [ ] Block mapping table built by reading source files, not guessed
- [ ] No commentary's own section numbers were treated as verse numbers
- [ ] Straddling blocks included in both verse packages
- [ ] Derived-ID commentaries verified by grep, not assumed
- [ ] Grouped transclusions handled — no verse in a run mapped to nothing
- [ ] Generation script saved to `0-INBOX/temp/verse-context-batch-ch<N>.py`
- [ ] Script run successfully; printed summary matches expected file count
- [ ] Three spot-checked files pass format verification
- [ ] No existing `2-RAILS/Verses/` files were overwritten
- [ ] All generated files have `status: draft`
- [ ] Prose is in the correct language, with at least one inline block citation per commentary subsection

---

## Mode 3 — Structural position for a verse group under one outline node

For root texts with a nested outline (the commentarial topical-division tradition — *sa bcad* / ས་བཅད་ in Tibetan): one contextual paragraph per verse group, tracing the commentary's own division.

**Where it goes.** The paragraph Mode 3 produces is the `## Structural Position` section of each verse package in the group — not a separate file. Add `structural-position` to each package's `layer_order:`, and record the group in `coarser_groupings:`. A working draft of a whole chapter's paragraphs may be kept under `0-INBOX/temp/` while composing, but the finished text belongs in the packages, addressed by verse ID like everything else in `2-RAILS/Verses/`.

### What this mode produces

For every group of root-text verses that appears under one leaf outline heading in an outline-plus-root-text file, produce a contextual paragraph in the original language that:

1. Quotes the verses exactly as they appear in the source file.
2. Traces the full nested outline path — from the outermost relevant container all the way down to the specific leaf section — and closes with the tradition's fixed "these are the words that …" formula.

### Step 1 — Read and parse the source file

The source file is large; read it in chunks using `offset` and `limit`. Because the file interleaves outline headings with verse blocks, pay attention to:

- **Outline headings**: lines carrying the outline anchor (`^toc-…` in a standalone outline block, `^N-N-0` for a body heading — see `4-SYSTEM/Guidelines/annotation-conventions.md` §2 and §4). Indentation or heading level encodes nesting depth.
- **Verse blocks**: lines under an outline heading that carry verse content but no outline anchor.
- **Chapter colophon**: marks the end of a chapter's verse content.

Group the verses: every consecutive set of verse lines that falls under the same leaf-level outline heading is one verse group. Note the full ancestor chain of that heading — that chain is the outline path you will trace.

### Step 2 — Build the outline path in the original language

The paragraph must state the position of the verse group in the outline. Reconstruct this path in natural prose by working **outward to inward**: start from the outermost relevant container (usually the chapter group), state how many sub-sections it contains, name them, pick the one that leads to the target, and repeat at each level until you reach the leaf section.

The sentence frame, the ordinals, the count words and the closing verbs are properties of the **tradition's own idiom**, not of this skill. The Tibetan set below is given because it is the fullest worked-out case; a vault in another language declares its equivalents in `4-SYSTEM/Guidelines/vault-annex.md` and follows the same structure.

#### Core sentence frame (Tibetan example)

```
ཞེས་པའི་[VERSE-COUNT-PHRASE]་འདི་[ནི/དག་ནི]་[PATH-CHAIN]་གཞུང་ཚིག་ཡིན་ནོ།།
```

- Use `འདི་ནི་` for a single-verse group.
- Use `འདི་དག་ནི་` for a multi-verse group.

#### Path chain construction

Each level of the chain follows one of two patterns:

**A. Branching level** — when the parent contains multiple named sub-sections and you must say "from the N sub-sections, the Kth one is…":

```
[PARENT-NAME]-ལ་ [CHILD-1] དང་ [CHILD-2] གཉིས་ལས། [ORDINAL]-པ་ [CHILD-K]-…
```

When there are three named children:
```
[PARENT-NAME]-ལ་ [CHILD-1]། [CHILD-2]། [CHILD-3]-བཅས་གསུམ་ལས། [ORDINAL]-པ་ [CHILD-K]-…
```

When there are more children, list them with `།` separators and close with `-བཅས་[N]-ལས།`.

**B. Direct level** — when a container has exactly one named part that is the target:
```
[CONTAINER-NAME]-ཡི་ [PART-NAME]-བཤད་པ་ལ་…
```

**Ordinals (Tibetan):**

| Position | Tibetan |
|----------|---------|
| 1st | དང་པོ་ |
| 2nd | གཉིས་པ་ |
| 3rd | གསུམ་པ་ |
| 4th | བཞི་པ་ |
| 5th | ལྔ་པ་ |
| 6th | དྲུག་པ་ |
| 7th | བདུན་པ་ |

**Count words for sub-sections (Tibetan):**

| Count | Tibetan |
|-------|---------|
| 2 | གཉིས་ལས། |
| 3 | གསུམ་ལས། |
| 4 | བཞི་ལས། |
| 5 | ལྔ་ལས། |
| 6 | དྲུག་ལས། |

#### Closing the path

The final clause names the leaf section and takes the verb that matches the outline label:

- `[LEAF-SECTION]-སྟོན་པའི་གཞུང་ཚིག་ཡིན་ནོ།།` — when the section "shows/demonstrates" something.
- `[LEAF-SECTION]-བཤད་པའི་གཞུང་ཚིག་ཡིན་ནོ།།` — when the section "explains" something.
- `[LEAF-SECTION]-བསྒྲུབ་པའི་གཞུང་ཚིག་ཡིན་ནོ།།` — when the section "establishes" something through scripture or reasoning.
- `[LEAF-SECTION]-བསྟན་པའི་གཞུང་ཚིག་ཡིན་ནོ།།` — when the section "teaches/presents" through an example.
- For a cross-reference section: `འདིར་མ་བཤད་པ་གཞུང་གཞན་དུ་ཞལ་འཕང་བའི་གཞུང་ཚིག་ཡིན་ནོ།།`

### Step 3 — Count the verses correctly

| Lines in group | Phrase to use (Tibetan) |
|---------------|---------------|
| 2 (half-verse) | `ཚིགས་སུ་བཅད་པ་འདི་ནི་` |
| 4 (1 full verse / shloka) | `ཤློཀ་གཅིག་པོ་འདི་ནི་` |
| 8 (2 shlokas) | `ཤློཀ་གཉིས་པོ་འདི་དག་ནི་` |
| 12 (3 shlokas) | `ཤློཀ་གསུམ་པོ་འདི་དག་ནི་` |
| 16 (4 shlokas) | `ཤློཀ་བཞི་པོ་འདི་དག་ནི་` |
| 20 (5 shlokas) | `ཤློཀ་ལྔ་པོ་འདི་དག་ནི་` |
| 28 (7 shlokas) | `ཤློཀ་བདུན་པོ་འདི་དག་ནི་` |

For edge cases (e.g. a group that runs 6 lines because it contains one 4-line verse plus a 2-line fragment), treat the 4-line block as one verse and the 2-line block as a separate group if they appear under different headings. If they appear under the same heading, count the combined line count and use the nearest verse count plus note the fragment.

### Step 4 — Write the paragraph into the packages

For each verse group:

1. Compose the paragraph per Steps 2–3.
2. Write it into the `## Structural Position` section of **every** verse package in the group, citing the commentary blocks that carry the outline headings you traced.
3. Add `structural-position` to each package's `layer_order:`.
4. Record the group in each package's `coarser_groupings:` under the commentary whose outline it follows.

While composing a whole chapter at once, keep the running draft in `0-INBOX/temp/` — one entry per group, in outline order, each headed by its leaf section name and verse IDs — then distribute it into the packages when the chapter is complete.

### Key principles

**Trace every ancestor.** Every node in the hierarchy from the outermost container to the leaf must appear in the paragraph. Do not skip levels.

**Name all siblings when branching.** Whenever you state "from N sub-sections," list every sibling by name before naming the target. That is what gives the reader a complete picture of the outline branch.

**Use the outline heading names verbatim.** Do not paraphrase outline headings; quote them exactly as they appear in the source file. The names carry precise doctrinal meaning.

**Match the closing verb to the outline label.** Choose the verb from the actual heading used in the source — a heading about an example closes with the "teaches by example" verb; a heading about reasoning closes with the "establishes" verb.

**Copy verses exactly.** Do not alter spacing, punctuation, or line-ending markers.

**Chapter scope.** If the user specifies a chapter, process only the verse groups between that chapter's first outline heading and its closing colophon.

### Examples

Worked examples of every pattern above, from a Tibetan vault, are in
[`references/examples-bo.md`](references/examples-bo.md). They are
illustrations, not a contract — the rules are here; only the specimens are
there.

### Completion check — Mode 3

- [ ] Every verse group under a leaf outline node has a paragraph.
- [ ] Each paragraph traces the full ancestor chain, names all siblings at every branch, and uses the heading names verbatim.
- [ ] The verse-count phrase matches the actual line count of the group.
- [ ] The closing verb matches the outline label.
- [ ] The paragraph is written into the `## Structural Position` section of every package in the group, with citations.
- [ ] `layer_order:` includes `structural-position`; `coarser_groupings:` records the group.
- [ ] No free-standing file was left in `2-RAILS/Verses/` under a name that is not a verse ID.

---

## Mode 4 — Regenerate the AI Overview only

Rewrites just the `## AI Overview` section of an existing package, from that package's own already-cited Traditional Interpretation. Use it after new commentaries are added to a verse, or to upgrade a thin overview to the full four-part structure. It touches no other layer.

**It never reads `1-SOURCES/` directly.** Its only source of substance is the paraphrases already written and cited in the package.

### Inputs

- **Verse ID** — block ID of the target verse, no caret.
- **Verse package** — `2-RAILS/Verses/<verse-id>.md`. Its **Traditional Interpretation** section (one cited English paraphrase per commentary, plus any Divergences) is the **only** source of substance. If that section is empty or missing, stop and run Mode 1 first — do not fabricate.

### Output

The `## AI Overview` section of `2-RAILS/Verses/<verse-id>.md`, written or replaced in place. No other section is modified. No new file is created.

### Output format

Four parts, in this order, each in the original language, each section omitted outright when no material attests it:

```markdown
## AI Overview (<original-language label>)

**<Core synthesis — two or three sentences: the verse's primary message and the
general consensus among the commentators, in one neutral synthetic voice.>**
(1-SOURCES/Commentaries/<file>.md#^<block>)

### Key themes
- **<theme name>** — <one or two sentences unpacking how the commentaries
  develop this theme.> (1-SOURCES/Commentaries/<file>.md#^<block>)
- **<theme name>** — <…> (1-SOURCES/Commentaries/<file-a>.md#^<block>, 1-SOURCES/Commentaries/<file-b>.md#^<block>)

### Divergences ⚑
- **<term or concept>** — <contrast the readings explicitly: where one commentary
  glosses X, another reads Y.> (1-SOURCES/Commentaries/<file-a>.md#^<block>; 1-SOURCES/Commentaries/<file-b>.md#^<block>)

### Practical application
- <how the commentaries suggest applying the verse to mind-training, conduct, or
  meditative practice.> (1-SOURCES/Commentaries/<file>.md#^<block>)
```

The heading keeps the schema's form: English name first, original-language label in parentheses.

### Rules

1. **Strict grounding.** Use only the paraphrases (and Divergences) already written in this package's Traditional Interpretation section. No parametric knowledge, no external history, lineage, or doctrine. If a statement cannot be traced to a cited paraphrase above, cut it.
2. **Citation on every claim.** Every factual claim, interpretation or gloss ends immediately with its source link(s). When commentators agree, cite them together. **Attribution lives in the trailing citations, never in the sentence** — "commentary X says…" is the wrong style; the cited link *is* the attribution. The prose carries one voice.
3. **Never resolve disagreements by choosing a winner.** Where commentaries split on a term, a metaphor, or a level of meaning, contrast the positions explicitly, attribute each side, and mark the section ⚑. Do not fabricate consensus.
4. **Original language, scholarly neutral tone.** Respectful, objective, classical register; do not water down or modernise technical terminology. Lead with the answer; keep bullets skimmable.
5. **Replace only the AI Overview section.** Do not edit Source Text, Traditional Interpretation, Word Commentary, or any other layer. Do not alter the frontmatter except to leave `status` as it was — the LLM never sets `complete`.
6. **Omit empty sections.** Drop Divergences when the commentaries agree; drop Practical application when no commentary attaches practice instruction. Never write an empty heading.
7. **Do not modify any file in `1-SOURCES/`.**

### Procedure

1. Read `2-RAILS/Verses/<verse-id>.md`. Locate **Traditional Interpretation** and read every per-commentary paraphrase and any Divergences, noting the citation attached to each claim. If the section is empty or absent, stop and report — run Mode 1 first.
2. Identify the **settled reading** the commentaries collectively give the verse, and draft the **core synthesis** (2–3 sentences), ending with the citations it rests on.
3. Extract two or more **key themes**; for each, write a 1–2 sentence unpacking grounded in the cited paraphrases.
4. Scan for genuine disagreement. For each, write a **divergences** bullet that contrasts the positions and attributes each side; mark the section ⚑. Omit the section entirely if there is none.
5. If any commentary attaches mind-training, conduct, or meditation guidance, summarise it under **practical application**. Omit if none.
6. Assemble the section in the order above and replace the existing `## AI Overview` in place (insert it after Traditional Interpretation if absent). Leave every other section and the frontmatter untouched.
7. **Verify the citations.** Re-read what you wrote and confirm every line carries a citation that exists in Traditional Interpretation, and that no uncited claim slipped in.

The prompt this mode runs — reusable verbatim, including outside a vault — is in [`references/ai-overview-prompt.md`](references/ai-overview-prompt.md). If a second-model tool is available, use it for the synthesis pass; otherwise compose and verify the same way.

### Completion check — Mode 4

- [ ] Read the package's Traditional Interpretation; did not read `1-SOURCES/` directly.
- [ ] AI Overview written in the original language with core synthesis + key themes (+ divergences / practical application where attested).
- [ ] Every claim ends with a citation that exists in Traditional Interpretation; no uncited claim added.
- [ ] Disagreements contrasted and ⚑-marked, never flattened into false consensus.
- [ ] Attribution is by trailing citation, not by naming a commentary in the sentence.
- [ ] Empty sections omitted, not left as bare headings.
- [ ] Only the AI Overview section changed; all other layers and the frontmatter untouched; `status` not set to `complete`.

---

## After this skill

Verse packages are what `verse-translate` and the translation tracks read instead of
the bare root line, and what `multilevel-summary` calibrates for an audience.
`graded-translate` Phase 3 reads their `concepts_in_verse:` lists to know which
lemmas are load-bearing in a verse.
