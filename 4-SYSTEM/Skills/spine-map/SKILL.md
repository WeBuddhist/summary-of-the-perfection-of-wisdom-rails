---
name: spine-map
description: Build one commentary's routing index from its own TOC nodes and claim IDs onto the canonical spine slots of the root text — the once-per-commentary judgment that lets claims-consolidation assemble any topic's packet by script instead of re-reading every raw claims file per topic.
---

# spine-map

This skill answers one question per commentary, once: **which of this commentary's own
structural-outline nodes (Tibetan ས་བཅད / *sa bcad*) — or, where that outline is coarser
than the spine, which of its claims — hold the content for which canonical spine slot of
the root text?** The answer is a small
routing table at `2-RAILS/Claims/raw/spine-map/<registered-id>.md`. It records addresses
only — node numbers, claim IDs, slot names — and never what a claim says.

It exists because `claims-consolidate` (Phase 1) used to re-derive this mapping inside every
topic run: Stage 1 read every raw claims file in the corpus once per topic, so a full run
over *T* topics with *N* commentaries meant *N × T* full-corpus reads of the same unchanged
files. The mapping is per-commentary, not per-topic — resolving one commentary's numbering
against the spine answers it for **every slot at once** — so it belongs here, computed once,
and reused by `assemble_packet.py` for every topic thereafter.

Correct output is a table in which **every claim in the commentary's raw claims file has
exactly one disposition** (routed to a slot by node, routed to a slot by claim ID, flagged
ambiguous, or logged under an unmapped node), the counts are computed rather than
hand-tallied, and `verify_spine_map.py` exits clean. A map that leaves a claim
undispositioned silently deletes that claim from every future topic page — which is exactly
the "silent claim loss" failure the consolidation pipeline exists to prevent.

**This skill makes no interpretive claims and therefore adds no link to the citation chain.**
It is an index over `2-RAILS/Claims/raw/tree-guided/`, read-only on everything it touches.

---

## Inputs

- **The commentary's finished TOC tree** — `2-RAILS/Sections/Raw/toc-tree/<registered-id>.md`,
  `status: complete`. This is the structure being mapped *from*. If it is missing or not
  QC-clean, stop: run `toc-generate` first.
- **The commentary's raw claims file** — `2-RAILS/Claims/raw/tree-guided/<registered-id>.md`.
  Read its **claim heading lines** (`##### c-… <title>`) for routing; you do not need to read
  claim bodies except to resolve a genuine ambiguity.
- **The root text** — `1-SOURCES/Text/<root>.md` — ground truth for what each spine slot *is*
  (its verse, its block ID, its opening words). Consult it whenever a node title does not
  itself name the slot.
- **The canonical slot list** — the vault annex (`4-SYSTEM/Guidelines/vault-annex.md`,
  section "Canonical spine slots"). This is the vault's registry of spine slots and their
  root anchors. Never invent a slot ID that is not
  registered there; if the commentary needs one that does not exist, stop and ask the human
  contributor to register it first.
- If any of the above is missing for a commentary that should be mapped, stop and ask rather
  than guessing a mapping.

## Output

One file at `2-RAILS/Claims/raw/spine-map/<registered-id>.md`.

It sits under `Claims/raw/` because it is per-commentary and derived from one commentary in
isolation, like everything else there — but it is an **index layer, not an extraction**: it
adds no claims and is regenerable at any time without touching the extractions it points at.

---

## Output file format

Template: `4-SYSTEM/Skills/spine-map/templates/spine-map.md`. Follow it exactly — `assemble_packet.py` and
`verify_spine_map.py` both parse these tables, so heading names and column order are a
contract, not a style preference.

