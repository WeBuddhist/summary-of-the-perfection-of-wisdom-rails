---
name: claims-consolidate
description: >
  Consolidate one topic's claims across every commentary into a single
  question-driven topic page — mapping each commentary in isolation, then generating
  the questions and synthesising per facet, closed by a mandatory coverage check — and
  then run an adversarial attribution audit of the finished page against the raw
  claims files.

  Trigger on "consolidate the claims", "build the topic page", "what do the
  commentaries say about X", "synthesise the claims on this topic", "audit the topic
  page", "check the citations on this page".

  The audit is not optional polish: a topic page that has not been audited has not
  been checked for attribution or quote fidelity.
---

# Consolidate claims into a topic page, then audit it

Two phases, and the second one is a gate:

| Phase | Does | Output |
|---|---|---|
| 1 — Consolidate | Per-commentary mapping in isolation → questions → per-facet synthesis → coverage check | the topic page |
| 2 — Audit | A **fresh agent** re-checks every citation against the raw claims files | a report; the page is not edited |

Phase 2 is deliberately **report-only and run by a fresh agent**. An agent that just
wrote a page is the worst possible auditor of it — it will confirm its own
paraphrases. Dispatch the audit as its own isolated subagent that has not seen Phase
1's reasoning, and fix what it reports by re-running the relevant part of Phase 1.

**Output language.** The page's analytical content — synthesis, questions,
divergence discussion, coverage notes — can be written in English (the default) or
entirely in the source language. The pipeline, gates, and rules are identical either way;
only the prose language changes, and a source-language page carries its own filename,
frontmatter and heading anchors. Say which language you are writing in before you start,
and follow **Phase 1 — output language** below in full when it is not English.

---

## Phase 1 — Consolidate the topic page

Per-commentary mapping happens in isolation — one commentary at a time, without sight of the others — so a strong commentary cannot colour the reading of a weak one. The coverage check at the end is mandatory.

This is step 5 of the corpus-wide claims pipeline documented in full at
`4-SYSTEM/Skills/claims-consolidate/references/claims-methodology.md` §2/§4. It takes every commentary's finished
raw claims file and produces one consolidated topic page — the first point in the
pipeline where claims from different commentaries are actually compared against each
other. It exists to prevent two failure modes: **silent claim loss** (a claim that
exists in the corpus never reaching any topic page, with no record that it was even
considered) and **false consensus** (commentaries that genuinely disagree being
merged into one flattened statement). Correct output is a page where every fact in the
corpus relevant to the topic is either synthesised into Consensus/⚑ Divergence/Unique,
or explicitly logged as reviewed-and-excluded — nothing simply absent without a trace.

---

### Inputs

- **A topic definition**: a spine slot (a specific node of the text's canonical
  structure — e.g. one homage/verse-group of a praise, one chapter-section of a
  treatise — or `global` for a cross-cutting topic like recitation benefits) plus a
  starting list of likely facets. Facets are *observed, not fixed* — derive them from
  what the corpus actually discusses, adjust per topic; do not force a fixed facet list
  onto every topic.
- **Every commentary's spine map** at `2-RAILS/Claims/raw/spine-map/<registered_id>.md`,
  built once per commentary by the `spine-map` skill. This is what resolves "which node
  of *this* commentary is this spine slot" — never uniform across commentaries (Rule 1).
  A commentary with a raw claims file but no spine map is a hard stop, not a silent
  omission: `assemble_packet.py` exits non-zero on it.
- **Every commentary's raw claims file** at `2-RAILS/Claims/raw/tree-guided/<registered_id>.md`
  (all commentaries that have one at run time — do not wait for 100% corpus coverage,
  but do consult everything that exists, including silence as a finding). Read by the
  assembler, not by you: never re-open these while consolidating.
- **The registered slot list** in the vault annex (`4-SYSTEM/Guidelines/vault-annex.md`,
  section "Canonical spine slots") — the topic's slot ID and root anchor come from there.
  See **Spine slots** below.
- **The root text**, if the vault addresses one — `1-SOURCES/Text/` — as ground truth
  for the slot's verse text when writing the topic page's heading and framing.
- If missing any of the above for a commentary that should plausibly be consulted,
  stop and ask the human contributor rather than silently excluding it.

#### Spine slots

A **spine slot** is one addressable unit of the root text's own canonical structure, and it
is what a topic page is keyed to.

