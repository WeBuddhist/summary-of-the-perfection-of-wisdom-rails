# Review brief — Phakpa Düpa sources (2026-10-03)

For the text expert. The Sanskrit root, its Tibetan translation, a Chinese translation and four Tibetan commentaries are now in `1-SOURCES/`, segmented by the Dzongsar team's alignment rows, with tables of contents, TOC-driven block ids and every alignment written as a transclusion. Everything below that a machine can prove has been proved; the checklist is what needs human eyes. Full detail: `0-INBOX/phakpadoepa-intake-report.md`; every decision with its reason: `0-INBOX/raw-data/intake-manifest.yaml`.

## At a glance

| File | Role | Blocks | Headings and their source | Transclusions |
|---|---|---|---|---|
| `Text/sa-ratnagunasancayagatha.md` | Root (Sanskrit) | 373 | 9 — Wikisource dkar chag, **editorial Sanskrit** labels | — |
| `Translations/bo-ratnagunasancayagatha.md` | Translation of the root; what everything else points at | 308 | 9 — Wikisource dkar chag (Derge), verbatim | 307 → Sanskrit |
| `Translations/zh-ratnagunasancayagatha.md` | Translation, aligned to the Tibetan | 333 | 9 — dkar chag, **editorial Chinese** labels | 308 → Tibetan |
| `Commentaries/bo-rangjung-dorje-tika.md` | Commentary (author left empty) | 323 | 317 — its Wikisource Index (Lhasa 2013 ལྕགས་པར།), up to 11 levels | 331 |
| `Commentaries/bo-mipham-lekshe.md` | Commentary, Ju Mipham | 487 | 453 — its Wikisource Index (dbu can MS), up to 24 levels | 324 |
| `Commentaries/bo-shasana-dibam-bedon-dronme.md` | Commentary, Shāsana Dhīpaṃ | 297 | 140 — Dzongsar TOC doc's numbered labels, up to 13 levels | 340 |
| `Commentaries/bo-khenrab-jamyang-norbu-dronme.md` | Commentary, Khenrab Jamyang | 349 | 143 — Dzongsar TOC doc's numbered labels, up to 11 levels | 345 |
| `Commentaries/bo-cone-drakpa-shedrup-gyalwe-gongsal.md` | Commentary, Cone Drakpa Shedrup (Wikisource only) | 73 | 72 — its Wikisource Index, up to 6 levels | none |
| `Commentaries/bo-senge-zangpo-kadrel.md` | Commentary, Sengge Zangpo (Wikisource only, Derge) | 33 | 32 chapters — its Wikisource Index | none |

## Checked automatically

- **No letter lost or added** in any file (`verify.py`: `missing=0 extra=0`); every row of every alignment doc is exactly one block, or the declared parts of a split row.
- **Every transclusion equals the human row pairing** (`aligned_ok` n/n), carried from each doc's own copy of the root onto the display Tibetan by letters, and **its text really is in the transcluded segment** (`content_ok` n/n; 7 rows at 50–90 % are edition variants, listed below).
- **Ids**: unique in every file, from the TOC (`^<path>-0` headings, `^<section>-<n>` blocks, counting without gaps); every transclusion resolves. An independent read-only review also found the section starts aligned across the three languages, no backward step in any commentary's transclusions, and topically plausible headings in samples of 16 per commentary (`0-INBOX/temp/independent-review.md`).
- **Publication dry run**: the library linter's only errors are the empty `category_id` and a missing `source` URL for the Sanskrit and Chinese; the parser builds text, edition, TOC and alignment payloads for all seven files.
- **Coverage**: three commentaries transclude every root segment; Rangjung Dorje's all but one (below).

## Review checklist

Most important first.

