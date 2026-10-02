---
name: format-commentary
description: >
  Format a commentary for the collection: repair OCR damage, structure the
  headings, normalise spacing and punctuation, and apply block IDs — producing a clean,
  navigable file that later skills can segment, cite, and transclude.

  Trigger on "format this commentary", "normalise this commentary", "fix the OCR in
  this file", "clean up the headings", "prepare this commentary".

  Runs BEFORE `segment-commentary`. This is where OCR repair belongs — the segmentation
  skills are forbidden from altering text, so anything not fixed here stays broken.
---

# Format and normalise a commentary

| Mode | Text | Use |
|---|---|---|
| 1 — Generic | Tibetan commentary | The default |
| 2 — Chinese | Chinese commentary | Different punctuation and 科判 conventions |
| 3 — Full pipeline | A commentary that comes with a companion outline file | Scripted heading alignment, segmentation and ID stamping |

**Mode 1 is the default.** Reach for Mode 3 only when the commentary comes with
a separate bullet-list outline file to align its headings against — that is the
precondition the whole pipeline is built on. Every measured figure in Mode 3
(the 800-character ceiling, the shad-spacing counts, the "I / 1 / 2" root
labels) is **calibration from the corpus it was developed on, not a rule** —
re-measure on your own file before trusting any of them.

### Pre-step — reflow Tibetan one clause per line

`4-SYSTEM/Skills/format-commentary/scripts/shad_linebreak.py` reflows a Tibetan file so every shad group
(`། ` / `།།` / `། །`) ends a line, with Botok Unicode normalisation, wikilink
unwrapping and `>`-marker removal. Run it when a file arrives as fixed-width
wrapped text or one giant run, and you want the one-clause-per-line shape that
`segment-commentary` Phase 2 expects.

```bash
python3 4-SYSTEM/Skills/format-commentary/scripts/shad_linebreak.py <input.md>   # -> <input>_segmented.md
```

It writes a new `_segmented` file and never touches the original, sets
`status: 1-segmented` in the frontmatter, and keeps a leading `༄༅། །` yig-mgo
attached to the text that follows it. It **does** normalise Unicode, so it is a
`format-commentary` step (this is the OCR/normalisation stage), not a
`segment-commentary` one.

**This is the OCR-repair step, and the only one.** `segment-commentary` and
`add-block-ids` are both bound by a no-loss assertion and cannot fix a broken
character. If a commentary reaches them still damaged, the damage is permanent for
everything downstream that cites it. Do the repair here, and where a reading is
genuinely uncertain, leave an `[Ed: …]` note rather than a silent guess.

---

## Mode 1 — Generic Tibetan commentary

**Role:** Expert Editor in Tibetan Buddhist Literature, Text Reconstruction, and Markdown Formatting.

**Task:** Process Tibetan commentaries by fixing OCR errors, structuring the text with specific hierarchical logic, and applying precise metadata via Obsidian block references.

**1. OCR Cleanup & Text Reconstruction**

- **No Deletions:** Strictly preserve the entire source text. Do not omit any analysis or citations.

- **Grammar Fixes:** Reconstruct Tibetan syllables. Fix broken words caused by OCR (e.g., join vowels to bases, ensure correct tsheg placement).

- **Latin Prefix Removal:** Actively identify and remove stray Latin characters (e.g., 'm', 'g', 'b', 't') that were incorrectly prefixed to Tibetan words during the OCR process (e.g., change "mཚན་མ་" to "མཚན་མ་").

- **Continuous Flow:** Remove arbitrary line numbers and arbitrary line breaks *within* sentences, to form smooth, logically grouped text. (Line breaks that the source itself uses to mark a clause or a verse pāda are content, not noise — keep those.)

- **Uncertain readings:** where a reading cannot be recovered with confidence, leave an `[Ed: …]` note rather than a silent guess. This is the last step that may alter a character; after it, every downstream skill is bound by a no-loss assertion.

**2. Heading Structure (མགོ་བརྗོད་རྩ་དོན)**

Headings follow `4-SYSTEM/Guidelines/annotation-conventions.md` §2 — **markdown level = depth in the
structural tree, and every heading carries the full decimal path plus the `-0`
slot.**

| Level | Markdown | Purpose | Block ID |
|---|---|---|---|
| 1 | `#` | Main title. No numerical prefix. | none |
| 2 | `##` | Top-level division (chapter / first sa-bcad level) | `^N-0` |
| 3 | `###` | Section | `^N-N-0` |
| 4 | `####` | Sub-section | `^N-N-N-0` |
| 5 | `#####` | Sub-sub-section | `^N-N-N-N-0` |
| 6 | `######` | Fifth-level node | `^N-N-N-N-N-0` |
| 7+ | `######` + `**bold**` title | Deeper nodes | full path + `-0` |

- The first `##` section immediately following the title is numbered `0`
  (e.g. `## 0. མཆོད་བརྗོད། ^0-0`); subsequent sections are `1.`, `2.`, …
