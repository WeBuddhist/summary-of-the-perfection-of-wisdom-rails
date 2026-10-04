#!/usr/bin/env python3
"""The `md_rows` adapter: one work from Google-Docs Markdown exports of a
row-aligned corpus (format: ../references/md-export-format.md).

Manifest entry (all paths under raw_root unless noted):

    - key: bo-some-commentary
      path: 1-SOURCES/Commentaries/bo-some-commentary.md
      adapter: md_rows
      id_scheme: h2                      # flat for a text with no TOC
      text: commentary.md                # THIS work's rows = its segmentation
      pair:                              # optional: the human row alignment
        own_side: commentary.md          #   this side of the pair (= text, or a letter-identical copy)
        target_side: root-copy.md        #   the other side: the target text cut the way the aligners cut it
      target: bo-root                    # work key the transclusions point at (built earlier)
      min_overlap: 3                     # letters a row needs inside a target segment to transclude it
      pair_corrections:                  # human-decided re-pairings (never invented)
        - {row: 15, target_side_rows: [14], reason: "…", decided_by: "…", date: "…"}
      text_corrections:                  # human-decided text fixes
        - {row: 83, find: "s", replace: "", reason: "…", decided_by: "…", date: "…"}
      toc:                               # where the headings come from
        kind: tree | labels | projected | outline | none
        tree: 2-RAILS/Sections/Raw/toc-tree/<id>.md     # kind: tree (vault path; toc-generate)
        doc: commentary-toc.md                           # kind: labels
        labels: ["༥༽ …།", …]                             # kind: labels, verbatim, in order
        numbered: true                                   # kind: labels whose own "3.1.2." gives path and depth
        path_corrections:                                # numbered: human-decided fixes of numbering slips
          - {n: 57, label: "3.1.1.1. …", path: "3.1.2.1", reason: "…", decided_by: "…", date: "…"}
        source_work: <commentary key>                    # kind: projected
        file: 2-RAILS/Sections/Raw/toc-wikisource/<id>.md # kind: outline (wiki-toc-import)
        reason: "…"                                      # kind: none
      row_splits:                        # human-decided: cut a row so a heading can stand inside it
        - {row: 10, at: ["clause", …], targets: [[0], [1], []], reason: "…", decided_by: "…", date: "…"}
      merge_rows:                        # human-decided: one block per target segment
        {mode: by_target, joiner: " ", reason: "…", decided_by: "…", date: "…"}
      line_breaks:                       # human-decided: one verse line per line (see _line_breaks)
        {after: "regex" | phrases: 7 | before: {row: [clause, …]}, reason: "…", decided_by: "…", date: "…"}
      supplement_rows:                   # human-decided: text the corpus lacks, from another source
        - {row: 33, text: "…", source: "…", reason: "…", decided_by: "…", date: "…"}

What it guarantees:
  * Every row with letters becomes exactly one block, in row order. Rows are
    never merged or split; a row without letters is not a block (its raw
    text, if any, is kept in the sidecar).
  * A block transcludes exactly the target segments its paired row's letters
    fall in (concordance.py), after any human pair_correction. A row whose
    counterpart is empty transcludes nothing.
  * Headings sit only between rows. Ids come from the headings (h2 scheme),
    so the TOC is applied before ids and transclusions are written.
"""
import hashlib
import pathlib
import re
import sys

from common import raw_path
from concordance import Concordance
from md_export import read_rows, strip_markup
from project import Projector, is_letter
import vault_writer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "toc-generate" / "scripts"))
from toc_tree_ingest import parse_toc_line          # noqa: E402

ZW = "​﻿"


def has_letters(text):
    return any(is_letter(c) for c in text)


def letters(text):
    return "".join(c for c in text if is_letter(c))


def _supplement_rows(ctx, rel):
    """Rows a manifest adds to a raw text (`supplement_rows` on the work whose
    `text` it is): text the corpus lacks, taken from another human source,
    each with its source, reason, who and when. They follow the raw rows."""
    out = []
    for w in ctx.m["works"]:
        if w.get("text") != rel:
            continue
        for x in w.get("supplement_rows") or []:
            out.append({"row": int(x["row"]), "text": x["text"], "runs": [], "raw": x["text"],
                        "supplement": {k: v for k, v in x.items() if k not in ("row", "text")}})
    return out


def _rows(ctx, rel):
    rows = read_rows(raw_path(ctx.raw, rel))
    sup = _supplement_rows(ctx, rel)
    if sup:
        last = max((r["row"] for r in rows), default=0)
        if min(x["row"] for x in sup) <= last:
            raise ValueError(f"{rel}: supplement_rows must be numbered after the last raw row ({last})")
        rows = rows + sorted(sup, key=lambda x: x["row"])
    return rows


