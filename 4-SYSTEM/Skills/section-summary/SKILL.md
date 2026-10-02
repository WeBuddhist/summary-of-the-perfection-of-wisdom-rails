---
name: section-summary
description: >
  Summarise one node of a text's structural outline: first once per commentary
  in that commentary's own language and terminology, then as a single combined section
  reconciling all the commentaries on that node, with an English translation.

  Trigger on "summarise this section", "write the section summary", "summarise this TOC
  node across the commentaries", "combine the section summaries", or any request for
  what a given section of the text says according to its commentaries.

  Every claim cites a block ID. Phase 1 never translates; Phase 2 is where English
  first appears.
---

# Section summaries — per commentary, then combined

Two phases, run in order, once per TOC node:

| Phase | Scope | Output |
|---|---|---|
| 1 — Raw | One node, **one** commentary | `2-RAILS/Sections/Raw/<commentary>/<node-id>.md` |
| 2 — Combined | One node, **all** commentaries | `2-RAILS/Sections/<node-id>.md` |

Phase 1 runs once per commentary covering the node — three commentaries on node
`1.2.3` means three Phase 1 runs, then one Phase 2 run over all three.

**The language rule is the point of the split.** Phase 1 stays in the commentary's own
language and uses the commentary's own terminology, untranslated — that keeps the
terminological evidence intact for `bilingual-glossary` and `term-definition`. Phase 2
preserves that original-language terminology *and* adds an English translation
alongside it. Translating in Phase 1 destroys the evidence and cannot be recovered
from the summary.

Node IDs come from `toc-generate`. Run that first — there is nothing to summarise
per-node until the tree exists.

---

## Phase 1 — Raw — one commentary's reading of one node

Original language only. Every claim cites a block ID in that commentary.

This skill produces the **per-commentary, original-language summary** of one node in the text's table of contents. One commentary per file. No translation, no paraphrase outside the commentary's own vocabulary, and every claim grounded in a block-ID citation.

The output of this skill is the raw input that `section-summary-combined` later merges across commentaries.

---

### Inputs

- **Commentary file** — one file from `1-SOURCES/Commentaries/<commentary-name>.md`. Must be properly formatted with heading IDs and block IDs (see `4-SYSTEM/Guidelines/source-formatting.md`).
- **TOC node** — the node-ID and heading text of the section to summarise (e.g. `^1-1-0` "Ganthārambhakathā"). The node corresponds to a heading in the commentary file.

If multiple commentaries cover the same node, run this skill once per commentary.

### Output

One file at:

```
2-RAILS/Sections/Raw/<commentary-name>/<node-id>.md
```

`<commentary-name>` matches the commentary filename without the language prefix or `.md` extension (`pi-dhammasangani-atthakatha.md` → `dhammasangani-atthakatha`). `<node-id>` matches the heading's block ID with the caret stripped (`^1-1-0` → `1-1-0`).

Create the parent directory if it does not exist.

---

### Output file format

```markdown
---
node_id: <e.g. 1-1-0>
node_heading: <the original-language heading text>
commentary: <commentary-name>
commentary_file: 1-SOURCES/Commentaries/<commentary-name>.md
language: <pi | sa | bo | zh | ...>
status: draft
---

### <node-heading verbatim>

<one or more short paragraphs in the original language, summarising what this
node of the commentary covers. Use only the commentary's own terminology.
Every factual claim — what is defined, what example is given, what the
commentator concludes — must end with a citation to the supporting block(s).>

(1-SOURCES/Commentaries/<commentary-name>.md#^<block-id>)
```

A second paragraph follows the same shape. Keep the summary compact — the goal is orientation for a translator, not a re-presentation of the commentary.

---

### Rules

1. **Original language only.** If the commentary is in Pali, the summary is in Pali. If Sanskrit, Sanskrit. No translation, no English glosses inside the paragraph. The frontmatter `language` field reflects this.
2. **Use the commentary's terminology verbatim.** Do not normalise spellings, do not substitute synonyms, do not switch to a more familiar word. If the commentary writes *kusalā dhammā*, the summary writes *kusalā dhammā* — never "wholesome states".
3. **Compress; do not paraphrase.** A summary is shorter than the source. It is not a different reading of the source. If a point cannot be made in the commentary's own words, leave it out.
4. **Cite every claim.** Each paragraph ends with one or more `(1-SOURCES/Commentaries/<commentary-name>.md#^<block-id>)` references that anchor every factual statement in the paragraph to a specific block.
5. **Cover only the node.** Do not summarise child nodes inside the parent — they get their own files. Reference children by their heading text in passing if essential for narrative coherence.
6. **No new vocabulary.** Never introduce a term that does not appear in the commentary's discussion of this node.

