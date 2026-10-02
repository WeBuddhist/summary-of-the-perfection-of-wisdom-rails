---
name: segment-commentary
description: >
  Break a commentary into short, individually-referenceable blocks — prose
  paragraphs, verse stanzas, quotations — so every claim can later cite one. Handles
  the three states a commentary arrives in: one continuous run of text, one clause per
  line, or already segmented but needing boundaries re-drawn after TOC headings went in.

  Trigger on "segment this commentary", "re-paragraph this text", "the blocks are too
  long", "split this into citation units", "resegment", "re-draw the block boundaries",
  or when a commentary's text is one unbroken run and needs breaking up before block
  IDs are applied.

  Runs BEFORE block-ID stamping and before verse-context. Never interprets,
  translates, or alters a single character of the source.
---

# Segment a commentary into citation-sized blocks

**Pick the phase by what the file currently looks like** — these are not all run in
sequence on every text:

| The file arrives as | Run | Then |
|---|---|---|
| One continuous run of prose, or very long paragraphs | Phase 1 | Phase 3 after TOC ingest |
| One clause per line (OCR output, a line-broken source) | Phase 2 | Phase 3 after TOC ingest |
| Already segmented, TOC headings now ingested | Phase 3 only | — |

Phases 1 and 2 are **alternative entry points for different input shapes**, not
consecutive steps. Phase 3 is the later pass that runs once headings exist, because a
heading changes where a sensible block boundary falls.

**The integrity rule governing all three phases.** Per `4-SYSTEM/Guidelines/skill-locations.md`, the only
permitted edits to a source file are structural. Inserting or removing a paragraph
break is structural; rewording, glossing, normalising spelling, or "fixing" the text
is interpretation and is forbidden here. OCR repair belongs to `format-commentary`,
which runs first. Every bundled script enforces this with a no-loss assertion:
**output minus whitespace must equal input minus whitespace**, or it aborts and
writes nothing. Do not weaken that assertion.


**Language scope — Tibetan.** Every rule set below (terminal particles, shad and
double-shad boundaries, syllable caps counted by tsheg, the objection/reply and
enumeration markers, the verse-pāda detector) is specific to classical Tibetan.
The *architecture* — deterministic pre-pass, windowed LLM judgment, script-applied
whitespace-only edit, no-loss gate — is language-neutral and is what to reuse.
A Pāli, Sanskrit, Chinese or English commentary needs its own boundary rule set
written for that language before any of these scripts will give sensible output;
do not run the Tibetan rules on another script and hand-fix the result.

**Dependencies.** Phase 1 is stdlib-only. **Phases 2 and 3 call the Gemini API**
and will not run without them: `pip install google-genai`, plus a key in the
`GEMINI_API_KEY` environment variable (`resegment.py` also reads a repo-root
`.env` automatically). `4-SYSTEM/Skills/segment-commentary/scripts/list_models.py` lists the models the key
can reach. The QC checkers and every Phase-1 script make no API calls.

---

## Phase 1 — Segment continuous prose into blocks

For a commentary that is one unbroken run, or has paragraphs far too long to cite. Boundaries come from the functional content — quotation frames, objection/answer markers, sa-bcad enumerations, sentence-final particles, verse detection.

**Role:** Expert editor in classical Tibetan Buddhist commentary (`འགྲེལ་པ་`) structure and Obsidian markdown.

**Task:** Insert block boundaries into a Tibetan commentary so each block is a citation-sized unit (a prose sentence or two, one verse stanza, or one quotation) — without adding, removing, reordering, or re-spelling any character of the source.

The boundaries follow the text's own functional signals: quotation frames, objection/answer markers, sa-bcad enumerations, sentence-final particles, and verse meter. Most of this is done deterministically by the scripts in `4-SYSTEM/Skills/segment-commentary/scripts/`; you only hand-finish what the rules cannot resolve.

**Scope and the citation chain.** This skill operates on files in `1-SOURCES/Commentaries/`. Per the permission rule in `4-SYSTEM/Guidelines/skill-locations.md`, the only permitted edits to a source file are structural (block boundaries, block IDs, navigation, factual `[Ed:...]` notes). Inserting a paragraph break is structural; rewording, glossing, or "fixing" the text is interpretation and is forbidden here. If the text needs OCR repair, that belongs to `format-commentary`, which runs first. Every script here enforces this with a no-loss assertion: the output minus whitespace must equal the input minus whitespace, or it aborts and writes nothing.