- **The registry of slot IDs lives in the vault annex**, under the heading "Canonical spine
  slots". It lists every slot ID, what root-text unit it anchors to, and any global
  (non-spine) slots such as a cross-cutting `benefits` or `structure` topic.
- **A skill never coins a slot locally.** If the topic you were asked to consolidate has no
  registered slot, stop and ask the human contributor to register one. A locally invented
  slot ID silently forks the naming space and every later re-run produces a second page.
- **Derivation rule (generic):** one slot per unit of the root text's *own* structure, at
  whatever granularity keeps a topic page under roughly **40–50 claims**. If a slot's page
  would exceed that, split one spine level down and register the finer slots; if many slots
  would each hold a handful of claims, group them one level up. Never pick the granularity
  per text by taste — pick it by that page-size trigger.

### Output

One file at `2-RAILS/Claims/<topic-slug>.md`, where `<topic-slug>` is the registered slot ID (or a
registered global topic slug) — spine + topic, never claim content, never renamed on a
re-run.

---

### Output file format

Follow `4-SYSTEM/Skills/claims-consolidate/templates/consolidated-claims-topic.md` exactly:

```markdown
---
topic: <spine-derived slug>
spine: <which spine node(s) this covers, or "global">
method: question-driven-consolidation
sources:
  - 2-RAILS/Claims/raw/tree-guided/<registered-id-1>.md
  - 2-RAILS/Claims/raw/tree-guided/<registered-id-2>.md
  ...
consolidation_questions:
  - "<question 1>"
  - "<question 2>"
date: <YYYY-MM-DD>
status: draft
---

## <Topic title>

> Consolidated from the raw claims files listed in `sources:`. Every attestation
> cites a raw claim ID; raw claims cite `1-SOURCES/` segments. This page never
> cites a commentary file directly, and regenerating it never touches `raw/`.

### Questions asked

1. <question 1>
2. <question 2>

---

### <Facet heading>

#### Consensus
<shared assertion, original language + English gloss>
— attested: `<registered_id>:<claim_id>`, ... (<n> commentaries)

#### ⚑ Divergences
<every genuinely conflicting position, each attributed, or "None observed.">

#### Unique
<single-commentary claims, each cited, or "None.">

---
### Claims reviewed, not separately cited

<Every claim ID the mapping pass placed in this topic's bucket that did not become an
attestation above, each with a one-line reason (structural-only, duplicate of an
existing attestation, etc.). This section is what makes the coverage check pass —
never leave a gap here silently unexplained.>

---

### Coverage

| Commentary (`registered_id`) | Claims consulted | Contributed to |
|---|---|---|
| <id-1> | ... | ... |

**Commentaries silent on this topic:** <list with reasoning where derivable, or "none">
```

---

### Rules

1. **Node numbering is never assumed uniform.** One commentary may nest a spine
   slot's content at TOC node `1.1.N`, another at top-level node `N`, another may
   group several sub-facets per slot, another may title nodes by epithet/name instead
   of ordinal, another may run every slot inside a single undivided node. This is
   resolved once per commentary by the `spine-map` skill against that commentary's
   *own* TOC tree and the root text — never re-derived here, and never assumed from a
   node number that worked for another commentary. If a packet looks wrong for a
   commentary, fix its spine map and re-assemble; do not patch the topic page.
2. **Extraction and consolidation stay separate.** Never edit, reinterpret, or
   "correct" anything under `2-RAILS/Claims/raw/` or `1-SOURCES/` while consolidating.
   Read-only on both. This skill writes only to `2-RAILS/Claims/<topic-slug>.md`.
3. **Citations are always `registered_id:claim_id`.** A bare claim ID (e.g. `c-1-1-3`)
   collides across commentaries — every citation on the page must carry both parts,
   copied verbatim from the source raw claims file.
4. **No consensus flattening.** A genuine disagreement between commentaries is a ⚑
   Divergence, always attributed to each holder, never merged into one Consensus
   statement that erases the disagreement.
5. **Silence is a finding, not a gap.** Every commentary consulted must appear in the
   Coverage table or the "Commentaries silent on this topic" line — never simply
   absent with no record it was checked. State the reason for silence when one is
   derivable from the source (e.g. "this transmission's colophon is missing").
6. **Ambiguous claims are carried through transparently, never silently resolved.**
   A claim the mapping pass could not confidently place must be flagged as ambiguous,
   and the consolidation pass must either use it with a visible flag explaining the
   uncertainty, or explicitly log it as excluded with a reason — never silently
   absorbed as if certain, never silently dropped.
