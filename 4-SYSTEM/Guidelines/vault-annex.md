# Vault Annex — summary-of-the-perfection-of-wisdom conventions

The methodology guidelines (`0-VAULT-Structure.md`, `../../1-SOURCES/About Sources.md`, `../../2-RAILS/About Rails.md`, `../../3-TRANSFORMATIONS/About Transformations.md`) are **text-agnostic** — they apply to any Railroads vault built on any classical text. This annex records the conventions that are specific to *this* vault: **the Verse Summary of the Perfection of Wisdom — ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པ། / रत्नगुणसंचयगाथा (Ratnaguṇasañcayagāthā, "Phakpa Düpa")**.

When the Guidelines and this annex disagree on a vault-specific detail, this annex wins — **for the points it actually states**. Everything it does not state follows the defaults unchanged.

Sections 1–3 and 7 were filled at the first intake of the corpus (2026-10-03, `aligned-corpus-intake` Route B, following the hand-off from `heart-sutra-rails` and its standing decisions D1–D13); the intake report is `0-INBOX/phakpadoepa-intake-report.md` and the review brief for the text expert `0-INBOX/review-brief.md`.

---

## 1. The text

This vault serves **the Ratnaguṇasañcayagāthā** — the verse summary of the Perfection of Wisdom in Eight Thousand Lines — in its Sanskrit text, its Tibetan translation, a Chinese translation aligned to the Tibetan, and six Tibetan commentaries — four segmented and aligned by hand by the Dzongsar team, two taken from Wikisource without alignment (§3).

| Order | Text | Role | File |
| ----- | ---- | ---- | ---- |
| 1 | रत्नगुणसंचयगाथा | **Root** (Sanskrit) | `1-SOURCES/Text/sa-ratnagunasancayagatha.md` |
| 2 | ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པ། | Translation of 1 — **the stored Tibetan text** (the "display" segmentation) | `1-SOURCES/Translations/bo-ratnagunasancayagatha.md` |
| 3 | 佛母寶德藏般若波羅蜜經 | Translation, aligned to 2 | `1-SOURCES/Translations/zh-ratnagunasancayagatha.md` |

**Direction of every relation (D1).** The Sanskrit is the root and the Tibetan its translation. Everything the humans aligned to the Tibetan — the Chinese and every commentary — points at the Tibetan file (`root_text:` and every transclusion). Nothing is re-pointed to the Sanskrit.

