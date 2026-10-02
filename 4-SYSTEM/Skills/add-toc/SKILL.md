---
name: add-toc
description: >
  Generate a nested, decimal-numbered Table of Contents (TOC / dkar-chag) from
  a flat draft list at the top of a markdown document. Each entry in the
  output is tagged with a `^toc-X-Y-Z` block ID. The output file is saved to
  0-INBOX/temp/ with the prefix `toc-` added to the original filename.

  Trigger this skill whenever the user says things like:
  "add a TOC", "generate a table of contents", "create a dkar chag",
  "prepend a TOC to this file", "add block-ID toc entries", or any request
  to produce a nested outline at the top of a document.
---

# Add-TOC Skill

The input is a **flat, unindented list** of outline items already present in
the document's TOC section (originally written for Tibetan texts; the
hierarchy-inference heuristics below are Tibetan-specific — adapt the ordinal
vocabulary for another language). All items sit at the same bullet level
regardless of their structural depth. Your job is to read this list,
reconstruct the hierarchy from the text itself, and write a clean nested TOC.

Note: the `^toc-X-Y-Z` IDs produced by this skill are a **separate namespace**
from the `^N-0` / `^N-N-0` heading anchors — see `4-SYSTEM/Guidelines/annotation-conventions.md` §4.
They index the standalone decimal outline block this skill builds, not the body
headings themselves. A TOC entry may link to its heading; it never replaces it.
Do not confuse the two.

---

## Step 1 -- Read the draft TOC

Use the Read tool to fetch only the opening portion of the file -- enough to
capture the full TOC section. Stop at the first `---` or `##` heading that
follows the TOC list.

*Example (from the Bodhicaryāvatāra)* — the draft looks like this (all
bullets at the same level):

```
* །དབུ་ནས་ཞབས་སུ་བསྡུས་པའི་དོན་གང་ཡིན་ཞེ་ན༑
* དགོས་ཆེད་སུ་ཞིག་གི་དོན་དུ་མཛད་ཅེ་ན།
* གཉིས་པ་སློབ་མས་ཇི་ལྟར་ཉན་པའི་ཚུལ་ལ། ཀུན་སློང་དང་། ཀུན་སྤྱོད་གཉིས། དང་པོ།
* གཉིས་པ་ཀུན་སྤྱོད་ལའང་། སྤང་བྱའི་ཀུན་སྤྱོད་དང་། བླང་བྱའི་ཀུན་སྤྱོད་གཉིས།...
* དྲི་མ་དྲུག་ནི།
...
```

---

## Step 2 -- Infer the hierarchy

Hierarchy is encoded entirely in the text. Read each item and assign a depth
using these signals, in order of priority:

### 2a. Ordinal prefixes signal sibling rank

An item beginning with an ordinal is a sibling of other items at the same
ordinal series. The series restarts when a new parent is introduced:

*Example (from the Bodhicaryāvatāra) — Tibetan ordinal vocabulary*:

| Prefix | Meaning |
|---|---|
| དང་པོ། / དང་པོ་ | first |
| གཉིས་པ། / གཉིས་པ་ | second |
| གསུམ་པ། / གསུམ་པ་ | third |
| བཞི་པ། / བཞི་པ་ | fourth |
| ལྔ་པ། / ལྔ་པ་ | fifth |
| དྲུག་པ། / དྲུག་པ་ | sixth |
| བདུན་པ། / བདུན་པ་ | seventh |
| ... | ... |

Bracket markers (༡༽, ༢༽, ཀ༽, ཁ༽) and parenthetical numbers follow the same
logic. For another language, substitute that language's own ordinal series.

### 2b. "Introduction + enumeration" items shift depth

An item that **introduces sub-items** (ending with a count like `གཉིས།`,
`གསུམ་སྟེ།`, `བཞི་ལས།`, or with `ལ།` in the Tibetan example) is a parent. The
next item(s) are its children -- one level deeper.

An item that simply names one element of an enumeration (short, no trailing
count phrase) is a leaf at that depth.

### 2c. Depth resets when a peer ordinal appears