---

**What good output looks like**

- **Granularity:** 1–2 sentences of prose per block; one stanza per verse block; one quotation per quote block — small enough that a downstream rail can cite exactly the span it needs. A prose block that exceeds ~40 tsheg-delimited syllables should be split unless it is a single indivisible clause, quotation, or stanza.
- **Verses (ཚིགས་བཅད):** one independent stanza per block. Keep a stanza's pādas together; never merge two independent stanzas into one block.
- **Quotes (ལུང་འདྲེན):** the source attribution (e.g. `སྡུད་པ་ལས།`) on its own block above the quote, and the closing formula (e.g. `ཞེས་སོ། །`) on its own block below it (format-commentary §3).

---

**Pipeline position**

```
format-commentary            →  commentary-segmentation  →  verse-context / verse-context-batch
(OCR clean, heading structure)   (this skill: boundaries)     (rails consume the blocks)
```

Do not run this skill on text that is not yet OCR-clean.

```
[Stage 0]                   [Stage 1]               [Stage 2]              [check]        [human]
preclean_commentary.py  →  segment_commentary.py  →  stage2_refine.py  →  no-loss vs  →  approval
(strip scaffolding,         (deterministic            (mechanical            source         + hand review
 optional)                  boundaries)               refinement)
```

---

**Scripts at a glance**

| Script | Stage | Role |
|---|---|---|
| `preclean_commentary.py` | 0 | Strip prior scaffolding (index numbers, block IDs, heading IDs, per-line breaks) back to continuous prose. Optional. |
| `segment_commentary.py`  | 1 | Deterministic boundary insertion. The core of the skill. |
| `stage2_refine.py`       | 2 | Mechanical refinement of the Stage-1 draft (newline expansion, citation/lead-in splits, optional connector splits). |
| `batch_segment.py`       | 0+1 | Run Stage 0 + Stage 1 over a whole directory in parallel; emits per-file reports plus a batch summary and a combined flagged-rows file. |

All scripts share `--dry-run` (validate, write nothing) and a `--report` TSV. Paths below are relative to the vault root.

---

**Stage 0 — pre-clean already-formatted files (optional, run first when needed)**

Some commentary files arrive already carrying scaffolding from an earlier pass: standalone OCR index numbers (a line that is just `1`, `2`, `3`…), Obsidian block / verse IDs (`^0-1`, `^1-2`, `^1-2-0`), markdown heading markers (`##`, `###`), and line breaks that wrap verses and split sentences across lines. Segmentation re-derives boundaries from continuous prose, so this scaffolding must be removed **before** Stage 1. If a file is already plain, under-segmented running text, skip this stage.

```
python3 4-SYSTEM/Skills/segment-commentary/scripts/preclean_commentary.py \
    "1-SOURCES/Commentaries/<file>.md" \
    "0-INBOX/temp/<file>.preclean.md" \
    --report "0-INBOX/temp/<file>.preclean.tsv"
```

What it removes (editorial scaffolding only — never a character of body text):

- **Index / outline numbers** — any whitespace-bounded token consisting solely of digits (ASCII `0-9` or Tibetan `༠-༩`) with optional internal dots (hierarchical numbers such as `4.11`, `1.2.3`) and an optional trailing `.` or `)`, removed unconditionally. Covers simple counters (`1`, `2`, `3`), terminated counters (`1.`, `2.`), and hierarchical section labels (`4.11`, `1.2.3.`). Catches both an OCR line counter on its own line *and* an inline outline number sitting before a sa-bcad opener (e.g. `…ཏོ། །19. དང་པོ་ནི།…`). Numbers fused to body text (e.g. `ལོ16`) are left untouched — Tibetan never delimits a real syllable with a bare space.
- **Block / verse IDs** — `^N`, `^N-N`, `^N-N-N` … wherever they appear.
- **Heading markers** — all `#` characters are stripped from the body. Heading text is preserved as plain prose and acts as a natural separator between prose runs; a heading whose text is a bare number (likely OCR noise) is flagged `heading-suspect` in the report.
- **Intra-section line breaks** — consecutive content lines are joined into one continuous run, so Stage 1 starts from raw prose. Heading-text lines (now plain prose) still act as run separators, so a section title never fuses onto neighbouring content.

Frontmatter (the leading `--- … ---` block) is preserved verbatim and excluded from the no-loss comparison.

---

**Stage 1 — deterministic boundary detection (script)**