---

### Procedure

1. Open the commentary file and locate the heading whose block ID matches the requested node-id.
2. Identify the block range that belongs to that heading: from the first block under the heading down to (but not including) the next heading at the same level or higher.
3. Read every block in that range.
4. Draft a one- to four-paragraph summary in the original language. Each paragraph addresses one move the commentator makes (a definition, an example, a refutation, a synthesis).
5. After each paragraph, place the block-ID citations for the source blocks it draws on.
6. Fill the frontmatter. Set `status: draft`.
7. Write the file to `2-RAILS/Sections/Raw/<commentary-name>/<node-id>.md`.

---

### Examples

#### Example invocation

> "Run `section-summary-raw` for node `^1-1-0` (Ganthārambhakathā) of `pi-dhammasangani-atthakatha.md`."

#### Example output skeleton

```markdown
---
node_id: 1-1-0
node_heading: Ganthārambhakathā
commentary: dhammasangani-atthakatha
commentary_file: 1-SOURCES/Commentaries/pi-dhammasangani-atthakatha.md
language: pi
status: draft
---

### Ganthārambhakathā

Imissā ganthārambhakathāya Buddhaghosācariyo paṭhamaṃ namassanaṃ karoti,
tato Dhammasaṅgaṇī-aṭṭhakathāya nāmaṃ niyamento Aṭṭhasālinīti vohāraṃ vadati.
(1-SOURCES/Commentaries/pi-dhammasangani-atthakatha.md#^1-1)
(1-SOURCES/Commentaries/pi-dhammasangani-atthakatha.md#^1-2)

Ācariyo āha — Abhidhammapiṭake satta pakaraṇāni honti, tesu paṭhamaṃ
Dhammasaṅgaṇi nāma, tassā aṭṭhakathā Aṭṭhasālinīti.
(1-SOURCES/Commentaries/pi-dhammasangani-atthakatha.md#^1-3)
```

---

### Completion check

Before marking the file complete, verify:

- [ ] Frontmatter complete (`node_id`, `node_heading`, `commentary`, `commentary_file`, `language`, `status`)
- [ ] Heading on line below frontmatter matches `node_heading` exactly
- [ ] Every paragraph ends with at least one citation
- [ ] Every citation points to a block actually present in the source file
- [ ] Summary is in the original language only — no translation interleaved
- [ ] No terminology used that is not attested in the source range

---

## Phase 2 — Combined — reconcile every commentary on that node

Reads every Phase 1 file for the node. Preserves original-language terminology, records where commentaries diverge rather than smoothing it away, and adds the English translation.

This skill produces the **combined section summary** for one node in the table of contents. It reads every raw per-commentary summary that exists for the node under `2-RAILS/Sections/Raw/`, synthesises them into a single original-language summary, flags interpretive divergences across commentaries, and adds an English translation underneath.

The output is one of the three context layers loaded by `translate-section` (alongside `verse-context` and the per-track bilingual glossary).

---

### Inputs

- **Node ID** — the TOC node to combine (e.g. `1-1-0`).
- **All raw summary files** for that node under `2-RAILS/Sections/Raw/*/<node-id>.md`. Run `glob` for `2-RAILS/Sections/Raw/*/<node-id>.md` to discover them.

If only one commentary covers the node, this skill still runs — it produces a single-source combined summary and adds the English translation.

### Output

One file at:

```
2-RAILS/Sections/<node-id>.md
```

If the file already exists, update it in place. Preserve any manual edits to existing paragraphs unless the underlying raw summaries have changed.

---

### Output file format

