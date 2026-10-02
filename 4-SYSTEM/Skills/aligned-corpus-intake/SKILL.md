---
name: aligned-corpus-intake
description: >
  Turn a human-made, human-segmented and human-aligned corpus — OpenPecha API
  downloads and Dzongsar-style Google-Docs exports (.docx Tsadel/Tsadrel
  line-parallel alignments, sentence segmentations, citation and sa-bcad TOC
  docs, numbered alignment references, metadata sheets) — into vault source
  files in 1-SOURCES/ that the WeBuddhist library linter/parser publishes:
  root texts, aligned translations and commentaries with headings, block ids
  and transclusions, plus a lossless sidecar of every annotation layer.
  Use it when the user says: "parse the raw data", "ingest these docs",
  "convert the docx alignments", "bring the commentaries and translations into
  sources", "make these ready for the webuddhist library", "import the
  OpenPecha download", "keep all the human segmentation and alignment".
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

## Completion check

- [ ] In every commentary, each numbered block transcludes exactly the root ids its number names; unnumbered blocks transclude nothing; numbers that name no root segment are listed as review items
- [ ] Every unique raw document is either in the manifest (as a work, an overlay, a ref map or `extra_raw`) or listed in the report as not ingested, with the reason
- [ ] `verify.py` prints `OK` and `missing=0` for every work, on the vault
- [ ] The publication linter reports no errors other than the empty `category_id`; the parser builds text, edition, TOC and alignment payloads for every file
- [ ] Translations meant for `translation-upload` show `identity_alignment: true` in the report
- [ ] Every review item (drift, typo'd reference, candidate refs, inferred refs, misfiled docs) is in the report
- [ ] New `registered_id`s and the `Annotations/` folder are in the vault annex
- [ ] Nothing under `0-INBOX/raw-data/` changed
