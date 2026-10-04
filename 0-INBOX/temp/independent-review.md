# Independent review: ratnagunasancayagatha sources (sa, bo, zh, 4 bo commentaries)

Read-only review. Checks were run with Python scripts (kept in the session scratchpad: check.py, gaps.py, starts.py, mono.py, comm.py, samp.py, heads.py, body.py). Line numbers below are 1-based file lines.

## Verdicts

| # | Check | Verdict |
|---|-------|---------|
| 1 | Section starts across sa / bo / zh | pass (matches the known/expected pattern) |
| 2 | Id sequences, uniqueness, heading nesting | pass for 5 of 7 files; issues in bo-mipham-lekshe.md and bo-rangjung-dorje-tika.md (duplicate heading ids, one out-of-order block of headings, one skipped level) |
| 3 | Every transclusion target exists | pass (0 broken targets in all 7 files) |
| 4 | Commentary headings vs transcluded root ids | pass (0 backward jumps; samples plausible) |
| 5 | Leftover granular / odd headings | pass (nothing found) |
| 6 | Other problems | minor new kinds only (NBSP, double spaces, editorial notes inside zh text, duplicated raw_sources entry) |

## 1. Section starts (pass)

- sa: all 9 headings ^0-0 ... ^8-0 are followed by sa blocks ^0-2, ^1-1, ^2-1 ... ^8-1. Sanskrit editor-supplied chapter titles ("२. शक्रपरिवर्त" etc.) and "...नाम ..." colophons sit at the END of the preceding section (e.g. sa ^1-28 colophon, ^1-29 title of ch. 2; ^2-65, ^3-9, ^4-12, ^4-98, ^5-5, ^5-134). They are never transcluded by bo, which is consistent.
- bo -> sa: first block after each heading transcludes sa ^0-2, ^1-1, ^2-1, ^3-1, ^4-1, ^5-1, ^6-1, ^7-1 (same id). Section 2 (bo ^2-1 "གང་ཞིག་གཟུགས་ལ་མི་གནས…" -> sa ^2-1) opens after the marker; the marker bo ^1-28 (སྐབས་གཉིས་པ…) stays at the end of section 1 and transcludes sa ^1-29. Markers སྐབས་གསུམ་པ … བརྒྱད་པ are inside the first row of sections 3-8 and align with the first sa verse.
- Section 8: bo ^8-1 (marker + split half of Tibetan row 367) has NO sa transclusion; bo ^8-2 -> sa ^8-1. zh ^8-1 -> bo ^8-2, and zh ^7-1 transcludes bo ^7-1 and bo ^8-1. sa ^7-1 is a single block. This is exactly the expected "one row later in sa/zh" pattern.
- zh -> bo: first zh block after each heading transcludes bo ^1-1, ^2-1, ^3-1, ^4-1, ^5-1, ^6-1, ^7-1 (+^8-1), ^8-2 (same ids as the bo block). Section 0: zh ^0-2 -> bo ^0-3 (the Chinese has no counterpart of bo ^0-2, the title/homage row, so bo ^0-2 is not transcluded by zh; zh ^0-3 "行品第一" is an untransluded title row).
- Order of root blocks is monotone: bo -> sa and zh -> bo transclusion targets never go backward (0 backward steps).
- Alignment coverage (information only): bo blocks without sa transclusion: only ^8-1. sa blocks never transcluded by bo: 8-4-type content is all chapter titles/colophons plus these content items worth a human glance: sa ^4-92 (verse "बीजं प्रतीत्य च भवेद् यवशालिकादेः…" 19,4, no Tibetan counterpart between bo ^4-73 -> sa ^4-91 and bo ^4-74 -> sa ^4-93), and sa ^8-3, ^8-4 (Haribhadra praśasti, Sanskrit only). zh blocks without bo transclusion are titles/editorial rows (zh ^0-3, 2-12, 2-21, 2-29, 2-39, 2-49, 2-57, 3-4, 3-7, 4-11, 4-22, ... 5-123). bo blocks not transcluded by zh: ^0-2, ^4-22, ^8-3, ^8-4.

## 2. Id sequences (issues in two commentaries)