```markdown
---
node_id: <e.g. 1-1-0>
node_heading: <original-language heading text>
language: <primary original language, e.g. pi>
commentaries: [<commentary-name>, <commentary-name>, ...]
raw_sources:
  - 2-RAILS/Sections/Raw/<commentary-name>/<node-id>.md
  - 2-RAILS/Sections/Raw/<commentary-name>/<node-id>.md
status: draft
---

### <node-heading verbatim>

#### Synthesis (original language)

<one or more paragraphs in the original language that state what every
commentary agrees on for this node. Use the commentary tradition's own
terminology. Each paragraph ends with citations to the raw summaries it
draws on, e.g. (Raw/dhammasangani-atthakatha/1-1-0.md), and through them
to the original commentary block IDs.>

#### Divergences

<only include this section if commentaries differ on what this node does
or how it should be read. Each divergence is one line:>

- **<topic>** — <commentary-A> reads ... ⚑; <commentary-B> reads ... ⚑.
  (Raw/<commentary-A>/<node-id>.md) (Raw/<commentary-B>/<node-id>.md)

#### English translation

<English translation of the Synthesis paragraphs above, in the same order.
This is the only English content in the file. The translation preserves
the technical Pali (or other source-language) terms in italics on first
mention, glossed parenthetically, and as-is thereafter.>
```

---

### Rules

1. **Original-language synthesis comes first; the English translation is downstream.** Never draft the English first and back-translate.
2. **Synthesis states only what every raw summary supports.** Anything attested in only one commentary, or contested across commentaries, goes in **Divergences**, never in Synthesis.
3. **Cite the raw summaries, not the source files directly.** The raw summaries already carry the source-block citations; the combined file cites the raw layer to keep responsibility traceable.
4. **Preserve original-language terminology.** The Synthesis paragraphs use the same vocabulary as the raw summaries. Do not substitute a commentator's term with a synonym.
5. **The English translation is faithful, not paraphrastic.** Translate the Synthesis sentence-for-sentence. Preserve the technical terms; gloss them parenthetically on first mention; never replace them with English equivalents that erase distinctions the original-language summary makes.
6. **Divergence flag ⚑** marks every genuine interpretive split. The translation skill needs to see these — they often mark passages that require a translator decision rather than a default rendering.

---

### Procedure

1. Glob `2-RAILS/Sections/Raw/*/<node-id>.md`. If no files match, abort with an error — `section-summary-raw` must run first.
2. Read each raw summary. Note the commentary name, the language, and every claim asserted.
3. Identify the claims that every raw summary supports (consensus) and the claims that appear in only some, or that conflict between commentaries (divergence).
4. Draft the Synthesis in the primary source language. Each paragraph closes with citations to the raw files that support it.
5. If divergences exist, write the **Divergences** section. One bullet per divergence, both commentary positions marked with ⚑, both raw files cited.
6. Translate the Synthesis into English. Preserve technical terms (italicised on first mention with a parenthetical gloss; bare thereafter). Do not translate the Divergences.
7. Fill the frontmatter. Set `status: draft`.
8. Write the file to `2-RAILS/Sections/<node-id>.md`.

---

### Example

For node `1-1-0`:

```markdown
---
node_id: 1-1-0
node_heading: Ganthārambhakathā
language: pi
commentaries: [dhammasangani-atthakatha, dhammasangani-mulatiika]
raw_sources:
  - 2-RAILS/Sections/Raw/dhammasangani-atthakatha/1-1-0.md
  - 2-RAILS/Sections/Raw/dhammasangani-mulatiika/1-1-0.md
status: draft
---

### Ganthārambhakathā

#### Synthesis (original language)

Imissā ganthārambhakathāya ācariyo paṭhamaṃ ratanattayassa namassanaṃ
karoti, tato Dhammasaṅgaṇī-aṭṭhakathāya nāmaṃ niyameti.
(Raw/dhammasangani-atthakatha/1-1-0.md)
(Raw/dhammasangani-mulatiika/1-1-0.md)

#### English translation

In this opening section the commentator first pays homage to the Triple
Gem, then fixes the name of the *Dhammasaṅgaṇī-aṭṭhakathā* (commentary to
the Dhammasaṅgaṇī).
```

---

### Completion check

- [ ] Every raw summary under `2-RAILS/Sections/Raw/*/<node-id>.md` is listed in `raw_sources`
- [ ] Synthesis contains only consensus claims
- [ ] Every divergence is flagged with ⚑ and cited to both raw files
- [ ] English translation tracks the Synthesis paragraph-for-paragraph
- [ ] Technical source-language terms are preserved (italicised, glossed on first mention)
- [ ] Heading matches `node_heading` exactly
- [ ] Frontmatter complete

---

## After this skill

`2-RAILS/Sections/<node-id>.md` is what the translation skills load to get a section's
meaning, and what `commentary-claims` and `local-wiki-article` build on. It is a rail:
downstream work cites it, so re-running Phase 2 means re-checking whatever cited it.