def _line_breaks(spec, row, text, runs):
    """line_breaks (human-decided): break a block into lines (one verse line
    each) without touching a letter. A break at a space turns the space into
    the newline; elsewhere a newline is inserted.
        line_breaks: {after: <regex>}                 break after each match
        line_breaks: {phrases: 7}                     CJK verse: break at whitespace, and
                                                      every 7 characters of a longer unspaced run
        line_breaks: {before: {<row>: [clause, …]}}   break before each clause (verbatim,
                                                      found once, in order) — e.g. from another edition
    Returns (text, runs, number of breaks)."""
    lb = spec.get("line_breaks")
    if not lb:
        return text, runs, 0
    cuts = set()
    if lb.get("after"):
        for m in re.finditer(lb["after"], text):
            cuts.add(m.end())
    if lb.get("phrases"):
        n = int(lb["phrases"])
        for m in re.finditer(r"\S+", text):
            cuts.add(m.start())
            w = m.group(0)
            if len(w) > n and len(w) % n == 0:
                cuts.update(m.start() + k for k in range(n, len(w), n))
    for clause in (lb.get("before") or {}).get(row) or (lb.get("before") or {}).get(str(row)) or []:
        if text.count(clause) != 1:
            raise ValueError(f"{spec['key']}: line break clause {clause[:30]!r} is not found exactly once in row {row}")
        cuts.add(text.index(clause))
    # a cut at either edge of the text, or inside leading/trailing space, is no break
    lo = len(text) - len(text.lstrip())
    hi = len(text.rstrip())
    cuts = sorted(c for c in cuts if lo < c < hi)
    n = 0
    for c in reversed(cuts):
        if text[c - 1] == "\n" or text[c] == "\n":
            continue
        if text[c - 1] in " \t":                     # the space before the cut becomes the newline
            text = text[:c - 1] + "\n" + text[c:]
        elif text[c] in " \t":
            text = text[:c] + "\n" + text[c + 1:]
        else:
            text = text[:c] + "\n" + text[c:]
            runs = _shift_runs(runs, c, 0, 1)
        n += 1
    return text, runs, n


def _shift_runs(runs, pos, removed, added=0):
    out = []
    for r in runs:
        r = dict(r)
        for k in ("start", "end"):
            if r[k] >= pos + removed:
                r[k] += added - removed
            elif r[k] > pos:
                r[k] = pos + min(r[k] - pos, added)
        if r["end"] > r["start"]:
            out.append(r)
    return out


# --------------------------------------------------------------------------
# rows -> blocks
# --------------------------------------------------------------------------

def _blocks(ctx, spec, rep):
    rel = spec["text"]
    corr = {}
    for c in spec.get("text_corrections") or []:
        corr.setdefault(int(c["row"]), []).append(c)
    items, empty_rows = [], []
    for r in _rows(ctx, rel):
        text, runs = r["text"], [dict(x, layer="emphasis") for x in r["runs"]]
        src = {"file": rel, "row": r["row"]}
        if r.get("supplement"):
            src["supplement"] = r["supplement"]
        for c in corr.pop(r["row"], []):
            if text.count(c["find"]) != 1:
                raise ValueError(f"{spec['key']}: text correction {c} does not match exactly once in row {r['row']}")
            pos = text.index(c["find"])
            text = text[:pos] + c["replace"] + text[pos + len(c["find"]):]
            runs = _shift_runs(runs, pos, len(c["find"]), len(c["replace"]))
            src.setdefault("corrections", []).append({k: v for k, v in c.items() if k != "row" and v is not None})
        text, runs, n_breaks = _line_breaks(spec, r["row"], text, runs)
        if n_breaks:
            src["line_breaks"] = n_breaks
        if runs or "\\" in r["raw"]:
            src["raw"] = r["raw"]
        if not has_letters(text):
            if r["raw"].strip() or src.get("corrections"):
                empty_rows.append(src | {"raw": r["raw"]})
            continue
        item = {"kind": "block", "text": text, "row": r["row"], "source": src}
        if runs:
            item["annotations"] = runs
        items.append(item)
    if corr:
        raise ValueError(f"{spec['key']}: text_corrections name rows that do not exist: {sorted(corr)}")
    rep["rows"] = len(items)
    return items, empty_rows


# --------------------------------------------------------------------------
# the human row pairing -> transclusion targets
# --------------------------------------------------------------------------

