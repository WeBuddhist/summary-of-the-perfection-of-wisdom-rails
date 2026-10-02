---
registered_id: <registered-id>
title: "<title in the original language, verbatim from the commentary frontmatter>"
title_in_english: "<English title verbatim from the commentary frontmatter>"
author: "<author in the original language, verbatim>"
author_in_use: "<verbatim from the commentary frontmatter — the human-curated in-article name form; omit the key if the source frontmatter does not carry it>"
author_in_english: "<English author verbatim>"
source_file: $COMMENTARIES/<filename>.md
toc_tree_source: <path to the toc-tree file actually used>
tree_qc_reports: [<path to qc_check_tree.py's report>, <path to qc_tree_vs_source.py's report>]
language: <lang_tag>
citation_form: block-id | segment | line
method: tree-guided-extraction
claim_id_scheme: "c-<decimal-with-dashes>-<n>, e.g. node 1.2.3's third claim is c-1-2-3-3 — never a bare decimal, never collides with a node heading number"
claim_count: <integer, computed by counting claim headings below — never copied from another file>
status: draft
---

## Tree-guided claims — <title_in_english>

**Commentary:** `<registered-id>` · <author_in_english>
**Source:** [`<filename>.md`]($COMMENTARIES/<filename>.md)
**TOC tree:** [`toc-tree-<registered-id>.md`](<relative path to toc_tree_source>)
**Citation form:** <one sentence stating how the citations in this file resolve to the
source — block ID, segment number, or line number.>

> Every claim below was extracted fresh from this node's own text, in isolation, by a
> subagent that saw only this node's source window and never any other commentary's claims
> file. No claim is copied, paraphrased, or re-bucketed from an earlier extraction run of
> any kind. Headings and their decimal numbers are drawn from the commentary's own
> TOC tree, not invented here. Claim IDs (`c-...`) are never node decimals.

---

### Grounding index

<One entry per distinct referent actually named in the commentary body, its TOC-tree node
titles, or its frontmatter. Keep every kind-group heading even when empty ("None
attested."). Populated cumulatively as each node's subagent reports what it found in its
own window; the orchestrating agent merges the reports, deduplicating only when the source
itself equates two mentions.>

#### Figures and forms (deities, aspects, emanations) — optional, drop for a genre with no such referents
| ID | Name (verbatim) | What the source says it is | Attested at |
|---|---|---|---|
| FIG-1 | … | | |

#### Persons (authors, teachers, lineage figures, requesters)
| ID | Name (verbatim) | Role stated in the source | Attested at |
|---|---|---|---|
| PER-1 | … | | |

#### Places
| ID | Name (verbatim) | Context | Attested at |
|---|---|---|---|
| PLC-1 | … | | |

#### Texts and mantras cited
| ID | Name / incipit (verbatim) | How the source uses it | Attested at |
|---|---|---|---|
| TXT-1 | … | | |

#### Events and dates
| ID | Event / date (verbatim) | Context | Attested at |
|---|---|---|---|
| EVT-1 | … | | |

---

### 0. Front matter

<Anything before the tree's first node's window — opening formula, homage, colophon
preamble — extracted as its own claims, same rules as every other node. Omit this heading
only if the tree's first node genuinely opens the document.>

#### c-0-1 <short label>
**Original:** <the claim, commentator's own wording, quoted from THIS node's window only>
**English:** <one-line gloss>
**Type:** structural | word-gloss | etymology | iconography | identification | doctrinal | activity | practice | ritual | mantra | benefit | attribution
**Referent:** <Grounding-index ID(s) with basis — `(stated)` only if the name is inside
*this claim's own* `**Original:**` string, `(node)` from the enclosing node's title,
`(section-opener)` from the node's own opening sentence — or exactly `[unanchored]`.>
**Cite:** ($COMMENTARIES/<filename>.md#^<block-id>)

---

### 1. <node title, exactly as the tree gives it> [[<pointer, if the tree has one>]]

<Claims from this node's own window before its first child's window begins.>

#### c-1-1 <short label>
**Original:** <…>
**English:** <…>
**Type:** <…>
**Referent:** <…>
**Cite:** ($COMMENTARIES/<filename>.md#^<block-id>)

---

#### 1.1 <child node title> [[<pointer>]]

##### c-1-1-1 <short label>
**Original:** <…>
**English:** <…>
**Type:** <…>
**Referent:** <…>
**Cite:** ($COMMENTARIES/<filename>.md#^<block-id>)

⚑ **c-1-1-2 <short label — internal tension>**
- **Position 1:** <original language> — (…md#^<block-id>)
- **Position 2:** <original language> — (…md#^<block-id>)
**English:** <one line stating what the tension is>

---

<... one heading per TOC-tree node, in the tree's own document order, depth mirrored by
heading level (## depth 1, ### depth 2, #### depth 3+, capped at #### — flatten anything
deeper into a nested list under the #### heading) ...>

### Z. Back matter

<Anything after the tree's last node's window — closing benefits, colophon, dedication.
Omit if the tree's last node genuinely closes the document.>

---

### Internal tensions (rollup)

<One line per ⚑ claim above. If none, write "None observed." and keep the heading.>

- ⚑ c-1-1-2 — <one-line English gloss> (see node 1.1)

---

### Unanchored claims (rollup)

<One line per claim marked `[unanchored]`, with the reason. If every claim is anchored,
write "None — all claims anchored." and keep the heading.>

- c-1-2-4 — <reason>

---

### Coverage log

| Node | Source window | Claims extracted | Notes |
|---|---|---|---|
| 0 (front matter) | <first block ID>–<block ID> | c-0-1, … | |
| 1 | <block ID>–<block ID> | c-1-1 | |
| 1.1 | <block ID>–<block ID> | c-1-1-1, c-1-1-2 | |
| … | | | |
| Z (back matter) | | | |

**Nodes with no independently attested line (`[[?]]` in the tree):** <list them and which
neighbouring node's window you folded their extraction into — do not skip a node's claims
just because its own pointer is unresolved.>
**Segments yielding no claim:** <list ranges that are pure root-text quotation, colophon,
or scribal matter, so a reviewer can see nothing was skipped silently.>
