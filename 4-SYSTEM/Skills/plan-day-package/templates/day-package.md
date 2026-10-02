---
day: <N>
chapter: <C>
verses: "<C>-<a> to <C>-<b>"
date: "<date>"
status: draft
language: <lang>
document_type: <source-of-record | translation>
translated_from: "<path to the source-of-record package — translations only>"
sources:
  plan_day_file: "<the plan day file section 1 was taken from>"
  schedule_file: "<the stream's schedule.md>"
  verse_source: "<the designated verse source for this stream>"
  rail_files:
    - "$VERSES/<verse-id>.md"
protected: true
edit_policy: "confirm-with-human-before-edit-move-delete"
---

> 🔒 **PROTECTED — SOURCE OF TRUTH.** Downstream tools read this file directly.
> Do not edit, move, rename or delete it without explicit human confirmation.
> Regenerating it counts as editing it. After an approved change, re-baseline
> the drift guard.

# Day <N> — <title>

**Date:** <date>  
**Chapter:** <C>  
**Verses covered:** <range>

---

<!-- sec:challenge -->
## 1. <heading for the plan-track section>

<!-- challenge:opening -->
### <heading>
<!-- challenge:tradition -->
### <heading>
<!-- challenge:practice -->
### <heading>

*(Source: <the plan day file actually used>)*

---

<!-- sec:verses -->
## 2. <heading for the verse section>

<one blockquote per verse; text taken from the stream's designated verse source
by block ID, with each source line kept as its own `> ` line — never collapsed
into one paragraph>

---

<!-- sec:rails -->
## 3. <heading for the rails section>

<!-- verse:<C>-<a> -->
### Verse <C>-<a>

<!-- sub:root-verse -->
#### <Root Verse heading>
<!-- sub:interlinear -->
#### <Interlinear Gloss heading>
<!-- sub:commentary -->
#### <Commentary Explanations heading>
<!-- cm:<machine-id> -->
##### <Display Name (Work)>
<!-- cm:<machine-id> -->
##### <Display Name (Work)>
<!-- sub:stories -->
#### <Stories heading>                      (optional)
<!-- story:<id> -->
##### <Title>
<!-- sub:metaphors -->
#### <Metaphors heading>                    (optional)
<!-- sub:quotations -->
#### <Quotations heading>                   (optional)
<!-- sub:teaching-points -->
#### <Main Teaching Points heading>
<!-- sub:key-terms -->
#### <Key Terms heading>
<!-- sub:synthesis -->
#### <Verse Synthesis heading>
**Brief introduction.** <one-paragraph overview>
**Key points.**
- <condensed recap bullets — mirroring the Main Teaching Points>

Sources: [[…]] [[…]]

---

<!--
  Format invariants — see the skill's Rules for the reasoning.

  * Every tracked heading is immediately preceded by its `<!-- … -->` anchor,
    with no blank line between.
  * Commentator and story H5 headings are DISPLAY-ONLY: name + work, or story
    title. The machine id lives only in the anchor above. Never write the id in
    a heading or in prose.
  * The plan's declared first commentator comes first in every commentary
    section; the others follow in source order. A verse whose rail has no block
    for that commentator is left as it is.
  * Include exactly the commentators the rail has. Never invent a missing one.
  * Optional sub-sections appear only when the rail has them.
  * A Divergences heading must start with the word "Divergences" (a leading ⚑ is
    allowed). If it does not, the validator treats it as a commentator block.
  * Story ids may be placeholders and may repeat within a verse; keep them as
    the rail has them.
  * Provenance is one `Sources: [[…]]` line per leaf section. No inline
    `([[…]])` in prose, no `![[…]]` transclusions — the consumer is a raw-fetch
    API, not Obsidian. A table keeps its own Source column.
  * The synthesis has two labelled parts, worded exactly `**Brief introduction.**`
    then `**Key points.**`. Do not rename them to "Overview" or "Main points",
    which collide with the separate teaching-points section. The bulleted recap
    belongs to the synthesis by design; it is not a duplication error.
  * The verse blocks must exactly cover the `verses:` range in the frontmatter.
-->
