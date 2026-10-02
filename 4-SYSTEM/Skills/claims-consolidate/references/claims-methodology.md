# Claims methodology — extraction and consolidation

**Purpose of this document:** the full record of the claims-gathering methodology, written so
that any future session — including one with no conversation history — can pick up the work
without re-deriving the reasoning.

The goal: gather **every fact/claim** a text's commentaries make, per commentary and then
consolidated, with the citation chain intact at every step — in a way that scales from a
short liturgy with a handful of commentaries to a large treatise with very long ones.

Throughout, *N* is the number of commentaries in the corpus being worked on. Figures drawn
from a pilot run are labelled as examples; none of them is a threshold.

---

## 1. The core principle: extract first, merge later

Extraction and consolidation are **separate phases**, never interleaved:

- **Extraction** reads one commentary in isolation and records what *it* says — expensive,
  careful, done once per commentary, redoable per commentary.
- **Consolidation** compares finished claims files — cheap, disposable, redoable at any time
  without re-reading a single commentary.

Merge decisions made *during* reading are made with incomplete information: the first
commentary read silently defines the topic space, and later commentaries with different
granularity (a 24 KB digest vs a 400 KB treatise) map onto it badly. Extraction errors and
merge errors contaminate each other and neither can be redone alone. This is why the
alternatives in §5 were considered and rejected.

Meaning-based segmentation of the source (`segment-commentary`) improves citation quality
and within-commentary consistency, and is part of the pipeline — but it does **not** fix the
cross-commentary granularity problem, which is about the topic space, not the text units.

---

## 2. The pipeline

```
per commentary (isolation):
  1. clean + frontmatter + resegment          (raw-to-sources, segment-commentary)
  2. TOC tree                                 (toc-generate, QC-gated)
     → $SECTIONS_RAW/toc-tree/<id>.md
  3. tree-guided claims extraction            (commentary-claims Strategy 1, per-node subagents)
     → $CLAIMS/raw/tree-guided/<id>.md

corpus-wide (after all extractions):
  4. spine map, per commentary                  (spine-map, one isolated subagent each)
     → $CLAIMS/raw/spine-map/<id>.md            — built ONCE, reused by every topic
  4b. packet assembly, per topic                (assemble_packet.py — deterministic)
     → $WORK/packet-<slot>.md                   + manifest for the coverage check
  5. question-driven consolidation per bucket   (one subagent per topic)
     → $CLAIMS/<topic>.md
  5b. coverage check + gap closure              (deterministic diff + small repair pass)
  5c. verification gates                        (gate 1: verify_consolidation.py script;
                                                 gate 2: adversarial audit,
                                                 fresh agent per page)
  6. generated indexes                          (matrix, tags, graph — from topic pages)
```

Only step 6 is a fully deterministic script with no model judgment. Step 4 was originally
designed as one too ("bucket claims by spine + facet — mechanical script, no judgment") but a
pilot run found this assumption wrong — see "Bucketing is not mechanical" below. Steps 3, 4,
and 5 all use model judgment, always on a small, local input (one commentary, or one topic's
assembled packet). 5b's diff itself is deterministic; only the gap-closing repair pass (when
a gap is found) uses judgment, and only on the specific claims the diff flagged.

### Why the spine matters

All commentaries on one root text share its canonical structure. So topic alignment is two
stages — slot each claim to its unit of that structure (via the per-commentary mapping pass,
step 4 — see below for why this needs a real read, not a lookup), then compare a handful of
claims semantically *within* a bucket — never one expensive global matching over thousands
of claims.

### The mapping is per-commentary, not per-topic

An earlier design ran the mapping pass **inside every topic run**: for each topic, one
isolated subagent per commentary re-read that commentary's whole raw claims file to find the
topic's claims. That is correct but quadratic in the wrong variable. With *N* commentaries
and *T* topics it implies *N × T* full-file reads of an unchanged corpus, at full price each
time, because the isolation guard means fresh contexts with no cache reuse. (Pilot example:
16 commentaries / 2,975 claims / ~3.8 MB of raw claims files, ~22 spine slots plus global
topics ≈ 400 full-file reads, ~25× re-reading of the same corpus.)