def _pair(ctx, spec, items, rep):
    pair = spec["pair"]
    own_rel, tgt_rel = pair.get("own_side", spec["text"]), pair["target_side"]
    if own_rel != spec["text"]:
        own = {r["row"]: letters(r["text"]) for r in _rows(ctx, own_rel)}
        mine = {r["row"]: letters(r["text"]) for r in _rows(ctx, spec["text"]) if not r.get("supplement")}
        bad = sorted(k for k in set(own) | set(mine) if own.get(k, "") != mine.get(k, ""))
        if bad:
            raise ValueError(f"{spec['key']}: pair.own_side differs from text in rows {bad[:10]}")
    tgt_rows = _rows(ctx, tgt_rel)
    tgt_text = {r["row"]: r["text"] for r in tgt_rows}
    target = ctx.works[spec["target"]]
    conc = Concordance(target["blocks"], [(r["row"], r["text"]) for r in tgt_rows if has_letters(r["text"])],
                       min_overlap=spec.get("min_overlap", 3))
    rep["concordance"] = conc.stats
    corrections = {int(c["row"]): c for c in spec.get("pair_corrections") or []}
    used, multi, unaligned, review = set(), [], [], []
    for it in items:
        k = it["row"]
        human = [k] if has_letters(tgt_text.get(k, "")) else []
        rows = human
        al = {"pair_row": k}
        if k in corrections:
            c = corrections.pop(k)
            rows = [int(x) for x in c.get("target_side_rows") or []]
            al["correction"] = {"human_pairing": human, "corrected_to": rows,
                                **{x: c[x] for x in ("reason", "decided_by", "date") if c.get(x)}}
        targets, detail, variants, dropped, flags = [], {}, [], [], []
        for tr in rows:
            x = conc.row(tr)
            for t in x["targets"]:
                if t not in targets:
                    targets.append(t)
            detail.update(x["detail"])
            variants += x["variants"]
            dropped += x["dropped"]
            flags += [f for f in x["flags"] if f not in flags]
            used.add(tr)
        targets.sort(key=conc.pos.get)
        if "correction" in al:
            al["correction"]["human_targets"] = sorted(
                {t for tr in human for t in conc.row(tr)["targets"]}, key=conc.pos.get)
        if rows:
            al["target_side_text"] = "\n".join(tgt_text[r] for r in rows)
            al["targets"] = detail
            if variants:
                al["variants"] = variants
            if dropped:
                al["dropped_overlaps"] = dropped
                review.append({"row": k, "dropped_overlaps": dropped})
            if flags:
                al["flags"] = flags
            if len(targets) > 1:
                multi.append({"row": k, "targets": targets})
            if rows and not targets:
                review.append({"row": k, "issue": "paired row's letters were not found in the target"})
        else:
            al["unaligned"] = True
            unaligned.append(k)
        it["targets"] = targets
        it["alignment"] = al
    if corrections:
        raise ValueError(f"{spec['key']}: pair_corrections name rows that are not blocks: {sorted(corrections)}")
    orphan = [k for k, t in tgt_text.items() if has_letters(t) and k not in used]
    rep.update({"aligned_blocks": sum(1 for it in items if it["targets"]),
                "unaligned_blocks": unaligned, "blocks_spanning_several_targets": multi,
                "target_side_rows_without_counterpart": orphan, "alignment_review": review})
    return {"target_side_rows_without_counterpart": [{"row": k, "text": tgt_text[k]} for k in orphan],
            "concordance": conc.stats}


# --------------------------------------------------------------------------
# human-decided row merges
# --------------------------------------------------------------------------

def _merge_by_target(spec, items, rep):
    """merge_rows: {mode: by_target, joiner: " ", reason, decided_by, date}.
    Consecutive rows that transclude exactly the same target segments become
    one block (texts joined by `joiner`), so a finely cut translation has one
    block per segment of the text it translates instead of repeating that
    segment's transclusion. Rows with no target are never merged. Every row
    number stays in the block's sidecar entry (`source.merged_rows`), with
    each row's own alignment."""
    m = spec.get("merge_rows")
    if not m:
        return items
    if m.get("mode") != "by_target":
        raise ValueError(f"{spec['key']}: unknown merge_rows mode {m.get('mode')!r}")
    joiner = m.get("joiner", " ")
    out, merged = [], 0
    for it in items:
        prev = out[-1] if out else None
        if (prev and it["kind"] == "block" and prev["kind"] == "block" and it.get("targets")
                and prev.get("targets") == it["targets"]):
            if "merged_rows" not in prev["source"]:
                prev["source"]["merged_rows"] = [{"row": prev["row"], "text": prev["text"],
                                                  "alignment": prev.get("alignment")}]
                prev["source"]["merge"] = {k: m[k] for k in ("mode", "joiner", "reason", "decided_by", "date") if k in m}
            shift = len(prev["text"]) + len(joiner)
            runs = [dict(r, start=r["start"] + shift, end=r["end"] + shift) for r in it.get("annotations") or []]
            if runs:
                prev["annotations"] = (prev.get("annotations") or []) + runs
            prev["text"] = prev["text"] + joiner + it["text"]
            prev["source"]["merged_rows"].append({"row": it["row"], "text": it["text"],
                                                  "alignment": it.get("alignment")})
            merged += 1
            continue
        out.append(it)
    rep["rows_merged_into_previous"] = merged
    return out


# --------------------------------------------------------------------------
# human-decided row splits
# --------------------------------------------------------------------------

