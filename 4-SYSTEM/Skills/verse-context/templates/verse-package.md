---
ref: <verse-id, e.g. 1-1>
unit_type: single          # single | group | template | instance
unit_verses: [<ref>]       # list every verse if this is a group or template
coarser_groupings: {}      # commentary-id: [verses it reads as one unit]
template_ref:              # for unit_type: instance only
commentary_coverage: []    # registered_ids of the commentaries used
tradition_coverage: []     # traditions represented in Traditional Interpretation
concepts_in_verse: []      # term (disambiguating-phrase) — concepts the verse introduces
concepts_in_commentary: [] # term (disambiguating-phrase) — further concepts the commentaries raise
stories: []                # names of narratives the commentaries attach to this verse
layer_order: []            # which optional layers this package carries, in order
note:                      # e.g. citation fallback used, see About Rails §5
status: draft              # the LLM always leaves draft; only a domain specialist sets complete
---

<!-- HOW TO USE: copy this file to <verse-id>.md (e.g. 1-1.md) and fill it in.

 REQUIRED sections, never deleted: Source Text · Traditional Interpretation
 (with Synthesis, and Divergences where they exist) · AI Overview ·
 Disambiguated Restatement · Concept Links.

 OPTIONAL sections: delete the heading outright if no cited material exists for
 this verse. Order them as `layer_order:` declares. The available headings are
 listed in 2-RAILS/About Rails.md §5.

 LANGUAGE: Traditional Interpretation paraphrases and Translation Notes are in
 English; every other section is in the original language, unless the vault
 annex says otherwise.

 CITATION: every claim ends with a (1-SOURCES/.../<file>.md#^<block>) citation.
 A claim that cannot be cited is not written; the field is left blank.

 Full rules: 2-RAILS/About Rails.md §5 · generation procedure:
 4-SYSTEM/Skills/verse-context/SKILL.md

 This file mirrors the vault's own copy-me skeleton at 2-RAILS/Verses/_TEMPLATE.md.
 If the two ever differ, About Rails §5 is the authority and both are fixed to
 match it. -->

## Source Text

### <Source language>
![[1-SOURCES/Text/<lang>-root-text.md#^<ref>]]

**Variants**
[Ed: <cross-edition or cross-language variant, with citation — or delete this block>]

## Traditional Interpretation

### <commentary-id> — <Commentary full name> (<language>)
<English paraphrase of this commentary's reading; every claim cited.>
(1-SOURCES/Commentaries/<file>.md#^<block>)

<!-- repeat one ### subsection per commentary, in the annex's tier order -->

### Synthesis
<What the sources agree on. Do not flatten disagreement here.>

### Divergences
<Only where commentaries genuinely disagree. Attribute each position, flag ⚑. Delete if none.>

## AI Overview

<!-- The reader-facing compression of Traditional Interpretation above, in the
     original language. Every citation here must already appear above — verify
     them one by one before saving. -->

**<Headline reading: one or two sentences answering what the verse says.>**
(1-SOURCES/Commentaries/<file>.md#^<block>)

**Key points**
- <key point> (1-SOURCES/Commentaries/<file>.md#^<block>)
- <key point> (1-SOURCES/Commentaries/<file>.md#^<block>)
<!-- 3–6 points; ⚑ and cite both sides on anything the commentaries split on -->

## Disambiguated Restatement

<Short rewrite of the verse in the original language with every ambiguity the
synthesis resolved made explicit: referents fixed, senses chosen, compounds
parsed. Cite the blocks that authorise each choice. This is what transformation
skills consume.>
(1-SOURCES/Commentaries/<file>.md#^<block>)

<!-- ===== OPTIONAL LAYERS — delete any with no cited material ===== -->

## Key Concepts

### Concepts the verse introduces
- **<term>** (<disambiguating phrase>) — <one-line note>
  (1-SOURCES/Commentaries/<file>.md#^<block>) · [[2-RAILS/Local-Wiki/<term>_(<disambiguator>).md]]

### Further concepts the commentaries raise
- **<term>** (<disambiguating phrase>) — <one-line note>
  (1-SOURCES/Commentaries/<file>.md#^<block>) · [[2-RAILS/Local-Wiki/<term>_(<disambiguator>).md]]

## Concept Links
- [[2-RAILS/Local-Wiki/<term>_(<disambiguator>).md]]