The observation that fixes it: **resolving one commentary's numbering against the spine
answers it for every slot at once.** "Which node of commentary X is slot 5" and "…is slot 12"
are the same act of reading its TOC tree. Split out, that judgment is made *N* times total
instead of *N × T*.

So the mapping lives in its own artifact — `$CLAIMS/raw/spine-map/<id>.md`, written by the
`spine-map` skill — and packet assembly is a deterministic script,
`$SKILLS/claims-consolidate/assemble_packet.py`. Consolidation itself is unchanged: it works
from a packet, generates its questions from it, and never re-opens a raw file.

What this buys beyond tokens:

- **Verbatim quoting by construction.** The assembler *copies* claim blocks out of the raw
  files. The quote-fidelity errors a retrospective audit finds (silently elided syllables,
  normalized orthography) are a model retyping the original language; a script cannot.
- **A deterministic coverage input.** The packet's `## Manifest` is exactly the "claim IDs
  the mapping pass placed in this topic's bucket" that step 5b diffs against — now computed,
  not model-reported.
- **Loud failure instead of silent omission.** A commentary with claims but no spine map, or
  with no disposition for a slot, exits the assembler non-zero. Under the per-topic design a
  commentary quietly missing from one topic's fan-out left no trace.
- **Reusability downstream.** `$VERSES/` needs the same root-verse → commentary-passage
  routing; it can read the spine maps instead of re-deriving them.

The judgment that was in step 4 did not become cheaper or more mechanical — it moved. The
isolation requirement (one agent per commentary, never several at once) moved with it, for
the same anti-contamination reason.

### Bucketing is not mechanical — it needs a per-commentary mapping pass

**TOC node numbering for "which spine slot is this" is not uniform across commentaries.**
One commentary nests a slot's content at node `1.1.N`, another at top-level node `N`, another
groups several sub-facets per slot under one node, another titles nodes by a descriptive name
instead of an ordinal, and structures otherwise merge or split relative to the canonical
spine. A fixed formula (e.g. "node `1.1.N` is always slot N") silently mis-buckets claims the
moment it hits a commentary organized differently — and in any real corpus several are.

The fix: **one isolated subagent per commentary**, reading that commentary's own TOC tree,
its raw claims file, and (for texts with a verse-numbered spine) the relevant root-text
passage as ground truth — never a script applying one node-numbering rule to every
commentary. This subagent also resolves the corpus-wide **completeness guarantee**: it must
place every claim into the topic bucket, an explicit `ambiguous` list (uncertain fit, with a
reason — never silently dropped, never silently force-fit), or leave it out as genuinely
irrelevant; and it must explicitly mark a commentary silent on a slot rather than leaving it
merely empty.

That subagent is the `spine-map` skill and its output is the routing index (node numbers,
claim IDs, slot names — addresses, never claim content), written once per commentary. The
claim *content* the consolidation pass needs is copied out of the raw files verbatim at
packet time by `assemble_packet.py`, so step 5 never re-opens a raw claims file. The
completeness guarantee is mechanically enforced rather than merely required:
`verify_spine_map.py` fails any map in which a claim has zero dispositions (silent loss) or
two (silent duplication).

