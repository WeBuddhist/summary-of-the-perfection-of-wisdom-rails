---
registered_id: <id>
spine_scheme: <scheme name from the vault annex, "Canonical spine slots">
source_tree: $SECTIONS_RAW/toc-tree/<id>.md
source_claims: $CLAIMS/raw/tree-guided/<id>.md
root_text: $SOURCE_TEXTS/<root-text-file>.md
claim_count: <computed>
mapped_claims: <computed>
extra_claims: <computed>
ambiguous_claims: <computed>
unmapped_claims: <computed>
date: <YYYY-MM-DD>
status: draft
---

# Spine map — <registered-id>

> Routing index only. This file records **which of this commentary's own TOC nodes hold
> which canonical spine slot's content** — nothing about what the claims say. It never
> quotes, interprets, or restates a claim; `assemble_packet.py` copies the claim text
> itself verbatim out of the raw claims file at packet time. Every claim in that file has
> exactly one disposition below.

**Structure of this commentary.** <Two to four sentences: how this commentary's tree is
shaped, where the spine content sits within it, and what evidence establishes the
correspondence — node titles naming the root text's units by ordinal or by descriptive
name, root-verse quotations inside the claims, and so on. This paragraph is what lets a
later reader trust the table without redoing the mapping.>

## Slot map

Node routing is **by subtree**: a row mapping node `1.1.3` collects every claim under
`1.1.3` and its descendants. Never map a node alongside its own ancestor or descendant
under a different slot — route the parent's own direct claims through Claim-level routing
instead.

| Slot | Root anchor | Node(s) | Node title(s) (verbatim) | Claims |
|---|---|---|---|---|
| `<slot-id>` | `^<block-id>` | `<n.n.n>` | <verbatim title from the TOC tree> | <n> |

## Claim-level routing

For commentaries whose structural outline is coarser than the spine (one node covering
several slots), and for a parent node's own direct claims. Ranges use an **en-dash**, never
a plain hyphen — claim IDs contain hyphens: `` `c-2-1-2-1-2`–`c-2-1-2-1-6` ``.

| Slot | Claim ID(s) | Why routed by claim rather than by node |
|---|---|---|
| `<slot-id>` | `<c-…>`–`<c-…>` | <the routing reason — never the claim's content> |

## Ambiguous claims

Claims that cannot be confidently routed. Never force-fit to the nearest slot, never drop.
The assembler passes these into each candidate slot's packet with a visible flag.

| Claim ID | Candidate slots | Why uncertain |
|---|---|---|
| (none) | | |

## Silent slots

Every registered slot this commentary does not treat. Absence is a finding, not a gap — a
slot that is neither mapped nor listed here will fail `assemble_packet.py`.

| Slot | Why silent (where derivable) |
|---|---|
| `<slot-id>` | <reason from the source, or "no reason derivable"> |

## Unmapped nodes

Nodes holding claims that belong to no spine slot — the commentary's own front matter,
colophon, ritual appendices, story collections. A legitimate disposition, not a failure.
`0` and `z` are the extraction's front-/back-matter pseudo-nodes and are expected here.

| Node | Title (verbatim) | Claims | Why not a spine slot |
|---|---|---|---|
| `<n>` | <verbatim title, or a note for pseudo-nodes> | <n> | <reason> |