When you see the "second" marker after a series of children, you return to
the depth of the matching "first" marker that opened that sibling series.

### 2d. Items with no ordinal prefix

Items with no ordinal prefix and no introduction phrase are at the same depth
as the previous item unless context indicates otherwise.

---

## Step 3 -- Assign toc_ids

Walk the hierarchy in document order. Maintain a counter per depth level;
reset deeper counters whenever you move up to a shallower level.

```
depth 1  ->  1, 2, 3, ...
depth 2  ->  1-1, 1-2, ..., 2-1, 2-2, ...
depth 3  ->  1-1-1, 1-1-2, ..., 1-2-1, ...
```

---

## Step 4 -- Clean the display text

Strip from each item:
- Leading `*` or `-` bullet
- Leading ordinal prefix (in the Tibetan example: དང་པོ།, གཉིས་པ།, གཉིས་པ་, གསུམ་པ།, བཞི་པ།, etc.)
- Leading bracket markers (༡༽, ༢༽, ཀ༽, ཁ༽, ...)
- Leading decimal labels (༡.༡, ༢.༡, ... or 1.1, 2.1, ... depending on language)
- Trailing `ལོ།།` -> replace with `།` (Tibetan example)
- Trailing `།།` -> replace with `།` (Tibetan example)
- Trailing block IDs (`^anything`)
- Wiki-link wrappers (`[[#^id|text]]` -> keep `text`)

Do **not** strip the body of the item -- keep the full descriptive phrase.

---

## Step 5 -- Render

Format each entry as:

```
{INDENT}* {DECIMAL} {CLEAN_TEXT} ^toc-{TOC_ID}
```

- `INDENT`: 3 spaces × (depth − 1); depth-1 items have no indent
- `DECIMAL`: `1.` for depth-1, `1.1` for depth-2, `1.1.1` for depth-3, etc.
- No blank lines between entries
- Precede the block with `## Table of Contents` (or the equivalent bilingual/native-language heading, e.g. `## དཀར་ཆག / Table of Contents`)
- Follow it with `---`

*Example (from the Bodhicaryāvatāra)*:
```
## དཀར་ཆག / Table of Contents

* 1. བཤད་བྱའི་ཡན་ལག་བཤད་པ། ^toc-1
   * 1.1 སློབ་དཔོན་གྱིས་ཆོས་ཇི་ལྟར་འཆད་ཚུལ། ^toc-1-1
      * 1.1.1 སློབ་དཔོན་སངས་རྒྱས་ཀྱིས་ཆོས་ཇི་ལྟར་འཆད་ཚུལ། ^toc-1-1-1
      * 1.1.2 སློབ་དཔོན་དགྲ་བཅོམ་པས་ཆོས་ཇི་ལྟར་འཆད་ཚུལ། ^toc-1-1-2
   * 1.2 སློབ་མས་ཇི་ལྟར་ཉན་ཚུལ། ^toc-1-2
* 2. བཤད་བྱ་དངོས་བཤད་པ། ^toc-2

---
```

---

## Step 6 -- Write the output

Write the complete file (new TOC section + original body) to:

```
0-INBOX/temp/toc-{original-filename}
```

If an existing TOC section is present, **replace it** — never leave two. A TOC
section is the heading that opens the outline block together with the bullet
list under it, whatever that heading is called in the document's own language
(`## དཀར་ཆག`, `## དཀར་ཆག / Table of Contents`, `## Table of Contents`, `## Contents`,
`## Outline`, …), up to the `---` or the next `##` heading that closes it.
Delete that whole block and write the new one in its place. Splice the TOC
immediately after the YAML frontmatter.

---

## Step 7 -- Verify and present

Read the first 40 lines of the output file to confirm the structure looks
right. Report the output path to the user.

---

## Provenance

The hard-coded vault output folder it wrote to is now the logical name `0-INBOX/temp/`,
resolved per repo from `4-SYSTEM/Guidelines/skill-locations.md`; the conventions reference now points
at `4-SYSTEM/Guidelines/annotation-conventions.md` §4. The Tibetan-specific hierarchy heuristics are
unchanged and labelled as examples.