def _split_rows(spec, items, rep):
    """row_splits: [{row, at: [clause, …], targets: [[i, …], …], reason,
    decided_by, date}]. The row is cut before each clause (verbatim, found
    exactly once) into len(at)+1 blocks, so a heading can stand inside what
    was one alignment row. `targets` gives, per part, the indices into the
    row's own transclusion targets that part shows (default: all on the first
    part). Every letter stays; the row number stays on every part."""
    splits = {int(x["row"]): x for x in spec.get("row_splits") or []}
    if not splits:
        return items
    out = []
    for it in items:
        x = splits.pop(it.get("row"), None) if it["kind"] == "block" else None
        if not x:
            out.append(it)
            continue
        text, row = it["text"], it["row"]
        cuts = []
        for clause in x["at"]:
            if text.count(clause) != 1:
                raise ValueError(f"{spec['key']}: split clause {clause[:30]!r} is not found exactly once in row {row}")
            cuts.append(text.index(clause))
        if not cuts or cuts[0] == 0 or cuts != sorted(cuts):
            raise ValueError(f"{spec['key']}: row_splits for row {row} must cut inside the row, in order")
        bounds = [0] + cuts + [len(text)]
        n = len(bounds) - 1
        tg = it.get("targets") or []
        per = x.get("targets")
        if per is not None and (len(per) != n or any(j >= len(tg) for p in per for j in p)):
            raise ValueError(f"{spec['key']}: row_splits targets for row {row} do not fit its {n} parts / {len(tg)} targets")
        meta = {k: x[k] for k in ("reason", "decided_by", "date") if x.get(k)}
        for i in range(n):
            a, b = bounds[i], bounds[i + 1]
            piece = text[a:b]
            lead = len(piece) - len(piece.lstrip())
            new = {k: v for k, v in it.items() if k not in ("annotations",)}
            new["text"] = piece.strip()
            runs = [dict(r, start=max(r["start"], a) - a - lead, end=min(r["end"], b) - a - lead)
                    for r in it.get("annotations") or [] if r["end"] > a and r["start"] < b]
            runs = [r for r in runs if r["end"] > r["start"] >= 0]
            if runs:
                new["annotations"] = runs
            new["source"] = dict(it["source"], part=i + 1, split={"of": n, **({"at": x["at"][i - 1]} if i else {}), **meta})
            new["targets"] = [tg[j] for j in per[i]] if per is not None else (list(tg) if i == 0 else [])
            if it.get("alignment"):
                new["alignment"] = dict(it["alignment"], row_targets=list(tg), part=i + 1)
            new["rowkey"] = str(row) if i == 0 else f"{row}.{i + 1}"
            out.append(new)
    if splits:
        raise ValueError(f"{spec['key']}: row_splits name rows that are not blocks: {sorted(splits)}")
    rep["rows_split"] = {str(x["row"]): len(x["at"]) + 1 for x in spec.get("row_splits") or []}
    return out


# --------------------------------------------------------------------------
# headings
# --------------------------------------------------------------------------

def pretoc_layout(title, items):
    """The exact text toc-generate reads (the line numbers its tree pointers
    use): '# title', then one paragraph per block. No frontmatter, so a
    metadata change can never shift a pointer. Returns (text, line -> item)."""
    lines = [f"# {' '.join(vault_writer.clean_lines(title))}", ""]
    where = {}
    for idx, it in enumerate(items):
        if it["kind"] != "block":
            continue
        tl = vault_writer.clean_lines(it["text"])
        for j in range(len(tl)):
            where[len(lines) + 1 + j] = idx
        lines += tl + [""]
    return "\n".join(lines).rstrip() + "\n", where