A finding worth stating because it is the general case rather than the exception: **the
structural outline is sometimes coarser than the spine.** (Pilot example: one commentary
carried all twenty-one homages of a praise inside a single undivided node, 75 claims, so no
node-level rule could route it at all. Its spine map routed those slots by claim-ID range
instead, using the extraction's own root-verse quotation claims as the boundary markers.) Any
spine-mapping method that assumes one node per slot will silently mis-route commentaries of
this shape.

### The coverage invariant (step 5b)

Question generation is a "derived completeness check" — free extraction first, generated
questions catch what free reading missed. The mechanism that *enforces* this rather than
leaving it aspirational: after step 5 writes a topic page, **mechanically diff** every claim
ID step 4 placed in that topic's main bucket against every claim ID the topic page actually
cites. Any claim in the gap must be closed — folded into the page, or logged with a one-line
reason in an explicit "Claims reviewed, not separately cited" section — never left silently
absent. (Pilot example: this caught real, specific, fixable gaps of roughly 5–12% of a
topic's mapped claims per page, mostly non-substantive structural or duplicate claims once
reviewed — but not always; one commentary's parallel mantra-syllable benefit glosses were
found missing and folded in on review.) The diff itself is a deterministic set comparison,
not a model judgment call; only the repair pass over the flagged gap uses judgment, and only
on the specific claims flagged — never a full re-read of the topic.

### The verification gates (step 5c) — what a retrospective audit proved necessary

A retrospective adversarial audit of the first pilot pages — a fresh agent per page
re-checking every one of 418 unique citations against the raw claims files — found zero
fabricated claim IDs, but **one critical finding** (a "corroboration" cited to a claim that
contains nothing of the sort — the consolidator had a real corpus idea attached to the wrong
claim ID), one moderate overstretch, and ~16 minor findings falling into a stable taxonomy:
partial-support padding of consensus attestation lists, the same claim cited on both sides of
one divergence, page-level harmonizations presented as a claim's own reading, epistemic
upgrades ("endorses" for a tentative aside), silently elided syllables in original-language
quotes, hand-tallied "(N commentaries)" labels (five of five wrong on the worst page), and
consulted claims left with no disposition anywhere.

Consolidation therefore ends with two mandatory gates, encoded in the skill:

- **Gate 1 — deterministic** (`$SKILLS/claims-consolidate/verify_consolidation.py`):
  citation existence (both heading and ⚑ bold-block claim forms), recomputed count labels,
  both-sides-of-a-divergence flags, disposition completeness against the Coverage table,
  prefix discipline. Zero ERRORs required.
- **Gate 2 — adversarial attribution audit** (Phase 2 of `claims-consolidate`): a fresh
  agent that did not write the page checks every attribution against the raw claims —
  attribution fidelity, verbatim quote fidelity, divergence reality, epistemic strength.
  Report-only; the consolidator fixes, the auditor re-checks. No critical/moderate finding
  may remain.

The corresponding prevention rules (full-statement support, re-read-before-corroborating,
one side per divergence, verbatim-or-ellipsis quoting, harmonization attributed to the page,
computed counts, no undispositioned claims) are Rules 9–16 of the consolidation skill.

---

## 3. Extraction — three methods, kept separate

All three write under `$CLAIMS/raw/`, one file per commentary, and are **genuinely
different techniques**, not revisions of one another:

| Method | Skill | Output | Character |
|---|---|---|---|
| Direct, fixed categories | `commentary-claims` Strategy 3 | `raw/<id>.md` | One pass, nine fixed categories (A–I) |
| TOC-scaffolded | `commentary-claims` Strategy 2 | `raw/toc-scaffolded/<id>.md` | One pass, re-bucketed under the tree |
| Tree-guided | `commentary-claims` Strategy 1 | `raw/tree-guided/<id>.md` | Fresh extraction, one isolated subagent per TOC node |

**Tree-guided is the preferred method** — claims inherit their spine location for free, which
makes consolidation bucketing nearly automatic. Requires a QC-clean TOC tree first.

A model-comparison experiment (same skill, two models over three commentaries) found claim
counts differing 5–12 per commentary purely from granularity choices, while ⚑
internal-tension findings matched exactly. Lesson baked into §4: consolidation must match
claims by *content*, never expect one-to-one claim alignment between extraction runs.

---

## 4. Consolidation — question-driven, per topic

### Where files go

- **`$CLAIMS/raw/…`** — all per-commentary extractions (input layer, never modified by
  consolidation).
- **`$CLAIMS/<topic>.md`** — one consolidated page per topic (output layer).

This mirrors the `$SECTIONS` pattern (`Raw/` = per-commentary, top level = combined) — one
rule for the whole vault.

### How the questions are produced — generated, not authored

No human writes the question list. Two free sources:

1. **From the spine, mechanically:** every spine slot × its observed facets, plus global
   topics, is a scripted question grid.
2. **From the extractions themselves:** every raw claim implies a question — one
   commentary's "the left hand's three fingers symbolise the Three Jewels" becomes "what does
   each commentary say the left hand symbolises?", asked of all the others.

The union of both is the question set. This makes question-driven consolidation a **derived
completeness check**: free extraction first, then generated questions catch what free reading
missed.

### What each topic page contains

Per facet: **Consensus** (with per-commentary attestations), **⚑ Divergences** (never
flattened — vault hard rule), **Unique** (claims only one commentator makes). Plus a coverage
table including which commentaries are *silent* on the topic — absence is a finding.

### Questions are recorded in the page itself

Frontmatter `consolidation_questions:` (machine-queryable) **and** a visible
`## Questions asked` section. A question that found no answers is kept and marked "no
commentary addresses this" rather than deleted. Template:
`$SKILLS/claims-consolidate/templates/consolidated-claims-topic.md`.

### Invariants

1. Topic pages cite **raw claim IDs**, never source files — the chain is
   topic page → raw claim → source segment.
2. Each consolidated answer lives in **exactly one** file; indexes point, never duplicate.
3. File names come from **spine + topic**, never claim content — stable across re-runs.
4. Consolidation is disposable: regenerating any topic page never touches `raw/`.

### Scaling rule

> Folders follow the text's spine; files sit at the level where a page stays readable;
> anything finer becomes headings inside the file.

A short praise: one page per root-text unit plus a handful of global pages, facets as
headings. A long treatise: one folder per chapter, one file per topic/term or verse-group.
The split trigger is mechanical: when a topic page would exceed ~40–50 claims or a few
hundred lines, split one spine level down. Never decide file granularity per-text by taste.

---

## 5. Alternatives considered and rejected (and why)

Recorded so they are not re-proposed from scratch:

- **File-per-claim, merged during reading** ("see a claim → check if a file exists → append
  or create"): granularity decided blind, first-commentary bias, sequential (no parallelism),
  extraction and merge errors entangled, thousands of unstable stub files.
- **Tags-as-method** (tag claims inline while reading, index the tags, graph at the end):
  flat namespace with no citation payload; tag drift recreates the matching problem with less
  structure; requires annotating inside `$SOURCES/`, which is frozen. Tags/wikilinks are
  valuable **as generated output** from finished topic pages — not as the method.
- **Pairwise/tournament merge** (merge 1+2, then +3 …): order-dependent, early merges shape
  everything, drifts by the tenth commentary.
- **Embedding clustering:** right tool when a corpus has *no* shared spine; unnecessary when
  one exists, and clusters still need human cleanup.
- **Knowledge-graph triples:** machine-queryable but destroys verbatim original-language
  fidelity — the thing the whole citation chain protects. Actively skipped.
- **Question-driven as the *only* extraction:** finds only what was asked; unique/unexpected
  claims get missed. Kept as the consolidation mechanism and second-pass completeness check,
  not the primary extraction.
- **No consolidation (RAG-style, query-time merge):** cheap and always current, but no
  browsable artifact and no persistent divergence record. Available "for free" over the claim
  files anyway; not a substitute for topic pages.

---

## 6. Related layout decisions

- **TOC trees** live at `$SECTIONS_RAW/toc-tree/<registered-id>.md`. Rationale: the tree is
  raw distilled structure — per-commentary, descriptive, every title attestation-checked —
  so it belongs with the other per-commentary distillations under `Sections/Raw/`.
- **Claims layout:** per-commentary extractions live under `$CLAIMS/raw/`; the `$CLAIMS/`
  top level is reserved for consolidated topic pages.

---

## 7. Where everything lives

| Thing | Path |
|---|---|
| This methodology | `$SKILLS/claims-consolidate/references/claims-methodology.md` |
| Topic-page template | `$SKILLS/claims-consolidate/templates/consolidated-claims-topic.md` |
| Canonical Claims rules | `$RAILS/About Rails.md` §6b (wins over CLAUDE.md on conflict) |
| TOC trees | `$SECTIONS_RAW/toc-tree/<registered-id>.md` |
| Raw claims | `$CLAIMS/raw/{,toc-scaffolded/,tree-guided/}<registered-id>.md` |
| Spine maps (routing index) | `$CLAIMS/raw/spine-map/<registered-id>.md` |
| Canonical spine slot registry | `$SYSTEM/Guidelines/vault-annex.md`, "Canonical spine slots" |
| Spine-map skill + its verifier | `$SKILLS/spine-map/{SKILL.md,verify_spine_map.py}` |
| Packet assembler | `$SKILLS/claims-consolidate/assemble_packet.py` |
| Consolidated topic pages | `$CLAIMS/<topic>.md` |