- **There is no segment cap.** A node at `1.2.2.1.1.4` in the tree gets
  `^1-2-2-1-1-4-0`. Never flatten, merge, or truncate a deep tree to fit a
  shorter ID. Markdown stops at `######`; depth beyond six is carried by the
  block ID, with the heading title wrapped in `**bold**` so the extra depth is
  visible.
- **Every heading takes a block ID**, written inline at the end of the heading
  line. (An older version of this skill said the opposite — "do NOT add block
  IDs to any heading level". That rule is retired; a parser expecting `^N-0`
  finds no structure without it.)
- **Never `^TOC-N`.** That scheme is deprecated (`4-SYSTEM/Guidelines/annotation-conventions.md` §6).
- **Spacing:** exactly one blank line before and after every heading, including
  between two adjacent heading lines.

**3. Paragraph & Verse Formatting**

- **Logical Blocks (Granularity):** Break long prose sections into short, discrete paragraphs, so each is a usable citation unit. If a paragraph runs well past a few lines of Tibetan, find a logical break point and split it. Prefer under-cutting to over-cutting: an over-long block is recoverable, a wrong break is not.

- **Verses (ཚིགས་བཅད):** Count and separate blocks by each independent stanza. An independent stanza is defined by its context. Keep verse lines together within a single stanza, but do not group multiple independent stanzas into the same block.

- **Quotes (ལུང་འདྲེན):** Place source references (e.g., སྡུད་པ་ལས།) on their own separate line above the quote. Place concluding remarks (e.g., ཞེས་སོ། །) on their own separate line below the quote.

**4. Obsidian Block IDs**

Body IDs follow `4-SYSTEM/Guidelines/annotation-conventions.md` §3 — **keyed off the enclosing `##`
label, two segments, restarting only at `##`.**

- **Placement:** one ID at the end of every discrete text block (a short paragraph, an independent verse stanza, a standalone citation line), on the block's **last line**, preceded by one space.

- **Format:** `^{label}-{n}`, where `{label}` is the enclosing `##` heading's own label (`1`, `I`, `a`, … — whatever that heading's `^{label}-0` carries) and `{n}` is a counter starting at 1.

- **Restart:** the counter restarts **only at a new `##`**. It runs straight through `###`, `####` and deeper headings. A body block sitting under a `####` still gets the two-segment `^{label}-{n}` form — never `^{label}-{h3}-{n}`. Only heading lines carry more than two segments.

- Content before the first `##` takes label `0`: `^0-1`, `^0-2`, …

- **Transclusion lines (`![[…]]`) never take an ID and never advance the counter.** They are structural, not content.

- **No zero-padding** on any segment.

If the file's `##` headings were labelled by hand by a contributor, do not
generate or edit those labels — `add-block-ids` Mode 1 owns that case, and this
skill only prepares the text it runs on.

**5. Output Protocol**

- Provide the final cleaned and formatted Tibetan text as a single Markdown file.
- Preserve the frontmatter block untouched except through the `frontmatter` skill.

---

## Mode 2 — Chinese commentary

> **Reading note (English).** This mode is written in Chinese because its users
> are. Two things to know before following it:
> (1) Every worked example below — the text, its author, translator, and
> frontmatter — is **example material from one commentary**, not a rule. Swap in
> your own text's values.
> (2) Its §3 restart rule ("the counter restarts at every `##` **or** `###`")
> is a local variant that predates `4-SYSTEM/Guidelines/annotation-conventions.md`. **The canonical rule
> is Mode 1's: the body counter restarts only at `##`, and runs straight through
> `###` and deeper.** Follow Mode 1 for IDs; follow this mode for the 科判 →
> heading-level mapping, the verse formatting, and the batch protocol, which are
> what it is actually for.

### 目的

此技能定義了在 `1-SOURCES/Commentaries/` 文件夾中，對《入菩薩行論》中文註釋進行格式化、結構化和標準化的標準程序。它將傳統中文科判映射到 Markdown 標題層次結構中，將長篇散文分解為高度細粒度的段落，嵌入根頌，應用精確的 Obsidian 區塊識別碼，並實施穩健的批處理協議以處理長文本。

---

### 核心原則

1.  **嚴格保留**: 不刪除、不總結、不更改任何註釋文本。保留原始措辭，包括傳統科判標籤（例如 `甲一`、`乙二`、`丙三`）。
2.  **段落細粒度化**: 將長篇散文部分分解為非常簡短、獨立的段落（理想情況下為 1-3 句，不超過 3-4 行中文文本）。這對於精確的區塊引用至關重要。
3.  **傳統科判映射**: 將分層的中文科判標籤映射到 Markdown 標題層次結構，最高到四級標題 (`####`)。
4.  **根頌嵌入**: 在該頌詞的註釋之前，立即插入一個指向根文本文件中匹配根頌的嵌入連結。
5.  **Obsidian 區塊識別碼**: 在每個獨立的文本區塊（段落、頌詞、獨立列表項）末尾應用順序、唯一的區塊識別碼，並在每個標題下重新開始計數。
6.  **分批處理**: 由於註釋文本極長，必須以大約 **100-150 行文本**（或約 3000-5000 字）的順序批次（塊）進行處理文本，並維護一個狀態區塊以確保連續性。