```markdown
---
registered_id: <id>
spine_scheme: <the annex's scheme name>
source_tree: 2-RAILS/Sections/Raw/toc-tree/<id>.md
source_claims: 2-RAILS/Claims/raw/tree-guided/<id>.md
root_text: 1-SOURCES/Text/<root>.md
claim_count: <total claims in the raw file — computed>
mapped_claims: <computed>
extra_claims: <computed>
ambiguous_claims: <computed>
unmapped_claims: <computed>
date: <YYYY-MM-DD>
status: draft
---

# Spine map — <registered-id>

> Routing index only. …

**Structure of this commentary.** <Two to four sentences: how this commentary's tree is
shaped, where the spine content sits in it, and what evidence establishes the correspondence
(node titles that name the root text's units by ordinal or by descriptive name, root-verse
quotations inside the claims, etc.). This paragraph is what a later reader needs to trust the table.>

## Slot map

| Slot | Root anchor | Node(s) | Node title(s) (verbatim) | Claims |
|---|---|---|---|---|
| `<slot-id>` | `^<block-id>` | `<n.n.n>` | <verbatim node title from the TOC tree> | <n> |

## Claim-level routing

| Slot | Claim ID(s) | Why routed by claim rather than by node |
|---|---|---|
| `<slot-id>` | `c-2-1-2-1-1`–`c-2-1-2-1-6` | <routing reason — e.g. "node 2.1.2.1 runs several spine slots undivided; boundaries are the root-verse quotation claims."> |

## Ambiguous claims

| Claim ID | Candidate slots | Why uncertain |
|---|---|---|
| (none) | | |

## Silent slots

| Slot | Why silent (where derivable) |
|---|---|

## Unmapped nodes

| Node | Title (verbatim) | Claims | Why not a spine slot |
|---|---|---|---|
```

---

## Rules

1. **Routing only — never interpretation.** This file records addresses. Do not restate,
   summarise, paraphrase, or evaluate a claim's content anywhere in it. The "why" columns
   explain the *routing decision*, not the doctrine. (A spine map is not a rail in the
   citation-chain sense and must never become one.)
2. **Node numbering is never assumed uniform.** This is `claims-consolidate` (Phase 1) Rule 1, and it
   is the whole reason this skill needs a model rather than a script. One commentary nests a
   slot's content at `1.1.N`, another at top level `N`, another titles nodes by a descriptive
   name instead of an ordinal, another runs every slot inside a single undivided node. Verify
   every row against *this* commentary's own tree and the root text. A numbering rule that worked
   for the last commentary is evidence of nothing about this one.
3. **Every claim gets exactly one disposition.** Every claim ID in the raw file must be
   covered by exactly one of: a Slot map node's subtree, a Claim-level routing row, an
   Ambiguous row, or an Unmapped nodes row. Neither zero (silent loss) nor two (silent
   duplication into two packets) is acceptable. `verify_spine_map.py` enforces this.
4. **Never map a node and its own descendant to different slots.** Node routing is by
   subtree, so mapping node `1.1` sweeps in every `1.1.*`. When a parent node has its own
   direct claims that belong somewhere else, route *those claims* through Claim-level
   routing and leave the parent node unmapped.
5. **Node titles are copied verbatim.** Character-for-character from the TOC tree — no
   normalization, no truncation, no translation in that column.
6. **Counts are computed, never hand-tallied.** Fill the Claims column and every frontmatter
   count from `verify_spine_map.py --counts <id>`, then let the verifier recompute them.
   (`claims-consolidate` (Phase 1) Rule 15, same discipline, same reason.)
7. **Silence is a finding.** A registered slot this commentary genuinely does not treat goes
   in Silent slots with a reason where one is derivable — never simply left out. A slot that
   is neither mapped nor marked silent is a gap, and `assemble_packet.py` will fail on it.
8. **Ambiguity is carried through, never silently resolved.** A claim you cannot confidently
   route goes in Ambiguous claims with its candidate slots and the reason — never
   force-fitted to the nearest slot, never dropped. The assembler passes it into every
   candidate slot's packet with a visible flag so the consolidator decides in the open.
9. **Slot IDs come from the annex registry.** Lowercase-hyphenated, exactly as registered in
   the vault annex under "Canonical spine slots". Never coin one locally — a locally invented
   slot ID forks the naming space and every later re-run produces a second page.
10. **Read-only on everything but the output.** Never modify `1-SOURCES/`,
    `2-RAILS/Claims/raw/tree-guided/`, or `2-RAILS/Sections/Raw/toc-tree/` while mapping.