def sha1_text(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _frontmatter(text):
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    import yaml
    return yaml.safe_load(m.group(1)) or {}


def _clean_label(label):
    """toc-generate E2 rule: drop a trailing tsheg, end with a shad."""
    s = label.strip().strip(ZW).strip()
    s = re.sub(r"\[\[[^\]]*\]\]\s*$", "", s).strip()
    s = s.rstrip("་").rstrip()
    if not s.endswith("།"):
        s += "།"
    return s


def _insert(items, placements):
    """placements: [(item_index, 'before'|'after', heading)] in TOC order."""
    before, after = {}, {}
    for idx, where, h in placements:
        (before if where == "before" else after).setdefault(idx, []).append(h)
    out = []
    for idx, it in enumerate(items):
        out += before.get(idx, [])
        out.append(it)
        out += after.get(idx, [])
    return out


def _apply_tree(ctx, spec, items, rep, title):
    toc = spec["toc"]
    tree_path = ctx.vault / toc["tree"]
    tree = tree_path.read_text(encoding="utf-8")
    text, where = pretoc_layout(title, items)
    want = _frontmatter(tree).get("pointer_source_sha1")
    have = sha1_text(text)
    if want != have:
        raise ValueError(f"{spec['key']}: {toc['tree']} pointers were computed against pre-TOC text "
                         f"{want}, the build now produces {have} — rebuild the tree")
    nodes = [n for n in (parse_toc_line(l) for l in tree.splitlines()) if n]
    if not nodes:
        raise ValueError(f"{spec['key']}: no nodes in {toc['tree']}")
    shift = 0
    top = [n for n in nodes if n["depth"] == 1]
    if len(top) == 1 and letters(top[0]["label"]) and letters(top[0]["label"]) == letters(title):
        nodes.remove(top[0])
        shift = 1
        rep["toc_title_node_excluded"] = top[0]["label"]
    anchors = {}
    for a in toc.get("anchors") or []:
        anchors[str(a["decimal"])] = a
    # the placement pass's evidence, kept in the tree file under '## Placement'
    m = re.search(r"^## Placement\s*\n+```[a-z]*\n(.*?)\n```", tree, re.S | re.M)
    if m:
        for line in m.group(1).splitlines():
            parts = line.split("\t")
            if len(parts) >= 4 and parts[0].strip():
                anchors.setdefault(parts[0].strip(), {"decimal": parts[0].strip(), "line": parts[1].strip(),
                                                      "position": parts[2].strip(), "clause": parts[3].strip()})
    nlines = text.count("\n")
    placements = []
    for n in nodes:
        p = n["pointer"]
        if p is None:
            raise ValueError(f"{spec['key']}: tree node {n['decimal_id']} has no line pointer")
        idx = None
        for line in range(p, nlines + 2):
            if line in where:
                idx = where[line]
                break
        if idx is None:
            raise ValueError(f"{spec['key']}: tree node {n['decimal_id']} points past the last block (line {p})")
        h = {"kind": "heading", "path": n["decimal_id"], "level": n["depth"] - shift,
             "title": _clean_label(n["label"]),
             "source": {"origin": "toc-tree", "tree": toc["tree"], "pointer": p, "row": items[idx]["row"],
                        **({"anchor": anchors[n["decimal_id"]]} if n["decimal_id"] in anchors else {})}}
        placements.append((idx, "before", h))
    rep["headings"] = len(placements)
    return _insert(items, placements)


def _find_norm(hay, needle, start=0):
    """Find needle in hay ignoring zero-width spaces; return (s, e) in hay."""
    idx = [i for i, c in enumerate(hay) if c not in ZW]
    h = "".join(hay[i] for i in idx)
    n = "".join(c for c in needle if c not in ZW)
    s0 = next((k for k, i in enumerate(idx) if i >= start), len(idx))
    k = h.find(n, s0)
    if k < 0:
        return None
    return idx[k], idx[k + len(n) - 1] + 1


def _apply_labels(ctx, spec, items, rep):
    """A human TOC given as heading labels in a separate doc (e.g. Dzongsar
    '(toc)' exports). Each label is found verbatim in that doc; its place in
    the commentary is found by projecting the doc onto the commentary's
    letters. A label that is also inside a row is moved out of the row into
    the heading (the row keeps the author's words); a label that exists only
    in the doc is a heading at the row boundary where the doc puts it.
    Headings go at row boundaries only: a label falling inside a row goes
    before the row unless more of the row precedes it than follows it."""
    toc = spec["toc"]
    doc_rel = toc["doc"]
    paras = []
    for i, line in enumerate(open(raw_path(ctx.raw, doc_rel), encoding="utf-8").read().split("\n"), 1):
        clean, _ = strip_markup(line)
        clean = clean.strip()
        if clean:
            paras.append((i, clean))
    doc_text = "\n".join(p for _, p in paras)
    line_of = []
    for i, p in paras:
        line_of += [i] * (len(p) + 1)
    comm, spans = "", []
    for idx, it in enumerate(items):
        s = len(comm)
        comm += it["text"]
        spans.append((s, len(comm), idx))
        comm += "\n"
    proj = Projector(doc_text, comm)

    def locate(pos):
        for s, e, idx in spans:
            if s <= pos < e or pos == e:
                return idx, pos - s
        return None, None

    placements, cursor, moved = [], 0, []
    removals = {}                                  # item idx -> [(start, end, label)]
    seen_paths = set()
    path_fixes = {int(x["n"]): x for x in toc.get("path_corrections") or []}
    for n, x in path_fixes.items():
        if x.get("label") != toc["labels"][n - 1]:
            raise ValueError(f"{spec['key']}: path_corrections n={n} names {x.get('label')!r}, "
                             f"label {n} is {toc['labels'][n - 1]!r}")
    for n, label in enumerate(toc["labels"], 1):
        hit = _find_norm(doc_text, label, cursor)
        if hit is None:
            raise ValueError(f"{spec['key']}: TOC label not found (in order) in {doc_rel}: {label!r}")
        s, e = hit
        cursor = e
        bs = s                                     # where the label's words begin (after a number)
        if toc.get("numbered"):
            m0 = re.match(r"\s*\d+(?:\.\d+)*\.?\s*", doc_text[s:e])
            bs = s + (m0.end() if m0 else 0)
        lab_letters = sum(1 for c in doc_text[bs:e] if is_letter(c))
        mapped = [proj.pos(i) for i in range(bs, e) if is_letter(doc_text[i]) and proj.pos(i) is not None]
        h = {"kind": "heading", "path": str(n), "level": 1,
             "title": " ".join(doc_text[s:e].split()).strip(ZW).strip(),
             "source": {"origin": None, "toc_doc": doc_rel, "toc_line": line_of[s]}}
        if toc.get("numbered"):
            # the label's own decimal number ("3.1.2. …") gives its path and depth
            m = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$", h["title"])
            if not m:
                raise ValueError(f"{spec['key']}: numbered TOC label has no decimal number: {label!r}")
            h["path"], h["title"] = m.group(1), m.group(2).strip()
            h["source"]["label"] = label
            fix = path_fixes.get(n)
            if fix:
                # a human numbering slip, corrected in the manifest (reason recorded there)
                h["source"]["label_path"] = h["path"]
                h["path"] = str(fix["path"])
            h["level"] = h["path"].count(".") + 1
            parent = h["path"].rpartition(".")[0]
            if h["path"] in seen_paths or (parent and parent not in seen_paths):
                raise ValueError(f"{spec['key']}: numbered TOC label {n} has path {h['path']} (duplicate or "
                                 f"parent missing) — add a toc.path_corrections entry: {label!r}")
            seen_paths.add(h["path"])
        if toc.get("numbered") and lab_letters and len(mapped) >= 0.9 * lab_letters:
            # a numbered TOC doc's label is an editorial line: the row is never
            # cut into; the heading goes before the label's words where the
            # commentary has them too
            idx, off = locate(min(mapped))
            it = items[idx]
            before = sum(1 for c in it["text"][:off] if is_letter(c))
            after = sum(1 for c in it["text"][off:] if is_letter(c))
            h["source"].update({"origin": "toc_doc_words_in_row", "row": it["row"], "offset_in_row": off})
        elif lab_letters and len(mapped) >= 0.9 * lab_letters:
            # the label is in the commentary text too: move it out of its row
            idx, off = locate(min(mapped))
            it = items[idx]
            r = _find_norm(it["text"], doc_text[bs:e], max(0, off - 2))
            if r is None:
                raise ValueError(f"{spec['key']}: label {label!r} maps into row {it['row']} but is not there verbatim")
            removals.setdefault(idx, []).append((r[0], r[1], doc_text[bs:e]))
            before = sum(1 for c in it["text"][:r[0]] if is_letter(c))
            after = sum(1 for c in it["text"][r[1]:] if is_letter(c))
            h["source"].update({"origin": "row", "row": it["row"], "offset_in_row": r[0]})
        else:
            # only in the TOC doc: place it where the doc's next commentary letter falls
            pos = None
            for i in range(e, len(doc_text)):
                if is_letter(doc_text[i]) and proj.pos(i) is not None:
                    pos = proj.pos(i)
                    break
            if pos is None:
                raise ValueError(f"{spec['key']}: cannot place TOC-doc-only label {label!r}")
            idx, off = locate(pos)
            it = items[idx]
            before = sum(1 for c in it["text"][:off] if is_letter(c))
            after = sum(1 for c in it["text"][off:] if is_letter(c))
            h["source"].update({"origin": "toc_doc", "row": it["row"], "offset_in_row": off})
        where = "before" if before == 0 or before <= after else "after"
        if before:
            h["source"]["inside_row"] = {"letters_before": before, "letters_after": after,
                                         "placed": f"{where} row {it['row']}"}
        h["source"]["placement"] = where
        placements.append((idx, where, h))
    # move in-row labels out of their rows (author's words stay)
    for idx, rem in removals.items():
        it = items[idx]
        text, runs = it["text"], it.get("annotations") or []
        for s, e, lab in sorted(rem, reverse=True):
            e2 = e
            while e2 < len(text) and text[e2] in " \t" + ZW:
                e2 += 1
            text = text[:s] + text[e2:]
            runs = _shift_runs(runs, s, e2 - s)
            moved.append({"row": it["row"], "text": lab})
        it["source"]["toc_labels_moved_to_headings"] = [lab for _, _, lab in sorted(rem)]
        it["text"] = text.strip(" \t")
        if runs:
            it["annotations"] = runs
        elif "annotations" in it:
            it.pop("annotations")
    rep["headings"] = len(placements)
    rep["toc_labels_moved_from_rows"] = moved
    out = _insert(items, placements)
    gone = [it["row"] for it in out if it["kind"] == "block" and not has_letters(it["text"])]
    rep["rows_that_were_only_toc_labels"] = gone
    return [it for it in out if it["kind"] != "block" or has_letters(it["text"])], gone


# --------------------------------------------------------------------------
# a TOC projected from a commentary onto a root text (or its translations)
# --------------------------------------------------------------------------

def _spec(ctx, key):
    for w in ctx.m["works"]:
        if w["key"] == key:
            return w
    raise ValueError(f"no work {key!r} in the manifest")


def _lettered_rows(ctx, rel):
    return [(str(r["row"]), r["text"]) for r in _rows(ctx, rel) if has_letters(r["text"])]


def _source_sections(ctx, toc):
    """Walk the source commentary (rows + its own headings) and return, for
    every row of the stored root it comments on, the TOC node whose section
    first reaches it — the projection through the commentary's own human
    row alignment. Returns (display_rows_in_order, row -> node-index | None,
    nodes)."""
    src = _spec(ctx, toc["source_work"])
    items, _ = _blocks(ctx, src, {})
    kind = (src.get("toc") or {}).get("kind")
    if kind == "tree":
        items = _apply_tree(ctx, src, items, {}, src["title"])
    elif kind == "labels":
        items, _ = _apply_labels(ctx, src, items, {})
    else:
        raise ValueError(f"{toc['source_work']} has no TOC to project")
    stored = _spec(ctx, src["target"])                      # the stored root the commentary points at
    disp = _lettered_rows(ctx, stored["text"])
    order = [r for r, _ in disp]
    copy = _lettered_rows(ctx, src["pair"]["target_side"])
    conc = Concordance(disp, [(int(r), t) for r, t in copy], min_overlap=src.get("min_overlap", 3))
    corrections = {int(c["row"]): [int(x) for x in c.get("target_side_rows") or []]
                   for c in src.get("pair_corrections") or []}
    copy_rows = {int(r) for r, _ in copy}
    nodes, node_of, cur = [], {}, None
    for it in items:
        if it["kind"] == "heading":
            nodes.append(it)
            cur = len(nodes) - 1
            continue
        k = it["row"]
        rows = corrections.get(k, [k] if k in copy_rows else [])
        for r in rows:
            for d in conc.row(r)["targets"]:
                node_of.setdefault(d, cur)
    # rows the commentary never reaches belong to the section before them
    last = None
    for d in order:
        if d in node_of:
            last = node_of[d]
        else:
            node_of[d] = last
    return order, node_of, nodes


def load_outline(ctx, rel):
    """An outline file (wiki-toc-import): frontmatter + one ```yaml block
    `nodes: [{path, start_row, labels: {lang: title}, …}]`, start rows counted
    in the raw text of the work named by `placed_on`."""
    import yaml
    text = (ctx.vault / rel).read_text(encoding="utf-8")
    fm = _frontmatter(text)
    m = re.search(r"^```yaml\n(.*?)\n```", text, re.S | re.M)
    if not m:
        raise ValueError(f"{rel}: no ```yaml nodes block")
    nodes = (yaml.safe_load(m.group(1)) or {}).get("nodes") or []
    if not nodes:
        raise ValueError(f"{rel}: no nodes")
    return fm, nodes


def _outline_sections(ctx, spec, toc):
    """toc: {kind: outline, file: <vault path>}. The outline's nodes start at
    rows of the work it was placed on; every lettered row of that work belongs
    to the deepest node starting at or before it (rows before the first node
    belong to none). Returns (rows_in_order, row -> node-index | None, heading
    items in this work's language, placed_on key)."""
    fm, raw_nodes = load_outline(ctx, toc["file"])
    placed = _spec(ctx, fm["placed_on"])
    want = fm.get("placed_on_sha1")
    have = hashlib.sha1(raw_path(ctx.raw, placed["text"]).read_bytes()).hexdigest()
    if want != have:
        raise ValueError(f"{spec['key']}: {toc['file']} was placed on {placed['text']} {want}, "
                         f"the raw file is now {have} — re-place the outline")
    parts = {int(x["row"]): len(x["at"]) + 1 for x in placed.get("row_splits") or []}
    order = []
    for d, _ in _lettered_rows(ctx, placed["text"]):
        order += [d] + [f"{d}.{i}" for i in range(2, parts.get(int(d), 1) + 1)]
    at = {d: i for i, d in enumerate(order)}
    lang = (spec.get("frontmatter") or {}).get("lang_tag")
    nodes, last = [], 0
    for n in raw_nodes:
        path, start = str(n["path"]), str(n["start_row"])
        if start not in at:
            raise ValueError(f"{toc['file']}: node {path} starts at row {start}, not a lettered row (or split part) of {placed['text']}")
        if at[start] < last:
            raise ValueError(f"{toc['file']}: node {path} starts before the node above it")
        last = at[start]
        title = (n.get("labels") or {}).get(lang)
        if not title:
            raise ValueError(f"{toc['file']}: node {path} has no {lang!r} label")
        nodes.append({"kind": "heading", "path": path, "title": title.strip(),
                      "level": len(path.split(".")), "start_row": start, "start_pos": at[start]})
    node_of, cur = {}, None
    for d in order:
        for i, n in enumerate(nodes):
            if n["start_pos"] <= at[d]:
                cur = i
        node_of[d] = cur
    return order, node_of, nodes, fm["placed_on"]


def _apply_projected(ctx, spec, items, rep):
    """toc: {kind: projected, source_work: <commentary key>}. The commentary's
    TOC nodes are carried onto this work's rows: onto the stored root through
    the commentary's own row alignment, and from there onto a translation of
    it (or onto the text it translates) through that pair's row alignment.
    Headings stand only between rows; a node that reaches no row of this work
    gets no heading here (recorded).

    toc: {kind: outline, file: …} works the same way from an outline placed
    on the rows of one work (`placed_on`): that work takes the headings at the
    placed rows, the works paired with it through their row alignment, each
    in its own language."""
    toc = spec["toc"]
    if toc["kind"] == "outline":
        order, node_of, nodes, stored_key = _outline_sections(ctx, spec, toc)
        via = {"origin": "outline", "file": toc["file"], "via": stored_key}
    else:
        order, node_of, nodes = _source_sections(ctx, toc)
        stored_key = _spec(ctx, toc["source_work"])["target"]
        via = {"origin": "projected", "from": toc["source_work"], "via": stored_key}
    pos = {d: i for i, d in enumerate(order)}
    # this work's row -> stored-root rows
    if spec["key"] == stored_key:
        to_stored = {}                                   # rows (and split parts) are their own keys
    elif spec.get("target") == stored_key:              # a translation of the stored root
        tgt = _lettered_rows(ctx, spec["pair"]["target_side"])
        conc = Concordance([(d, t) for d, t in _lettered_rows(ctx, _spec(ctx, stored_key)["text"])],
                           [(int(r), t) for r, t in tgt], min_overlap=spec.get("min_overlap", 3))
        to_stored = {it["row"]: conc.row(it["row"])["targets"] for it in items}
    elif _spec(ctx, stored_key).get("target") == spec["key"]:   # the text the stored root translates
        st = _spec(ctx, stored_key)
        corr = {int(c["row"]): [int(x) for x in c.get("target_side_rows") or []]
                for c in st.get("pair_corrections") or []}
        to_stored = {}
        for d in order:
            row = int(d.split(".")[0])                     # a split part counts as its row
            for r in corr.get(row, [row]):
                to_stored.setdefault(r, []).append(d)
        to_stored = {it["row"]: sorted(to_stored.get(it["row"], []), key=pos.get) for it in items}
    else:
        raise ValueError(f"{spec['key']}: no row alignment links it to {stored_key}")
    # parent of each node, from heading levels in tree order
    parent, stack = [], []
    for i, n in enumerate(nodes):
        lvl = vault_writer.heading_level(n)
        while stack and vault_writer.heading_level(nodes[stack[-1]]) >= lvl:
            stack.pop()
        parent.append(stack[-1] if stack else None)
        stack.append(i)
    emitted, placements, current, moved_back = set(), [], None, []
    for idx, it in enumerate(items):
        keys = [it.get("rowkey", str(it["row"]))] if spec["key"] == stored_key else to_stored.get(it["row"], [])
        ds = [d for d in keys if d in pos]
        node = node_of.get(min(ds, key=pos.get)) if ds else current
        if node is None or node == current:
            continue
        if current is not None and node < current:
            moved_back.append(it["row"])                 # mapping runs backwards: stay in the current section
            continue
        chain, n = [], node
        while n is not None and n not in emitted:
            chain.append(n)
            n = parent[n]
        for n in reversed(chain):
            h = {k: v for k, v in nodes[n].items() if k not in ("start_row", "start_pos")}
            h["source"] = {**via, "node": nodes[n]["path"], "row": it["row"]}
            placements.append((idx, "before", h))
            emitted.add(n)
        current = node
    dropped = [{"node": n["path"], "title": n["title"]} for i, n in enumerate(nodes) if i not in emitted]
    rep["headings"] = len(placements)
    rep["toc_nodes_without_rows"] = dropped
    if moved_back:
        rep["rows_kept_in_current_section"] = moved_back
    return _insert(items, placements), dropped


# --------------------------------------------------------------------------
# the adapter
# --------------------------------------------------------------------------

def adapt_md_rows(ctx, spec, rep):
    items, empty_rows = _blocks(ctx, spec, rep)
    extra = {}
    if empty_rows:
        extra["rows_without_letters"] = empty_rows
    if spec.get("pair"):
        extra |= _pair(ctx, spec, items, rep)
    items = _split_rows(spec, items, rep)
    items = _merge_by_target(spec, items, rep)
    toc = spec.get("toc") or {"kind": "none"}
    title = spec["title"]
    if toc["kind"] == "tree":
        items = _apply_tree(ctx, spec, items, rep, title)
    elif toc["kind"] == "labels":
        items, gone = _apply_labels(ctx, spec, items, rep)
        if gone:
            extra["rows_that_were_only_toc_labels"] = gone
    elif toc["kind"] in ("projected", "outline"):
        items, dropped = _apply_projected(ctx, spec, items, rep)
        if dropped:
            extra["toc_nodes_without_rows"] = dropped
    elif toc["kind"] != "none":
        raise ValueError(f"{spec['key']}: unknown toc kind {toc['kind']!r}")
    extra["toc"] = {k: v for k, v in toc.items() if k != "labels"}
    rep["blocks"] = sum(1 for it in items if it["kind"] == "block")
    flat = spec.get("id_scheme", "flat") == "flat"
    for it in items:
        if it["kind"] == "block":
            row = it.pop("row")
            it.pop("rowkey", None)
            it["source"]["row"] = row
            if flat:
                # a text with no TOC keeps the human row number as its id
                # (gaps where a row is empty on this side), so ^N is row N of
                # the alignment doc and pairs read across files at a glance
                if row == 0:
                    raise ValueError(f"{spec['key']}: text before the first numbered row cannot take a flat id")
                it["id"] = str(row)
    return items, extra


def pretoc_source(ctx, spec):
    """(text, line map) of the pre-TOC file for a work whose toc is a tree."""
    rep = {}
    items, _ = _blocks(ctx, spec, rep)
    text, where = pretoc_layout(spec["title"], items)
    rows = {line: items[i]["row"] for line, i in where.items()}
    return text, rows