---

### 1. 標題結構與科判對照

傳統中文註釋使用廣泛的分層科判（以天干：甲、乙、丙、丁...；地支：子、丑、寅、卯...；或中文數字：一、二、三... 作為前綴）來組織其分析。這些必須映射到 Markdown 標題樹中：

-   **一級標題 (`#`)**: 主書名。僅在文件頂部（位於前置元數據下方）使用一次。無區塊識別碼。
-   **二級標題 (`##`)**: 品。格式：`## N. [品名] ^N-0`（例如：`## 1. 第一品 讚菩提心功德品 ^1-0`）。
-   **三級標題 (`###`)**: 主要結構劃分（通常是 `甲` 級）。格式：`### N.M [劃分標題] ^N-M-0`（例如：`### 1.1 甲一、釋題 ^1-1-0`）。
-   **四級標題 (`####`)**: 次級劃分（通常是 `乙` 或 `丙` 級）。格式：`#### N.M.P [次級劃分標題] ^N-M-P-0`（例如：`#### 1.1.1 乙一、譯文皈敬 ^1-1-1-0`）。
-   **更細粒度的劃分**: 對於更深層次（例如 `丁`、`戊`、`己`、`子`、`丑` 等），請勿使用深於 `####` 的標題（五級標題 `#####` 受限制）。相反，將它們格式化為標準段落中的粗體文本，後跟一個區塊識別碼（例如：`**丁一、所為義。** 由於稱揚殊勝皈境功德... ^1-1-5`）。

#### 格式規則:
-   每個標題前後必須留一個空行。
-   標題的識別碼格式始終以 `-0` 結尾（為標題保留）。
-   請勿在標題行末尾使用插入符號 `^` 添加區塊識別碼；而應將其內聯寫在標題文本的末尾（例如：`### 1.1 甲一、釋題 ^1-1-0`）。

---

### 2. 段落與頌詞格式

-   **散文粒度**: 長段落必須在邏輯斷點處（例如，論證的過渡、新的次級論點或引文之前/之後）進行拆分。保持段落簡短（1-2 句，最多 3-4 行），以優化其引用。
-   **根頌嵌入**: 每當引入一個根頌時，插入一個指向根文本文件的嵌入連結。
    -   格式：`![[1-SOURCES/Text/<root-text>.md#^1-1]]`（其中 `<root-text>.md` 是前置元數據中聲明的根文本，`^1-1` 是匹配的頌詞識別碼）。
-   **中文頌詞翻譯**: 如果註釋包含根頌的中文翻譯（通常是四行詩節），請將其格式化為獨立的區塊，每行頌詞單獨成行：
    ```markdown
    為己一切生中備諮詢，  
    亦為利他與我同類機，  
    遵依正士智者之所許，  
    入菩薩行論釋今當作。 ^1-10
    ```
    注意：在每個行末使用兩個空格來表示區塊內的換行，並將區塊識別碼放在最後一行的末尾。

---

### 3. Obsidian 區塊識別碼規範

-   **位置**: 在每個獨立的文本區塊（段落、頌詞、獨立列表項）的末尾添加一個唯一的區塊識別碼。
-   **識別碼格式**: 正文區塊一律為 **兩段** `^N-V`（`N` 取自所屬二級標題 `##` 的標籤，`V` 是從 1 開始的順序計數器）。標題行才使用完整路徑（見上文第 1 節）。
-   **序列重啟**: 順序計數器 (`V`) **只在每個新的二級標題 (`##`) 下**重新從 `1` 開始；遇到 `###`、`####` 及更深的標題時不重啟，繼續累加。（此處已依 `4-SYSTEM/Guidelines/annotation-conventions.md` §3 更正；舊版本寫作「`##` 或 `###`」，不再適用。）
-   **嵌入連結行（`![[…]]`）不取識別碼，也不佔用計數器。**
-   **標題上不使用插入符號**: 請勿在標題行上使用帶有插入符號 `^` 的區塊識別碼。標題使用內聯的 `-0` 格式（例如：`### 1.1 甲一、釋題 ^1-1-0`）。

---

### 4. 分批處理協議

由於中文註釋文本極長，必須以大約 **100-150 行文本**（或約 3000-5000 字）的順序批次（塊）進行處理。

為確保在不同運行之間保持結構一致性，代理必須遵循以下協議：

#### 步驟 1: 識別和拆分
1.  讀取原始文本文件並識別自然邊界（例如，章節末尾、主要 `甲` 部分的末尾）。
2.  將文件拆分為順序批次。如有需要，將原始批次保存在 `0-INBOX/temp/` 中。