11. **`status: draft`, always.** An LLM never marks its own output complete — a domain
    specialist does, per `2-RAILS/About Rails.md`.

---

## Procedure

1. **Get the claim inventory.** Run:

   ```
   python3 4-SYSTEM/Skills/spine-map/verify_spine_map.py --counts <registered-id>
   ```

   This prints every node that holds claims, how many, and the node's title from the TOC
   tree. It is the checklist for step 5: every node listed here must end up somewhere.

2. **Read the TOC tree in full.** `2-RAILS/Sections/Raw/toc-tree/<registered-id>.md`. Identify
   which branch carries the root text's spine content and which branches are the commentary's
   own additions (front matter, origin narrative, ritual appendices, story collections,
   colophon).

3. **Read the canonical slot list.** The vault annex, section "Canonical spine slots" — the
   registered slots and their root anchors.

4. **Establish the correspondence, with evidence.** For each slot, find the node whose title
   or content attests it — an ordinal (Tibetan example: བཅུ་གསུམ་པ་ཕྱག་འཚལ་, "thirteenth
   homage"), a descriptive name the tradition uses for that unit, or a quotation of the root
   verse. Where the tree is coarser than the spine (one node holding several slots), scan
   that node's **claim heading lines** in the raw claims file: root-verse quotation claims
   ("Verse N quoted: …") are the reliable boundary markers. Consult the root
   text whenever the correspondence is not self-evident from the title.

5. **Assign a disposition to every node from step 1.** Spine nodes → Slot map rows. Coarse
   nodes covering several slots → Claim-level routing rows, using en-dash ranges
   (`c-2-1-2-1-2`–`c-2-1-2-1-6`) rather than listing every ID. A parent node's own direct
   claims → Claim-level routing (Rule 4). Everything genuinely outside the spine (front
   matter, `0`/`z` pseudo-nodes, the commentary's own appendices) → Unmapped nodes with a
   reason. Anything you cannot decide → Ambiguous claims.

6. **List the silent slots.** Every registered slot with no row in the Slot map and no
   Claim-level routing row goes in Silent slots, with a reason where derivable from the
   source.

7. **Write the file** at `2-RAILS/Claims/raw/spine-map/<registered-id>.md`, per the template.
   Fill counts from step 1.

8. **Verify (gate, mandatory).**

   ```
   python3 4-SYSTEM/Skills/spine-map/verify_spine_map.py 2-RAILS/Claims/raw/spine-map/<registered-id>.md
   ```

   Fix every ERROR and re-run until zero remain; review each WARN and either fix it or note
   why it stands. The checks are: node existence against the tree, claim existence against
   the raw file, disposition completeness (no uncovered, no doubly-covered claims),
   ancestor/descendant node overlap, recomputed counts, and slot hygiene.

**Orchestration.** Commentaries are independent — this fans out cleanly, one isolated agent
per commentary, exactly like `commentary-claims` (Strategy 1)'s per-node isolation and for the same
reason: an agent that has just mapped another commentary's tree is primed to see the same
numbering here, which is the specific error Rule 2 exists to prevent.

---

## Completion check

- [ ] `2-RAILS/Claims/raw/spine-map/<registered-id>.md` exists and follows the template's
      exact heading names and column order
- [ ] Every node reported by `--counts` has a disposition (slot, claim-level routing,
      ambiguous, or unmapped) — none silently omitted
- [ ] Every registered slot from the annex appears in the Slot map, in Claim-level routing,
      or in Silent slots — none simply absent
- [ ] Node titles copied verbatim from the TOC tree
- [ ] No node is mapped alongside its own ancestor or descendant under a different slot
- [ ] Counts filled from `--counts` and confirmed by the verifier, not hand-tallied
- [ ] No claim content is restated, summarised, or interpreted anywhere in the file
- [ ] `verify_spine_map.py` run on the finished file — zero ERRORs, every WARN fixed or
      consciously accepted
- [ ] `status: draft` in frontmatter
- [ ] No file under `1-SOURCES/`, `Claims/raw/tree-guided/`, or `Sections/Raw/toc-tree/` was
      modified