`4-SYSTEM/Skills/segment-commentary/scripts/segment_commentary.py` inserts a paragraph break at every high-confidence *functional* boundary, and only there:

- `terminal-particle` — a clause-final particle (`འོ`/`ནོ`/`དོ`/`སོ`/`ཏོ`/`གོ`/`ལོ`…) plus `།` ends a prose sentence. Broad catch-all; runs last so more specific markers claim a position first.
- `quote-close` — explicit closers (`ཞེས་སོ། །`, `ཅེས་སོ། །`, `ཞེས་གསུངས་སོ། །`, `ཞེས་པའོ། །`, `ཞེས་བྱ་བའོ། །`…) end a citation.
- `quote-open` — a source-attribution marker (`…ལས།`, `…གསུངས།`) gets its own block before the cited passage.
- `enumeration-head` — a sa-bcad head closing on a number-word + suffix (e.g. `…ལ་གསུམ་སྟེ།`, `…ལ་གཉིས་ལས།`) ends a node.
- `ordinal-open` — `དང་པོ་…`, `གཉིས་པ་…`, `གསུམ་པ་…` opens a new topical node.
- `objection-close` / `objection-open` — `…ཅེ་ན།` / `…ཞེ་ན།` / `…སྙམ་ན།` closes an objection; `འོ་ན་…` opens the reply. `objection-open` is a weak-context rule: it only auto-cuts when it sits just after a shad; otherwise it is reported as a `-candidate` for a human to judge rather than cut blindly.
- `verse-stanza` — a run of 2–4 consecutive clause units, each 6–11 syllables, uniform in length (max − min ≤ 2), each ending on a strong (double) shad, is peeled out as one protected stanza: emitted whole, never run through the rule engine or the syllable cap, never flagged `STAGE2_REVIEW`. A single-shad unit sandwiched between two stanza pādas is bridged into the run (some sources mark pāda ends with a single shad). An isolated pāda-length clause stays with the surrounding prose, so a medium prose sentence is never mistaken for a one-line verse.

After the rule pass it enforces a syllable cap: any segment still longer than `--max-syllables` is split at shad (clause) boundaries; over-cap segments with no internal shad are flagged `STAGE2_REVIEW:NO_SHAD_FOUND`. Over-fragmented adjacent segments are merged back while they fit the cap (citation boundaries are never merged away). The run also prints a **quote-balance** check (count of `quote-open` vs `quote-close`); a `MISMATCH` points to an unclosed or stray citation marker worth a look.

Two ways to run it:

```
# (a) cap-based — finer control, every over-cap block flagged for review:
python3 4-SYSTEM/Skills/segment-commentary/scripts/segment_commentary.py \
    "0-INBOX/temp/<file>.preclean.md" \
    "0-INBOX/temp/<file>.segmented.md" \
    --report "0-INBOX/temp/<file>.segreport.tsv" \
    --max-syllables 40

# (b) structural — closest match to the canonical block layout:
python3 4-SYSTEM/Skills/segment-commentary/scripts/segment_commentary.py \
    "0-INBOX/temp/<file>.preclean.md" \
    "0-INBOX/temp/<file>.structural.md" \
    --report "0-INBOX/temp/<file>.segreport.tsv" \
    --structural
```

`--structural` breaks prose only at strong (double-shad) sentence ends, section heads, and citation frames; emits verses one pāda per line; splits citation markers and re-attaches short closing formulas to their block; and implies **no syllable cap**. It is the best single-pass match for the layout downstream rails expect. Use the cap-based mode (a) when you want every long run surfaced for manual review instead.

Note the default for `--max-syllables` is **50** if you omit it; the granularity target is ~40, so pass `--max-syllables 40` explicitly (the batch runner already defaults to 40). The cap is ignored under `--structural`.

The Stage-1 output goes to `0-INBOX/temp/` — never overwrite the source until boundaries are approved.

**Batch mode.** To process an entire directory in parallel:

```
python3 4-SYSTEM/Skills/segment-commentary/scripts/batch_segment.py \
    "1-SOURCES/Commentaries" "0-INBOX/temp/segmented" \
    --preclean --max-syllables 40
```

It runs Stage 0 (with `--preclean`) then Stage 1 per file across all CPUs, skips files whose output already exists (`--force` to redo), and writes `batch_summary.tsv` (one row per file, including the quote-balance status) and `batch_flagged.tsv` (every `STAGE2_REVIEW` row across all files) into the output directory.

