# Raw data conventions this skill reads

What the human-made raw material looks like, decoded from the Diamond Sūtra corpus (2026-10-02) and extended from the Heart Sūtra corpus (2026-10-02; marked *Heart*). Treat this as the starting legend for a new corpus from the same teams, and **re-check it per document**: colour meanings drift between documents, and every legend used is recorded in the manifest entry and copied into the sidecar.

---

## 1. OpenPecha backend download (API v2)

Layout: `texts/<text_id>/{text.json, instances/<id>.json, annotations/<id>.json, alignments/<id>.json}` plus `tree.json`.

| Item | Meaning |
|---|---|
| `instances/<id>.json` → `content` | The full text of one edition (the critical instance). |
| annotation `segmentation` | Human segment spans (character offsets, end-exclusive). |
| annotation `durchen` | Variant readings: span + `note` such as `ཏ་] ༼སྣར་༽༼པེ་༽ཏཱ་` (reading] ‹witnesses› variant). |
| annotation `bibliography` | Spans typed `title` etc. |
| annotation `search_segmentation` | Search chunks — not human structure; ignored. |
| `alignments/<id>.json` | `alignment_annotation` spans on THIS text, each with `aligned_segments` ids into `target_annotation`, whose spans are offsets into the **parent** instance's `content` (the parent is in `tree.json` → `pairs`). Target spans need not coincide with the parent's segmentation. |

`text.json` carries titles, alt titles, licence, BDRC work id and contributors with BDRC person ids — the authoritative source for author/translator ids.

**Several instances** (*Heart*). A text may carry a critical instance plus a placeholder (`type: diplomatic`, `source: source-name`, 37 characters of sample data). `openpecha_model.load` reads the instance `tree.json` pairs the text by, else its only `critical` one; pass `instance_id` to override.

**Machine output.** Instances whose `source` is `Openpecha AI` (titles ending "AI Draft", "Easy to Read", "Word by Word") are machine translations, not human work: never ingested as sources.

**Upstream alignment of the title.** A derived text's first segment is often aligned to the parent's title line. The adapters treat the parent's `# title ^0` as a mapping target: a segment (or Tsadrel row) that maps only to it becomes the derived file's own title line, recorded in the sidecar; any later one is kept with the preceding block and flagged — never dropped.

**Languages the publication API lacks** (e.g. `tibphono` phonetics) cannot pass the linter; such a text is reported, not built.

---

## 2. Dzongsar Google-Docs exports (.docx)

Read with `scripts/docx_model.py` (stdlib only): paragraphs, runs with colour / highlight / shading / bold / italic / underline, Word comments, bookmarks, and the number Word *renders* for auto-numbered paragraphs (`numPr`). The rendered number is often the human reference, and it is not in the text.

### 2a. Document kinds (sheet columns)

| Kind | What it is |
|---|---|
| Clean text | One or a few giant paragraphs; inline titles still present. Text check only. |
| Sentence segmentation ("Segm", "Tsadel") | One segment per paragraph, often auto-numbered. |
| Citation | Same rows as the segmentation, plus citation colours and bold/italic. |
| TOC | Citation doc + *sa bcad* headings in **bold red `ff0000`**, numbered `1.`, `1.1.`, `3.4.2.6.7.7.` (the outline path), + inline announcements in magenta `ff00ff`. |
| TOC + alignment numbers | The TOC doc with a leading number on each paragraph naming the root segment(s) it comments on — the most complete layer. |
| Tsadrel pair | Two docs, line-parallel: row *i* of "Root text Tsadrel" ↔ row *i* of "Commentary Tsadrel Alignment" (or translation). A blank row = no counterpart. Rows are auto-numbered list items. |

### 2b. Alignment number syntax