#### 步驟 2: 讀取狀態
在處理新批次之前，從上一個已處理文件的末尾或當前會話上下文中讀取 **狀態區塊**。狀態區塊跟踪：
-   `current_chapter`（章節號，例如 `1`）
-   `current_section`（分段號，例如 `1.1`）
-   `current_subsection`（次級分段號，例如 `1.1.1` 或 `none`）
-   `block_counter`（順序區塊計數器，例如 `45`）

#### 步驟 3: 格式化批次
處理批次，應用所有格式化、科判映射和區塊識別碼規則。確保：
-   如果遇到新標題，將 `block_counter` 重置為 `1`（或適當的子計數器）。
-   每個格式化的段落/頌詞都遞增 `block_counter`。

#### 步驟 4: 寫入和追加
將格式化的文本追加到 `1-SOURCES/Commentaries/` 中的目標文件。

#### 步驟 5: 寫入狀態區塊
在已處理批次的末尾，將更新後的狀態區塊作為 HTML 注釋寫入，以便下次運行可以讀取它：
```markdown
<!-- BATCH_STATE
current_chapter: 1
current_section: 1.2
current_subsection: 1.2.1
block_counter: 18
-->
```

---

### 5. 示例

#### 原始中文註釋輸入:
```text
入菩薩行論廣解卷一
極尊正士諸具大悲心者足下恭敬頂禮。
誰之智慧盡除諸罪，相好功德熾然四身，輪超法界際，大悲流露六十支分韻音，無垢光明普照無邊諸眾生，任運成辦，恒常無間，善能破除無邊眾生愚癡諸黑暗，於諸能仁自在上師大士聖妙吉祥足前，我今恭敬禮。
為己一切生中備諮詢，亦為利他與我同類機，遵依正士智者之所許，入菩薩行論釋今當作。自見取執絹網所繫縛，謂言欲證小乘菩提果，不須證入甚深真如性，願捨諸顛倒說而諦聽。
其所造《入菩薩行論》分四：甲一、釋題；甲二、皈敬；甲三、正義；甲四、結義。今初：
梵語有四種，此是桑支達語也。此論題名「菩提」，藏語降曲；「薩埵」，藏語「生巴」；「雜雅」，藏语「覺巴」；阿瓦打[冒-目+阿]藏語「[覺/勿]巴。」
```

#### 格式化輸出:
```markdown
---
title: 入菩薩行論廣解
author: 賈曹傑 (Gyaltsab Je)
translator: 隆蓮法師 (Longlian)
language: Chinese
file_type: commentary
lang_tag: zh
verse_id_format: verse
registered_id: gyaltsab-je
root_text: 1-SOURCES/Text/<root-text>.md
covers_verses: 1-1–10-58
source_description: "隆蓮法師譯《入菩薩行論廣解》。"
---

# 入菩薩行論廣解

## 0. Introduction ^0-0

入菩薩行論廣解  
寂天菩薩造頌　傑操大師註解　隆蓮法師譯 ^0-1

極尊正士諸具大悲心者足下恭敬頂禮。 ^0-2

誰之智慧盡除諸罪，相好功德熾然四身，輪超法界際，大悲流露六十支分韻音，無垢光明普照無邊諸眾生，任運成辦，恒常無間，善能破除無邊眾生愚癡諸黑暗，於諸能仁自在上師大士聖妙吉祥足前，我今恭敬禮。 ^0-3

為己一切生中備諮詢，  
亦為利他與我同類機，  
遵依正士智者之所許，  
入菩薩行論釋今當作。 ^0-4

自見取執絹網所繫縛，謂言欲證小乘菩提果，不須證入甚深真如性，願捨諸顛倒說而諦聽。 ^0-5

### 0.1 總綱科判 ^0-1-0

其所造《入菩薩行論》分四：甲一、釋題；甲二、皈敬；甲三、正義；甲四、結義。今初： ^0-6

#### 0.1.1 甲一、釋題 ^0-1-1-0

梵語有四種，此是桑支達語也。此論題名「菩提」，藏語降曲；「薩埵」，藏語「生巴」；「雜雅」，藏语「覺巴」；阿瓦打[冒-目+阿]藏語「[覺/勿]巴。」 ^0-7

<!-- BATCH_STATE
current_chapter: 0
current_section: 0.1
current_subsection: 0.1.1
block_counter: 1
-->
```

---

### 6. 品質檢查表

-   [ ] 文件頂部存在包含所有必需字段的前置元數據區塊。
-   [ ] 標題嚴格按照 `## N. 標題 ^N-0`（或 `### N.M 標題 ^N-M-0`）的格式。
-   [ ] 標題行末尾沒有插入符號 `^`。
-   [ ] 所有散文部分都已拆分為短段落（最多 3-4 行）。
-   [ ] 根頌嵌入已正確插入，格式為 `![[1-SOURCES/Text/<root-text>.md#^N-V]]`。
-   [ ] 區塊識別碼是順序的、唯一的，並**只**在每個二級標題 (`##`) 下從 1 重新開始。
-   [ ] 狀態區塊已追加到批次末尾。
-   [ ] 沒有遺漏或總結任何文本、註釋或科判標籤。