7. **The coverage check is mandatory, not optional.** After the page is written,
   every claim ID the mapping pass placed in the topic's main bucket must be
   mechanically accounted for — cited in a facet section, or logged in "Claims
   reviewed, not separately cited." A page that has not passed this check is not
   finished, regardless of how complete it looks.
8. **`status: draft`, always.** An LLM never marks its own consolidation `complete` —
   that is a domain specialist's judgment call, per `2-RAILS/About Rails.md`.

The following rules encode the error classes a retrospective adversarial audit of the
first pilot pages found (example figures: one critical false-corroboration, one moderate
overstretch, ~16 minor findings across 418 citations). Each rule exists because the audit
caught a real instance of its violation:

9. **Full-statement support.** A claim may be listed in a Consensus attestation list
   only if it supports the *entire* consensus statement. If the statement bundles two
   propositions (pilot example: "recite at dusk/dawn" + "wrathful at dusk, peaceful
   at dawn") and some claims attest only one, either split the facet into two
   statements, or split the attestation list ("attested (timing only): …"). Never pad
   a list with same-topic-but-partial claims — the count becomes a false measure of
   how widely the full statement is attested.
10. **Corroboration must be re-read, not remembered.** Before writing "X and Y
    independently attest…", re-open both claims in the packet and confirm each one
    actually contains the shared content. The audit's single critical finding was exactly
    this: a framing attributed to a second commentary whose cited claim contains no such
    framing — the consolidator had the right *idea* in the corpus but attached the wrong
    claim ID.
11. **One side per divergence.** A claim ID appears on at most one side of any single
    ⚑ divergence. If it seems to support two readings, that is a finding about the
    claim — say so explicitly rather than citing it both ways.
12. **Verbatim quotes or marked ellipsis.** Original-language text quoted *from a specific
    claim* is copied character-for-character from the packet's `**Original:**` field — no
    silent elision (use … for omissions), no orthographic normalization, no dropped
    particles. Synthesised consensus wording in the original language is permitted, but
    must not be attributed to a specific claim ID.
13. **Harmonization is the page's, not the claim's.** When the page derives something
    the claim does not itself state (pilot example: reading 7×7=49 into a claim
    whose own gloss says only "cycles of seven"), attribute the derivation to the
    page ("read together, these imply…"), never to the claim.
14. **Epistemic strength is copied, not upgraded.** A tentative authorial aside ("I think";
    Tibetan example: …སྙམ་མོ) is reported as tentative — never as "endorses" or "holds."
15. **Counts are computed, never hand-tallied.** Every "(N commentaries)" label and every
    "N of <corpus size>" arithmetic statement is recomputed from the final attestation list
    before the page is done (the deterministic checker does this — see Procedure step 6).
    Hand-tallied count labels are wrong far more often than they look.
16. **Every consulted claim gets a disposition.** Any claim ID the Coverage table
    lists as consulted must appear either as a citation in some facet or as an entry
    in "Claims reviewed, not separately cited" — no third state.

---

### Procedure

1. **Define the topic.** Fix the spine slot and a starting facet list. If this is
   part of a larger run covering many topics, this list comes from the corpus-wide
   spine grid (methodology §4 — every registered spine slot × its observed facets); if a
   one-off topic, derive facets from a quick read of 2–3 raw claims files' content on that
   spine slot.

2. **Confirm every commentary has a spine map.** The per-commentary routing lives at
   `2-RAILS/Claims/raw/spine-map/<registered-id>.md`, built once per commentary by the
   `spine-map` skill. If any commentary with a raw claims file lacks one, stop and run
   `spine-map` on it first — step 3 will fail loudly rather than silently omitting it.

3. **Assemble the packet — deterministic, no model call.**

   ```
   python3 4-SYSTEM/Skills/claims-consolidate/assemble_packet.py <slot> \
       --out 0-INBOX/temp/packet-<slot>.md \
       --manifest-out 0-INBOX/temp/manifest-<slot>.txt
   ```

   This replaces what used to be a per-commentary mapping pass run once per topic — a
   full re-read of every raw claims file for every topic, i.e. (commentaries × topics)
   full-corpus reads across a complete run. The routing judgment now happens once per
   commentary, in the spine map; this script does only the mechanical part: collecting the slot's claims
   out of each raw file and concatenating them.

   The packet carries, per commentary: its node(s) and verbatim node titles, every claim
   block **copied character-for-character** from the raw file, claims routed by ID rather
   than node (flagged ⓘ), ambiguous claims (flagged ⚑, to be carried through per Rule 6),
   and an explicit silence marker where the spine map records silence. A non-zero exit
   means a real gap — a commentary with no disposition for this slot, or none at all —
   never proceed past it.

   Because the script copies rather than retypes, it also removes at the source the
   quote-fidelity error class the pilot audit found (silently elided syllables, normalized
   orthography). Quote the original language **from the packet**, never from memory.

4. **Stage 2 — consolidation, one agent per topic, downstream of the full packet.**
   Working only from the packet (never re-opening raw files):
   a. Generate consolidation questions: a facet grid (mechanical, from the topic's
      facets) plus claim-inversion (every distinctive claim in the packet becomes a
      question asked of the others). Record in `consolidation_questions:` frontmatter
      and echo in `## Questions asked`. A question nobody answers is kept, marked "no
      commentary addresses this," never deleted.
   b. Per facet, write Consensus / ⚑ Divergences / Unique, citing
      `registered_id:claim_id` throughout.
   c. Build the Coverage table covering every commentary in the packet, silent or not.
   d. Write the file at `2-RAILS/Claims/<topic-slug>.md` per `4-SYSTEM/Skills/claims-consolidate/templates/consolidated-claims-topic.md`. Report back
      the exact list of every claim ID cited (`registered_id:claim_id` form).

5. **Coverage check (deterministic, no model judgment).** Diff the packet's
   `## Manifest` (equivalently, `--manifest-out`) against the claim IDs Stage 2
   reported as cited.
   For every ID in the gap: read where it would fit, and either (a) fold it into the
   appropriate facet section, or (b) add it with a one-line reason to a new "Claims
   reviewed, not separately cited" section (create this section, positioned just
   before "## Coverage", if it doesn't exist). Use `Edit`, not `Write`, for this pass
   — the file already exists and should be modified incrementally. This may be a
   separate small agent per topic, given only the gap list, so it does not need to
   re-read the whole corpus.

6. **Deterministic checks (gate 1).** Run the bundled checker on the finished page:

   ```
   python3 4-SYSTEM/Skills/claims-consolidate/verify_consolidation.py 2-RAILS/Claims/<topic-slug>.md
   ```

   It verifies citation existence (including ⚑ bold-block internal-tension claims),
   recomputes every "(N commentaries)" label, flags claims cited on both sides of a
   facet's Consensus/Divergences, finds undispositioned Coverage-table claims, and
   counts unprefixed citations. **Fix every ERROR and re-run until zero remain**;
   review each WARN and either fix it or note why it stands. Also confirm the file
   matches the template's section structure and `status: draft`.

7. **Adversarial attribution audit (gate 2 — model judgment).** Run **Phase 2** below on
   the page (one fresh agent per page that did
   NOT write it, checking every attribution against the raw files). This is what the
   deterministic checker cannot do: confirm each claim actually *says* what the page
   attributes to it, quotes are faithful, divergences are real, epistemic strength is
   preserved. Fix every critical and moderate finding, apply or consciously decline
   each minor one, then re-run the audit on the changed sections. A page that has not
   passed both gates is not finished. (The pilot pages skipped this gate on first
   writing; the retrospective audit then found a false corroboration that reached the
   final file — the gate exists so that never happens again.)

**Implementation note — orchestration.** Packet assembly is now a script, so the only
model work per topic is Stage 2 (one agent, working from the packet) plus any gap-closing
repair. Topics are therefore independent and fan out cleanly — consolidating twenty-odd
slots is twenty-odd parallel Stage-2 agents, each reading one packet, not a corpus.

The isolation guard that used to live in Stage 1 has moved upstream to `spine-map`, which
is still one isolated agent per commentary and still for the original reason: an agent
primed on one commentary's numbering mis-reads the next one's. Do not hand a single agent
several commentaries' spine maps to build at once.

The coverage diff is a plain set comparison against the packet manifest, not a model call.

---

### Completion check

- [ ] Every commentary with a raw claims file has a spine map, and the packet was
      assembled with `assemble_packet.py` exiting zero — none silently skipped
- [ ] Every claim ID in the packet's `## Manifest` is accounted for on the finished
      page — either cited or logged in "Claims reviewed, not separately cited"
      (coverage check run and gap closed)
- [ ] Every citation on the page is in `registered_id:claim_id` form
- [ ] No ⚑ divergence was flattened into a false consensus
- [ ] Coverage table lists every commentary consulted, with silence stated and
      reasoned where derivable
- [ ] `status: draft` in frontmatter; `consolidation_questions:` populated and
      echoed in `## Questions asked`
- [ ] **Gate 1:** `verify_consolidation.py` run on the final page — zero ERRORs,
      every WARN either fixed or consciously accepted
- [ ] **Gate 2:** Phase 2 run by a fresh agent — zero critical/moderate findings
      outstanding
- [ ] No file under `2-RAILS/Claims/raw/` or `1-SOURCES/` was modified

---

## Phase 1 — output language

Everything above assumes the default: an English topic page. This section specifies *only*
what differs when the consolidation is written **in the source language** instead. Where
this section is silent, Phase 1 above governs unchanged — its Stage-1 packet, question
generation, coverage check, Rules 1–16 and both verification gates all apply.

**Why a source-language layer exists.** The claims' textual authority is in the source
language at every step (source segment → raw claim `**Original:**`). An English topic page
interposes an analysis layer that source-language-generating transformations must not
round-trip through (source → English gloss → new source text is exactly the drift the rails
prevent). A source-language topic page keeps the whole chain in one language and is directly
reviewable by the tradition's own readers. The English/source-language pairs also serve as a
methodological comparison of consolidation quality by working language.

**Vault-rule note:** CLAUDE.md §10 sets English as the analysis language of `2-RAILS/`.
Source-language claims pages are a **human-contributor-authorized exception**, scoped to
`2-RAILS/Claims/<topic>-<lang>.md` files only. Record that authorization in the vault annex before
producing them.

The Tibetan case is used below as the worked example; the rules themselves are
language-independent.

### 1. Output file and frontmatter

- Path: `2-RAILS/Claims/<topic-slug>-<lang>.md`, where `<lang>` is the language tag (e.g. `-bo`).
  **The default-language page keeps the unsuffixed name; do not rename it.**
- Frontmatter adds two fields and localizes one:

  ```yaml
  topic: <topic-slug>-<lang>
  lang_tag: <lang>
  counterpart: 2-RAILS/Claims/<topic-slug>.md   # the default-language page, if it exists
  consolidation_questions:               # the questions, in the source language
    - "..."
  ```

  All other fields (`spine`, `method`, `sources`, `date`, `status: draft`) as in the
  base template.

### 2. Language of content

Everything analytical is in the source language: the synthesis statements, divergence
discussions, unique-claim summaries, question list, review-section reasons, coverage-table
notes. **Three things stay Latin-script for tooling:**

- claim citations — always `registered_id:claim_id`, never translated or transliterated;
- frontmatter field names and values that are paths/slugs;
- the English anchor word in each structural heading (next section).

**No English glosses are added to the source-language content** — the raw claims files
already carry English per claim. (This is deliberate: it keeps the page a clean test of
source-language consolidation, not a bilingual hybrid.)

### 3. Structural headings — bilingual anchors

**This table is load-bearing.** The deterministic checker (gate 1,
`4-SYSTEM/Skills/claims-consolidate/verify_consolidation.py`) parses pages by the **English anchor word in
parentheses**. Every structural heading is source-language first with the English anchor in
parentheses, verbatim. Tibetan worked example:

| Base heading | Source-language page heading |
|---|---|
| `## Questions asked` | `## དྲི་བ་བཏོན་པ (Questions asked)` |
| `### Consensus` | `### མཐུན་སྣང (Consensus)` |
| `### ⚑ Divergences` | `### ⚑ མི་མཐུན་པ (Divergences)` |
| `### Unique` | `### ཐུན་མིན (Unique)` |
| `## Claims reviewed, not separately cited` | `## བསྐྱར་ཞིབ་བྱས་ཀྱང་ལུང་མ་དྲངས་པ (Claims reviewed, not separately cited)` |
| `## Coverage` | `## ཁྱབ་ཚད (Coverage)` |

Without the exact English anchor words in parentheses, a source-language page will not
parse in `verify_consolidation.py` and gate 1 cannot run.

Facet headings (`## …`) are free source-language text — the checker does not key on them.
Attestation count labels use Arabic numerals in the form `(འགྲེལ་པ 13)` — i.e. the
source-language word for "commentary" followed by the numeral — and the checker recomputes
these exactly as it does `(13 commentaries)`.

### 4. Rules — two become easier, none are waived

- **Rule 12** (verbatim quotes) now covers *all* quoted content naturally: since the page is
  in the source language, every attested claim — Consensus, ⚑, and Unique alike — quotes its
  `**Original:**` field inline rather than paraphrasing in English. This is the norm on a
  source-language page, not an option.
- **Rule 14** (epistemic strength): quote the marker itself (Tibetan example: …སྙམ་མོ)
  instead of characterizing it.

### 5. Independence for comparison

When a default-language counterpart page exists, the source-language consolidator **must not
read it**. Work only from the Stage-1 packet, exactly as the English consolidator did.
Reading the counterpart would contaminate the language comparison and copy its errors. (The
two pages are compared *after* both exist — by a human or a dedicated comparison pass —
never during writing.)

### 6. Gates

Both gates apply unchanged. Gate 1 (`verify_consolidation.py`) parses the bilingual anchors
and the localized count labels of §3. Gate 2 (Phase 2) runs identically — the auditor checks
the source-language synthesis against the raw `**Original:**` fields, where quote fidelity is
now a character-level comparison in one language.

### Completion check (in addition to Phase 1's)

- [ ] File at `2-RAILS/Claims/<topic-slug>-<lang>.md`; default-language counterpart untouched
- [ ] `lang_tag:` and `counterpart:` in frontmatter; questions in the source language
- [ ] All structural headings carry the exact bilingual anchors of the §3 table
- [ ] Analytical content is in the source language throughout; citations stay
      `registered_id:claim_id`
- [ ] Every attested claim quotes its `**Original:**` field verbatim inline
- [ ] The default-language counterpart was never opened during consolidation

---

## Phase 2 — Adversarial attribution audit

Run as a FRESH agent that has not seen Phase 1. Checks attribution fidelity, quote fidelity, whether claimed divergences are real, and epistemic strength. Report-only — it never edits the page.

The second verification gate of this skill, also runnable standalone on any existing topic
page. A deterministic script can prove a cited claim *exists*; only a reader can prove the
claim actually *says* what the page attributes to it. This gate exists because a
retrospective audit of the first pilot pages found exactly the failure a smart consolidator
produces: a real corpus idea attached to the wrong claim ID — a "corroboration" by a claim
containing nothing of the sort — which no existence check can catch. Correct output is a findings report
precise enough that every finding can be fixed by editing one identified span of the
page, with no re-research.

**The auditor must be a fresh context that did not write the page.** An agent auditing
its own consolidation re-reads its own intentions, not the text.

---

### Inputs

- **The topic page to audit**: `2-RAILS/Claims/<topic-slug>.md`.
- **The raw claims files** it cites: `2-RAILS/Claims/raw/tree-guided/<registered_id>.md`
  (ground truth — claims appear as `#### c-… title` blocks with **Original**,
  **English**, **Type**, **Referent**, **Cite** fields, and as `⚑ **c-… title**`
  bold blocks for internal tensions).
- Run the deterministic checker first if it has not been run —
  `python3 4-SYSTEM/Skills/claims-consolidate/verify_consolidation.py <page>` — so the audit
  spends model judgment only on what the script cannot decide.

### Output

A structured findings report, delivered as the audit's response (report-only — this
skill **never edits the page or any other file**). When the human contributor wants
the findings preserved, write the report to
`0-INBOX/temp/claims-audit-<topic-slug>-<YYYY-MM-DD>.md` — never anywhere in `2-RAILS/`.