| Style | Where | Forms |
|---|---|---|
| dotted | Chinese commentaries (refs to the Chinese root's numbered segments) | `12.` `12-15.` `1-3,5.` `17-19` (a range may drop the dot); a Tibetan tsheg may follow (`3.་`); the first few may be Word auto-numbers rather than typed |
| bare | Tibetan commentaries (refs to a root reference numbering) | `14` `1-3` `198,199,201` — never followed by a dot (a dotted number is a heading's outline number) |

**Tibetan numerals are never alignment numbers** (*Heart*). A paragraph opening with `༥༽`, `༡)` or `༡༠༽` is an enumeration in the text itself; `parse_ref_prefix` reads only Arabic digits (ASCII or full-width).

**Word list numbering may be shifted against the human numbering** (*Heart*). In the Heart corpus the numbered root the commentaries were aligned against (`D1…/Root text Alignments/M29C34F4A … -Segmentation.docx`, 81 Word list items) numbers the title as item 1, while every commentary counts from the first line after the title (`1` = རྒྱ་གར་སྐད་དུ, `5` = འདི་སྐད་བདག་གིས་ཐོས་པ…, `80` = colophon). Established by scoring every numbered paragraph of 24 commentaries against root item N and N+1 (N+1 wins in every doc). Build such a root with `number_offset: -1`: the item that becomes 0 is the title line, block `^N` is the human segment N, and the Word number stays in the sidecar (`source.rendered`). Check the offset per corpus — never assume it.

**The numbers are root segment ids.** They refer to one specific numbered copy of the root — in this corpus the Tibetan `It is for reference only/…Root text.docx` (431 typed numbers, title unnumbered) for every Tibetan commentary, and the 127 auto-numbered segments of MFF4994FD for every Chinese one. Build the root from that copy so its block `^N` is segment N, and transclude each number as written. Other splits of the root (the 430-row Tsadel, the 489-row "original") go in the root's sidecar as `alt_segmentations`. An older alignment made against a different numbering (Cone D2, 489-row) is kept as an overlay with its own concordance (`build_ref_map`). A paragraph that is only a number applies to the next paragraph.

### 2c. Colour legends seen

| Colour / format | Meaning (documents where seen) |
|---|---|
| `ff0000` bold | *sa bcad* heading with outline number (Tibetan TOC docs) |
| `ff0000` plain | flagged character / reviewer flag (Chinese 解義; Cone D2) |
| `ff00ff` | inline *sa bcad* announcement (Tibetan); heading (Chinese 註解 27 doubts, 義脈 科判, 講話, 講記) |
| `ff00ff` + bold | top-level heading (講記) |
| `4a86e8` (+bold) | root lemma quoted in the commentary (Chinese) |
| `980000` | quoted root passage (Tibetan Citation docs; Chinese 論 Tsadrel) |
| `0000a0` | title and 分 chapter headings (解義) |
| `00ff00` | closing formula after a quote, ཞེས་བྱ་བ (Vasubandhu Citation) |
| `00ffff` | citation source and closing formula, ་ལས། … ཞེས་གསུངས (Cone Citation) |
| `ff9900` | text of a citation (Cone Citation) |
| **bold** | root-text words inside a commentary |
| ***bold italic*** | verses (and colophon) |
| `Heading1` style | real heading only where the doc says so (講義 title, 自序); on every paragraph of a Tsadrel doc it is a Google-Docs artefact |
| `hl=white`, `shd=fefefe`, colours on whitespace-only runs | paste artefacts — ignored |

### 2d. Merge markers inside Tsadrel rows

`_ _`, `__`, `____` and a lone `-` join several full-text paragraphs into one row. They are not text; the Tsadrel cross-check strips them before locating a row.

### 2d′. Raw paths (*Heart*)

Drive exports put a no-break space (U+00A0) after the ID in many file and folder names (`M29C34F4A ཤེས་རབ་…`). Manifests are written with plain spaces; `common.raw_path` resolves each path component by its NFC, space-normalised name and fails on an ambiguous match.

### 2e. Things that are not text of the work

CBETA colophon blocks (`#【經文資訊】…`, `#---`) at the head of each fascicle: moved to the sidecar (`excluded_paragraphs`) with the reason.

---

## 3. Metadata spreadsheets

Two layouts: *entries* (label | bo-or-zh | en rows: `author`, `title_short`, `title_long_clean`, `title_alt_N`, `is_commentary_of`, …) and *card* (row 1 headers, row 2 values, BDRC person in column D). Most `Resources/R*.xlsx` files are an empty template. Use **cell text, not hyperlinks** (several `source` cells carry a stale hyperlink), and never take Chinese authors from the tracking sheet's column L (shifted by one row) or the catalogue's "Author name" column (unrelated names).

---

## 4. IDs

`M…` main/root text, `R…` resource (commentary or ancillary), `E…` older e-text ids of the same commentaries (E4C456D1 = RF67A9A4E, E4BF16EE = RF161D626). The 8 hex digits are shared across roles (M42AE7A72 / R42AE7A72). `A1__`, `D5__` … are download numbers, not ids.