---

## Mode 3 — Full formatting pipeline

### What this does

This mode formats a segmented Tibetan commentary file (in `0-INBOX/temp/`) that has a companion **outline file** -- a separate bullet-list ས་བཅད (bare topical outline) whose entries carry one dash-separated number per nesting depth.

> **Outline anchor scheme.** `align_headings.py` reads the outline's anchors as
> `^TOC-N-N-N…`, which is the scheme `4-SYSTEM/Guidelines/annotation-conventions.md` §6 deprecates. The
> script only uses those anchors to read a node's **depth** (its segment count)
> — it never writes them into the commentary, and the IDs it stamps are the
> canonical `^N-…-0` / `^{label}-{n}` forms. If your outline uses the current
> `^toc-X-Y-Z` namespace (§4), the depth reading is identical and the script
> needs only a case-insensitive prefix match. Do not "fix" an outline file into
> `^TOC-` form to satisfy the script. That outline is the ground truth for heading structure; the commentary file's own headings are matched against it rather than inferred purely from local context, because a commentary's headings are often bare, wrongly leveled, or formatted as bullets instead of real markdown headings.

Three tasks, each independently useful, normally run in this order:

1. **Heading tagging** (`4-SYSTEM/Skills/format-commentary/scripts/align_headings.py`) -- aligns the commentary's heading-shaped lines against the outline and rewrites each with the correct `#` depth.
2. **Segmentation** (`4-SYSTEM/Skills/format-commentary/scripts/find_long_segments.py`) -- in report mode (default), lists long body segments that look like two-or-more merged thoughts; with `--apply`, actually splits them at the vault's own sentence-break convention.
3. **Obsidian Block IDs** (`4-SYSTEM/Skills/format-commentary/scripts/tag_heading_block_ids.py` then `4-SYSTEM/Skills/format-commentary/scripts/tag_body_block_ids.py`) -- stamps two independent id sequences, one for headings and one for body text.