---

### Output file format

```markdown
## Audit report — <topic-slug>.md (<date>)

### VERIFIED
<N of M unique citations checked and found accurate. State plainly what was
confirmed in full — consensus lists, divergence positions, quotes, review-section
reasons.>

### ERRORS
<One entry per citation whose attribution is wrong or distorted:>
1. **`registered_id:claim_id` — <severity>.**
   - Page says: <what the page attributes, quoted>
   - Raw claim says: <what the claim actually contains, quoted>
   - <If identifiable: the claim ID the page probably meant.>

### QUOTE MISMATCHES
<Each original-language string presented as a quote from a specific claim that differs
from the raw `**Original:**` field, with both versions. "None found." if clean.>

### OTHER INTEGRITY ISSUES
<Count-label arithmetic, coverage-table mislabels, omitted in-corpus attestations
that would change a divergence's shape, raw-file inconsistencies worth a human
source check.>

**Bottom line:** <one paragraph: is the page trustworthy, and what must change.>
```

Severity scale: **critical** = a statement attributed that the claim does not make, a
fabricated corroboration, or a wrong-way divergence; **moderate** = real overstretch
that changes what a reader would believe is attested; **minor** = nuance loss,
interpolated framing, slightly-off gloss, arithmetic slips.

---

### Rules

