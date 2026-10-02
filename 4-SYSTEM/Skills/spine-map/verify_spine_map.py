#!/usr/bin/env python3
"""Deterministic checks for one commentary's spine map (spine-map skill).

Usage:
    python3 verify_spine_map.py <spine-map.md>
    python3 verify_spine_map.py --counts <registered_id>   # per-node claim inventory,
                                                           # to author the map against

Paths to the commentary's TOC tree and raw claims file are read from the map's own
frontmatter (`source_tree:`, `source_claims:`), resolved against the vault root.

Checks (all deterministic — no model judgment):
  1. NODE EXISTENCE — every node decimal in the Slot map and Unmapped nodes tables
     is a real node of that commentary's own TOC tree.
  2. CLAIM EXISTENCE — every claim ID in the Extra claims and Ambiguous claims
     tables is a real claim in that commentary's raw claims file. Recognises both
     forms tree-guided extractions use: heading claims (`#### c-... title`) and
     internal-tension claims (`⚑ **c-... title**`).
  3. DISPOSITION COMPLETENESS — the invariant the packet assembler depends on:
     every claim in the raw file is covered by exactly one disposition (a mapped
     node's subtree, an Extra-claims row, an Ambiguous row, or an Unmapped-nodes
     row). Uncovered claims and doubly-covered claims are both errors — an
     uncovered claim can never reach a topic page, and a doubly-covered one is
     silently duplicated into two packets.
  4. COUNTS RECOMPUTED — every per-row `Claims` count and every frontmatter count
     is recomputed from the claims file, never trusted as written (the same
     hand-tally discipline as claims-consolidation Rule 15).
  5. SLOT HYGIENE — slot IDs are lowercase-hyphenated, no slot is listed both in
     the Slot map and in Silent slots, and no node is claimed by two slots.

NOT covered here (needs model judgment — that is what the skill's own read is for):
  whether a node genuinely *is* the spine slot it was mapped to, whether a node
  title actually names that slot, whether an ambiguity was correctly identified.

Exit code 0 = no errors (warnings allowed); 1 = at least one error.
"""
import os
import re
import sys

CLAIM_HEAD = re.compile(r'^#{3,6}\s+(c-[0-9a-z][0-9a-zA-Z\-]*)\b', re.M)
TENSION_HEAD = re.compile(r'^⚑\s+\*\*(c-[0-9a-z][0-9a-zA-Z\-]*)\b', re.M)
TREE_NODE = re.compile(r'^\s*\*\s+([0-9]+(?:\.[0-9]+)*)\.?\s+(\S.*?)\s*(?:\[\[\d+\]\])?\s*$', re.M)
CLAIM_ID = re.compile(r'(c-[0-9a-z][0-9a-zA-Z\-]*)')
RANGE = re.compile(r'(c-[0-9a-z][0-9a-zA-Z\-]*?)(?:\s*[–—]\s*|\s+-\s+)(c-[0-9a-z][0-9a-zA-Z\-]*)')
NODE_ID = re.compile(r'([0-9]+(?:\.[0-9]+)*|[a-z])')

# tree-guided extractions bucket material lying outside the sa-bcad tree under two
# pseudo-nodes: `0` (front matter, before the first division) and `z` (back matter,
# colophon/dedication). Neither is a node of the TOC tree, and neither is an error.
PSEUDO_NODES = {'0', 'z'}


def vault_root(start):
    d = os.path.dirname(os.path.abspath(start))
    while d != '/' and not os.path.isdir(os.path.join(d, '2-RAILS')):
        d = os.path.dirname(d)
    return d