**One segmentation per text (D2).** Each text is stored once, cut as its display doc cuts it. Every other cut of the root in the raw data (each commentary's own copy) is carried onto the stored segmentation by letters (`4-SYSTEM/Skills/aligned-corpus-intake/scripts/concordance.py`) and kept only as evidence in the sidecars.

---

## 2. Addressing scheme

**`verse_id_format`:** `section-paragraph` for every file. **Format example:** `^4-12` (block 12 of top-level section 4); headings `^<decimal path>-0`, e.g. `^3-1-2-1-1-8-0`.

Ids are **dictated by the table of contents**, applied before any id or transclusion is written (D3):

| Markdown | Role | Anchor |
| -------- | ---- | ------ |
| `#` | The title | `^0` |
| `##` … `######` | TOC node, depth 1 … | `^<decimal-path>-0` (full path, no cap; depth ≥ 6 keeps `######` and a bold title) |
| body block | One human alignment row (or one part of a split row) | `^<top-level>-<n>` — n counts the blocks under the current top-level heading, through deeper headings |
| body block before the first heading | — | `^0-<n>` |

### Root and translations

The root has no outline of its own and the Dzongsar data has no TOC for it. Its TOC is the **དཀར་ཆག of the Derge Kangyur text on Wikisource** (transclusion page revision 1352701; Index:ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པ།.pdf, revision 1216723): ཀླད་ཀྱི་དོན། (node **0**) and the eight སྐབས་ (nodes **1–8**, numbered as the topics are) — `2-RAILS/Sections/Raw/toc-wikisource/ratnagunasancayagatha.md`. The Index's proofread pages carry no inline headings; each node stands where its `<section>` (part1–part9) begins on the pages, found by letters in the display Tibetan, and is carried onto the Sanskrit and Chinese through their row pairings. Headings are in each file's own language: Tibetan verbatim; Sanskrit and Chinese editorial renderings in each text's vocabulary (D4/D5). The document's own title line precedes node 0 (`^0-1`).

### Commentaries

Where each commentary's TOC comes from (D6) is recorded in the manifest and in §3: its Wikisource Index page (Rangjung Dorje, Mipham — `2-RAILS/Sections/Raw/toc-wikisource/<id>.md`) or the Dzongsar TOC doc's own decimal-numbered labels (Shāsana Dhīpaṃ, Khenrab Jamyang — `toc.kind: labels`, `numbered: true`).

### Verse numbering rule

Not applicable as such: the root's verses are not numbered in the Tibetan display text. Ids follow the alignment rows within the eight topics (root, translations) or the TOC sections (commentaries); the row number of every block stays in its sidecar entry (`source.row`).

### ⚑ Registered deviations — overrides of the default conventions

#### ⚑ Root and translation TOC taken from the Wikisource dkar chag — overrides `annotation-conventions.md` §1–§2 (registered 2026-10-03)

Files: the three files in §1. The default gives a root text the headings of its own structure. Here the headings are the Derge edition's table of contents on Wikisource, placed at its `<section>` tags, and the Sanskrit and Chinese headings are editorial renderings. **Why:** standing decision D4 of the vault owner (carried over from `heart-sutra-rails`); the vault owner confirmed on 2026-10-03 that the dkar chag be used, as the Index has no inline headings. Node 0 (ཀླད་ཀྱི་དོན།) takes the reserved `0` slot so that node numbers equal the topic numbers (སྐབས་དང་པོ = `^1-0`).

#### ⚑ Alignment rows split where a heading falls inside them — overrides the intake's one-row-one-block rule (registered 2026-10-03)

Files: `bo-ratnagunasancayagatha.md` (1 row), `bo-rangjung-dorje-tika.md` (90 rows), `bo-mipham-lekshe.md` (141 rows), `bo-shasana-dibam-bedon-dronme.md` (24 rows), `bo-khenrab-jamyang-norbu-dronme.md` (32 rows). Each row is cut before a verbatim clause where its TOC source puts a heading (Wikisource page position, or the TOC doc's label position when it lies 15 or more letters inside the row). Every letter stays; each part keeps its row number in the sidecar; each root segment the row transcludes is shown once, with the first part that quotes it. **Why:** standing decision D7 (manifest `row_splits`).

#### ⚑ Text added to Mipham's commentary from the Wikisource manuscript — overrides `About Sources.md` (one source per file) (registered 2026-10-03)

File: `1-SOURCES/Commentaries/bo-mipham-lekshe.md`, row 209. The Dzongsar text lacks the opening of TOC section 1.3.2.2.1.1.3.5 and the body of 1.3.2.2.1.1.3.5.1 (a copying gap); the missing passage is added verbatim from Page …ལག་བྲིས་དབུ་ཅན།.pdf/182 (revision 1247289). **Why:** standing decision D8. Written as a `text_correction` of row 209 (supplement rows can only follow the last row); provenance in the manifest and the block's sidecar entry (`source.corrections`).

#### ⚑ Commentary `##` labels come from the TOC, not from a hand-written label — overrides `annotation-conventions.md` §3 (registered 2026-10-03)

Files: `1-SOURCES/Commentaries/*.md`. The heading's path is the Wikisource heading's number or the TOC doc label's own decimal number (numbering slips corrected for the expert to check: 71 + 8 in the TOC docs, manifest `toc.path_corrections`; 3 + 14 in the Wikisource Index TOCs, the outline files' `path_corrections`, with each source number kept as `path_in_source`; one level the Mipham Index skips is kept as numbered). **Why:** D3 — segment ids are dictated by the TOC sections, whose numbering is attested.

#### ⚑ Blocks before the first heading are section 0 without a `## 0` heading — overrides `add-block-ids` Mode 1 rule 6 (registered 2026-10-03)

Files: `1-SOURCES/Commentaries/*.md`. A commentary's title line and opening verses precede its first TOC node and take `^0-1`, `^0-2`, … under the `#` title rather than an invented `## 0` heading. (In the root and translations section 0 is a real TOC node, ཀླད་ཀྱི་དོན།, and the title line before it is `^0-1`.)

#### ⚑ Square brackets removed from source texts (registered 2026-10-03)

Files: `sa-ratnagunasancayagatha.md` (the Sanskrit edition's bracketed chapter titles, restorations and praśasti labels — 41 brackets) and `bo-rangjung-dorje-tika.md` (one bracketed Sanskrit word, row 8). The words are kept, the brackets removed, because Obsidian renders bracketed text like link syntax (D10, `text_corrections`; originals in the sidecar).

#### ⚑ Sanskrit verse numbers removed from the text — overrides `About Sources.md` (verbatim text) (registered 2026-10-04)

File: `1-SOURCES/Text/sa-ratnagunasancayagatha.md`. The edition's `॥ १,१ ॥` numbers (chapter, verse of the edition's 32 chapters; 301 of them, plus `॥ ४. ५ ॥` and the praśasti numbers `ह्प्र्`/`ल्प्र्`) are the modern editor's numbering of Vaidya's edition (GRETIL marks the same numbering, `Rgs_1.1`, as added in digitisation), not root text, and follow a different division from this file's TOC. Each is replaced by the verse-end `॥` and kept as metadata: the manifest's `text_corrections` and the block's sidecar entry (`source.corrections[].verse`, e.g. `12.4`). **Why:** the vault owner's decision of 2026-10-04 ("Remove, keep as metadata").

#### ⚑ One verse line per line in the root and translations (registered 2026-10-04)

Files: the three files in §1. Each block is one alignment row (in the verses, one verse) shown as its verse lines, under one block id: the Tibetan breaks after each line's shad pair (། །); the Sanskrit at the pāda boundaries of the DSBC Devanāgarī edition (book 402, copy in `0-INBOX/raw-data/dsbc-ratnagunasancayagatha/`), the edition itself marking only the half-verse; the Chinese at its seven-character phrases. Letters are unchanged; ids are unchanged. **Why:** the vault owner's instruction of 2026-10-04 (manifest `line_breaks`).

### Re-segmentation and ID-migration log

**2026-10-04 — formatting and two commentaries added; no id changed.** The Sanskrit verse numbers were removed and verse line breaks added to the root and translations (see the deviations above); every block keeps its id. Two commentaries were added from Wikisource (§3). Earlier the same intake (2026-10-03 → 04) corrected 17 Wikisource heading numbers in the Rangjung Dorje and Mipham outlines before anything cited them.

**2026-10-03 — first intake.** No migration: `1-SOURCES/` was empty and nothing in `2-RAILS/` or `3-TRANSFORMATIONS/` cited a source id. An earlier docx/OpenPecha-based raw-data set was removed from `0-INBOX/raw-data/` by the vault owner before this intake (it remains in git history).

---

## 2a. Canonical spine slots — *not yet defined*

The claims pipeline has not been run in this vault. When it is, register the spine here first.

---

## 3. Registered commentary IDs

Every commentary file in `1-SOURCES/Commentaries/` declares a `registered_id` in its frontmatter. That short ID is the only string used to attribute claims to the commentary throughout `2-RAILS/`. Once assigned, a `registered_id` never changes.

| `registered_id` | Author / Title | School or tradition | Language | TOC source | File |
| --------------- | -------------- | ------------------- | -------- | ---------- | ---- |
| `rangjung-dorje-tika` | *(author left empty — see below)* — འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པའི་ཊཱི་ཀ་ཡིད་བཞིན་གྱི་ནོར་བུ་རིན་པོ་ཆེ་ལྟ་བུ་ཕ་རོལ་ཏུ་ཕྱིན་པ་རྒྱ་མཚོའི་སྡེ། | — | Tibetan | Wikisource Index TOC (ལྕགས་པར།, Lhasa 2013; revision 1132973) — 317 nodes | `1-SOURCES/Commentaries/bo-rangjung-dorje-tika.md` |
| `mipham-lekshe` | འཇུ་མི་ཕམ། — ཡོན་ཏན་རིན་ཆེན་སྡུད་པའི་འགྲེལ་པ་རྒྱལ་བའི་ཡུམ་གྱི་དགོངས་དོན་ལ་ཕྱིན་ཅི་མ་ལོག་པར་འཇུག་པའི་ལེགས་བཤད། | — | Tibetan | Wikisource Index TOC (dbu can manuscript; revision 1132490) — 453 nodes | `1-SOURCES/Commentaries/bo-mipham-lekshe.md` |
| `shasana-dibam-bedon-dronme` | ཤཱ་ས་ན་དཱི་བཾ། — འཕགས་པ་མདོ་སྡུད་པའི་འགྲེལ་པ་རྒྱས་པ་སྦས་དོན་གསལ་བའི་སྒྲོན་མེ། | — | Tibetan | Dzongsar TOC doc labels, numbered (140) | `1-SOURCES/Commentaries/bo-shasana-dibam-bedon-dronme.md` |
| `khenrab-jamyang-norbu-dronme` | མཁྱེན་རབ་འཇམ་དབྱངས་བློ་བཟང་འཕྲིན་ལས། — ཡོན་ཏན་རིན་པོ་ཆེ་སྡུད་པ་ཚིགས་སུ་བཅད་པའི་འགྲེལ་པ་ཟབ་མོ་རྟེན་འབྱུང་གི་དེ་ཁོ་ན་ཉིད་གསལ་བར་བྱེད་པའི་ནོར་བུའི་སྒྲོན་མེ་སྐལ་བཟང་རེ་སྐོང་། | — | Tibetan | Dzongsar TOC doc labels, numbered (143) | `1-SOURCES/Commentaries/bo-khenrab-jamyang-norbu-dronme.md` |
| `cone-drakpa-shedrup-gyalwe-gongsal` | ཅོ་ནེ་གྲགས་པ་བཤད་སྒྲུབ། — སྡུད་པའི་འགྲེལ་པ་རྒྱལ་བའི་དགོངས་གསལ། | — | Tibetan | Wikisource Index TOC (ཤིང་པར།; revision 1177625) — 72 nodes | `1-SOURCES/Commentaries/bo-cone-drakpa-shedrup-gyalwe-gongsal.md` |
| `senge-zangpo-kadrel` | སློབ་དཔོན་སེངྒེ་བཟང་པོ། — བཅོམ་ལྡན་འདས་ཡོན་ཏན་རིན་པོ་ཆེ་སྡུད་པའི་ཚིགས་སུ་བཅད་པའི་དཀའ་འགྲེལ། | — | Tibetan | Wikisource Index TOC (Derge Tengyur; revision 1132976) — its 32 chapters | `1-SOURCES/Commentaries/bo-senge-zangpo-kadrel.md` |

`rangjung-dorje-tika` is named from the text's self-attribution (བདག་འདྲའི་སེམས་དཔའ་རང་བྱུང་རྡོ་རྗེ་ཡིས།) and the text sheet; its frontmatter `author` is left empty on the vault owner's instruction (2026-10-03) because the metadata sheet names Karmapa Mikyo Dorje instead — for the text expert to settle. `shasana-dibam-bedon-dronme` and `khenrab-jamyang-norbu-dronme` are not in the vault owner's text sheet; they were ingested on the vault owner's instruction (2026-10-03). `cone-drakpa-shedrup-gyalwe-gongsal` and `senge-zangpo-kadrel` (sheet rows 3 and 4) have no Dzongsar export: their text was taken from their Wikisource Index pages on the vault owner's instruction (2026-10-04), one block per TOC section, with **no transclusions** (no human alignment exists; `alignment_status: none`). School is left blank where the raw data does not record it.

**Tier ordering.** These are independent works, not a root commentary with sub-commentaries. Present them in the order of this roster (the Dzongsar files comm-1 … comm-4, then the two Wikisource-only texts). Do not invent a hierarchy.

### Typed folder — `1-SOURCES/Annotations/`

One `<stem>.annotations.json` sidecar per source file, written only by `aligned-corpus-intake`. It keeps what markdown cannot: each block's alignment row and raw export text, emphasis spans, the paired row's text, every target segment with the letters and character span it covers, edition variants, human corrections with the original pairing or text, split-row parts, and where each heading came from. Machine data: rails cite the source block, never the sidecar.

---

## 4. Language tracks

| Tag | Language | Role | Translation track | Plan stream |
| --- | -------- | ---- | ----------------- | ----------- |
| `sa` | Sanskrit | Root (source) | — | — |
| `bo` | Tibetan | Translation of the root; the text the commentaries comment on | — | — |
| `zh` | Chinese (Traditional) | Translation aligned to the Tibetan | — | — |

No transformation tracks exist yet.

### Analysis language per rail section

The default: Traditional Interpretation paraphrases and Translation Notes in English, everything else in the original language. No departures recorded.

---

## 5. Bilingual glossary pairs

None yet.

---

## 6. Active transformation tracks

None yet.

---

## 7. Source-language tags used in this vault

| Tag | Script / System | Use in this vault |
| --- | --------------- | ----------------- |
| `-sa` | Devanāgarī | The Sanskrit root |
| `-bo` | Unicode Tibetan | The Tibetan translation and all commentaries |
| `-zh` | Unicode Traditional Chinese | The Chinese translation |

---

## 8. Where to look next

- [`0-VAULT-Structure.md`](0-VAULT-Structure.md) — the architecture in full.
- [`../../1-SOURCES/About Sources.md`](../../1-SOURCES/About%20Sources.md) — source-file rules.
- [`../../2-RAILS/About Rails.md`](../../2-RAILS/About%20Rails.md) — rails schema.
- [`../../3-TRANSFORMATIONS/About Transformations.md`](../../3-TRANSFORMATIONS/About%20Transformations.md) — track and output rules.
- [`annotation-conventions.md`](annotation-conventions.md) — the default block-ID conventions this annex registers deviations from.
- [`vault-variants.md`](vault-variants.md) — the three documented vault shapes, if this vault is not the common case.
- [`../CLAUDE.md`](../CLAUDE.md) — the operational quick-reference. *This annex overrides it on the points recorded above.*
- [Top-level `README.md`](../../README.md) — pipeline overview and reading paths.