### Tables of contents
- [ ] **Root section 2 placement** — Wikisource opens section 2 (ལམ་ཐམས་ཅད་ཤེས་པ་ཉིད་བསྟན།) *after* the inline marker སྐབས་གཉིས་པ་… (Tibetan `^1-28`, which therefore ends section 1), while every other section opens *with* its marker. Kept as Wikisource has it. Move it? (`2-RAILS/Sections/Raw/toc-wikisource/ratnagunasancayagatha.md`, node 2.)
- [ ] **Root section 8** opens inside Tibetan row 367 (split there, `^7-1` / `^8-1`); the Sanskrit and Chinese rows 367 are not split, so their section 8 heading stands one row later (before `^8-1` = row 368).
- [ ] **18 editorial headings** in the Sanskrit and Chinese (nodes 0–8). Attested in the translation itself: सर्वाकारज्ञता, सर्वज्ञता/一切智, अनुपूर्व/漸次; the rest are standard terms (उपोद्घातः, मार्गज्ञता, सर्वाकाराभिसंबोधः, मूर्धाभिसमयः, एकक्षणाभिसंबोधः, धर्मकायः; 序分, 一切相智, 道相智, 一切相現觀, 頂現觀, 一剎那證菩提, 法身). Evidence per label: `0-INBOX/temp/pair-review/root-toc-labels.md`.
- [ ] **79 TOC-number corrections** (Claude's) in the two TOC docs, `toc.path_corrections` in the manifest. Shāsana Dhīpaṃ: 69 labels numbered `3.1.1.1…` / `3.1.1.2…` that stand under `3.1.2 སྒོམ་བྱེད་སྦྱོར་བཞི།` (→ `3.1.2.1…` / `3.1.2.2…`; within them `…2.34`, read as one label covering items 3–4, → `.3`), and two labels repeating sibling numbers `3.1.1.1.2.2.1.2–3` after `…1.4` (→ `.5`, `.6`); Khenrab Jamyang: three label groups that restart a sibling count (`3.3.2.1.2.3.1 དངོས།` after `…3.3 ས་མཚམས།` → `…3.4`, etc.) and `3.3.2.1.3.12` (→ `.1`). The original number stays in each heading's sidecar entry (`source.label_path`). Some of these may rather be children of the preceding label — check.
- [ ] **17 Wikisource heading numbers corrected** (Claude's; the outline files' `path_corrections`, the Index's own number kept as `path_in_source`) — they would have given duplicate ids: Rangjung Dorje `2.4.1.2.4.2.1` repeated (second → `…2.2`, with its 2 children); Mipham `1.3.2.2.1.1.3.1.5.1.1.1` repeated (→ `…1.2`), `…3.3.2.2.1.1.2.2.1` repeated (second → `…2.2.2`, with 8 descendants), and the two children of `…3.4.3 དེ་ལྟར་རྟོགས་པ་ཐོབ་པའི་ཡོན་ཏན།` numbered `…3.4.2.3.1–2` (→ `…3.4.3.1–2`, with descendants).
- [ ] **Mipham: a heading level missing on Wikisource** — `1.3.2.2.1.2.1.1.1 བསམ་གཏན་བཞི་ལ་བསླབ་པ།` and `…1.1.2 གཟུགས་མེད་…` stand under a `1.3.2.2.1.2.1.1` that the Index never gives; kept as numbered (their parent heading is absent).
- [ ] **Rangjung Dorje's Wikisource edition** interpolates the *sa bcad* enumeration sentences (e.g. བཞི་པ་ཆོས་ཀྱི་རང་བཞིན་ལ་གཉིས་ཏེ།…) that the Dzongsar text lacks; 122 headings therefore stand where the shared text resumes, and chains of headings with no shared text between them stand together. Spot-check a few.
- [ ] **Deep machine-placed TOCs** — 317 + 453 Wikisource headings placed by letter matching (not by hand). Spot-check headings in both commentaries, especially Mipham, where each heading stands before its own ༈ label in the text.

### Added 2026-10-04
- [ ] **Two commentaries from Wikisource, not aligned** — `bo-cone-drakpa-shedrup-gyalwe-gongsal.md` (72 headings; Wikisource pages not yet validated, so OCR-level errors are possible) and `bo-senge-zangpo-kadrel.md` (Derge). No transclusions: no human alignment exists. Sengge Zangpo's TOC is its 32 chapters, so each block is a whole chapter (median ~3,800 letters, longest ~42,000) — finer segmentation can follow.
- [ ] **Sanskrit verse numbers removed** (305), kept as metadata per block; **verse lines** added in the Sanskrit (pāda breaks from DSBC; rows 145, 146, 336, 344 and 373 by Claude from the metre), Tibetan and Chinese. Row 344: removing `[दुःशील भोति]` left the next word glued, so a space stands where the bracket was.

### Text added or changed
- [ ] **Mipham row 209 — passage added from Wikisource (D8).** The Dzongsar text jumps from …ཕམ་པར་བྱེད་ནུས་སོ། to མེད་པ་ཡིན་པའི་ཕྱིར་རོ། ། and lacks the opening of 1.3.2.2.1.1.3.5 (དེས་བསླབ་བྱ་ཆོས་ཀྱི་ཆེ་བ།) and the body of 1.3.2.2.1.1.3.5.1 (from རྩ་བའི་ས་བཅད་ལྔ་པ་… to …གཉིས་སུ་); added verbatim from Page …ལག་བྲིས་དབུ་ཅན།.pdf/182, revision 1247289. File `bo-mipham-lekshe.md`, section 1 (blocks around the 1.3.2.2.1.1.3.5 headings).
- [ ] **Brackets removed, words kept (D10)** — 41 in the Sanskrit (chapter titles such as `[१. सर्वाकारज्ञताचर्यापरिवर्त]`, restorations, the praśasti labels; two pairs span rows 137–138 and 336–337) and `[དྷྱཱན་པཱའ་ར་མི་ཏཱ་]` in Rangjung Dorje row 8.

### Pairings corrected (Claude's, D12)
- [ ] **Chinese** — ZH 27→Tibetan 26+27, 28→27+28, 29→28+29 (half-verse slips); 36→36+37 and 37→38+39 (the Chinese compresses four verses into two rows); 135→136 (ZH 135 is a verbatim duplicate of ZH 136; Tibetan 135 has no Chinese); 210→209+210 (ZH 209 is empty).
- [ ] **Khenrab Jamyang row 277** — commentary on the translators' colophon, paired in the doc with its root copy's *different* colophon (Zhalu Lotsāwa's revision note); left without a transclusion. It comments on the display colophon `bo-ratnagunasancayagatha.md#^8-4` — add that link?
- [ ] The Sanskrit–Tibetan pairing was read in full: **no errors**. Content on one side only: Sanskrit 19,4 (row 201) has no Tibetan; rows 151–152 the Tibetan compresses Sanskrit 14,3–4.

### Split rows (D7)
- [ ] **288 alignment rows split** where a heading falls inside them: Tibetan 1, Rangjung Dorje 90, Mipham 141, Shāsana Dhīpaṃ 24, Khenrab Jamyang 32. Each part shows the root segments it quotes (8-letter runs of the segment found in the part; else the first part). Sidecar: `source.part`, `source.split`, `alignment.row_targets`. Spot-check that each transclusion stands with the part that comments on it.
- [ ] TOC-doc labels within 15 letters of a row edge were left at the row boundary (19 in Shāsana Dhīpaṃ, 2 in Khenrab Jamyang), e.g. a heading after a row that ends …དང་པོ་ནི།

### Metadata
- [ ] **Rangjung Dorje commentary — author empty** (vault owner). The text names its author (བདག་འདྲའི་སེམས་དཔའ་རང་བྱུང་རྡོ་རྗེ་ཡིས།, row 3), the text sheet gives ཀརྨ་པ་རང་བྱུང་རྡོ་རྗེ།, the metadata sheet ཀརྨ་པ་མི་བསྐྱོད་རྡོ་རྗེ། with source `MW4CZ295070` and the generic title མདོ་སྡུད་པ་ཚིགས་སུ་བཅད་པའི་འགྲེལ་པ། — the sheet may describe another work. Settle author, source and English title.
- [ ] **Tibetan root CSV** gives `Peltsek Rakṣita` as the English *author* (the translator's name); not used. Translator taken from the colophon.
- [ ] **Shāsana Dhīpaṃ title** taken from the text (the sheet's ཕགས་པ… lacks the initial འ). Shāsana Dhīpaṃ and Khenrab Jamyang are not in the text sheet.
- [ ] `license: unknown` everywhere; `category_id` empty (needed for upload); Sanskrit and Chinese have no `source` URL; no BDRC/OP ids for authors (linter warns).

### Source quality
- [ ] **Stray Latin characters** in the Tibetan display text: rows 51, 60, 71 (`ā`), 292 (`གང་གāའི`), 359 (`བཻḍūརྱ`); Tibetan typo `བྱག་ཆུབ` row 156; a stray `I` in Chinese row 360. Kept as made.
- [ ] **Editorial notes inside the Chinese text** (from the Dzongsar doc, kept as made): `(此品攝第九歎品)` (`^2-57`), the block `【漢譯與前第八品合】` (`^3-4`), `｛此行僅現於漢譯｝` (`^4-22` and the 卷中 row). Also non-breaking and double spaces in several commentaries (Khenrab Jamyang, Shāsana Dhīpaṃ).
- [ ] **Edition-variant rows** (50–90 % of the paired root text found): Rangjung Dorje row 127; Shāsana Dhīpaṃ rows 132, 140, 157, 257; Khenrab Jamyang rows 141, 273.

## Root passages some commentaries never transclude

| Segment | Passage | Commentary |
|---|---|---|
| `bo-ratnagunasancayagatha.md#^1-28` | སྐབས་གཉིས་པ་ལམ་ཐམས་ཅད་ཤེས་པ་ཉིད་བསྟན། ། (the bare topic marker) | Rangjung Dorje |

(Title, homage and colophons left out of the count.)

## Where to look

- Sources: `1-SOURCES/Text/`, `1-SOURCES/Translations/`, `1-SOURCES/Commentaries/`; sidecars `1-SOURCES/Annotations/`
- Outlines: `2-RAILS/Sections/Raw/toc-wikisource/` (root, Rangjung Dorje, Mipham)
- Manifest (every decision): `0-INBOX/raw-data/intake-manifest.yaml` — generated by `0-INBOX/temp/make_manifest.py`
- Report: `0-INBOX/phakpadoepa-intake-report.md`; vault annex: `4-SYSTEM/Guidelines/vault-annex.md`
- Evidence: `0-INBOX/temp/pair-review/` (pair readings, heading renderings), `0-INBOX/temp/wiki-toc-*/` (Wikisource pages, placements), `0-INBOX/temp/coverage.txt`, `0-INBOX/temp/intake-verify.json`
