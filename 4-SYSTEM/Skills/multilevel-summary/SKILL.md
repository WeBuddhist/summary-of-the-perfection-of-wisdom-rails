---
name: multilevel-summary
description: Generate an audience-targeted summary of a verse or chapter from the verse and section rails, calibrating language, length, and fidelity to the specified audience.
---

# multilevel-summary

This skill produces a summary of a verse or a full chapter, grounded exclusively in the rails compiled from the traditional commentaries: `2-RAILS/Verses/<verse-id>.md` for verse scope and `2-RAILS/Sections/<node-id>.md` for chapter scope. The summary is calibrated to one of three audiences — kids, general, or academic — each with its own priority ranking for fidelity, language register, and length. The output is saved to `3-TRANSFORMATIONS/Adaptations/multilevel-summaries/<audience>/` and ends with Obsidian segment-links pointing back to the specific blocks the rails cite.

The skill prevents free-floating paraphrase: every claim in the summary must be traceable through a rail to a commentary block. Nothing is added from parametric knowledge.

**Read the rails, not the sources.** A transformation cites `2-RAILS/`; it never reaches past the rails into `1-SOURCES/`. The one exception is the fallback in Rule 3 below, which is explicitly marked in the output when it is used.

---

## Inputs

| Field | Description | Example |
|---|---|---|
| `scope-type` | `verse` or `chapter` | `verse` |
| `scope-id` | Verse ID (in the root text's `verse_id_format`) or chapter number / chapter title | `1-1`, or `1`, or the chapter's own title |
| `audience` | `kids`, `general`, or `academic` | `general` |
| `root-text` | The root text this vault addresses, **per `4-SYSTEM/Guidelines/vault-annex.md`**. Used only to transclude the verse; never re-interpreted here. | per annex |

If the chapter is given by name rather than number, resolve the number from the chapter heading (`## N. … ^N-0`) in the root text named in the vault annex before proceeding.

If any required input is missing, ask the human before starting — do not assume.

---

## Output

**Verse scope:**
```
3-TRANSFORMATIONS/Adaptations/multilevel-summaries/<audience>/verse-<verse-id>.md
```

**Chapter scope:**
```
3-TRANSFORMATIONS/Adaptations/multilevel-summaries/<audience>/chapter-<N>.md
```

If the file already exists, read it first and update in place, preserving any manual refinements.

---

## Output file format

```markdown
---
transformation_type: adaptation
track: multilevel-summaries/<audience>
scope: verse | chapter
scope_id: <e.g. 1-1 or 1>
audience: kids | general | academic
context_packages:
  - 2-RAILS/Verses/<verse-id>.md          # or 2-RAILS/Sections/<node-id>.md
commentaries_used:
  - <registered_id>
  - <registered_id>
covers_verses: <single id, or first–last for a chapter>
generation_date: <YYYY-MM-DD>
note:                                     # set only when the Rule 3 fallback was used
status: draft
---

# [Verse N-M / Chapter N] — <audience> Summary

## Root Text

![[1-SOURCES/Text/<lang>-root-text.md#^<verse-id>]]

*(For chapter scope: transclude the chapter heading block and the first verse only, then note the full verse range covered.)*

## Summary

<The summary text, calibrated to the audience priorities below.>

---

## Sources

<List of Obsidian block-links to every commentary passage the rail cites, one per line, in the format:>

- [[1-SOURCES/Commentaries/<commentary-file>.md#^<block-id>]] (<registered_id>)
```

---

## Audience priority rules

Write the summary according to the priority weights for the specified audience. Higher priority = more weight in every trade-off decision.

### kids (6th-grade level)

| Priority | Criterion |
|---|---|
| 5 | Easy language with illustration — use concrete images, analogies, and simple vocabulary a 6th-grader knows. Where the commentary itself uses an analogy or story, reproduce it. Where it does not, you may add a short illustrative image *only if* it does not introduce meaning not in the commentaries. |
| 4 | Not long — aim for 100–150 words. Cut anything the commentary treats as secondary. |
| 3 | Truth to the commentaries — all content must be traceable to a commentary block. |

### general (educated adult, no prior Buddhist study)

| Priority | Criterion |
|---|---|
| 5 | Truth to the commentaries — every claim must trace to a commentary block. No interpretive liberties. |
| 3 | Not too long — aim for 150–250 words. Include the main point of each major commentary but do not elaborate every sub-division. |
| 2 | Easy language — prefer plain English or clear modern prose over technical terminology. Translate technical original-language terms on first use. |

### academic (scholar or advanced student)

| Priority | Criterion |
|---|---|
| 5 | Truth to the commentaries — cite specific commentators by registered ID for each claim. Note divergences. |
| 4 | Classical language — use established Dharma terminology (original-language terms in the vault's standard romanisation, with an English gloss in parentheses on first use). Match the register of scholarly Buddhist studies writing. |
| 3 | Not too long — aim for 200–350 words. Be comprehensive but not exhaustive; refer to the source blocks for full elaboration. |

---

## Rules

1. **The rail is the source.** For verse scope read `2-RAILS/Verses/<verse-id>.md`; for chapter scope read `2-RAILS/Sections/<node-id>.md` for the chapter's node and, where the chapter's verses have packages, their `2-RAILS/Verses/` files too. The rail's Traditional Interpretation, Synthesis, Divergences and AI Overview are what the summary compresses. Record every rail you read in `context_packages:`.
2. **Root text per the vault annex.** The Root Text section transcludes the root text that `4-SYSTEM/Guidelines/vault-annex.md` names for this vault. Where the annex names more than one source language, use the one it marks primary. Transclude — never copy the verse text in.
3. **Fallback when no rail exists.** If there is no rail file for the scope, and only then, scan `1-SOURCES/Commentaries/` directly: for each commentary, find the verse's transclusion anchor `![[…#^<verse-id>]]` and collect the blocks that follow it up to the next transclusion anchor or the next heading. Some commentaries group several consecutive transclusions and comment after the last one — scan forward through *all* consecutive transclusion lines to the first line of prose, and treat that prose as belonging to every verse in the run. When this fallback is used, the output **must** carry `status: draft` and a frontmatter `note:` saying which scope had no rail and that the summary was taken from the commentaries directly. Say so in the body too. The proper fix is to build the rail with `verse-context` / `section-summary` and regenerate.
4. **Summary content comes only from the rail (or, under Rule 3, the cited commentary blocks)** — no parametric Buddhist knowledge. If nothing discusses the verse, state that explicitly in the summary and leave the Sources list empty for that verse.
5. **All source links go in the Sources section** — use Obsidian block-links with full literal paths (`[[1-SOURCES/Commentaries/<file>.md#^<block-id>]]`). Do not inline citations in the summary text itself (keep it readable for the audience).
6. **For chapter scope, cover the chapter in aggregate** — do not produce a verse-by-verse list. Synthesise the overarching theme and key teachings the rails draw out across the chapter. You may group verses thematically where the section rail suggests that structure.
7. **Divergences are noted at academic level; simplified or omitted at general level; omitted at kids level** — at academic level mark divergences with ⚑ and name the commentators on each side, exactly as the rail attributes them.
8. **Do not mark `status: complete`** — only a human contributor sets that field. Always write `status: draft`.
9. **Illustrations (kids only)** — a short bracketed note `[Illustration idea: ...]` may follow the summary if an image would help a child picture the teaching, but only when the commentary itself suggests a concrete image or the teaching has an obvious visual correlate. Never invent doctrine to make an illustration work.
10. **Do not generate from an incomplete rail without saying so.** If the rail exists but is not `status: complete`, you may still summarise it, but set `status: draft` and record the rail's status in `note:`.

---

## Procedure

### For verse scope

1. Read `4-SYSTEM/Guidelines/vault-annex.md` and note the root text and the registered commentary IDs.
2. Open `2-RAILS/Verses/<verse-id>.md`.
   a. If it exists: read the Traditional Interpretation (per-commentary paraphrases, Synthesis, Divergences), the AI Overview, and the Disambiguated Restatement. Collect every `(1-SOURCES/Commentaries/<file>.md#^<block>)` citation it carries, together with each commentary's `registered_id`. Note the rail's `status:`.
   b. If it does not exist: apply the Rule 3 fallback and record that you did.
3. Locate the block `^<verse-id>` in the root text and record the verse text (for the transclusion line and for your own reading — not to be copied into the output).
4. If nothing addresses the verse, write a summary noting this and stop. Set `status: draft`.
5. Draft the **Summary** section according to the audience priority rules for the specified audience.
6. Draft the **Sources** section: one Obsidian block-link per collected block, labelled with the `registered_id`.
7. Fill the YAML frontmatter: `transformation_type: adaptation`, `track: multilevel-summaries/<audience>`, `context_packages:` listing every rail read, `commentaries_used:` listing only the `registered_id` values that actually had blocks for this verse, `covers_verses:`, `generation_date:`, `status: draft`, and `note:` where Rule 3 or Rule 10 applies.
8. Write the file to `3-TRANSFORMATIONS/Adaptations/multilevel-summaries/<audience>/verse-<verse-id>.md`.

### For chapter scope

1. Read the vault annex as above. Identify the chapter heading `## N. … ^N-0` in the root text and collect the block IDs of all verses in that chapter.
2. Open `2-RAILS/Sections/<node-id>.md` for the chapter's outline node and read its per-commentary summaries and English translation. Then open every `2-RAILS/Verses/<verse-id>.md` that exists for the chapter's verses and read them. Accumulate the citations across all of them. Where neither a section rail nor any verse rail exists, apply the Rule 3 fallback for the chapter and record it.
3. Read all collected material. Identify the major themes and structural divisions the rails draw out across the chapter.
4. Draft the **Summary** as a chapter-level synthesis (not a verse-by-verse list) according to the audience priority rules.
5. Draft the **Sources** section listing all commentary blocks used, grouped by `registered_id`.
6. Fill the YAML frontmatter with the chapter number as `scope_id`, the chapter's verse range as `covers_verses:`, and every rail read in `context_packages:`.
7. Write the file to `3-TRANSFORMATIONS/Adaptations/multilevel-summaries/<audience>/chapter-<N>.md`.

---

## Completion check

- [ ] `transformation_type: adaptation`, `track:`, `scope`, `scope_id`, `audience`, `context_packages`, `commentaries_used`, `covers_verses`, `generation_date` are set in frontmatter; `status: draft`
- [ ] Every rail read is listed in `context_packages:`
- [ ] Root Text section transcludes (does not copy) the verse or chapter opening from the root text the vault annex names
- [ ] Every claim in the Summary traces to a rail, and through it to a block in `1-SOURCES/Commentaries/`
- [ ] If the Rule 3 commentary-scan fallback was used, `note:` says so and the body says so
- [ ] Summary length and register match the audience priority table (kids ≤ 150 w, general ≤ 250 w, academic ≤ 350 w)
- [ ] Kids summaries: concrete language, illustration note present if applicable
- [ ] Academic summaries: divergences flagged with ⚑, commentators named by `registered_id`
- [ ] Sources section lists every commentary block used as an Obsidian block-link with a full literal path
- [ ] No parametric Buddhist knowledge introduced without a source block citation
- [ ] File written to the correct path under `3-TRANSFORMATIONS/Adaptations/multilevel-summaries/`
