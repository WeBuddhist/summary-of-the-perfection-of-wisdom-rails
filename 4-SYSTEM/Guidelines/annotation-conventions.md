# Annotation Conventions — Block IDs and Tag Schemes

The authoritative reference for how a text in this vault is marked up. Every
skill in `4-SYSTEM/Skills/` implements this document, and `4-SYSTEM/CLAUDE.md`
§5–§5b summarises it. **When a skill, `CLAUDE.md`, or a folder `About` file
disagrees with this document, this document wins** — fix the other one.

The one exception is a deviation this vault has *registered* in its annex
(`vault-annex.md`): see §7. A registered deviation overrides the default here
for the files it names, and nothing else.

This file exists because the same job was re-implemented in several vaults with
slightly different tag vocabularies. There is one vocabulary. It is here.

---

## 1. Content block IDs — the citation unit

Every verse or discrete prose block ends with a block ID. This is the only
mechanism for verse-level cross-referencing (`[[file#^1-23]]`).

```
[verse or prose block] ^1-1
```

- Placed at the end of the **last line** of the block, preceded by one space.
- **No zero-padding.** `^6-33`, never `^06-033`.
- The scheme in use is declared per file in the `verse_id_format` frontmatter
  field, so a parser never has to guess.

Two schemes exist side by side.

### 1a. `chapter-verse` — Tibetan, Pāli, Chinese, English, and the generic path

`^chapter-verse`, e.g. `^1-1`, `^6-33`. Verse numbers restart at 1 in each
chapter. Content before chapter 1 uses `^0-N`.

### 1b. Four-zone scheme — Sanskrit only

Sanskrit editions carry front matter, chapter intros and colophons that the
flat scheme cannot address, so they use zones:

| Zone | Symbol | Content ID | Heading ID |
|---|---|---|---|
| Pre-title | `T` | `^T-1`, `^T-2` … | — |
| Front matter | Roman numeral | `^I-1`, `^I-2` … | `^I-0`, `^II-0` … |
| Chapter intro | — | `^N-I`, `^N-II` … (chapter-relative) | — |
| Main verses | Arabic numeral | `^N-V` (`^1-1`, `^6-134`) | `^N-0` |
| Chapter colophon | lowercase letter | `^N-a`, `^N-b` … | — |
| Book colophon (after the last chapter) | lowercase letter | `^a`, `^b` … | — |

**Interpolated verses** — when a source edition repeats a verse number
(`॥24॥ … ॥24॥`), the second occurrence takes `^C-Vx1`, the third `^C-Vx2`. The
counter always starts at `1`, even for a single duplicate. Never a bare `^C-Vx`.

**Book title ID.** The generic rule below says the `#` title line takes no ID.
Sanskrit is the one documented exception: when the book *is* the root (nothing
above it), `#` takes `^0`. Only when the book sits inside a larger collection —
so `##` is the book level — does `#` go unlabelled.

---

## 2. Heading anchors — the `-0` slot

Headings are **editorial structure added to the text**, not original content.
To mark that distinction and to guarantee no collision with content IDs, every
heading block ID ends in **`-0`**. The zero slot is reserved for the heading;
original content in that section always starts at `1`.

| Level | Markdown | Purpose | Block ID | Example |
|---|---|---|---|---|
| 1 | `#` | Title of the work | none (see §1b) | `# [Title of the work]` |
| 2 | `##` | Chapter / top-level division | `^N-0` | `## 1. ལེའུ་དང་པོ། ^1-0` |
| 3 | `###` | Section | `^N-N-0` | `### 1.2 Some Section ^1-2-0` |
| 4 | `####` | Sub-section | `^N-N-N-0` | `#### 1.2.3 Sub-section ^1-2-3-0` |
| 5 | `#####` | Sub-sub-section | `^N-N-N-N-0` | `##### 1.2.3.1 … ^1-2-3-1-0` |
| 6 | `######` | Fifth-level node | `^N-N-N-N-N-0` | `###### 1.2.3.1.1 … ^1-2-3-1-1-0` |
| 7+ | `######` + `**bold**` title | Deeper nodes | full path + `-0` | `###### **1.2.3.1.1.4 …** ^1-2-3-1-1-4-0` |

```markdown
## 0. Introduction ^0-0

༄། །བྱང་ཆུབ་སེམས་དཔའི་སྤྱོད་པ་ལ་འཇུག་པ་བཞུགས་སོ། ། ^0-1

## 1. ལེའུ་དང་པོ། ^1-0

བདེ་གཤེགས་ཆོས་ཀྱི་སྐུ་མངའ་སྲས་བཅས་དང་། །
ལུང་བཞིན་མདོར་བསྡུས་ནས་ནི་བརྗོད་པར་བྱ། ། ^1-1

### 1.2 Some sub-section ^1-2-0

First prose block. ^1-2-1
Second prose block. ^1-2-2
```

Rules:
- Chapter `0` is always the pre-chapter introduction (`## 0. Introduction ^0-0`).
- **Heading block IDs use the full decimal path of the structural tree plus
  the `-0` slot. There is no segment cap.** A node numbered `1.2.2.1.1.4` in
  the tree gets `^1-2-2-1-1-4-0`; `1.3.2.2.2.2.1.1.1` gets
  `^1-3-2-2-2-2-1-1-1-0`. Depth follows the tree exactly — never flatten,
  merge or truncate a deep tree to fit a shorter ID.
