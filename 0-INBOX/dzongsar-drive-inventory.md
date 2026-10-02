---
title: "Dzongsar Drive export — Summary of the Perfection of Wisdom (Sañcayagāthā)"
status: draft
source_description: "Index of the Google Drive export (the Dzongsar tracking sheet and the Docs/Sheets it links) copied into 0-INBOX/raw-data/dzongsar-drive/. Scratch — not a source, never cited."
---

# Dzongsar Drive export — Summary of the Perfection of Wisdom (Sañcayagāthā)

**From:** `Dzongsar_corpus.zip`, `Dzongsar_missing_summary.zip` in ~/Downloads (exported from Google Drive on 2026-10-02 with the Claude in Chrome extension). Copied 2026-10-02; checksums are in `raw-data/dzongsar-drive/manifest.json`.

**What's here:** the `03_འཕགས་སྡུད།` section of the tracking sheet. That is 146 files: metadata sheets, clean texts, TOCs, segmentations, and root-text and commentary alignment docs. The folder paths are exactly as they were inside the zips. Three files are shared by all texts and copied whole: `Dzongsar_sheet.csv`, `links_manifest.csv` (which says what was downloaded from each sheet cell), and `Tibetan_Catalogue_Seg-Align_full_workbook.xlsx` (the master catalogue, with its authors and segmentation-guideline tabs).

## Sheet rows

Column letters are the sheet's columns. A Metadata · B Clean text · C TOC · D Sentence segmentation · E Verse segmentation · F Citation · H Root text (alignment) · I Commentary / other language (alignment). Files sit under `Dzongsar_corpus/Dzongsar/03_འཕགས་སྡུད།/<column folder>/`, and each file name starts with the row's ID.

| Row | ID | Title | Author | Kind | Downloaded | Missing | Sheet notes |
|---|---|---|---|---|---|---|---|
| 42 | M6BD866B7 | འཕགས་པ་སྡུད་པ། | སྟོན་པ་བཅོམ་ལྡན་འདས། | རྩ་བ། Sanskrit Tsawa Align · Tsawa and Sanskrit Alignment | A, B, H |  |  |
| 43 | M6BD866B7 | འཕགས་པ་སྡུད་པ། | སྟོན་པ་བཅོམ་ལྡན་འདས། | རྩ་བ། Chinese Tsawa Align · Tsawa and Chinese Alignment | H, I |  |  |
| 44 | M6BD866B7 | འཕགས་པ་སྡུད་པ། | སྟོན་པ་བཅོམ་ལྡན་འདས། | རྩ་བ། Sanskrit Tsawa Align · Tsawa and Sanskrit Alignment | H, I |  |  |
| 45 | R79FDDBD3 | འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པའི་ཊཱི་ཀ་ཡིད་བཞིན་གྱི་ནོར་བུ་རིན་པོ་ཆེ་ལྟ་བུ་ཕ་རོལ་ཏུ་ཕྱིན་པ་རྒྱ་མཚོའི་སྡེ་ཞེས་བྱ་བ་བཞུགས་སོ།། | ཀརྨ་མི་བསྐྱོད་རྡོ་རྗེ། | འགྲེལ་བ། {ཡི་གེ} · Commentary Alignments | A, B, C, H, I |  | Lobsang Dhondup; 880; Done |
| 46 | R09FD3ABF | ཡོན་ཏན་རིན་ཆེན་སྡུད་པའི་འགྲེལ་པ་རྒྱལ་བའི་ཡུམ་གྱི་དགོངས་དོན་ལ་ཕྱིན་ཅི་མ་ལོག་པར་འཇུག་པའི་ལེགས་བཤད་ཅེས་བྱ་བ་བཞུགས་སོ། ། | འཇུ་མི་ཕམ། | འབྲུ་འགྲེལ། · Commentary Alignments | A, B, C, H, D |  | kalsang Gyaltsen; 545; Done |
| 47 | R0804AAA2 | འཕགས་པ་མདོ་སྡུད་པའི་འགྲེལ་པ་རྒྱས་པ་སྤས་དོན་གསལ་བའི་སྒྲོན་མེ། | ཤཱ་ས་ན་དཱི་བཾ། | འགྲེལ་བ། {ཡི་གེ} · Commentary Alignments | A, B, C, H, I |  |  |
| 48 | R7AABAABE | ཡོན་ཏན་རིན་པོ་ཆེ་སྡུད་པ་ཚིགས་སུ་བཅད་པའི་འགྲེལ་པ། | མཁྱེན་རབ་འཇམ་དབྱངས་བློ་བཟང་འཕྲིན་ལས། | འགྲེལ་བ། {ཡི་གེ} · Commentary Alignment | A, C, H, I |  |  |

## Failed downloads

These links in the sheet could not be exported on the first pass. "Second pass" shows the result of the follow-up download (see below).

| Row | Column | Label | Link | Second pass |
|---|---|---|---|---|
| — | | none | | |

## External links in the sheet

- none

## Second pass: `Dzongsar_missing_summary.zip`

The first two zips skipped or failed some links. The Chrome extension then fetched every link the sheet lists for this text that was still missing, including the Tibetan, Chinese and General-list tabs and everything inside linked folders. The result is in `raw-data/dzongsar-drive/Dzongsar_missing_summary/`. Each top-level name starts with its number in the request: A = linked on the Dzongsar tab but never crawled, B = failed on the first pass, C = uploaded files skipped in the commentary folders, D = linked only from the other tabs.

- **Downloaded:** 116 files (A: 5, D: 111).
- **Renamed:** 39 paths. A name over 200 bytes was shortened at a tsheg, keeping its ID and extension, and extension-less files got one. Some nested Tibetan folder names had pushed full paths past macOS's 1024-byte limit. `path-renames.json` maps each original path to its new one; `missing_manifest.csv` still uses the original paths.
- **Overlap:** many items, especially a text's main folder, contain copies of files already in the first two zips. Nothing has been de-duplicated.
- **Not in git:** Dzongsar_missing_summary/…/Others/R0804AAA2 … B-2.pdf (105 MB, over GitHub's 100 MB limit; listed in .gitignore). It is on disk only.

Still unavailable (0 distinct links). Reasons: none.

| # | Item | Status | Link |
|---|---|---|---|
| — | none | | |

## Next step

None of this has been converted. The .docx alignment docs pair root-text segments with commentary or translation segments; their structure still needs a look before choosing a converter.
