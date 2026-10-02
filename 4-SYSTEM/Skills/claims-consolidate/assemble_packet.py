#!/usr/bin/env python3
"""Assemble one spine slot's consolidation packet from the per-commentary spine maps.

Usage:
    python3 assemble_packet.py <slot> [--out FILE] [--manifest-out FILE] [--vault DIR]
    python3 assemble_packet.py --list-slots [--vault DIR]

This replaces Stage 1 of claims-consolidation (the per-commentary mapping pass that
re-read every raw claims file once per topic). The routing decisions now live in
`2-RAILS/Claims/raw/spine-map/<registered-id>.md`, made once per commentary; this
script does the mechanical part — collecting the slot's claims out of every
commentary's raw file and concatenating them into one packet.

Nothing here uses model judgment. Every claim block in the output is copied
character-for-character out of `2-RAILS/Claims/raw/tree-guided/<id>.md`, which is
also why it fixes a whole error class a retrospective audit found: silently
elided syllables and normalized orthography in original-language quotes. A script
cannot mis-transcribe them.

The packet's `## Manifest` is the authoritative input to the coverage check
(claims-consolidate Phase 1, procedure step 5): diff it against the claim IDs the finished
topic page cites, and every ID in the gap must be closed.

Exit code 0 = packet written; 1 = a commentary has no disposition for the slot
(neither a Slot map row nor a Silent slots row) — a real gap, not a formatting nit.
"""
import os
import re
import sys
from datetime import date

CLAIM_HEAD = re.compile(r'^(#{3,6})\s+(c-[0-9a-z][0-9a-zA-Z\-]*)\s*(.*)$')
TENSION_HEAD = re.compile(r'^⚑\s+\*\*(c-[0-9a-z][0-9a-zA-Z\-]*)\s*(.*?)\*\*\s*$')
CLAIM_ID = re.compile(r'(c-[0-9a-z][0-9a-zA-Z\-]*)')
RANGE = re.compile(r'(c-[0-9a-z][0-9a-zA-Z\-]*?)(?:\s*[–—]\s*|\s+-\s+)(c-[0-9a-z][0-9a-zA-Z\-]*)')
NODE_ID = re.compile(r'([0-9]+(?:\.[0-9]+)*|[a-z])')


def expand_range(a, b):
    pa, pb = a.rsplit('-', 1), b.rsplit('-', 1)
    if pa[0] == pb[0] and pa[1].isdigit() and pb[1].isdigit():
        lo, hi = int(pa[1]), int(pb[1])
        if lo <= hi and hi - lo <= 500:
            return [f"{pa[0]}-{i}" for i in range(lo, hi + 1)]
    return [a, b]


def cell_ids(cell):
    """Claim IDs in a cell, expanding en-dash ranges (`c-1-2`–`c-1-8`)."""
    cell = re.sub(r'[`*]', '', cell)
    out = []
    for a, b in RANGE.findall(cell):
        out += expand_range(a, b)
    out += CLAIM_ID.findall(RANGE.sub(' ', cell))
    return out


def front_matter(txt):
    m = re.match(r'^---\n(.*?)\n---\n', txt, re.S)
    fm = {}
    if m:
        for line in m.group(1).split('\n'):
            kv = re.match(r'^([a-z_]+):\s*(.*)$', line)
            if kv:
                fm[kv.group(1)] = kv.group(2).strip().strip('"').strip("'")
    return fm


def table_rows(txt, heading_words):
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
        if re.match(r'^(slot|claim id|node|spine slot)', cells[0], re.I):
            continue
        rows.append(cells)
    return rows


def node_of(claim_id):
    segs = claim_id[2:].split('-')
    return '.'.join(segs[:-1]) if len(segs) > 1 else ''


def covers(node, target):
    return node == target or node.startswith(target + '.')


def clean(cell):
    return re.sub(r'[`*]', '', cell).strip()


def cell_nodes(cell):
    c = clean(cell)
    return [] if c in ('', '—', '-', 'none', 'None') else NODE_ID.findall(c)