1. **Read-only.** The audit changes nothing — not the page, not the raw files, not
   even typos. Findings go in the report; fixes are the consolidation skill's job.
2. **Ground truth is the raw claims file, only.** Judge the page against the cited
   claim's own `**Original:**` field and English gloss — never against the auditor's knowledge of
   the tradition, and never against `1-SOURCES/` directly (if the raw claim itself
   looks wrong against its source, flag it as a raw-file issue for a human; do not
   re-litigate the extraction).
3. **Every citation, not a sample.** All unique citations on the page are checked,
   including the "Claims reviewed, not separately cited" reasons and any
   ambiguous-claims sections. (Consensus lists ≤6 entries: check all; larger lists:
   check at least half, and all entries of any list whose statement bundles multiple
   propositions.)
4. **Check the specific failure classes** the pilot audit proved real:
   a. claims cited for content they do not contain (especially "X and Y independently
      attest…" — verify both);
   b. consensus statements bundling propositions their attestation lists only
      partially support;
   c. the same claim cited on both sides of one divergence;
   d. page-level harmonizations presented as a claim's own reading;
   e. epistemic upgrades (tentative → "endorses");
   f. original-language quote elisions/normalizations against the raw `**Original:**`
      field;
   g. divergences whose *other side* is attested in-corpus but omitted, flattening
      the disagreement.
5. **Cite exact claim IDs in every finding** and quote both sides (page wording vs
   raw wording) so the fix is mechanical.
6. **Do not pad.** If a section is clean, one sentence saying so. Findings ranked
   most severe first.

---

### Procedure

1. Read the topic page in full. List every unique `registered_id:claim_id` citation
   and note which section each appears in.
2. Read each cited raw claims file **once**, extracting the full content (`Original`,
   `English`, `Type`, `Referent`) of every claim the page cites — including ⚑ bold-block
   tension claims, which are not heading blocks.
3. Work through the page section by section:
   a. **Consensus sections** — for each attestation (per Rule 3's sampling floor),
      confirm the claim supports the *full* statement; note partial-support padding.
   b. **⚑ Divergence sections** — confirm each position is genuinely in its cited
      claim, attributed to the right authority, and that the two sides actually
      disagree; check whether any omitted in-corpus claim attests a listed
      "external" reading.
   c. **Unique sections** — confirm the claim says what is summarised and that no
      second commentary in the corpus attests the same content.
   d. **Quotes** — compare every original-language string attributed to a specific claim
      character-by-character against the raw `**Original:**` field.
   e. **Review/excluded sections** — confirm each one-line reason accurately
      describes the raw claim (a "pure heading" really is one, etc.).
   f. **Coverage table** — spot-check "Contributed to" labels against where the
      claims were actually used (a divergent claim labeled as Consensus is a
      finding).
4. Assemble the report in the format above, severity-ranked, and deliver it.
5. If the audit was invoked as gate 2 of Phase 1: after the
   consolidator fixes the findings, re-audit the changed sections (only) and confirm
   the fixes; the page passes when no critical or moderate finding remains.

---

### Completion check

- [ ] Every unique citation on the page was checked against its raw claim (sampling
      floor of Rule 3 met or exceeded; review-section reasons included)
- [ ] Every finding cites an exact `registered_id:claim_id` and quotes page wording
      vs raw wording
- [ ] Every finding carries a severity (critical / moderate / minor)
- [ ] All seven failure classes of Rule 4 were explicitly checked
- [ ] No file was modified anywhere in the vault (report written to `0-INBOX/temp/` only
      if the human asked for it)
- [ ] Bottom line states plainly whether the page is trustworthy and what must change

---

## After this skill

An audited topic page is the input to `wiki-article-from-claims`. Drafting an article
from an unaudited page propagates every attribution error into the article, where it
is much harder to find.
