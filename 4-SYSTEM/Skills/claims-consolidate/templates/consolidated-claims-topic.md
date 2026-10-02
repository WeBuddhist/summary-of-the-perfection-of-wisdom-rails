---
topic: <spine-derived slug — a registered slot ID, or a global topic slug>
spine: <which spine node(s) this covers, e.g. the root-text unit or verse range, or "global">
method: question-driven-consolidation
sources:
  - $CLAIMS/raw/tree-guided/<registered-id-1>.md
  - $CLAIMS/raw/tree-guided/<registered-id-2>.md
consolidation_questions:
  - "<question 1 asked of the raw claims for this topic>"
  - "<question 2>"
date: <YYYY-MM-DD>
status: draft
---

# <Topic title — original language and English>

> Consolidated from the raw claims files listed in `sources:`. Every attestation
> cites a raw claim ID; raw claims cite `$SOURCES/` segments. This page never
> cites a commentary file directly, and regenerating it never touches `raw/`.

## Questions asked

<The same list as `consolidation_questions:`, echoed here for readers. Every
answer section below must trace back to at least one of these questions; a
question with no answers found is kept and marked "no commentary addresses this".>

1. <question 1>
2. <question 2>

---

## <Facet heading, e.g. Name / Etymology>

### Consensus
<The shared assertion, stated once, in the original language with an English gloss.>
— attested: `<id-1>` B1, `<id-2>` B5, … (<n> commentaries)

### ⚑ Divergences
<Each position stated with its holder(s) and claim ID(s). If none: "None observed.">

### Unique
<Claims only one commentary makes on this facet, each with its claim ID. If none: "None.">

---

## <Next facet heading>

…

---

## Claims reviewed, not separately cited

<Every claim ID the mapping pass placed in this topic's bucket that did not become an
attestation above, each with a one-line reason.>

---

## Coverage

| Commentary (`registered_id`) | Claims consulted | Contributed to |
|---|---|---|
| <id-1> | B1, C3, E2 | Consensus (Name), Unique (Iconography) |
| <id-2> | … | … |

**Commentaries silent on this topic:** <list, or "none">

---

<!--
ORIGINAL-LANGUAGE VARIANT. For a page written in the source language rather than
English, see "Phase 1 — output language" in the skill: the file is named
`<topic-slug>-<lang>.md`, the frontmatter adds `lang_tag:` and `counterpart:`, and
every structural heading above carries its English anchor word in parentheses so the
deterministic checker can still parse the page. Tibetan worked example:

  ## དྲི་བ་བཏོན་པ (Questions asked)
  ### མཐུན་སྣང (Consensus)
  ### ⚑ མི་མཐུན་པ (Divergences)
  ### ཐུན་མིན (Unique)
  ## བསྐྱར་ཞིབ་བྱས་ཀྱང་ལུང་མ་དྲངས་པ (Claims reviewed, not separately cited)
  ## ཁྱབ་ཚད (Coverage)
-->