def front_matter(txt):
    m = re.match(r'^---\n(.*?)\n---\n', txt, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split('\n'):
        kv = re.match(r'^([a-z_]+):\s*(.*)$', line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return fm


def table_rows(txt, heading_words):
    """Return the data rows (list of cell-lists) of the table under a heading."""
    pat = r'^##+ [^\n]*(?:%s)[^\n]*$(.*?)(?=^## |\Z)' % '|'.join(heading_words)
    m = re.search(pat, txt, re.M | re.S)
    if not m:
        return []
    rows = []
    for line in m.group(1).split('\n'):
        if not line.strip().startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if not cells or set(''.join(cells)) <= set('-: '):
            continue
        if cells and re.match(r'^(slot|claim id|node|spine slot)', cells[0], re.I):
            continue
        rows.append(cells)
    return rows


def node_of(claim_id):
    """c-1-1-4-2 -> '1.1.4' ; c-z-1 -> 'z' ; c-0-3 -> '0'."""
    segs = claim_id[2:].split('-')
    return '.'.join(segs[:-1]) if len(segs) > 1 else ''


def covers(node, target):
    return node == target or node.startswith(target + '.')


def expand_range(a, b):
    """c-2-1-2-1-2 – c-2-1-2-1-6 -> the six IDs between, when only the last segment differs."""
    pa, pb = a.rsplit('-', 1), b.rsplit('-', 1)
    if pa[0] == pb[0] and pa[1].isdigit() and pb[1].isdigit():
        lo, hi = int(pa[1]), int(pb[1])
        if lo <= hi and hi - lo <= 500:
            return [f"{pa[0]}-{i}" for i in range(lo, hi + 1)], True
    return [a, b], False


def cell_ids(cell):
    """Claim IDs in a table cell, expanding en-dash ranges.

    A plain hyphen is never a range separator — claim IDs contain hyphens. Use an
    en-dash/em-dash (`c-1-2`–`c-1-8`), or a spaced hyphen.
    """
    cell = re.sub(r'[`*]', '', cell)
    out, partial = [], []
    for a, b in RANGE.findall(cell):
        ids, full = expand_range(a, b)
        out += ids
        if not full:
            partial.append((a, b))
    out += CLAIM_ID.findall(RANGE.sub(' ', cell))
    return out, partial


def cell_nodes(cell):
    cell = re.sub(r'[`*]', '', cell).strip()
    if not cell or cell in ('—', '-', 'none', 'None'):
        return []
    return [n for n in NODE_ID.findall(cell)]


def counts_mode(rid):
    """Print the per-node claim inventory for one commentary, so the Slot map's
    Claims column is filled from computed numbers rather than hand-tallied."""
    here = os.path.abspath(__file__)
    root = vault_root(here)
    path = os.path.join(root, '2-RAILS/Claims/raw/tree-guided', rid + '.md')
    if not os.path.isfile(path):
        print(f"ERROR: no raw claims file at {path}")
        sys.exit(2)
    txt = open(path, encoding='utf-8').read()
    ids = set(CLAIM_HEAD.findall(txt)) | set(TENSION_HEAD.findall(txt))
    tree_path = os.path.join(root, '2-RAILS/Sections/Raw/toc-tree', rid + '.md')
    titles = {}
    if os.path.isfile(tree_path):
        titles = dict(TREE_NODE.findall(open(tree_path, encoding='utf-8').read()))
    tally = {}
    for c in ids:
        tally[node_of(c)] = tally.get(node_of(c), 0) + 1

    def key(n):
        return [int(x) if x.isdigit() else x for x in n.split('.')]

    print(f"{rid}: {len(ids)} claims across {len(tally)} nodes")
    print(f"{'node':14s} {'claims':>6s}  title (from the TOC tree)")
    for n in sorted(tally, key=key):
        label = titles.get(n, '(pseudo-node — outside the sa-bcad tree)'
                           if n in PSEUDO_NODES else '⚠ NOT IN TREE')
        print(f"{n:14s} {tally[n]:6d}  {label}")
    print(f"\ntotal {sum(tally.values())} — every one of these needs exactly one "
          f"disposition in the spine map.")
    sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == '--counts':
        if len(sys.argv) < 3:
            print("usage: verify_spine_map.py --counts <registered_id>")
            sys.exit(2)
        counts_mode(sys.argv[2])
    path = os.path.abspath(sys.argv[1])
    txt = open(path, encoding='utf-8').read()
    root = vault_root(path)
    fm = front_matter(txt)

    errors, warnings = [], []

    claims_path = os.path.join(root, fm.get('source_claims', ''))
    tree_path = os.path.join(root, fm.get('source_tree', ''))
    if not os.path.isfile(claims_path):
        print(f"ERROR: source_claims not found: {fm.get('source_claims')}")
        sys.exit(1)
    ctxt = open(claims_path, encoding='utf-8').read()
    real_claims = set(CLAIM_HEAD.findall(ctxt)) | set(TENSION_HEAD.findall(ctxt))

    tree_nodes = set()
    if os.path.isfile(tree_path):
        tree_nodes = {n for n, _ in TREE_NODE.findall(open(tree_path, encoding='utf-8').read())}
    else:
        warnings.append(f"source_tree not found ({fm.get('source_tree')}) — node existence unchecked")

    # ---- gather the four dispositions ---------------------------------------------
    slot_rows = table_rows(txt, ['Slot map'])
    extra_rows = table_rows(txt, ['Claim-level routing', 'Extra claims'])
    amb_rows = table_rows(txt, ['Ambiguous claims'])
    silent_rows = table_rows(txt, ['Silent slots'])
    unmapped_rows = table_rows(txt, ['Unmapped nodes'])

    owner = {}          # claim id -> list of disposition labels
    slot_nodes = {}     # slot -> [nodes]
    node_owner = {}     # node -> slot

    def claim(cid, label):
        owner.setdefault(cid, []).append(label)

    for cells in slot_rows:
        slot = re.sub(r'[`*]', '', cells[0]).strip()
        if not slot:
            continue
        if not re.match(r'^[a-z][a-z0-9-]*$', slot):
            errors.append(f"slot id is not lowercase-hyphenated: “{slot}”")
        nodes = cell_nodes(cells[2]) if len(cells) > 2 else []
        slot_nodes[slot] = nodes
        for n in nodes:
            if tree_nodes and n not in tree_nodes and n not in PSEUDO_NODES:
                errors.append(f"slot `{slot}` maps node {n}, which is not in the TOC tree")
            if n in node_owner and node_owner[n] != slot:
                errors.append(f"node {n} is claimed by two slots: `{node_owner[n]}` and `{slot}`")
            for other, oslot in node_owner.items():
                if oslot == slot:
                    continue
                if covers(n, other) or covers(other, n):
                    anc, desc = (other, n) if covers(n, other) else (n, other)
                    errors.append(
                        f"node overlap: `{node_owner[anc] if anc in node_owner else slot}` maps "
                        f"node {anc}, which is an ancestor of node {desc} mapped by "
                        f"`{slot if desc == n else node_owner[desc]}` — the ancestor's subtree "
                        f"swallows the descendant's claims. Route the ancestor's own direct "
                        f"claims through the Extra claims table instead.")
            node_owner[n] = slot
        got = sorted(c for c in real_claims if any(covers(node_of(c), n) for n in nodes))
        for c in got:
            claim(c, f"slot:{slot}")
        if len(cells) > 4:
            stated = re.sub(r'[^0-9]', '', cells[4])
            if stated and int(stated) != len(got):
                errors.append(
                    f"slot `{slot}`: Claims column says {stated}, node subtree actually "
                    f"holds {len(got)} claims")

    for cells in extra_rows:
        slot = re.sub(r'[`*]', '', cells[0]).strip()
        if slot and not re.match(r'^[a-z][a-z0-9-]*$', slot):
            errors.append(f"claim-level routing: slot id is not lowercase-hyphenated: “{slot}”")
        ids, partial = cell_ids(cells[1] if len(cells) > 1 else '')
        for a, b in partial:
            errors.append(f"claim-level routing for `{slot}`: range {a}–{b} is not "
                          f"expandable (only the final segment may differ)")
        for cid in ids:
            if cid not in real_claims:
                errors.append(f"claim-level routing for `{slot}` lists nonexistent claim {cid}")
            else:
                claim(cid, f"extra:{slot}")

    for cells in amb_rows:
        ids, partial = cell_ids(cells[0])
        for a, b in partial:
            errors.append(f"Ambiguous claims: range {a}–{b} is not expandable")
        for cid in ids:
            if cid not in real_claims:
                errors.append(f"Ambiguous claims lists nonexistent claim {cid}")
            else:
                claim(cid, 'ambiguous')

    for cells in unmapped_rows:
        nodes = cell_nodes(cells[0])
        for n in nodes:
            if tree_nodes and n not in tree_nodes and n not in PSEUDO_NODES:
                warnings.append(f"Unmapped nodes lists node {n}, not found in the TOC tree")
        got = [c for c in real_claims if any(covers(node_of(c), n) for n in nodes)]
        for c in got:
            claim(c, 'unmapped')

    silent = {re.sub(r'[`*]', '', c[0]).strip() for c in silent_rows if c and c[0].strip()}
    for s in sorted(silent & set(slot_nodes)):
        errors.append(f"slot `{s}` appears in BOTH the Slot map and Silent slots")

    # ---- 3. disposition completeness ----------------------------------------------
    uncovered = sorted(c for c in real_claims if c not in owner)
    for c in uncovered[:25]:
        errors.append(
            f"undispositioned claim {c} (node {node_of(c) or '?'}) — not in any mapped "
            f"slot, extra, ambiguous, or unmapped node")
    if len(uncovered) > 25:
        errors.append(f"...and {len(uncovered) - 25} more undispositioned claims")

    doubled = sorted(c for c, labs in owner.items()
                     if len({l for l in labs}) > 1)
    for c in doubled[:15]:
        errors.append(f"claim {c} has two dispositions: {', '.join(sorted(set(owner[c])))}")
    if len(doubled) > 15:
        errors.append(f"...and {len(doubled) - 15} more doubly-dispositioned claims")

    # ---- 4. frontmatter counts recomputed -----------------------------------------
    actual = {
        'claim_count': len(real_claims),
        'mapped_claims': len([c for c, l in owner.items() if any(x.startswith('slot:') for x in l)]),
        'extra_claims': len([c for c, l in owner.items() if any(x.startswith('extra:') for x in l)]),
        'ambiguous_claims': len([c for c, l in owner.items() if 'ambiguous' in l]),
        'unmapped_claims': len([c for c, l in owner.items() if 'unmapped' in l]),
    }
    for k, v in actual.items():
        if k in fm and re.sub(r'[^0-9]', '', fm[k]) not in ('', str(v)):
            errors.append(f"frontmatter {k}: {fm[k]} — recomputed value is {v}")
        elif k not in fm:
            warnings.append(f"frontmatter is missing {k}: (recomputed value is {v})")

    # ---- report --------------------------------------------------------------------
    print(f"spine map: {os.path.basename(path)}  ({fm.get('registered_id', '?')})")
    print(f"claims: {len(real_claims)} total — {actual['mapped_claims']} mapped, "
          f"{actual['extra_claims']} extra, {actual['ambiguous_claims']} ambiguous, "
          f"{actual['unmapped_claims']} unmapped")
    print(f"slots mapped: {len(slot_nodes)}   slots marked silent: {len(silent)}")
    for e in errors:
        print(f"ERROR: {e}")
    for w in warnings:
        print(f"WARN:  {w}")
    if not errors and not warnings:
        print("clean.")
    print(f"result: {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