def load_claim_blocks(path):
    """claim_id -> (heading_line, block_text) preserving verbatim source formatting."""
    lines = open(path, encoding='utf-8').read().split('\n')
    blocks, cur, buf = {}, None, []
    for line in lines:
        h = CLAIM_HEAD.match(line)
        t = TENSION_HEAD.match(line)
        if h or t or line.startswith('#'):
            if cur:
                blocks[cur] = '\n'.join(buf).rstrip()
            if h:
                cur, buf = h.group(2), [line]
            elif t:
                cur, buf = t.group(1), [line]
            else:
                cur, buf = None, []
            continue
        if cur:
            buf.append(line)
    if cur:
        blocks[cur] = '\n'.join(buf).rstrip()
    return blocks


def main():
    args = sys.argv[1:]
    vault = os.getcwd()
    if '--vault' in args:
        vault = os.path.abspath(args[args.index('--vault') + 1])
    else:
        d = os.path.abspath(os.path.dirname(__file__))
        while d != '/' and not os.path.isdir(os.path.join(d, '2-RAILS')):
            d = os.path.dirname(d)
        vault = d

    map_dir = os.path.join(vault, '2-RAILS/Claims/raw/spine-map')
    raw_dir = os.path.join(vault, '2-RAILS/Claims/raw/tree-guided')
    if not os.path.isdir(map_dir):
        print(f"ERROR: no spine maps at {map_dir} — run the spine-map skill first")
        sys.exit(2)

    maps = sorted(f for f in os.listdir(map_dir) if f.endswith('.md'))

    if '--list-slots' in args:
        seen = {}
        for f in maps:
            txt = open(os.path.join(map_dir, f), encoding='utf-8').read()
            for cells in table_rows(txt, ['Slot map']):
                seen.setdefault(clean(cells[0]), []).append(f[:-3])
        for slot in sorted(seen):
            print(f"{slot:20s} {len(seen[slot]):2d} commentaries")
        sys.exit(0)

    if not args or args[0].startswith('--'):
        print(__doc__)
        sys.exit(2)
    slot = args[0]

    out_path = None
    if '--out' in args:
        out_path = os.path.abspath(args[args.index('--out') + 1])
    manifest_path = None
    if '--manifest-out' in args:
        manifest_path = os.path.abspath(args[args.index('--manifest-out') + 1])

    # A commentary with a raw claims file but no spine map would be silently absent
    # from every packet — the exact "silent claim loss" failure the consolidation
    # skill exists to prevent. Catch it before assembling anything.
    have_claims = {f[:-3] for f in os.listdir(raw_dir) if f.endswith('.md')} \
        if os.path.isdir(raw_dir) else set()
    unmapped_commentaries = sorted(have_claims - {f[:-3] for f in maps})

    sections, manifest, gaps = [], [], []
    n_present = n_silent = 0
    anchor = ''

    for f in maps:
        rid = f[:-3]
        mtxt = open(os.path.join(map_dir, f), encoding='utf-8').read()
        rows = [c for c in table_rows(mtxt, ['Slot map']) if clean(c[0]) == slot]
        silent = [c for c in table_rows(mtxt, ['Silent slots']) if clean(c[0]) == slot]
        extra = [c for c in table_rows(mtxt, ['Claim-level routing', 'Extra claims'])
                 if clean(c[0]) == slot]
        amb = [c for c in table_rows(mtxt, ['Ambiguous claims'])
               if slot in clean(c[1] if len(c) > 1 else '')]

        if not rows and not extra and not amb:
            if silent:
                n_silent += 1
                why = clean(silent[0][1]) if len(silent[0]) > 1 else ''
                sections.append(f"## {rid}\n\n**Silent on this slot.** {why}".rstrip())
            else:
                gaps.append(rid)
                sections.append(
                    f"## {rid}\n\n⚠ **No disposition for `{slot}` in this commentary's "
                    f"spine map** — neither a Slot map row nor a Silent slots row. "
                    f"Treat as unresolved, not as silence.")
            continue

        n_present += 1
        claims_file = os.path.join(raw_dir, f)
        if not os.path.isfile(claims_file):
            sections.append(f"## {rid}\n\n⚠ raw claims file missing: {claims_file}")
            continue
        blocks = load_claim_blocks(claims_file)

        nodes, titles = [], []
        for cells in rows:
            if not anchor and len(cells) > 1:
                anchor = clean(cells[1])
            nodes += cell_nodes(cells[2] if len(cells) > 2 else '')
            if len(cells) > 3 and clean(cells[3]):
                titles.append(clean(cells[3]))

        picked = []
        for cid in blocks:
            if any(covers(node_of(cid), n) for n in nodes):
                picked.append(cid)
        picked.sort(key=lambda c: [int(x) if x.isdigit() else x for x in c[2:].split('-')])

        extra_ids, amb_ids = [], []
        for cells in extra:
            for cid in cell_ids(cells[1] if len(cells) > 1 else ''):
                if cid in blocks and cid not in picked and cid not in extra_ids:
                    extra_ids.append(cid)
        for cells in amb:
            for cid in cell_ids(cells[0]):
                if cid in blocks and cid not in picked and cid not in extra_ids:
                    amb_ids.append(cid)

        head = [f"## {rid}"]
        if nodes:
            head.append(f"**Node(s):** {', '.join(nodes)}"
                        + (f" — {' / '.join(titles)}" if titles else ""))
        head.append(f"**Claims in this packet:** {len(picked)} mapped"
                    + (f", {len(extra_ids)} extra" if extra_ids else "")
                    + (f", {len(amb_ids)} ambiguous" if amb_ids else ""))
        body = ['\n'.join(head), '']

        for cid in picked:
            body.append(blocks[cid])
            body.append('')
            manifest.append(f"{rid}:{cid}")
        for cid in extra_ids:
            why = ''
            for cells in extra:
                if cid in cell_ids(cells[1] if len(cells) > 1 else ''):
                    why = clean(cells[2]) if len(cells) > 2 else ''
            body.append(f"> ⓘ **Routed by claim, not by node.** {why}".rstrip())
            body.append(blocks[cid])
            body.append('')
            manifest.append(f"{rid}:{cid}")
        for cid in amb_ids:
            why = ''
            for cells in amb:
                if cid in cell_ids(cells[0]):
                    why = clean(cells[2]) if len(cells) > 2 else ''
            body.append(f"> ⚑ **Ambiguous fit** — carry the uncertainty through to the "
                        f"page; never silently absorb or drop. {why}".rstrip())
            body.append(blocks[cid])
            body.append('')
            manifest.append(f"{rid}:{cid}")

        sections.append('\n'.join(body).rstrip())

    out = [
        f"# Consolidation packet — {slot}",
        "",
        f"> Assembled by `assemble_packet.py` on {date.today().isoformat()} from "
        f"`2-RAILS/Claims/raw/spine-map/`. Every claim block below is copied verbatim "
        f"from `2-RAILS/Claims/raw/tree-guided/<id>.md` — quote from it directly rather "
        f"than retyping, and never re-open the raw files while consolidating.",
        "",
        f"**Slot:** `{slot}`",
        f"**Root anchor:** {anchor or '(not recorded)'}",
        f"**Commentaries contributing:** {n_present} · **explicitly silent:** {n_silent}"
        + (f" · **⚠ no disposition:** {len(gaps)}" if gaps else "")
        + (f" · **⚠ no spine map at all:** {len(unmapped_commentaries)} "
           f"({', '.join(unmapped_commentaries)})" if unmapped_commentaries else ""),
        f"**Claims in packet:** {len(manifest)}",
        "",
        "## Manifest",
        "",
        "> The coverage check (claims-consolidation step 5) diffs this list against the "
        "claim IDs the finished topic page cites. Every ID in the gap must be either "
        "folded into a facet or logged in “Claims reviewed, not separately cited.”",
        "",
        "```",
        '\n'.join(manifest),
        "```",
        "",
        "---",
        "",
        '\n\n---\n\n'.join(sections),
        "",
    ]
    text = '\n'.join(out)

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        open(out_path, 'w', encoding='utf-8').write(text)
        print(f"packet: {out_path}")
    else:
        sys.stdout.write(text)

    if manifest_path:
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        open(manifest_path, 'w', encoding='utf-8').write('\n'.join(manifest) + '\n')
        print(f"manifest: {manifest_path}")

    if out_path or manifest_path:
        print(f"slot {slot}: {len(manifest)} claims from {n_present} commentaries "
              f"({n_silent} silent)")
    for rid in gaps:
        print(f"ERROR: {rid} has no disposition for slot `{slot}` — add a Slot map row "
              f"or a Silent slots row to its spine map", file=sys.stderr)
    for rid in unmapped_commentaries:
        print(f"ERROR: {rid} has a raw claims file but no spine map — it is missing from "
              f"this packet entirely. Run the spine-map skill on it before consolidating.",
              file=sys.stderr)
    sys.exit(1 if (gaps or unmapped_commentaries) else 0)


if __name__ == '__main__':
    main()
