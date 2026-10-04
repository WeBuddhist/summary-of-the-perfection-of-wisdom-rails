# Row-aligned Markdown exports — format and meaning

How a Dzongsar-style corpus looks once its Google Docs are downloaded as
Markdown and its metadata sheets as CSV, and how `md_rows` reads it. Written
from the Heart Sūtra corpus (2026-10-03); re-check against every new corpus.

---

## 1. The alignment documents

The team aligns two texts by keeping **two Google Docs whose paragraphs are one
auto-numbered list each**. Row *N* of one document is paired with row *N* of the
other. "Download → Markdown" turns each document into a numbered Markdown list:

```
12. རིགས་ཀྱི་བུ་གང་ལ་ལ་ … ཇི་ལྟར་བསླབ་པར་བྱ།␠␠
13.␠␠
14. ***verse line one***␠␠
   ***verse line two***␠␠
```

| What you see | What it means |
|---|---|
| `N.` at the start of a line | Row *N* — the alignment key. Rows run 1, 2, 3 … with no gaps. |
| An empty item (`13.` and nothing) | Row 13 has no text on this side: the other side's row 13 has no counterpart here. |
| Indented lines, or paragraphs after a blank line, before the next `N.` | Still row *N* (a verse, a split paragraph). |
| Text before `1.` | Row 0 — usually the document's own title line. No counterpart on the other side. |
| `␠␠` at a line end | Markdown hard break from the export. Not content. |
| `\[`, `\*`, … | Markdown escapes from the export. The text is `[`, `*`. |
| `*…*`, `**…**`, `***…***` | Italic / bold / bold-italic the team applied in the Doc (lemmas, verses, colophons). Not content: kept as emphasis spans in the sidecar. |
| `​` (zero-width space) | Present in the Docs; kept verbatim. |

**The numbers are row numbers, not root segment numbers.** Unlike the older
`.docx` corpora (where a number typed in front of a commentary paragraph names
the root segment it comments on — see `pecha-conventions.md`), here the pairing
is purely positional: row *N* ↔ row *N*.

## 2. The file set for one text

Renamed by the vault owner so the pairs are visible (Heart Sūtra example,
prefix `sherab-`):

| File | Role |
|---|---|
| `<p>-root-bo(display).md` | **The display segmentation** of the Tibetan: the one Tibetan text the library stores. |
| `<p>-root-sa(bo-sa).md` + `<p>-root-bo(bo-sa).md` | Sanskrit ↔ Tibetan pair (here the Tibetan side is byte-identical to the display). |
| `<p>-root-zh(bo-zh).md` + `<p>-root-bo(bo-zh).md` | Chinese ↔ Tibetan pair; the Tibetan side is cut its own way (and may be another edition). |
| `<p>-comm-N(root-com).md` + `<p>-root-N(root-com).md` | Commentary *N* ↔ the root text as **that commentary's aligners** cut it. Every commentary has its own cut of the root. |
| `<p>-comm-N(toc).md` | Optional "TOC" doc for commentary *N*: the commentary again, as plain paragraphs. **Check it**: some carry numbered heading labels (`༥༽ …`), some carry only old alignment numbers and bold lemmas — the Docs' colour-coded *sa bcad* does not survive a Markdown export. |
| `<p>-comm-N.csv`, `<p>-root.csv` | Metadata sheet: rows `field,BO,EN[,ZH]` under an `Entries,…` header (an emoji banner row may precede it). |

## 3. What a reader must decide per corpus

1. **Which segmentation is stored.** Exactly one cut per text goes into the
   library (here: `root-bo(display)`). Every other cut of the same text is a
   *copy*; nothing of it is stored except, in the sidecar, as evidence.
2. **Which way the translation relation runs.** Here the Sanskrit is the root and
   the Tibetan its translation; the Chinese and the commentaries were aligned to
   Tibetan, so they point at the Tibetan — never past it.
3. **Whether the copies are the same text.** Compare letters (`concordance.py`
   prints the statistics). Same text with a few readings apart: fine, the diff
   carries the alignment across. A different edition: still fine, the variants
   are recorded per row. Letters that cannot be placed: stop and look.
4. **Whether a row pairing is wrong.** Read the pairs of short texts in full.
   Fix only what a human decides (`pair_corrections`, `text_corrections` in the
   manifest, with reason, who, when). Never re-pair silently.
5. **Where the headings come from**: a TOC doc's labels (`toc.kind: labels`), a
   `toc-generate` tree (`toc.kind: tree`), a commentary's outline projected onto
   a root and its translations (`toc.kind: projected`), or none (`toc.kind:
   none` with the reason). The TOC comes *before* ids and transclusions — ids
   are derived from the sections.

## 4. How the alignment is carried onto the stored segmentation

`concordance.py`. Both sides are reduced to letters (whitespace, shad, tsheg,
danda and other punctuation dropped) and diffed. Each letter of a copy row votes
for the stored segment its matched letter belongs to; a row transcludes every
stored segment it has at least `min_overlap` (default 3) letters in. Neither
segmentation changes:

- a row smaller than a stored segment → several consecutive rows transclude the
  same segment (each keeps its exact character span in the sidecar);
- a row larger than a stored segment → the row transcludes 2–3 whole segments;
- a reading present in one edition only → recorded as a variant of that row; the
  rows after it are unaffected (the diff resynchronises immediately);
- a row whose counterpart is empty → no transclusion.

## 5. Checks that must pass (`verify.py`)

- `missing=0`: every letter of the source rows is in the output (headings moved
  out of rows count; human text corrections are applied first).
- `rows=…` equals the number of blocks (plus rows that were only a TOC label):
  every row is exactly one block — nothing merged, split or lost.
- `aligned_ok=n/n`: every block transcludes exactly what its row pairing gives.
- `content_ok=n/n`: independently, each paired row's letters are found in the
  segments it transcludes (≥ 50 %; 50–90 % rows are listed as edition variants
  for review).