Rules checked: unique ids; body ids 1,2,3 ... per top-level section with restart at each new top-level heading (section 0 counts continue across the pre-heading block, as ^0-1 precedes ^0-0 and next is ^0-2, which is the convention); headings end in -0, depth = id depth (depth > 6 keeps ###### with bold); parent heading present; sibling numbering continuous.

Pass with 0 issues: sa, bo, zh (9 headings each, ids ^0-0 ... ^8-0), bo-khenrab-jamyang-norbu-dronme.md (body ids), bo-shasana-dibam-bedon-dronme.md. All body ids in all 7 files run without gaps or repeats. The `# title ^0` on each file follows annotation-conventions §1b.

Issues (heading ids only; body ids are fine everywhere):

- bo-mipham-lekshe.md: duplicate heading ids (sibling number not incremented; second heading should be the next sibling):
  - line 1193 `^1-3-2-2-1-1-3-1-5-1-1-1-0` duplicates line 1187
  - line 1429 `^1-3-2-2-1-1-3-3-2-2-1-1-2-2-1-0` duplicates line 1413
  - line 1433 `^1-3-2-2-1-1-3-3-2-2-1-1-2-2-1-1-0` duplicates line 1417
  - line 1449 `^1-3-2-2-1-1-3-3-2-2-1-1-2-2-1-2-0` duplicates line 1423
  (At 1429-1449 the second set of headings, "ཀུན་རྫོབ་ཏུ་ཡང་སངས་རྒྱས་ཐོབ་པ་མི་འཐད་པའི་ཀླན་ཀ་སྤང་བ།" and its children, reuses the ids of the first set.)
- bo-mipham-lekshe.md line 1963 `^1-3-2-2-1-1-3-4-2-3-1-0` (and 1969 `...-2-3-2-0`): these children of ...-3-4-2-3 appear AFTER heading line 1959 `^...-3-4-3-0`, i.e. out of order; the heading at 1959 is probably misnumbered or misplaced.
- bo-mipham-lekshe.md lines 2096 and 2102 `^1-3-2-2-1-2-1-1-1-0`, `^1-3-2-2-1-2-1-1-2-0`: parent `^1-3-2-2-1-2-1-1-0` does not exist (the heading above is ^1-3-2-2-1-2-1-0, one level skipped); line 2108 `^1-3-2-2-1-2-1-2-0` then follows with sibling 1 missing.
- bo-rangjung-dorje-tika.md: line 572 `^2-4-1-2-4-2-1-0` duplicates line 564 (second heading "རྟོགས་བྱའི་དེའི་བློའི་རང་བཞིན།" should be ...-2-2-0).
- Sibling-number gaps (may be legitimate if nodes were pruned; flagged for awareness): khenrab line 715 `^3-3-2-1-3-3-0` (expected sibling 2); mipham line 331 `^1-3-2-2-1-1-1-1-2-2-3-0` (expected 2); rangjung line 1831 `^2-4-2-5-4-0` (expected 3); shasana line 231 `^3-1-1-1-3-3-0` (expected 2), line 996 `^3-1-2-1-1-11-2-9-0` (expected 7), line 1154 `^3-1-2-1-2-5-0` (expected 4).

## 3. Transclusion targets (pass)

Every `![[...#^id]]` in all 7 files points to an existing file and an existing block id (0 broken). Roots: bo -> sa, zh -> bo, commentaries -> bo.

## 4. Commentary headings vs transclusions (pass)

- Transclusion counts / distinct bo blocks: khenrab 345 / 305, mipham 324 / 306, rangjung 331 / 305, shasana 340 / 304.
- Backward steps in the sequence of transcluded root ids: 0 in all four (no large backward jumps, none at all).
- 16 headings sampled per commentary (spread across the file). Topics match the root passages, e.g. khenrab "ཞིང་དག་སྦྱོར་བ།" -> bo ^4-77; mipham "བྱང་ཆུབ་སེམས་དཔའི་…/ཡི་རང་" headings -> ^2-39..2-41; rangjung "ཇི་ལྟར་བསྔོ་བའི་དོན།" -> ^2-41 (dedication verse); shasana "ཐར་པ་ཆ་མཐུན།" -> ^4-52..4-54; "དངོས།" under the first chapter-1 node of khenrab -> ^0-4; intro headings -> ^0-2/^0-3. No mismatches found.
- Root blocks never transcluded (informational): all four skip ^0-1 (title row); khenrab also ^8-3, ^8-4; mipham ^8-4; rangjung ^1-28 (the "སྐབས་གཉིས་པ" marker), ^8-4; shasana ^0-2, ^8-3, ^8-4. Matches the files' covers_verses ranges.

## 5. Odd headings (pass)

No empty headings, no number-only titles, no consecutive identical titles, no markdown artefacts (`\`, `[`, `*`, `_`, `|`) except `**bold**`, which occurs only on ###### headings of depth >= 6 as the convention requires (verified: every ###### heading with id depth >= 6 is bold and no other heading is). No Latin/CJK/Devanagari in bo headings; no Tibetan/CJK in sa headings; no Tibetan/Devanagari in zh headings. No heading lacks a block id. Longest heading < 120 characters.

## 6. Other observations (new kinds only, all minor)

- bo-khenrab-jamyang-norbu-dronme.md: 25 non-breaking spaces (U+00A0), e.g. blocks ^3-29 (line 187), ^3-31 (line 197); 41 blocks with double spaces. bo-rangjung-dorje-tika.md: 4 U+00A0 (lines 46 ^0-2, 94 ^2-6). bo-shasana-dibam-bedon-dronme.md: double spaces in 161 blocks; bo-mipham-lekshe.md: 1.
- zh-ratnagunasancayagatha.md contains editorial notes as part of the Chinese text: line 385 ^2-57 "(此品攝第九歎品)", line 405 ^3-4 an entire block "【漢譯與前第八品合】", line 501 ^4-22 and line 521 "｛此行僅現於漢譯｝". If kept, consider marking them in the `[Ed:...]` form; as is they read as translation text.
- zh frontmatter `raw_sources` lists `phakpadoepa-root-zh(bo-zh).md` twice (lines 18 and 20, same sha1).
- bo-rangjung-dorje-tika.md frontmatter `author: null`.
- zh ^4-23 (transcluding bo ^4-21) appears to have two rows glued ("…心憂惱十方諸佛般若生…"), and bo ^4-22 is skipped by zh (zh ^4-21 -> bo ^4-20, ^4-23 -> bo ^4-21); possible row-shift in the Chinese alignment around bo ^4-20..4-22.
- No dangling transclusions (transclusion before a heading or at end of file), no empty blocks, no private-use / replacement / zero-width characters, no HTML tags, wikilinks or backslashes in any body text.