- **Markdown heading level follows tree depth.** `##` is the text's top-level
  division (chapter, or the first level of a commentary's *sa bcad*); each
  deeper tree level adds one `#`. Markdown stops at `######` (six), so nodes
  deeper than that keep `######`, wrap the heading title in `**bold**` to make
  the extra depth visible, and rely on the full-path block ID for the real
  depth. The block ID, not the number of `#`, is the authoritative record of a
  heading's position in the tree.
- When a TOC file's depth-1 entry is the work's own title (which is already
  the file's `#` line), that entry is excluded from insertion and its children
  start at `##`. Otherwise the tree's depth-1 nodes are the `##` headings.
- No zero-padding on any segment.

---

## 3. Commentary block IDs — keyed off a human label

Commentaries follow §1 and §2 with one difference in **who assigns the key**.
A `##` heading's ID in a commentary is written **by hand** by the contributor
and is never generated, edited or guessed by a skill — the contributor chooses
the label (`^1-0`, `^I-0`, `^a-0`, or any short token) to key that section to
the root text's structure. Everything beneath it is then derived from that same
label:

```markdown
# ༄༅། །ཕྱག་འཚལ་ཉེར་གཅིག་གི་བསྟོད་འགྲེལ … ^0
## དང་པོ་སྦྱོར་བ་ཚོགས་བསགས། ^1-0        ← manual, never touched
### ཚོགས་ཞིང་སྤྱན་འདྲེན་པ། ^1-1-0         ← derived
དེའང་རྗེ་བཙུན་སྒྲོལ་མའི་ཡོན་ཏན་… ^1-1      ← derived, body counter off the same label
![[bo-root-text#^1-1]]                    ← transclusion: never consumes a counter value
```

The `#` title is the one auto-generated ID (`^0`). Transclusion lines are
structural, not content — they never take an ID and never advance the body
counter.

---

## 4. `^toc-X-Y-Z` — a separate namespace

The standalone decimal outline block that `add-toc` writes at the top of a
document uses `^toc-X-Y-Z`. **This is not the same namespace as the `^N-0`
heading anchors** and the two must not be conflated: `^toc-1-2-0` indexes a
line in the outline block, `^1-2-0` indexes the actual body heading. A TOC
entry may link to its heading; it never replaces it.

---

## 5. Inline TOC wikilinks

Texts in the commentarial tradition announce their own structure inline
(*sa bcad* / ས་བཅད): a sentence enumerates the upcoming sections before
treating each one. Those phrases are original content, and they are also the
textual source of the headings. Tagging them makes that link explicit.

```markdown
## ལེའུ་དང་པོ། ^1-0
[[#^1-0|ལེའུ་དང་པོ་]]ལ་[[#^1-1-0|མདོར་བསྟན་པ་]]དང་[[#^1-2-0|རྒྱས་པར་བཤད་པ་]]གཉིས་ཡོད་པ་ལས།

### མདོར་བསྟན་པ། ^1-1-0
[[#^1-1-0|དང་པོ་མདོར་བསྟན་པ་]]ནི་འདི་དང་འདིའོ།།
```

- In the **enumeration sentence**, each announced term links forward to the
  heading it introduces: `[[#^N-N-0|term]]`.
- In the **body of a section**, the restatement of that section's title links
  to its own heading. This self-reference is deliberate: it marks the phrase as
  the textual source of the heading, so a backlink index can show, for every
  heading, every place that announced it.
- Cross-file: `[[relative/path#^N-N-0|term]]`.
- Display text is the structural term alone, not the full grammatical phrase.
- Wikilinks are the **only** inline tagging mechanism. No italics, no HTML
  spans.

This step is optional — run it only for texts that actually contain such
announcements.

---

## 6. Deprecated — `^TOC-N`

Older drafts and one-off scripts used `^TOC-N` for chapter anchors
(`## 1. … ^TOC-1`). **It is wrong.** The canonical form is `^N-0`. A parser
expecting `^N-0` does not recognise a `^TOC-N` anchor, so the text silently
ends up with no table of contents and no error. Correct any `^TOC-N` you
encounter before using the file.

---

## 7. Registered deviations — declared in the vault annex

The schemes above are the default. A vault may declare a bounded deviation in
its annex (`4-SYSTEM/Guidelines/vault-annex.md`) when the text genuinely
needs it; a skill honours a declared deviation and never invents one. The
recognised deviations are:

- **`^I-*` intro / `^a-*` back-matter zones** for non-Sanskrit texts whose
  front matter (homage, prologue, translator's preface) or back matter
  (colophon, dedication) must stay addressable apart from the chapters
  (`^I-1`, `^I-2`, …; `^a-1`, `^a-2`, …; headings `^I-0`, `^a-0`). The
  annex names which files use them and the `verse_id_format` value they
  declare.
- **Bible-style `book-verse`** (`verse_id_format: book-verse`) for texts
  addressed by book and verse with no chapter level: `^N-V` where `N` is the
  book. The annex lists the book numbering.
- **Letter sub-namespaces** for a heading whose children are lettered rather
  than numbered in the tradition (`^1-0a-1`, `^1-0b-1`, …): the letter is
  appended to the parent's `-0` slot and the children count from `1` under it.
  Use only when the source's own structure is lettered.
- **Flat `^N`** (`verse_id_format: verse`) for collections of short texts
  where each file is one text with no internal chapters: blocks are `^1`,
  `^2`, … and the single heading, if any, is `^0`.

A deviation is registered once, in the annex, with the list of files it
applies to. Files not listed follow §1–§2 unchanged.

---

## Where to look next

- [`../CLAUDE.md`](../CLAUDE.md) §5–§5b — the operational summary of this document.
- [`vault-annex.md`](vault-annex.md) — this vault's addressing scheme and any registered deviation.
- [`../../1-SOURCES/About Sources.md`](../../1-SOURCES/About%20Sources.md) §5 — block IDs in the context of the full source-file rules.
- [`skill-locations.md`](skill-locations.md) — the logical location names the shared skills use.
