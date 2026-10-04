---
name: aligned-corpus-intake
description: >
  Turn a human-made, human-segmented and human-aligned corpus — OpenPecha API
  downloads and Dzongsar-style Google-Docs exports (.docx Tsadel/Tsadrel
  line-parallel alignments, sentence segmentations, citation and sa-bcad TOC
  docs, numbered alignment references, metadata sheets; or the same Docs
  downloaded as Markdown row-for-row pairs with CSV metadata) — into vault source
  files in 1-SOURCES/ that the WeBuddhist library linter/parser publishes:
  root texts, aligned translations and commentaries with headings, block ids
  and transclusions, plus a lossless sidecar of every annotation layer.
  Use it when the user says: "parse the raw data", "ingest these docs",
  "convert the docx alignments", "bring the commentaries and translations into
  sources", "make these ready for the webuddhist library", "import the
  OpenPecha download", "keep all the human segmentation and alignment",
  "I downloaded the docs as .md and the sheets as .csv", "map each
  commentary's alignment onto the display segmentation".
profile: rails-vault
---

# aligned-corpus-intake

Converts a corpus whose segmentation, alignment, headings and citations were made **by people** into `1-SOURCES/` files without losing any of that work. A manifest names every work and the raw files that supply its text, segmentation, headings and alignment; adapters read them; a writer emits the vault markdown the publication tools read (`translation-upload`'s linter and parser), and a sidecar JSON per file keeps everything markdown cannot carry. A verifier then proves that every letter of every source reached the output, and that structure and transclusions are sound.

**The numbers are the alignment.** In these corpora a number written in front of a commentary segment (`14`, `1-3`, `198,199,201`, `12.`, `4-12.`) *is* the id of the root segment(s) it comments on. So the root file must be keyed by exactly the numbering the commentaries cite — find the numbered copy of the root they were aligned against and make its numbers the block ids — and each number is then transcluded as written: `1-3` → `^1 ^2 ^3`. A segment with no number has no alignment and gets no transclusion. Never re-map the numbers onto a different segmentation of the root; record other segmentations in the sidecar instead.

The failure it prevents: a converter that "cleans" human annotation away — dropping a row it cannot place, flattening a six-level *sa bcad* tree, discarding colour-coded citations or reviewer comments, or inventing an alignment the humans never made.

---

## Inputs

| Input | Where | Notes |
|---|---|---|
| Raw data | `0-INBOX/raw-data/` | Verbatim downloads, never edited. An inventory note in `0-INBOX/` per source helps. |
| Manifest | `0-INBOX/raw-data/intake-manifest.yaml` | One entry per work. Start from `templates/manifest.example.yaml`. Every frontmatter value comes from the raw data; empty means "not recorded". |
| Format legend | `references/pecha-conventions.md` | What each document kind, colour, number style and OpenPecha annotation means. Re-check per document. |
| Python 3 with `PyYAML` and `openpyxl` | — | The docx reader is stdlib only. |

If the corpus has a document kind or colour the reference does not describe, stop and characterise it first (see Procedure step 2) — never guess a legend.

## Output

| Path | What |
|---|---|
| `1-SOURCES/Text/<lang>-<slug>.md` | Root text(s) |
| `1-SOURCES/Translations/<lang>-<slug>.md` | Translations / parallel versions, aligned by transclusion |
| `1-SOURCES/Commentaries/<lang>-<slug>.md` | Commentaries, aligned by transclusion |
| `1-SOURCES/Annotations/<stem>.annotations.json` | Lossless sidecar per file (declared in the vault annex as a typed folder) |
| `0-INBOX/<corpus>-intake-report.md` | Counts, review items, unplaced rows, verifier output |

---

## Output file format

```markdown
---
title: <source-language title>
alt_titles: [...]
author: <name> [bdrc:P…]            # ids only where the source gives them
translator: ...
language: Tibetan
lang_tag: bo
file_type: root-text | translation | commentary
root_text: 1-SOURCES/Text/bo-<slug>.md     # translations and commentaries
registered_id: <short-id>                  # commentaries; registered in the annex
verse_id_format: verse | section-paragraph
category_id:                                # WeBuddhist category — chosen by a human
license: public | unknown | …
source: <URL of the doc / edition used>
bdrc_work_id / cbeta_id / other_ids: ...
source_description: "..."
related_translations: [...]                 # on whatever others derive from
related_commentaries: [...]
covers_verses: <first>–<last>               # on derived files
text_id: / edition_id: / toc_id:            # filled by the upload skill
raw_sources: [{file, sha1}, ...]            # every raw file read
intake: {skill, adapter, date, annotations: <sidecar path>}
---

# <title> ^0

## 1. <heading text exactly as in the source> ^1-0

### 1.1. <sub-heading> ^1-1-0

![[1-SOURCES/Text/bo-<slug>.md#^2]]
![[1-SOURCES/Text/bo-<slug>.md#^3]]

<block text, verbatim> ^1-2
```

Ids follow `4-SYSTEM/Guidelines/annotation-conventions.md`:
- **flat** (`id_scheme: flat`): `^N` = the human segment number, so a block id *is* the number the commentaries write. Translations aligned row-for-row keep the root's id (identity alignment, which `translation-upload` requires).
- **h2** (`id_scheme: h2`): headings carry their full outline path (`^3-4-2-6-7-7-0`; seven or more levels keep `######` and a bold title); body blocks are `^<top-level>-<n>`, counted through deeper headings, so content ids never exceed the parser's three parts.

Sidecar (`<stem>.annotations.json`): `blocks.<id>` → `source` (raw doc, paragraph, line, rows, typed prefix, refs), `role` (lemma/body), `annotations` (every formatted run with offsets and legend meaning; projected variant readings), `comments` (Word comments with author and date), `overlays` (secondary alignments); plus `headings`, `legend`, `notes`, `ref_map` (the reference-numbering concordance), `raw_alignment` / `tsadrel` (row-level pairs), `excluded_paragraphs` (with reason).

---

## Rules

1. **Never alter wording on your own.** Adapters may only split at paragraph/line boundaries the source has, trim a line's outer whitespace, and move a typed alignment prefix or an excluded paragraph into the sidecar (with its reason). The one exception is a correction a human has decided on, written in the manifest (`text_corrections` for text, `ref_corrections` for a mistyped alignment number) with its reason; the original stays in the sidecar. A block that would start with `#` or `![[` stops the build for a human decision.
2. **Never drop a row.** A row whose counterpart cannot be located is kept with the preceding block and flagged; an unplaceable overlay item is counted in the report. `verify.py` must report `missing=0` for every work.
3. **Never invent alignment.** Transclusions come only from a human alignment (the written numbers, row pairing, an upstream alignment annotation). A paragraph holding only a number applies it to the next segment. A number that names no root segment (a typo such as `189190`) gets no transclusion and goes in the report until a human decides how to read it (`ref_corrections`). Where one translation segment renders two root segments and the text cannot be split, it transcludes both. Use `refs: candidate` only if the numbers demonstrably do not refer to the root (check them against the root text first).
4. **Reproduce human errors, flag them.** A pairing that drifts, a typo'd reference (`189190`), a misfiled document: keep as made, set `alignment_status: needs-review` where it matters, list it in the report. Do not fix the human layer silently.
5. **One primary layer per file, the rest in the sidecar.** The most complete human layer drives the markdown; older or parallel layers (another alignment, an upstream copy, variant readings, formatting from another version) are overlays.
6. **`1-SOURCES/` is written only by this skill's build, whole files at a time,** from raw data in `0-INBOX/raw-data/`. Raw files are never modified. Re-running the build regenerates the files; once anything cites them, re-segmenting is a migration (annex log) — rebuild downstream rails.
7. **Metadata only from the source.** Author/translator ids from OpenPecha `text.json` or the catalogue; cell text, not hyperlinks; never the known-shifted columns (see the reference). `category_id` is left empty for a human.
8. **Commentary `registered_id`s are registered in the vault annex** before or with the build; the annex also declares `1-SOURCES/Annotations/` as a typed folder.
9. **Publication is a separate, confirmed step** (`translation-upload`). This skill never calls the library API to write.

---

## Procedure

1. **Inventory.** List the raw data (one inventory note per source in `0-INBOX/`). Group `.docx` files by content hash (copies abound) and pick one representative each.
2. **Characterise every unique document.** `python3 scripts/docx_model.py <file.docx>` shows runs with colours/bold/italic and Word comments; `--json` dumps the full model. For an OpenPecha text, `python3 scripts/openpecha_model.py <root> <text_id>`. Decide per document: its kind (§2a of the reference), its colour legend, its number style, and which doc is the most complete layer. For line-parallel pairs, check the rows line up at the start, middle and end.
3. **Find the identities.** The same work often arrives several times (an OpenPecha instance, a Google Doc, a printed edition). `scripts/project.py`'s `Projector(a, b).stats` shows whether two versions share their letters; if they do, the other version's layers become overlays.
4. **Pick the root numbering.** For every commentary, take a few numbered paragraphs and compare them with the root segment of that number in each candidate root doc (typed `N.` numbers or Word list numbers). The root doc whose segment N is what the paragraphs numbered N comment on is the root to build (`adapter: numbered`, `number_source: typed | auto`); other splits of the same text go under `alt_segmentations`.
5. **Write the manifest** in build order: roots first, then what aligns to them. Fill frontmatter from the metadata sheets and `text.json`. Record each document's legend and `notes` for the reviewer.
6. **Register** new `registered_id`s and the `Annotations/` folder in `4-SYSTEM/Guidelines/vault-annex.md`.
7. **Test build** outside the vault:
   `python3 scripts/build_sources.py 0-INBOX/raw-data/intake-manifest.yaml --out <scratch> --report <scratch>/report.json`
   then `python3 scripts/verify.py 0-INBOX/raw-data/intake-manifest.yaml --root <scratch>`.
   Fix the manifest (not the output) until every work is `OK` with `missing=0`. Then confirm, per commentary, that every numbered block's transclusions equal its written number(s) and every unnumbered block has none. Read every `unmapped_*`, `unresolved_refs`, `inferred_by_position`, overlay `unplaced` and tsadrel-agreement figure in the report.
7. **Publication dry run on a copy.** Run `translation-upload`'s `linter-root-text/lint_text_input.py` and `parser-root-text/parser.py` on a scratch copy (the linter edits files in place and both write into their own folder). Expect only: empty `category_id`, missing alt titles, contributors without ids.
9. **Build into the vault:** the same command without `--out`, then `verify.py` again on the vault.
10. **Report** in `0-INBOX/<corpus>-intake-report.md`: the works table, every review item, what was not ingested and why, and the verifier output. Hand the review items to the human.

---

## Route B — Markdown/CSV exports of row-aligned Docs (`adapter: md_rows`)

Use this route when the Google Docs arrive as **Markdown** (`Download → Markdown`) and the metadata sheets as **CSV**: every alignment doc is a numbered list, and **row N of one doc is paired with row N of the other** (`references/md-export-format.md`). There are no typed alignment numbers and no colours; the pairing is positional. Worked example: the Heart Sūtra intake of 2026-10-03 (`0-INBOX/raw-data/intake-manifest.yaml`, `0-INBOX/heart-sutra-intake-report.md`, and the how-to guide `4-SYSTEM/How-to guides/Ingest a row-aligned corpus.md`).

**The problem it solves.** Each human alignment was made against its *own copy* of the root text, cut into rows its own way (one cut per commentary, another for each translation). The library stores **one** root text with **one** segmentation. Every alignment must reach that segmentation without changing any segmentation — the stored root's, the commentary's, or the translation's.

**How.** `scripts/concordance.py` diffs the letters of each copy against the stored root (punctuation and spacing ignored) and lets every letter of a copy row vote for the stored segment it lands in. A commentary row then transcludes the stored segments its paired copy row falls in. Rows are never merged or split: a row smaller than a stored segment shares that segment with its neighbours; a row larger than one transcludes two or three whole segments; an edition variant (a word present on one side only) is recorded and does not shift anything after it; a row whose counterpart is empty transcludes nothing.

### B-Procedure

1. **Inventory and read the pairs.** For each pair, check the two files have the same row count and that rows line up at the start, middle and end (`python3 scripts/md_export.py <file.md>` lists rows). Decide: which cut is the **stored** segmentation of each text; which way each translation relation runs (the source language is the root; texts aligned to a translation point at that translation, never past it); which files are copies of the same text (`Concordance(...).stats` — letters matched, copy-only, target-only).
2. **Read every short pair in full** (root ↔ translation) and list rows whose pairing looks wrong. Only a human decides a fix; record it as `pair_corrections` (re-pairing) or `text_corrections` (a stray character) **with reason, who, and date**. The original pairing stays in the sidecar.
3. **Metadata.** From the CSV sheets (`md_export.py <file.csv> --meta`); ids not in the sheets may come from an earlier intake of a letter-identical document (say so in `source_description`). `category_id` stays empty for a human.
4. **Write the manifest** in dependency order: the root, its translation(s), then everything aligned to them. Each work: `text` (its own rows), `pair` (`own_side`, `target_side`), `target`, `title`, `frontmatter`, and `toc`. Template: `templates/manifest.example.yaml` (md_rows entries).
5. **TOC first — ids come from it.** Content ids are derived from the sections (`h2`: `^<top-level>-<n>`), so headings must exist before ids and transclusions are written:
   - `toc.kind: labels` — a TOC doc gives heading labels (e.g. `༥༽ …`). List them **verbatim, in order**; the build finds each in the doc, projects it onto the commentary, moves an in-row label out of its row into the heading, and places it at a row boundary.
   - `toc.kind: tree` — no TOC doc: run `toc-generate` (below).
   - `toc.kind: none` (with `reason`) — no outline exists; every block is section 0.
   - `toc.kind: projected` (with `source_work: <commentary key>`) — for a **root text and its translations** when the root has no outline of its own: the commentary's TOC is carried onto the stored root through the commentary's own row alignment (a heading stands before the first root segment its section comments on), and from there onto each translation, or onto the text the root translates, through that pair's row alignment. A node that reaches no segment of a file gets no heading there (listed in the sidecar). Choose the outline by projecting every commentary's and keeping the one that covers the root from title to colophon with nodes on distinct segments, in order; record why in the manifest.
   - `toc.kind: outline` (with `file: 2-RAILS/Sections/Raw/toc-wikisource/<id>.md`) — an outline taken from outside the corpus (a Wikisource Index page's table of contents, or a Wikipedia article, via `wiki-toc-import`), placed at rows of one work (`placed_on`). That work takes the headings at the placed rows; every work paired with it by rows takes them through the same projection as `projected`, each with the label in its own `lang_tag`. The build refuses an outline whose `placed_on_sha1` no longer matches the raw text. Preferred over `projected` for a root text: a commentary's *sa bcad* is usually far too granular for the root.
     Two human-decided manifest fields serve it: `row_splits` (`row`, `at: [clause…]`, `targets: [[i…]…]`, reason, decided_by, date) cuts a row before each verbatim clause so a heading can stand inside it — every letter stays, each part keeps the row number, and each part shows the listed share of the row's transclusions; outline nodes address part k as `start_row: "N.k"`. `supplement_rows` (`row` after the last raw row, `text`, `source`, reason, decided_by, date) adds text the corpus lacks from another human source, with its provenance in the block's sidecar entry. `merge_rows: {mode: by_target, joiner, reason, decided_by, date}` joins consecutive rows that transclude exactly the same target segments into one block — for a translation cut much finer than the text it translates (each row and its alignment stay in `source.merged_rows`). `verify.py` accepts declared splits and merges and counts supplement letters as source.
   - `id_scheme: flat` (no TOC): id = the human row number (gaps where a row is empty on this side). Use only if the vault owner wants no TOC on a text.
6. **toc-generate on row-segmented text.** Headings may only fall *between* rows, and `toc-generate`'s tree prompts emit no line pointers, so:
   1. `python3 scripts/build_sources.py <manifest> --stage pre-toc` writes `0-INBOX/temp/TOC-<id>/source.md` (`# title` + one paragraph per row, no frontmatter, so metadata edits never shift a line) and `source.json` (sha1, line → row).
   2. Run `toc-generate` Phases 0–C on that file exactly as its SKILL.md says (chunk; isolated subagents per chunk for A and B — tell them to read with `sed`, the rows are single very long lines; `python3 scripts/toc_rows.py merge <id>`; one tree subagent). Then `qc_check_tree.py` on the tree (before it carries pointers — that checker does not strip `[[N]]`).
   3. **Placement** — one isolated subagent with `prompts/place-toc-at-rows.md` writes `0-INBOX/temp/TOC-<id>/placement.md` (tree + `[[line]]` + a TSV of opening clauses); `python3 scripts/toc_rows.py place <id>` checks the tree is otherwise unchanged and installs the pointers.
   4. `qc_tree_vs_source.py` against `source.md`. Expected at row granularity, and **not** errors once checked: several headings sharing one row (a row announcing a chain, or several sections opening inside one long row), a section opening on a bare ordinal (`གཉིས་པ་ནི།`) whose title is only in the parent's enumeration, a title attested only in a closing formula. Check every flag against the source; record the check (evidence lines) at the end of the QC report with `issues_after_review: 0`. Anything else goes to a repair round (`pass4-qc-repair.md`, isolated), then placement again if the tree changed. A part the author announces but never opens is removed from the tree and reported, never given an invented position.
   5. `python3 scripts/toc_rows.py promote <id> <work-key> [--accept]` writes `2-RAILS/Sections/Raw/toc-tree/<id>.md` with `pointer_source_sha1` and the placement table, and moves the evidence next to it. The build refuses a tree whose sha1 no longer matches the pre-TOC text (rebuild the tree instead).
   6. The build performs Phase E: each heading goes before the row its pointer names (ids `^<path>-0`, a title-only root node excluded).
   A commentary whose scans find no division announcement of its own (Phase B empty; Phase A at most a doctrinal list) gets `toc.kind: none` with that reason — a tree built from a doctrinal list would title the rest of the text with its last item.
7. **Test build, verify, dry-run** exactly as steps 7–8 of the procedure above. `verify.py` adds, per md_rows work: `rows=` (every row with letters is exactly one block), `aligned_ok=` (transclusions equal the row pairing), `content_ok=` (the paired row's letters are really in the transcluded segments; 50–90 % rows listed as edition variants).
8. **Build into the vault, verify again, register, report** (steps 6, 9, 10 above).

**What the sidecar keeps per block** (`1-SOURCES/Annotations/<stem>.annotations.json`): the row number and raw export text, every emphasis span, the paired row's text, every target with the number of letters and character span it covers, the variants between the two editions, dropped boundary overlaps, any human correction with the original pairing, and for headings the label's source line and where inside a row it really fell.

---

## Completion check

- [ ] In every commentary, each numbered block transcludes exactly the root ids its number names; unnumbered blocks transclude nothing; numbers that name no root segment are listed as review items
- [ ] Every unique raw document is either in the manifest (as a work, an overlay, a ref map or `extra_raw`) or listed in the report as not ingested, with the reason
- [ ] `verify.py` prints `OK` and `missing=0` for every work, on the vault
- [ ] The publication linter reports no errors other than the empty `category_id`; the parser builds text, edition, TOC and alignment payloads for every file
- [ ] Translations meant for `translation-upload` show `identity_alignment: true` in the report
- [ ] Every review item (drift, typo'd reference, candidate refs, inferred refs, misfiled docs) is in the report
- [ ] New `registered_id`s and the `Annotations/` folder are in the vault annex
- [ ] Nothing under `0-INBOX/raw-data/` changed
- [ ] Route B: every md_rows work shows `rows` = blocks (+ label-only rows), `aligned_ok n/n`, `content_ok n/n`; every heading sits between rows; every `pair_correction`/`text_correction` carries reason, who and date; every commentary's `toc` is `labels`, a QC-clean `tree`, or `none` with a reason
