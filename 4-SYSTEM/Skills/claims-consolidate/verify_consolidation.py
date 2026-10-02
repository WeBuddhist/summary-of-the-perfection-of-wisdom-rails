#!/usr/bin/env python3
"""Deterministic checks for a consolidated claims topic page (claims-consolidation skill).

Usage:
    python3 verify_consolidation.py <topic-page.md> [<raw-tree-guided-dir>]

Default raw dir: 2-RAILS/Claims/raw/tree-guided/ resolved relative to the page's vault.

Checks (all deterministic — no model judgment):
  1. CITATION EXISTENCE — every `registered_id:claim_id` cited on the page resolves to a
     real claim in that commentary's raw file. Recognises both claim forms used by
     tree-guided extractions: heading claims (`#### c-... title`) and internal-tension
     claims (`⚑ **c-... title**`).
  2. COUNT LABELS — every "(N commentaries)" label is recomputed from the unique
     registered_ids actually cited in the same paragraph; mismatches are reported.
     (The pilot audit found five off-by-one labels produced by hand-counting.)
  3. CONSENSUS/DIVERGENCE OVERLAP — a claim ID cited under both `### Consensus` and
     `### ⚑ Divergences` of the same facet is flagged as a WARNING for human review
     (occasionally legitimate, often a sign the same claim is being used on both
     sides of a disagreement).
  4. DISPOSITION COMPLETENESS — every claim ID listed in the Coverage table's
     "Claims consulted" column must appear somewhere else on the page (cited in a
     facet section, or logged under "Claims reviewed, not separately cited" /
     "Ambiguous claims"). Undispositioned IDs are reported. Numeric ranges
     (`c-2-15–c-2-19`) are expanded when all but the final segment match; otherwise
     only the endpoints are checked and the range is noted as partially verifiable.
  5. PREFIX DISCIPLINE — bare backticked claim IDs (`` `c-...` `` with no
     `registered_id:` prefix) outside the Coverage table are counted and reported
     (rule: citations are always `registered_id:claim_id`).

NOT covered here (needs model judgment — run the claims-consolidation-audit skill):
  attribution fidelity (does the claim actually SAY what the page attributes to it),
  Tibetan quote fidelity for synthesised consensus lines, divergence reality,
  epistemic-strength fidelity ("endorses" vs "considers likely").

Exit code 0 = no errors (warnings allowed); 1 = at least one error.
"""
import re
import sys
import os
import glob

CITE = re.compile(r'([a-z][a-z0-9]*(?:-[a-z0-9]+)*):(c-[0-9a-z][0-9a-zA-Z\-]*)')
BARE = re.compile(r'`(c-[0-9a-z][0-9a-zA-Z\-]*)`')


def load_real_ids(raw_dir):
    real = {}
    for f in glob.glob(os.path.join(raw_dir, '*.md')):
        rid = os.path.basename(f)[:-3]
        txt = open(f, encoding='utf-8').read()
        ids = set(re.findall(r'^#{3,6}\s+(c-[0-9a-z][0-9a-zA-Z\-]*)\b', txt, re.M))
        ids |= set(re.findall(r'^⚑\s+\*\*(c-[0-9a-z][0-9a-zA-Z\-]*)\b', txt, re.M))
        real[rid] = ids
    return real