Run 1 before 3 (Block IDs are computed from heading depth/position, so headings must already be correctly leveled). Task 2 in **report mode** can run any time after 1, independently of 3 -- it only reads. Task 2 in **`--apply` mode** changes block boundaries, so it must run BEFORE Task 3b (body Block IDs) -- any split segment loses its old id (a single id can't identify two new pieces), and 3b is what assigns fresh ids to the pieces. If you run `--apply` on a file that's already been through Task 3, re-run 3b afterward before delivering.

### Task 1: Heading tagging (`align_headings.py`)

#### Why alignment, not just counting number-of-segments

A companion outline entry's `^TOC-1-1-2-2` tells you its depth (4 segments -> heading level 5) but the commentary's own heading TEXT differs slightly from the outline's -- the commentary adds an ordinal word (དང་པོ་/གཉིས་པ་/གསུམ་པ་/...) that the bare outline omits, and occasional wording drifts (e.g. outline `བོད་སྐད་ལྟར་སྨོས་པ` vs. commentary `བོད་སྐད་དུ་སྨོས་པ`). So matching is done by normalized-title similarity (ordinal-stripped, punctuation-stripped), using a Needleman-Wunsch global alignment over BOTH sequences in order -- this correctly handles:

- Outline nodes with **no heading of their own** in the body (the text goes straight from a parent heading into that parent's own children without ever stating the intermediate node -- e.g. "དགོས་པ་དངོས" is implied but never itself headed). These are expected gaps, not errors -- never fabricate heading text for them.
- Body headings with **no outline match** (hand-added `## N. Chapter N` title lines the outline doesn't track, or headings whose wording drifted too far to match confidently). Leave these completely untouched.
- Existing headings that are **already correctly leveled** -- these end up unchanged (idempotent).

#### What counts as a heading-candidate line

Any of: an existing markdown heading (`#` through `#############`), a `* **bold**` bullet, or a bare `**bold**` line. Commentaries commonly use bullets/bold as an ad-hoc heading substitute before this mode fixes them.

#### The glued-heading data quirk

Occasionally two headings end up on one physical line with a stray outline-number code stuck in the middle, e.g.:

```
**གསུམ་པ་ཕན་ཡོན་དཔེའི་སྒོ་ནས་བསྟན་པ།1.2.2.1.1.1.2.1.3.1 དང་པོ། གསེར་འགྱུར་...**
```

`align_headings.py` detects a 3+-segment dot-number glued directly onto non-whitespace (no space before it -- that's the signal it's stuck on, not just mentioned in prose) and splits it into two separate heading lines before alignment, so both halves get tagged at their correct (different) depths.

#### Running it

```bash
python3 4-SYSTEM/Skills/format-commentary/scripts/align_headings.py "<path-to-staged-file>" "<path-to-outline-file>"
```

Writes a `.BACKUP-YYYYMMDD-HHMMSS.md` next to the target before overwriting in place. Check the printed summary:

- **matched** should account for the large majority of heading-candidates.
- **low-confidence matches (<0.8)** -- skim every one of these; they're usually correct (wording drift) but occasionally a genuine mismatch. Never silently trust a run with many low-confidence matches on a new file family without spot-checking a handful of them against the source.
- **outline entries with no matching heading** and **body candidates with no outline match** are both normal in nonzero numbers (see above) -- only worry if the counts look wildly out of proportion to the file's length.

#### Verification: no heading level should jump by more than 1

After tagging, walk the headings in order and flag any place level increases by more than 1 step (e.g. level 5 straight to level 7). A jump of exactly the size of one missing outline node is expected and fine (see above); a jump you can't explain by a genuinely absent outline node is worth asking the user about rather than assuming. A quick way to check:

```python
prev = None
for lineno, level, text in headings:  # parsed the same way align_headings.py does
    if prev and level > prev[1] + 1:
        print(prev, "->", (lineno, level, text))
    prev = (lineno, level, text)
```

If the user has hand-corrected specific headings' levels since your last check, re-stage the file and re-run this check on the CURRENT content before reporting -- this file family is often being edited live by the user in parallel with your work.

#### Related manual cleanups (not automated by this skill, but common asks on the same files)

These aren't part of `align_headings.py` but come up on the same file family and are worth knowing:

- **Removing hand-added numbered chapter-title lines** (e.g. `### 2. ལེའུ་གཉིས་པ། སྡིག་པ་བཤགས་པ། ^2-0`) if the user no longer wants them, once the outline-based headings already carry that structure. Do this as a simple line-removal pass (also delete one of the two blank lines left dangling around each removed line, to avoid a double blank), keyed on a regex like `^#+\s*\d+\.\s*ལེའུ`.
- **Inserting a blank line between two headings that are directly adjacent** (no blank line between them) -- the convention wants one blank line between every pair of heading lines, matching example: `####### **...**` immediately followed by `######## **...**` should get a blank line inserted between them. Simple line-scan: after any heading line, if the very next line is also a heading line, insert a blank line.

### Task 2: Segmentation (`find_long_segments.py`)

#### What the segmentation convention actually is

**Calibration, not a rule.** The figures below were measured on one reference commentary; they are what a mature Tibetan sa-bcad commentary happened to look like, and they are the defaults the script ships with. Re-measure on your own file before trusting them. On that reference file: body segments in this file family are **not** "one sentence per block." In a sample of 1402 prose blocks in that file, ~84% legitimately contain more than one double-shad-terminated sentence merged into one coherent explanatory unit, with a median length around 420 characters. The file's own practical ceiling sits around 800 characters -- blocks at or above that are rare (~10% of prose blocks) and are exactly the ones worth a second look or a split. Two hypotheses were tested and rejected before landing on this: "split at every ordinal word (དང་པོ་/གཉིས་པ་/...)" only matched 57% of real block starts (43% of ordinals appear mid-block, continuing a thought rather than opening a new one), and "one sentence per block" is flatly contradicted by the 84% figure above. So: **don't lower `--min-length` "to be thorough"** -- that fights the vault's actual convention and over-splits perfectly normal blocks. The split point itself, when a block genuinely is too long, is the same signal the vault's own text uses at every real paragraph break: a double shad (the normal Tibetan full stop) with more text after it before the segment's end, chosen as the one nearest the exact midpoint among those falling within the middle 65% of the segment (between 20% and 85% of its length, so a split is never forced right at an edge).

**Watch for the double-shad spacing convention differing by commentary/edition.** One reference commentary spaces the two `།` characters apart (`། །`, ~4164 occurrences, essentially the only form used); another glues them with no space (`།།`, 693 occurrences vs. only 4 spaced ones) -- a different digitization convention, not an error in either file. `find_long_segments.py`'s break pattern matches either spacing (`།\s*།`) so this doesn't need per-file configuration, but if you're extending or reimplementing this logic, check both counts on a new file before assuming one convention -- a script hardcoded to only the spaced form would find almost no break points at all on a glued-convention file (this happened on the first `--apply` run against a glued-convention file: 1 giant 255k-character segment split into only 4 pieces before the fix, 302 sensible pieces after).

#### Two modes

**Report mode (default, no `--apply`)** -- never edits the file. Lists candidates for a human, or for a follow-up `--apply` run, to review.

```bash
python3 4-SYSTEM/Skills/format-commentary/scripts/find_long_segments.py "<path-to-staged-file>" --min-length 800 --out report.md
```

Deliver `report.md` to the user (it's a markdown table -- send it as a file, don't try to paste an 800+-row table into chat). Segments with a clean break are strong candidates; segments without one still get listed (long but no obvious midpoint) since they're worth a human look even though the split point isn't mechanically obvious -- never invent a split point for these without a clear sentence boundary to point to.

**Apply mode (`--apply`)** -- actually re-segments the file. For every prose body segment at or above `--min-length`, recursively finds the best interior double-shad break, splits there, and repeats on each resulting half -- so a block over-merged from three sentences becomes three blocks in one pass, not just two. A half that's still too long but has no further interior double-shad to split at is left as one piece (the same "long segment without an obvious break point" case report mode surfaces) -- this never invents a split point without a genuine sentence-boundary anchor.

```bash
python3 4-SYSTEM/Skills/format-commentary/scripts/find_long_segments.py "<path-to-staged-file>" --min-length 800 --apply
```

`--apply` is meant for two situations:

- **Cleaning up a handful of over-long segments** in an already-segmented file (the original use case) -- most calls will change very few blocks.
- **Segmenting a RAW or barely-segmented commentary from scratch** -- point it at a file where whole chapters sit in one giant paragraph, and it recursively cuts every such blob down to this vault's normal block granularity using the exact same break rule throughout. This is what makes Task 2 usable on **other commentary texts**, not just as a QC pass on the one it was reverse-engineered from. When asked to segment a new or raw commentary "the same way as the reference file," this is the tool -- there is no separate script for that request.

A segment's existing Obsidian Block ID (if any) is **dropped** when that segment is split -- one id can't identify two new pieces, and every piece needs its own fresh id. **Run Task 3b (`tag_body_block_ids.py`) again after any `--apply` run that reports changes**, to (re)stamp ids on the new block boundaries; it's explicitly designed to assign fresh ids to anchor-less segments, whatever caused them to lack one. A segment that was NOT split keeps its existing id untouched. Headings, frontmatter, lone image-embed lines, and verse/stanza quote blocks (consecutive `>` lines) are never touched or counted in either mode -- splitting a quoted verse doesn't make sense, and this task is scoped to prose only.

Writes a `.BACKUP-YYYYMMDD-HHMMSS.md` before overwriting, matching the other scripts' convention. Report-mode output is unaffected by the `--apply` code path -- running without `--apply` behaves exactly as before this capability was added.

### Task 3: Obsidian Block IDs -- two separate sequences

The `^label-N` anchors are **Obsidian Block IDs**. This skill stamps TWO independent sequences that must never be merged or cross-numbered:

#### 3a. Heading Block IDs (`tag_heading_block_ids.py`)

Tree-shaped, one id per heading, encoding its position in the outline:

- Every id is a path of 1-based sibling-position numbers (one segment per level below the first level-2 heading), always ending in a constant `-0`. The count of `-N-` segments in the id always equals `heading level - 1` -- e.g. `^I-1-1-2-0` is 4 segments -> level 5.
- The level-2 (`##`) headings get root labels: the FIRST one is `"I"`; every one after that is a plain arabic number starting at 1 (2nd level-2 heading -> `"1"`, 3rd -> `"2"`, ...). **This is the hand-set convention of the corpus the script was written for** — a roman numeral for the intro zone, arabic for the chapters (`4-SYSTEM/Guidelines/annotation-conventions.md` §7, the registered `^I-*` intro zone). A file whose `##` labels are plainly `1`, `2`, `3` from the start needs that root-labelling changed, or the script will disagree with its existing anchors — which is exactly what the validation step below catches.
- Every other heading gets its 1-based sibling index among headings sharing the same nearest-shallower-level ancestor, appended to that ancestor's path (ancestor's own trailing `-0` dropped), plus its own trailing `-0`.
- **Skipped levels** (outline has an implicit parent that never got its own heading -- see Task 1) are padded with an implicit sibling index of 1 for the missing level, so id depth still matches heading level across the gap. Don't try to "fix" this by inventing heading text.

```bash
python3 4-SYSTEM/Skills/format-commentary/scripts/tag_heading_block_ids.py "<path-to-staged-file>"
```

Check the printed depth-mismatch and duplicate-id counts -- both must be 0. Validate against any pre-existing hand-set anchors in the file (e.g. `^I-0`, `^1-0`) if present -- the algorithm should reproduce them exactly; if it doesn't, something about this file's root-labeling doesn't match the "I / 1 / 2 / ..." convention and you should ask the user rather than force it.

#### 3b. Body-text Block IDs (`tag_body_block_ids.py`)

Flat, restarts only at level-2 headings:

- `<label>` is inherited from the nearest preceding level-2 heading's OWN id (its label, with trailing `-0` dropped) -- so it's always `"I"`, `"1"`, `"2"`, etc., matching 3a's root labels.
- `<n>` restarts at 1 right after that level-2 heading and counts every body segment (paragraph or verse-stanza) continuously -- across every chapter and sub-heading under that ONE level-2 heading -- until the next level-2 heading. **This does not restart at chapter boundaries or at any heading deeper than level 2** -- and it is the canonical rule (`4-SYSTEM/Guidelines/annotation-conventions.md` §3).
- Content before the very first level-2 heading gets label `"0"` (`^0-1`, `^0-2`, …).
- **Every non-heading, non-frontmatter, non-lone-embed-line block gets an id, whether or not it already had one.** A body block that currently has NO anchor at all (e.g. a paragraph a human split off from a bigger block by hand, leaving the new fragment un-anchored) must still be tagged -- don't just renumber existing anchors and skip blocks that lack one. This was a real bug once: silently skipping anchor-less blocks left segments permanently untagged.
- Frontmatter (the `---`-delimited YAML block at the very top) and lone image-embed lines (`![[...]]`, referencing another file's own block) are never touched or counted.
- A heading line is always its own block boundary even with no blank line separating it from adjacent text (e.g. YAML frontmatter's closing `---` immediately followed by the `# document title` heading with no blank line between them) -- grouping blocks purely by blank lines would merge the heading into the frontmatter's "block" and corrupt it. `tag_body_block_ids.py` handles this; if you ever write a variant of this logic yourself, keep this in mind.

```bash
python3 4-SYSTEM/Skills/format-commentary/scripts/tag_body_block_ids.py "<path-to-staged-file>"
```

Check the printed per-label range (`label X: 1..N`) -- ranges should be gap-free and start at 1 for each label. The "segments that previously had NO Obsidian Block ID" list should be reviewed even when it's non-empty and the run looks otherwise fine -- each one is a real content segment that had silently been missing an id; tell the user about any it finds, since it means their file had a gap they may not know about.

### How to run the whole pipeline

1. Work on a copy in `0-INBOX/temp/`, with the outline file alongside it (Task 1 needs both).
2. **Re-read the file right before each task**, not just once at the start of the session -- a commentary being formatted is often edited live by the contributor in Obsidian at the same time. Diff the current file against what you last worked from before assuming nothing changed; if it moved, redo your analysis on the current content rather than clobbering their edits with stale output.
3. Run Task 1 (`align_headings.py`), review its summary. If Task 2 is being run in `--apply` mode (actually segmenting, not just checking), run it **next**, before Task 3 -- it changes block boundaries, so headings must already be correct (from Task 1) but body Block IDs must not be stamped yet (Task 3b runs after, to tag the new pieces). Then run Task 3a (`tag_heading_block_ids.py`) followed by 3b (`tag_body_block_ids.py`), in that order. Task 2 in **report mode** is the exception -- it can run independently at any point after Task 1 and never needs to run before delivering a file, since it only reads.
4. Each script writes its own timestamped backup next to the target before overwriting in place -- running the full pipeline leaves multiple backups, which is expected, not a bug.
5. Write the final file back to its **original path** (don't leave a `_tagged`/`_numbered`/`_segmented` sibling behind). Check the file's modification time against the copy you started from first, so a newer edit from the contributor is never silently overwritten.
6. Tell the user: how many headings were retagged (and flag any low-confidence matches you didn't already resolve); if Task 2 ran in `--apply` mode, how many segments were split and into how many pieces, and confirm Task 3b was re-run afterward; if Task 2 ran in report mode, how many long-segment candidates were found and where the report was sent; and the final Block ID ranges for both headings and body text.

### Notes on this kind of file

- These are large (multi-thousand-line) Tibetan commentary files with embedded verse quotes (`>` blockquote lines), transclusion embeds (`![[other-file#^id]]`), and pre-existing partial Obsidian Block IDs mixed in with the heading structure. None of the scripts here ever touch verse-quote content or cross-file embeds beyond deciding whether to skip them.
- If a file in this set doesn't come with a companion ས་བཅད outline file, or uses a different chapter-heading convention than this skill assumes, ask the user rather than guessing -- these scripts are intentionally narrow to the conventions validated on this vault's files. Don't assume a missing outline means the whole skill is blocked: Task 2 and Task 3 don't need one (one commentary had no outline anywhere in the vault and zero existing headings -- confirmed by filename/content search before asking -- so Task 1 was skipped on the user's confirmation and Tasks 2+3 ran alone; with no level-2 headings to key off of, every body segment ends up under a single label `"0"` in 3b, which is correct and expected until Task 1 can eventually run once an outline exists).
- **Segmenting a raw or freshly-received commentary from scratch** (no existing block structure at all, e.g. one giant paragraph per chapter): Task 2 `--apply` is the tool for this -- see "Apply mode" above. It only needs paragraph-level text to work on; it does not require Task 1/3 to have already run, though Task 1 should still run first if the file also needs heading alignment, since Task 2 skips heading lines when deciding what counts as a prose block. Always run Task 2 `--apply` before Task 3b so the newly-created pieces get proper Block IDs rather than being left anchor-less.
- Some commentaries use an older convention where the sa-bcad numbering is typed bare into the commentary text (no separate outline file) and body Block IDs restart at every chapter rather than at every level-2 heading. This pipeline does **not** handle that shape: it needs the companion outline, and its `tag_body_block_ids.py` restarts only at `##` (which is the canonical rule — `4-SYSTEM/Guidelines/annotation-conventions.md` §3). If it is unclear which convention a file uses, ask the contributor before picking one.