---

**Stage 2 — semantic refinement**

Most of the Stage-1 residue is mechanical and is handled by `4-SYSTEM/Skills/segment-commentary/scripts/stage2_refine.py`. Run it first, then hand-review only what it leaves behind.

```
python3 4-SYSTEM/Skills/segment-commentary/scripts/stage2_refine.py \
    "0-INBOX/temp/<file>.segmented.md" \
    "0-INBOX/temp/<file>.stage2.md" \
    --max-syllables 40 \
    --source "1-SOURCES/Commentaries/<file>.md" \
    --report "0-INBOX/temp/<file>.stage2.tsv"
```

It performs, deterministically and no-loss:

- **Newline expansion** (default) — `merge_short_segments` in Stage 1 joins consecutive source lines that were each under the cap, leaving an internal `\n` inside a block. For any over-cap block containing an internal `\n`, every `\n` becomes a paragraph break — each original source line becomes its own block. This restores boundaries the source already marked; it never guesses.
- **Citation lead-in / verse split** (default) — a short source-frame line glued onto a following stanza is peeled back onto its own block.
- **Connector split** (opt-in, `--split-connectors`) — over-cap *single-line* prose is split at strong sub-clause connectors (`ཅིང་`/`ཞིང་`/`སྟེ་`/`ཏེ་`/`ནས་`/`ལས་`), never producing a piece below 8 syllables. Off by default: a connector is a weaker signal than a source-marked line break, so prefer leaving a block whole over a wrong cut.

Passing `--source` adds a second no-loss assertion against the **original source file**, so any deviation inherited from Stage 1 is caught here rather than passed downstream silently. Blocks still over the cap that the tool can't safely split are reported as `STAGE2_MANUAL`.

**Hand-review** the `STAGE2_MANUAL` rows (and any `STAGE2_REVIEW` rows from Stage 1). These are prose runs with no lexical cue. Insert a paragraph break only at a genuine topic shift — where the commentary moves from a position to its reason, from one objection to the next, or from gloss to scriptural support. Rules for hand edits:

- Only *insert* `\n\n` boundaries. Do not change, reorder, or delete any syllable.
- For a verse embedded inside a larger prose paragraph (the script couldn't isolate it), do not split pādas: break before the first pāda and after the final `།།`, keeping the stanza together. Never merge two independent stanzas.
- Keep a `…ལས།` attribution line and its closing `ཞེས་སོ། །` on their own blocks (format-commentary §3).
- When a passage genuinely cannot be cut without breaking sense, leave it whole. Over-long is safer than wrong.

If you write any bespoke refinement code, read `4-SYSTEM/Skills/segment-commentary/scripts/segment_commentary.py` first — two facts save rewrites:

- **TSV index ≠ paragraph index.** The TSV numbers segments as the script counts them internally; `merge_short_segments` then merges short adjacent segments, so TSV row N does not map to output paragraph N.
- **Use the script's `_squeeze`** (the whitespace-translate table in `4-SYSTEM/Skills/segment-commentary/scripts/segment_commentary.py` / `stage2_refine.py`, not `re.sub(r'\s+','',s)`) for any no-loss check, or you may see phantom mismatches. If a mismatch appears, first test `squeeze(source) == squeeze(stage1_output)` to see whether it predates your change.

After Stage 2, re-run a no-loss check against the **original source** (the `--source` flag does this automatically) before proceeding.

---

**Procedure**

1. Confirm the file is OCR-clean (run `format-commentary` first if not).
2. If the file carries index numbers, block/verse IDs, headings, or per-line/per-verse breaks, run **Stage 0** (`preclean_commentary.py`) to `0-INBOX/temp/`. Skip if it is already plain running text.
3. Run **Stage 1** (`segment_commentary.py`, on the Stage-0 output if you ran it) to `0-INBOX/temp/`, producing the segmented draft and the TSV report. Use `--structural` for the canonical layout, or `--max-syllables 40` for review-oriented output. For many files at once, use `batch_segment.py`.
4. Run **Stage 2** (`stage2_refine.py`) with `--source` pointing at the original. Then hand-review the `STAGE2_MANUAL` / `STAGE2_REVIEW` rows.
5. Re-run the no-loss check against the **original source file**.
6. Have a domain specialist approve the boundaries.

**Output**

- A boundary-segmented commentary draft in `0-INBOX/temp/` (not the source — the source is only updated after human approval).
- TSV reports listing each segment, the rule that triggered its boundary, its syllable count, and any review flag.

**Rules recap**

- No character changes — boundaries only. The scripts enforce this; hand edits must honor it too.
- OCR repair and translation are out of scope (other skills own those).
- Never write block IDs in this step.
- When in doubt, under-cut rather than over-cut.

---

## Phase 2 — Re-paragraph a one-clause-per-line commentary

For a commentary that arrives with one clause per line. An LLM decides BY MEANING which adjacent lines form one sense unit — not by grammar rules or particle matching.

**Role:** Expert editor of classical Tibetan Buddhist commentary (འགྲེལ་པ་).

**Task:** Group a one-clause-per-line commentary into short, coherent paragraphs —
**by meaning, decided by the LLM**, not by hard grammar rules — while changing not one
word or character of the source.

**Precondition — the file really is one clause per line.** If the source is
running prose, this is a Phase 1 file, not a Phase 2 file. If it is prose that
*should* be reflowed one clause per line first, use `format-commentary`'s
`shad_linebreak.py` (reflow at shad, whitespace-only) and then come back here.

---

### The model

```
unit            = one non-blank, non-heading line (atomic; never altered)
default state   = every unit is its own paragraph
GROUP n..m      = lines n..m form ONE paragraph, joined onto a single line
headings        = pass through untouched, framed by blank lines
output          = paragraphs separated by exactly one blank line
```

The LLM only points at line numbers (`{"op":"merge","lines":[14,15,16]}`); the script
does all text handling. Lines the LLM does not group default to their own paragraph.

---

### Integrity rule — pure whitespace-only

The source is read-only ground truth. The only edits are added/removed newlines and
spaces (no `>` or other markers are introduced). The gate is therefore exact:

```
strip_all_whitespace(source) == strip_all_whitespace(output)
```

If the two character streams differ, the output is **not written**.

---

### How the LLM decides (content-based, not rules)

For each section the model reads the lines **and their context** and groups adjacent
lines into one paragraph when they form a single sense unit — one idea, one narrative
beat, one objection-and-reply exchange. It starts a new paragraph when the topic, the
actor, or the move in the argument shifts. Target length is about **2–4 lines**, leaning
shorter when unsure. There are no particle/verse/enumeration rules.

Mechanical guardrails the script still enforces (not judgments about the text): a group's
lines must be consecutive, must not cross a heading, and no line is used twice.

---

### Architecture

```
[Phase 1]  Number lines; slice into sections on TOC headings. A file with no headings is
           cut into windows of <= --window-lines lines at sentence-final particles, so no
           sense unit is split across a window boundary.
[Phase 2]  LLM returns paragraph groups by line number for each window.
[Phase 3]  Script validates (consecutive, no heading crossed, no overlap) and joins each
           group onto one line; uncovered lines become their own paragraph.
[Phase 4]  Integrity gate (whitespace-only). On mismatch, nothing is written.
```

---

### Script — `resegment.py`

```
# one file:
python3 4-SYSTEM/Skills/segment-commentary/scripts/resegment.py \
    "1-SOURCES/Commentaries/<commentary-id>.toc.md" --commentary-id <commentary-id>
```

**Setup:** `pip install google-genai`; key from `GEMINI_API_KEY` env **or** repo-root
`.env` (read automatically).

| Flag | Default | Purpose |
|---|---|---|
| `--commentary-id` | filename stem | Output id |
| `--window-lines` | 60 | Max content lines per LLM window (paragraph granularity) |
| `--model` | `gemini-2.5-flash` | Gemini model |
| `--fallback-model` | `gemini-2.0-flash` | Fallback if overloaded |
| `--force` | off | Reprocess all windows even if staged |
| `--apply-only` | off | Skip LLM calls; apply staged decisions |
| `--dry-run` | off | Integrity check only; write nothing |

**Outputs:**

| File | Purpose |
|---|---|
| `0-INBOX/temp/resegmented/<id>.reseg.md` | Re-paragraphed commentary (one line per paragraph) |
| `0-INBOX/temp/resegmented/<id>.ops.md` | Log of paragraph groups applied |
| `0-INBOX/temp/RESEG-<id>/windows/window-NNNN.json` | Per-window staging (resumable) |

Resumable (re-run skips staged windows); `--apply-only` re-applies staged decisions
without new LLM calls.

---

### QC pass — `qc_check.py`

`4-SYSTEM/Skills/segment-commentary/scripts/qc_check.py` is the deterministic, report-only companion to
`resegment.py`. It makes no API calls and no edits: it scans every block of a
`.reseg.md` and writes `<id>.qc.md` next to it listing blocks worth a human look.

```
python3 4-SYSTEM/Skills/segment-commentary/scripts/qc_check.py "0-INBOX/temp/resegmented/<id>.reseg.md"

# tune the over-length threshold (syllables):
python3 4-SYSTEM/Skills/segment-commentary/scripts/qc_check.py "0-INBOX/temp/resegmented/<id>.reseg.md" --over-length 60
```

| Flag | Means |
|---|---|
| `CONNECTOR_ENDING` | block ends in a connector particle (`དང་། ཞིང་། ཅིང་། ཤིང་། ནས། ལས། སྟེ། ཏེ། དེ། པས། ལ།`) — the sentence likely continues; the block may need merging forward |
| `OBJECTION_REPLY_FUSED` | block contains both an objection (`ཅེ་ན།/ཞེ་ན།/སྙམ་ན།`) and a reply (`འོ་ན།`) — two thoughts in one block |
| `OVER_LENGTH` | block exceeds `--over-length` syllables (default 60) — may hide a boundary |
| `SHORT_FRAGMENT` | block under 4 syllables — possible stray fragment |

It always exits 0. Read the report, then fix boundaries by re-running
`resegment.py` on the affected file — never by hand-editing the `.reseg.md`,
which would sidestep the integrity gate.

---

### Procedure

1. **Pilot one file**, then read `0-INBOX/temp/resegmented/<id>.reseg.md`. Confirm
   `✓ Integrity check passed`.
2. **Tune** `--window-lines` if paragraphs feel too long/short.
3. **Repeat** for the other files (loop over the folder in your shell).

---

### Rules

- **No text changes.** The whitespace-only integrity gate must pass or nothing is written.
- **Only whitespace is added/removed.** No `>`, `#`, or other characters are introduced.
- **Headings untouched; paragraphs never cross a heading.**
- **Output goes to `0-INBOX/temp/resegmented/`**, leaving the read-only source intact.
- **Judgment, not rules.** Grouping is interpretive (content/context), so paragraph
  breaks are not perfectly identical across runs.

---

## Phase 3 — Re-draw block boundaries after TOC ingest

Run after Phase 1 or 2 AND after TOC headings are in (`toc-generate` Phase E). The LLM flags merge/split decisions; a script applies them and proves no text was lost.

**Role:** Expert editor in classical Tibetan Buddhist commentary (འགྲེལ་པ་) structure.

**Task:** Identify which adjacent blocks should be merged into one thought unit and
which single blocks should be split at a topic boundary — then apply those operations
via script, preserving every character of the source.

---

### Pipeline position

```
Phase 1, Stage 1                    ← rule-based boundary detection
         ↓
[TOC ingest — `toc-generate`]        ← headings inserted into segmented file
         ↓
block-resegmentation                ← THIS SKILL: semantic merge/split
```

**Input:** a Stage-1 segmented file with TOC headings embedded, in `0-INBOX/temp/segmented/`
or wherever the TOC step wrote its output.

**Do not run** on a file that has block IDs already. Do not run before TOC headings
are included (the headings give the LLM section context).

---

### What good output looks like

- **One block = one citable thought.** A downstream rail file should be able to cite
  exactly the span it needs — no more, no less.
- **Verse stanzas are whole.** A 4-pāda stanza is one block. Never merge two
  independent stanzas; never leave half a stanza as a block.
- **Enumerations are complete.** An enumeration head plus all its items form one block
  (unless individual items are long enough to cite independently).
- **Lead-ins stay with their content.** A transition phrase like `བོད་སྐད་དུ།` is in
  the same block as the text it introduces.
- **Objections and replies are separate.** `ཅེ་ན།`/`ཞེ་ན།` block and `འོ་ན།` block are
  always two blocks.
- **Source attributions are separate.** A `…ལས།` attribution line is its own block;
  the quoted passage is its own block; the closing `ཞེས་སོ། །` is its own block.
- **Headings are untouched.** Markdown heading lines (`#`, `##`, `###`, …) pass
  through unchanged and are never part of a merge or split operation.

---

### Architecture — LLM flags, script applies

```
[Phase 1]  Script chunks the file into overlapping block windows
[Phase 2]  LLM reads each window, outputs a JSON operation list
           {"op": "merge", "blocks": [3, 4]}
           {"op": "split", "block": 7, "after": "<unique substring>"}
[Phase 3]  Script combines windows, deduplicates overlap zone, applies ops
[Phase 4]  Script runs squeeze(input) == squeeze(output); aborts on mismatch
[Phase 5]  QC pass — deterministic checks + optional LLM correction
[Phase 6]  Human reviews ops log + QC report; approves output
```

The LLM **never retypes Tibetan**. It only points at block numbers and verbatim
substrings. All text manipulation is done by the script.

---

### Scripts

Two scripts bundled in `scripts/`:

| Script | Purpose |
|---|---|
| `resegment--block-resegmentation.py` | Main resegmentation: chunk → LLM flag → apply → integrity check |
| `qc_check--block-resegmentation.py` | QC pass: deterministic checks → optional LLM correction → integrity check |

---

#### `resegment--block-resegmentation.py`

```
python3 4-SYSTEM/Skills/segment-commentary/scripts/resegment--block-resegmentation.py \
    "0-INBOX/temp/segmented/<file>.md" \
    --commentary-id <id>
```

**Setup:** `pip install google-genai` and set `GEMINI_API_KEY` in the environment.

**Key flags:**

| Flag | Default | Purpose |
|---|---|---|
| `--commentary-id` | inferred from filename | Short ID for output filenames and staging folder |
| `--window-size` | 40 | Blocks per LLM call |
| `--overlap` | 5 | Overlap blocks between adjacent windows |
| `--model` | `gemini-2.5-flash-preview-05-20` | Gemini model to use |
| `--fallback-model` | `gemini-2.0-flash` | Fallback if primary is overloaded |
| `--force` | off | Reprocess all windows even if staging files exist |
| `--apply-only` | off | Skip LLM calls; apply already-staged operations |
| `--dry-run` | off | Run integrity check only; write nothing |

**Outputs:**

| File | Purpose |
|---|---|
| `0-INBOX/temp/resegmented/<id>.reseg.md` | Resegmented commentary |
| `0-INBOX/temp/resegmented/<id>.ops.md` | Human-readable operations log |
| `0-INBOX/temp/RESEG-<id>/windows/window-NNNN.json` | Per-window staging (resumable) |

---

#### `qc_check--block-resegmentation.py`

Mirrors the QC pattern in `toc_tree_extractor`: detect → repair → re-check → report.
By default all four steps run automatically. Run after `resegment--block-resegmentation.py`.

```
python3 4-SYSTEM/Skills/segment-commentary/scripts/qc_check--block-resegmentation.py \
    "0-INBOX/temp/resegmented/<id>.reseg.md"
```

Use `--no-fix` to run detection only (no LLM repair):

```
python3 4-SYSTEM/Skills/segment-commentary/scripts/qc_check--block-resegmentation.py \
    "0-INBOX/temp/resegmented/<id>.reseg.md" --no-fix
```

**Steps:**

1. **Deterministic check** — scans every block for known violations; no API call.
2. **LLM repair** — sends the issues list + flagged blocks with context to Gemini,
   which outputs correction operations. Script applies them; integrity is verified.
3. **Re-check** — runs the deterministic checks again on the repaired output.
4. **Report** — written with `flags_before`, corrections applied, `flags_after`.

**What the deterministic checker flags:**

| Flag | Condition |
|---|---|
| `CONNECTOR_ENDING` | Block ends with `དང་།` / `ཞིང་།` / `ཅིང་།` / `ནས།` / `ལས།` / `སྟེ།` / `ཏེ།` — sentence incomplete |
| `OBJECTION_REPLY_FUSED` | Block contains both `ཅེ་ན།`/`ཞེ་ན།` and `འོ་ན།` — should be two blocks |
| `OVER_LENGTH` | Block exceeds 60 syllables — may contain a buried topic boundary |
| `SHORT_FRAGMENT` | Block is under 4 syllables — may be a split artifact |

**Outputs:**

| File | Purpose |
|---|---|
| `0-INBOX/temp/resegmented/<id>.qc.md` | QC report with `flags_before` / `flags_after` |
| `.reseg.md` updated in place | (only when real issues found and `--no-fix` not set) |

**Key flags:**

| Flag | Default | Purpose |
|---|---|---|
| `--no-fix` | off | Detection only; skip LLM repair |
| `--over-length` | 60 | Syllable threshold for OVER_LENGTH flag |
| `--dry-run` | off | Compute corrections but write nothing |
| `--model` | `gemini-2.5-flash-preview-05-20` | Gemini model |
| `--fallback-model` | `gemini-2.0-flash` | Fallback model |

---

### How the LLM decides

#### MERGE — adjacent blocks that form one thought

**M1 — Incomplete sentence.** A block ends with a connector particle that
grammatically requires continuation in the next block:
`དང་།` / `ཞིང་།` / `ཅིང་།` / `ནས།` / `ལས།` / `སྟེ།` / `ཏེ།`

**M2 — Broken verse stanza.** A standard stanza has 4 pādas (~7–9 syllables each,
ending with `།`). If a block has only 1–2 pādas and the stanza continues into the
next block, merge all pādas of the stanza. Never merge two independent stanzas.

**M3 — Lead-in orphaned from content.** A block ends with a transition phrase
(`བོད་སྐད་དུ།` / `འདི་ལྟར།` / topic-opener `དེ་ལ།`) that introduces the next block.
Merge the lead-in with the block it introduces.

**M4 — Incomplete enumeration.** A block opens an enumeration (`གཉིས་ཏེ།` /
`གསུམ་སྟེ།` / `བཞི་ལས།` etc.) and the remaining items continue in the next block.
Merge until the enumeration is complete.

#### SPLIT — one block that spans two thoughts

**S1 — Objection + reply.** A block contains both an objection marker
(`ཅེ་ན།` / `ཞེ་ན།` / `སྙམ་ན།`) and a reply opener (`འོ་ན།`). Split between them.

**S2 — Terminal particle + new topic.** A block has a sentence-final marker
(`སོ། །` / `འོ། །` / `ནོ། །` / `དོ། །`) mid-block followed immediately by a new
ordinal opener (`དང་པོ་` / `གཉིས་པ་` / `གསུམ་པ་`) or a new subject. Split after
the terminal particle.

**S3 — Source attribution fused to quote.** A block opens with a source attribution
(`…ལས།` or `…གསུངས།`) fused directly to the quoted passage. Split after the
attribution so it stands alone.

---

### Procedure

**Step 1 — Resegment**

Confirm the input file has TOC headings embedded and no block IDs yet. Then run:

```
python3 4-SYSTEM/Skills/segment-commentary/scripts/resegment--block-resegmentation.py \
    "0-INBOX/temp/segmented/<file>.md" \
    --commentary-id <id>
```

The script processes all windows (resumable — re-run after interruption without
`--force` to pick up where it stopped). On completion it prints: block count
before → after, operations applied, any conflicts in the overlap zone, and the
integrity check result.

- If integrity check fails (`✗`): the output file is **not written**. Read the
  error, fix the staging JSON if needed, re-run with `--apply-only`.
- If overlap-zone conflicts are listed: edit the relevant `window-NNNN.json`
  staging file, then re-run with `--apply-only`.

**Step 2 — QC**

```
python3 4-SYSTEM/Skills/segment-commentary/scripts/qc_check--block-resegmentation.py \
    "0-INBOX/temp/resegmented/<id>.reseg.md"
```

Runs all four steps automatically: detect → LLM repair → re-check → write report.
The `.reseg.md` file is updated in place if real issues are found.
Review `0-INBOX/temp/resegmented/<id>.qc.md` for the `flags_before` / `flags_after` summary.

To run detection only without repair: add `--no-fix`.

**Step 3 — Human review**

Review `0-INBOX/temp/resegmented/<id>.ops.md` (main operations) and
`0-INBOX/temp/resegmented/<id>.qc.md` (QC corrections). On approval the file is ready.

---

### Rules

- **No character changes.** The script enforces `squeeze(input) == squeeze(output)`.
  If this assertion fails, the output is not written.
- **Headings are never touched.** A block starting with `#` is always KEEP.
- **Output stays in `0-INBOX/temp/`** until a domain specialist approves.
- **When in doubt, under-merge rather than over-merge.** A slightly fragmented block
  is safer than a wrongly merged one that spans two citable ideas.

---

## After this skill

Next is `add-block-ids`, then `verse-context` / `section-summary` /
`commentary-claims`, all of which cite those IDs.

Re-segmenting a commentary **after** anything cites it invalidates those citations —
block IDs shift. If a resegmentation is unavoidable, rebuild every downstream rail
that cites the file, and rebuild any `toc-generate` tree too: its `[[N]]` line
pointers are computed against exact file bytes and will all be wrong.