def expand_range(a, b):
    """Expand c-x-...-N – c-x-...-M when all but the last segment match."""
    pa, pb = a.rsplit('-', 1), b.rsplit('-', 1)
    if pa[0] == pb[0] and pa[1].isdigit() and pb[1].isdigit():
        lo, hi = int(pa[1]), int(pb[1])
        if lo <= hi and hi - lo <= 200:
            return [f"{pa[0]}-{i}" for i in range(lo, hi + 1)], True
    return [a, b], False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    page_path = os.path.abspath(sys.argv[1])
    if len(sys.argv) > 2:
        raw_dir = sys.argv[2]
    else:
        # walk up to the vault root (dir containing 2-RAILS)
        d = os.path.dirname(page_path)
        while d != '/' and not os.path.isdir(os.path.join(d, '2-RAILS')):
            d = os.path.dirname(d)
        raw_dir = os.path.join(d, '2-RAILS/Claims/raw/tree-guided')
    real = load_real_ids(raw_dir)
    txt = open(page_path, encoding='utf-8').read()

    errors, warnings = [], []

    # ---- split page into segments -------------------------------------------------
    # Headings may be bilingual (Tibetan first, English anchor in parens) on -bo
    # pages, e.g. "## ཁྱབ་ཚད (Coverage)" — match on the English anchor anywhere
    # in the heading line.
    cov_m = re.search(r'^## [^\n]*Coverage[^\n]*$', txt, re.M)
    coverage = txt[cov_m.start():] if cov_m else ''
    body = txt[:cov_m.start()] if cov_m else txt
    reviewed_secs = re.findall(
        r'^##+ [^\n]*(?:Claims reviewed, not separately cited|Ambiguous claims)[^\n]*$'
        r'(.*?)(?=^## |\Z)', txt, re.M | re.S)
    reviewed_txt = '\n'.join(reviewed_secs)

    # ---- 1. citation existence ----------------------------------------------------
    cited = set()
    for rid, cid in CITE.findall(txt):
        cited.add((rid, cid))
        if rid not in real:
            errors.append(f"unknown commentary id in citation: {rid}:{cid}")
        elif cid not in real[rid]:
            errors.append(f"nonexistent claim cited: {rid}:{cid}")

    # ---- 2. count labels ----------------------------------------------------------
    for para in re.split(r'\n\s*\n', txt):
        m = re.search(r'\((\d+)\s+commentaries\)|\(འགྲེལ་པ\s*(\d+)\)', para)
        if not m:
            continue
        stated = int(m.group(1) or m.group(2))
        actual = len({rid for rid, _ in CITE.findall(para)})
        if actual and stated != actual:
            snippet = re.sub(r'\s+', ' ', para)[:80]
            errors.append(
                f"count label says ({stated} commentaries) but paragraph cites "
                f"{actual} unique commentaries: “{snippet}…”")

    # ---- 3. consensus/divergence overlap per facet --------------------------------
    for facet in re.split(r'^## ', body, flags=re.M)[1:]:
        title = facet.split('\n', 1)[0].strip()
        cons = re.search(r'### [^\n]*Consensus[^\n]*\n(.*?)(?=^### |\Z)', facet, re.M | re.S)
        div = re.search(r'### ⚑[^\n]*\n(.*?)(?=^### |\Z)', facet, re.M | re.S)
        if cons and div:
            a = set(CITE.findall(cons.group(1)))
            b = set(CITE.findall(div.group(1)))
            for rid, cid in sorted(a & b):
                warnings.append(
                    f"claim cited under BOTH Consensus and ⚑ Divergences of "
                    f"“{title}”: {rid}:{cid} — review which side it belongs on")

    # ---- 4. disposition completeness ----------------------------------------------
    if coverage:
        body_ids = set(CITE.findall(body)) | set(CITE.findall(reviewed_txt))
        # body citations may use ranges too: `rid:c-A`–`c-B` — expand them
        for src in (body, reviewed_txt):
            for rid, a, b in re.findall(
                    r'([a-z][a-z0-9]*(?:-[a-z0-9]+)*):(c-[0-9][0-9\-]*)`?\s*[–—-]\s*'
                    r'`?(?:[a-z][a-z0-9\-]*:)?(c-[0-9][0-9\-]*)', src):
                for cid in expand_range(a, b)[0]:
                    body_ids.add((rid, cid))
        for row in coverage.split('\n'):
            cells = [c.strip() for c in row.split('|')]
            if len(cells) < 4 or cells[1].startswith('---') or 'Claims consulted' in row:
                continue
            rid = re.sub(r'[`*]', '', cells[1]).strip()
            if rid not in real:
                continue
            cell = cells[2]
            # expand ranges first, then singles
            claimed = []
            for a, b in re.findall(r'(c-[0-9][0-9\-]*)\s*[–—-]\s*(c-[0-9][0-9\-]*)', cell):
                ids, full = expand_range(a, b)
                claimed += ids
                if not full:
                    warnings.append(
                        f"coverage range {rid}: {a}–{b} not fully expandable "
                        f"(prefixes differ) — only endpoints checked")
            cell_no_ranges = re.sub(r'c-[0-9][0-9\-]*\s*[–—-]\s*c-[0-9][0-9\-]*', ' ', cell)
            claimed += re.findall(r'(c-[0-9a-z][0-9a-zA-Z\-]*)', cell_no_ranges)
            for cid in claimed:
                if cid not in real.get(rid, set()):
                    errors.append(f"coverage table lists nonexistent claim {rid}:{cid}")
                elif (rid, cid) not in body_ids:
                    errors.append(
                        f"undispositioned claim: coverage table lists {rid}:{cid} as "
                        f"consulted, but it is neither cited in any facet nor logged "
                        f"as reviewed/excluded")

    # ---- 5. prefix discipline ------------------------------------------------------
    prefixed_spans = [m.span(2) for m in CITE.finditer(body)]
    bare_count = 0
    for m in BARE.finditer(body):
        if not any(a <= m.start(1) and m.end(1) <= b + 1 for a, b in prefixed_spans):
            bare_count += 1
    if bare_count:
        warnings.append(
            f"{bare_count} bare (unprefixed) backticked claim IDs in the page body — "
            f"rule: citations are always registered_id:claim_id")

    # ---- report --------------------------------------------------------------------
    print(f"page: {os.path.basename(page_path)}")
    print(f"citations: {len(cited)} unique")
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
