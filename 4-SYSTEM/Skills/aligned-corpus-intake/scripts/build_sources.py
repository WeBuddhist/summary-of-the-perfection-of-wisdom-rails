#!/usr/bin/env python3
"""Build vault source files from human-made raw data, driven by a manifest.

    python3 build_sources.py <manifest.yaml> [--only key,key] [--dry-run]

The manifest (see ../templates/manifest.example.yaml) lists every *work* to
produce, the raw files that supply its text, segmentation, headings and
alignment, the adapter that reads them, and its frontmatter. Works are built
in manifest order; a work may name an earlier work as its alignment target.

Every work produces:
  * the vault markdown file (frontmatter, '# title ^0', headings, transclusions,
    blocks with ids) — the shape the publication linter/parser reads;
  * a sidecar JSON with everything the markdown cannot carry: provenance of
    every block (raw file, paragraph, line), every formatted run (colour,
    bold, italic, highlight, …) with its offsets, reviewer comments, typed
    reference prefixes, variant notes, the raw alignment rows;
  * an entry in the intake report (counts, unmapped rows, warnings).

Adapters never alter wording. They may only: split on paragraph/line
boundaries the source already has, trim outer whitespace of a line, and
remove a typed alignment prefix (recorded in the sidecar).
"""
import argparse
import datetime
import json
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import docx_model                                  # noqa: E402
import openpecha_model                             # noqa: E402
from common import LetterIndex, letters_only, parse_ref_prefix, raw_path, sha1   # noqa: E402
from project import Projector                      # noqa: E402
import vault_writer                                # noqa: E402

NEUTRAL = docx_model.NEUTRAL_COLOURS
TITLE_ID = "0"          # the target's '# title ^0' line, as a mapping target


# --------------------------------------------------------------------------
# context shared across works
# --------------------------------------------------------------------------

class Ctx:
    def __init__(self, manifest, vault):
        self.m = manifest
        self.vault = pathlib.Path(vault)
        self.raw = self.vault / manifest.get("raw_root", "0-INBOX/raw-data")
        self.works = {}          # key -> {"path", "blocks": [(id, text)], "index"}
        self._docx = {}
        self.report = []

    def docx(self, rel):
        if rel not in self._docx:
            self._docx[rel] = docx_model.read(raw_path(self.raw, rel))
        return self._docx[rel]

    def op(self, text_id):
        return openpecha_model.load(self.raw / self.m.get("openpecha_root", "openpecha-api"), text_id)

    def index(self, key):
        w = self.works[key]
        if "index" not in w:
            w["index"] = LetterIndex(w["blocks"])
        return w["index"]


def formatted_runs(para, legend=None):
    """Runs that carry any non-neutral formatting, with offsets into the
    paragraph text, labelled by the document legend when one is given."""
    out, pos = [], 0
    legend = legend or {}
    for r in para["runs"]:
        n = len(r["text"])
        attrs = {k: r[k] for k in ("color", "highlight", "shading", "bold", "italic",
                                   "underline", "strike", "vert_align")
                 if r[k] and not (k == "color" and r[k] in NEUTRAL)
                 and not (k == "highlight" and r[k] == "white")}
        if attrs and r["text"].strip():
            label = legend.get(attrs.get("color")) if attrs.get("color") else None
            out.append({"start": pos, "end": pos + n, "text": r["text"],
                        **attrs, **({"meaning": label} if label else {})})
        pos += n
    return out


def para_colour(para):
    """Dominant non-neutral colour of a paragraph's visible letters."""
    weights = {}
    total = 0
    for r in para["runs"]:
        n = len(letters_only(r["text"]))
        total += n
        c = r["color"] if r["color"] not in NEUTRAL else None
        weights[c] = weights.get(c, 0) + n
    if not total:
        return None, False
    c = max(weights, key=weights.get)
    bold = sum(len(letters_only(r["text"])) for r in para["runs"] if r["bold"]) * 2 > total
    return (c if weights[c] * 2 > total else None), bold


def provenance(ctx, rels):
    out = []
    for rel in rels:
        try:
            p = raw_path(ctx.raw, rel)
        except FileNotFoundError:
            continue
        if p.exists():
            out.append({"file": f"{ctx.m.get('raw_root', '0-INBOX/raw-data')}/{rel}", "sha1": sha1(p)})
    return out


# --------------------------------------------------------------------------
# adapters
# --------------------------------------------------------------------------

def adapt_rows(ctx, spec, rep):
    """One block per non-empty paragraph; id = row number (paragraph index+1).
    Used for a human sentence/segment split whose rows ARE the segmentation."""
    doc = ctx.docx(spec["text"])
    items = []
    comments = doc["comments"]
    title_para = spec.get("title_paragraph")
    for p in doc["paragraphs"]:
        if not p["text"].strip():
            continue
        if title_para is not None and p["index"] == title_para:
            rep["title_text"] = p["text"]
            continue
        items.append({"kind": "block", "text": p["text"], "id": str(p["index"] + 1),
                      "source": {"doc": spec["text"], "paragraph": p["index"]},
                      "annotations": formatted_runs(p, spec.get("legend")),
                      **({"comments": [comments[c] for c in p["comment_ids"] if c in comments]}
                         if p["comment_ids"] else {})})
    rep["blocks"] = len(items)
    return items, {}


def adapt_numbered(ctx, spec, rep):
    """Blocks are the numbered segments; id = the segment's number.

    number_source: auto  — Word list numbering (the number Word renders);
                   typed — a number typed at the start of the paragraph
                           ("    12. text"), moved into the sidecar.
    An unnumbered paragraph before the first number is the title; any other
    unnumbered text is reported (it has no human id).

    number_offset: added to every number, for a doc whose list numbering is
    shifted against the numbering the aligners used (e.g. -1 when Word also
    numbered the title line, which the human numbering does not count). A
    paragraph whose number becomes 0 is the title. The number the doc shows
    stays in the sidecar ("rendered" / "typed_prefix")."""
    doc = ctx.docx(spec["text"])
    typed = spec.get("number_source", "auto") == "typed"
    offset = int(spec.get("number_offset") or 0)
    items, unnumbered = [], []
    for p in doc["paragraphs"]:
        if not p["text"].strip():
            continue
        n, text, src = None, p["text"], {"doc": spec["text"], "paragraph": p["index"]}
        if typed:
            refs, prefix, rest = parse_ref_prefix(p["text"])
            if refs and len(refs) == 1:
                n, text = refs[0], rest
                src["typed_prefix"] = prefix
        elif (p["numbering"] or {}).get("value"):
            n = p["numbering"]["value"]
            src["rendered"] = p["numbering"].get("rendered")
        if n is not None and offset:
            n += offset
            if n == 0 and not items and "title_text" not in rep:
                rep["title_text"] = text           # numbered title line
                rep["title_source"] = src
                continue
            if n < 1:
                raise ValueError(f"{spec['key']}: number_offset {offset} gives id {n} at paragraph {p['index']}")
        if n is not None:
            off = len(src.get("typed_prefix", ""))
            ann = [dict(a, start=a["start"] - off, end=a["end"] - off)
                   for a in formatted_runs(p, spec.get("legend")) if a["start"] >= off]
            items.append({"kind": "block", "text": text, "id": str(n), "source": src, "annotations": ann})
        elif not items and "title_text" not in rep:
            rep["title_text"] = p["text"]          # unnumbered opening line = the title
        else:
            unnumbered.append({"paragraph": p["index"], "text": p["text"]})
    rep["blocks"] = len(items)
    if unnumbered:
        rep["unnumbered_paragraphs"] = unnumbered
    apply_text_corrections(spec, items, rep)
    extra = {}
    if rep.get("title_source"):
        extra["title_source"] = rep.pop("title_source")
    if spec.get("align_via"):
        extra["raw_alignment"] = _align_via(ctx, spec, items, rep)
    if spec.get("alt_segmentations"):
        extra["alt_segmentations"] = [_alt_segmentation(ctx, a, items, rep) for a in spec["alt_segmentations"]]
    if spec.get("headings_from_openpecha"):
        items = _headings_from_openpecha(ctx, spec["headings_from_openpecha"], items, rep)
    if spec.get("overlays"):
        extra["overlay_summary"] = apply_overlays(ctx, spec, items, rep)
    return items, extra


def _alt_segmentation(ctx, alt, items, rep):
    """Record another human segmentation of the same text (rows of a doc)
    against this work's blocks: which rows each block overlaps, and the
    letters where the two versions differ (e.g. later corrections)."""
    rows = [p for p in ctx.docx(alt["doc"])["paragraphs"] if p["text"].strip()]
    rtext = "\n".join(p["text"] for p in rows)
    btext = "\n".join(it["text"] for it in items)
    boffs, pos = [], 0
    for it in items:
        boffs.append((it["id"], pos, pos + len(it["text"])))
        pos += len(it["text"]) + 1
    proj = Projector(rtext, btext)
    by_block = {}
    pos = 0
    for k, p in enumerate(rows):
        sp = proj.span(pos, pos + len(p["text"]))
        for bid, s0, e0 in boffs:
            if sp and s0 < sp[1] and e0 > sp[0]:
                by_block.setdefault(bid, []).append(p["index"] + 1)
        pos += len(p["text"]) + 1
    import difflib
    la, lb = letters_only(btext), letters_only(rtext)
    diffs = [{"op": o, "this": la[i1:i2], "alt": lb[j1:j2], "context": la[max(0, i1 - 12):i2 + 12]}
             for o, i1, i2, j1, j2 in difflib.SequenceMatcher(None, la, lb, autojunk=False).get_opcodes()
             if o != "equal"] if len(la) < 60000 else []
    rep[f"alt_segmentation:{alt.get('label', alt['doc'].split('/')[-1])}"] = {
        "rows": len(rows), "text_differences": len(diffs)}
    return {"label": alt.get("label"), "doc": alt["doc"], "rows_by_block": by_block,
            "text_differences": diffs, "projection": proj.stats}


def _headings_from_openpecha(ctx, hs, items, rep):
    """Insert the chapter headings an OpenPecha version of the same text
    carries as their own segments: each goes before the block where the
    next non-heading segment begins (located by letter projection)."""
    m = ctx.op(hs["text_id"])
    text = "\n".join(it["text"] for it in items)
    offs, pos = [], 0
    for i, it in enumerate(items):
        offs.append((i, pos, pos + len(it["text"])))
        pos += len(it["text"]) + 1
    proj = Projector(m["content"], text)
    segs = m["segments"]
    insert, n = {}, 0
    for k, sgm in enumerate(segs):
        clean = m["content"][sgm["start"]:sgm["end"]].strip().strip("\u200e")
        if not re.fullmatch(hs["pattern"], clean):
            continue
        n += 1
        nxt = next((x for x in segs[k + 1:] if not re.fullmatch(
            hs["pattern"], m["content"][x["start"]:x["end"]].strip())), None)
        sp = proj.span(nxt["start"], nxt["end"]) if nxt else None
        hit = next((i for i, s, e in offs if sp and s <= sp[0] < e), None)
        if hit is None:
            rep.setdefault("unplaced_headings", []).append(clean)
            continue
        insert.setdefault(hit, []).append({"kind": "heading", "path": str(n), "title": clean,
                                           "source": {"openpecha_text": hs["text_id"],
                                                      "openpecha_segment": sgm["id"]}})
    out = []
    for i, it in enumerate(items):
        out += insert.get(i, [])
        out.append(it)
    rep["headings"] = sum(len(v) for v in insert.values())
    return out


def apply_text_corrections(spec, items, rep):
    """Apply the manifest's text_corrections: [{id, find, replace, reason,
    source}] — later human corrections (e.g. a reviewer's emendation carried
    by another version). `find` must occur exactly once in the block; the
    original reading is kept in the block's sidecar entry."""
    by_id = {it.get("id"): it for it in items if it["kind"] == "block"}
    done = []
    for c in spec.get("text_corrections") or []:
        it = by_id.get(str(c["id"]))
        if it is None or it["text"].count(c["find"]) != 1:
            raise ValueError(f"text correction {c} does not match exactly once in block ^{c['id']}")
        it["text"] = it["text"].replace(c["find"], c["replace"])
        it["source"].setdefault("corrections", []).append(
            {"original": c["find"], "corrected": c["replace"], "reason": c["reason"],
             "source": c.get("source")})
        done.append(str(c["id"]))
    if done:
        rep["text_corrections"] = done


def _align_via(ctx, spec, items, rep):
    """Derive this work's transclusions from a separate line-parallel pair in
    which the same text was re-split (and possibly reordered) against the
    target's rows: each `other` row is located in this work's blocks, each
    `root_rows` row in the target, and the two id sets are linked."""
    own = LetterIndex([(it["id"], it["text"]) for it in items])
    tgt = ctx.index(spec["target"])
    rows_r = _row_lines(ctx, spec["align_via"]["root_rows"])
    rows_o = _row_lines(ctx, spec["align_via"]["other"])
    by_id = {it["id"]: it for it in items}
    raw, unmapped, hr, ho = [], [], 0, 0
    for i in range(max(len(rows_r), len(rows_o))):
        rt = rows_r[i]["text"] if i < len(rows_r) else ""
        ot = rows_o[i]["text"] if i < len(rows_o) else ""
        if not (rt.strip() and ot.strip()):
            continue
        tids, hr = tgt.find(rt, hr)
        oids, ho = own.find(ot, ho)
        raw.append({"row": i + 1, "target_ids": tids or [], "own_ids": oids or [], "text": ot})
        if not tids or not oids:
            unmapped.append({"row": i + 1, "text": ot})
            continue
        for oid in oids:
            t = by_id[oid].setdefault("targets", [])
            t += [x for x in tids if x not in t]
    for it in items:
        if it.get("targets"):
            it["targets"].sort(key=lambda x: int(x) if x.isdigit() else x)
    rep["aligned_rows"] = len(raw) - len(unmapped)
    rep["unmapped_rows"] = unmapped
    return raw


def _row_lines(ctx, rel):
    """Rows of a line-parallel (Tsadrel) doc: one row per paragraph."""
    return ctx.docx(rel)["paragraphs"]


def adapt_parallel(ctx, spec, rep):
    """A translation laid out row-for-row against a root split.

    spec.pair = {root_rows: <docx>, other: <docx>}; row i of one is row i of
    the other, a blank row has no counterpart. Each `root_rows` row is located
    in the target work's blocks by its letters, so the root split may differ
    from the target's segmentation. Block id = first target id (identity when
    the splits agree); rows sharing a first target are kept as lines of one
    block; every target is transcluded."""
    tgt = spec["target"]
    rows_r = _row_lines(ctx, spec["pair"]["root_rows"])
    rows_o = _row_lines(ctx, spec["pair"]["other"])
    comments = ctx.docx(spec["pair"]["other"])["comments"]
    mapper = RowMapper(ctx, tgt, [r["text"] for r in rows_r])
    n = max(len(rows_r), len(rows_o))
    blocks, order = {}, []
    unmapped, root_only, raw_pairs = [], [], []
    last = title_row = None
    for i in range(n):
        r = rows_r[i] if i < len(rows_r) else None
        o = rows_o[i] if i < len(rows_o) else None
        rt = r["text"] if r else ""
        ot = o["text"] if o else ""
        if not ot.strip():
            if rt.strip():
                root_only.append(i + 1)
            continue
        ids = mapper.ids(i) if rt.strip() else []
        raw_pairs.append({"row": i + 1, "root_row_text": rt, "targets": ids})
        if ids and set(ids) == {TITLE_ID}:
            if title_row is None and not order:
                # the row paired with the target's title is this file's title line
                title_row = {"row": i + 1, "text": ot, "root_row_text": rt,
                             "annotations": formatted_runs(o, spec.get("legend"))}
                rep["title_text"] = ot.strip()
                continue
            ids = []
        ids = [t for t in ids if t != TITLE_ID]
        flag = None
        if not ids:
            # never drop text: keep the row as a further line of the previous
            # block, flagged for review
            if last is None:
                unmapped.append({"row": i + 1, "text": ot, "kept": False})
                continue
            unmapped.append({"row": i + 1, "text": ot, "kept_in_block": last})
            key, flag = last, "row has no located counterpart; kept with the preceding block"
        else:
            key = ids[0]
        if key not in blocks:
            blocks[key] = {"kind": "block", "text": "", "id": key, "targets": [], "lines": [],
                           "source": {"doc": spec["pair"]["other"], "rows": []}, "annotations": [],
                           "comments": []}
            order.append(key)
        last = key
        b = blocks[key]
        off = sum(len(x) + 1 for x in b["lines"])
        b["lines"].append(ot.strip())
        b["source"]["rows"].append(i + 1)
        if flag:
            b["source"].setdefault("flags", []).append({"row": i + 1, "flag": flag})
        for t in ids:
            if t not in b["targets"]:
                b["targets"].append(t)
        for a in formatted_runs(o, spec.get("legend")):
            a = dict(a, row=i + 1, start=a["start"] + off, end=a["end"] + off)
            b["annotations"].append(a)
        b["comments"] += [comments[c] for c in o["comment_ids"] if c in comments]
    items = []
    for key in sorted(order, key=lambda k: [int(x) if x.isdigit() else x for x in re.split(r"[-]", k)]):
        b = blocks[key]
        b["text"] = "\n".join(b.pop("lines"))
        if not b["comments"]:
            b.pop("comments")
        items.append(b)
    identity = all(b["targets"] == [b["id"]] for b in items)
    rep.update({"blocks": len(items), "rows": n, "identity_alignment": identity,
                "rows_without_counterpart": root_only, "unmapped_rows": unmapped})
    extra = {"raw_alignment": raw_pairs}
    if title_row:
        extra["title_row"] = title_row
    if spec.get("overlays"):
        extra["overlay_summary"] = apply_overlays(ctx, spec, items, rep)
    return items, extra


def explode_lines(para):
    """Split a paragraph at its internal line breaks into pseudo-paragraphs
    (same index, a "line" number), each keeping its own runs."""
    out, cur = [], {"runs": []}
    def push():
        cur["text"] = "".join(r["text"] for r in cur["runs"])
        out.append(cur)
    for r in para["runs"]:
        parts = r["text"].split("\n")
        for k, part in enumerate(parts):
            if k:
                push()
                cur = {"runs": []}
            if part:
                cur["runs"].append(dict(r, text=part))
    push()
    return [dict(para, runs=q["runs"], text=q["text"], line=i, numbering=para["numbering"] if i == 0 else None)
            for i, q in enumerate(out)]


class RowMapper:
    """Map the rows of a root-side split onto a built target's block ids.

    First by sequential letter projection of the whole split onto the
    target (robust to small corrections made in one version only), then by
    order-free letter search (for splits whose rows were reordered)."""

    def __init__(self, ctx, target, rows):
        self.rows = rows
        tblocks = list(ctx.works[target]["blocks"])
        if ctx.works[target].get("title"):
            # the title line is a counterpart too: a row paired with it must
            # not be pushed onto the first block that shares its words
            tblocks = [(TITLE_ID, ctx.works[target]["title"])] + tblocks
        ttext = self.ttext = "\n".join(t for _, t in tblocks)
        self.toffs, pos = [], 0
        for bid, t in tblocks:
            self.toffs.append((bid, pos, pos + len(t)))
            pos += len(t) + 1
        rtext = "\n".join(rows)
        self.roffs, pos = [], 0
        for r in rows:
            self.roffs.append((pos, pos + len(r)))
            pos += len(r) + 1
        self.proj = Projector(rtext, ttext)
        self.idx = LetterIndex(tblocks)
        self.hint = 0
        self.past_title = False

    def ids(self, i):
        sp = self.proj.span(*self.roffs[i])
        if sp:
            out = []
            for bid, s, e in self.toffs:
                if s < sp[1] and e > sp[0]:
                    # count only blocks that receive a real share of the row
                    share = len(letters_only(self.ttext[max(s, sp[0]):min(e, sp[1])]))
                    if share >= min(3, len(letters_only(self.rows[i]))):
                        out.append(bid)
            if self.past_title:
                out = [t for t in out if t != TITLE_ID]
            if out:
                return self._seen(out)
        # once a row has reached the body, the title is behind us: search on
        # from the first block, so a body row repeating the title's words is
        # not sent back to the title line
        hint = self.hint
        if self.past_title and self.idx.ids and self.idx.ids[0] == TITLE_ID:
            hint = max(hint, self.idx.ends[0])
        ids, self.hint = self.idx.find(self.rows[i], hint)
        return self._seen(ids or [])

    def _seen(self, ids):
        if any(t != TITLE_ID for t in ids):
            self.past_title = True
        return ids


def _heading_level(spec, para):
    """Heading level by the document legend: {colour: level} plus optional
    {"<colour>+bold": level} and {"style:<name>": level}."""
    hl = spec.get("headings") or {}
    for pat in spec.get("heading_patterns") or []:
        if re.match(pat["regex"], para["text"].strip()):
            return pat["level"]
    if para["style"] and f"style:{para['style']}" in hl:
        return hl[f"style:{para['style']}"]
    c, bold = para_colour(para)
    if c and bold and f"{c}+bold" in hl:
        return hl[f"{c}+bold"]
    if c and c in hl:
        return hl[c]
    return None


def _ref_fix(spec, prefix, paragraph):
    """A human-decided reading of a written number (manifest ref_corrections):
    {"<written, spaces/dots removed>": {refs, reason, paragraphs?}}. With
    `paragraphs`, the reading applies only there (the same written number
    elsewhere stays as written)."""
    fix = (spec.get("ref_corrections") or {}).get(re.sub(r"[\s.．\u200b\ufeff]", "", prefix or ""))
    if fix and (not fix.get("paragraphs") or paragraph in fix["paragraphs"]):
        return fix
    return None


def adapt_ref_commentary(ctx, spec, rep):
    """Commentary whose paragraphs carry typed (or auto-numbered) references
    to the target's numbered segments (Pecha convention: '12.', '4-12.',
    '1-3,5.'). Headings come from the colour/style legend. A paragraph is
    split where an internal line starts with a reference."""
    doc = ctx.docx(spec["text"])
    refs_mode = spec.get("refs", "align")          # align | candidate | none
    ref_style = spec.get("ref_style", "dotted")
    ref_map = build_ref_map(ctx, spec["ref_map"], spec["target"], rep) if spec.get("ref_map") else None
    legend = spec.get("legend")
    lemma = set(spec.get("lemma_colours") or [])
    items, heads = [], [0, 0]
    n_refs = n_auto = 0
    candidates = []
    title_para = spec.get("title_paragraph")
    paras = doc["paragraphs"]
    if spec.get("split_lines"):
        paras = [q for p in paras for q in explode_lines(p)]
    excluded = []
    carry, carried_prefixes = None, []
    seen_comments = set()
    for p in paras:
        if not p["text"].strip():
            continue
        if title_para is not None and p["index"] == title_para:
            rep["title_text"] = p["text"]
            continue
        ex = next((e for e in spec.get("exclude_paragraphs") or []
                   if re.match(e["regex"], p["text"].strip())), None)
        if ex:
            excluded.append({"paragraph": p["index"], "text": p["text"], "reason": ex["reason"]})
            continue
        lvl = _heading_level(spec, p)
        if lvl and spec.get("heading_numbers"):
            mnum = re.match(r"^\s*(\d+(?:\.\d+)*)\.?", p["text"])
            if mnum:
                items.append({"kind": "heading", "path": mnum.group(1), "title": p["text"],
                              "source": {"doc": spec["text"], "paragraph": p["index"],
                                         "annotations": formatted_runs(p, legend)}})
                continue
            rep.setdefault("warnings", []).append(f"heading without outline number, paragraph {p['index']}")
        if lvl:
            if lvl == 1 or heads[0] == 0:
                heads = [heads[0] + 1, 0]
                path = str(heads[0])
            else:
                heads[1] += 1
                path = f"{heads[0]}.{heads[1]}"
            items.append({"kind": "heading", "path": path, "title": p["text"],
                          "source": {"doc": spec["text"], "paragraph": p["index"], "line": p.get("line"),
                                     "annotations": formatted_runs(p, legend)}})
            continue
        colour, _ = para_colour(p)
        role = "lemma" if colour in lemma else "body"
        runs = formatted_runs(p, legend)
        # split into segments at internal lines that begin with a reference
        lines = p["text"].split("\n")
        segs, cur, off = [], None, 0
        for li, line in enumerate(lines):
            refs, prefix, rest = parse_ref_prefix(line, ref_style) if refs_mode != "none" else (None, "", line)
            fix = _ref_fix(spec, prefix, p["index"]) if refs else None
            if fix:
                refs = list(fix["refs"])
                rep.setdefault("ref_corrections_applied", []).append(
                    {"paragraph": p["index"], "written": prefix.strip(), "read_as": refs})
            if cur is None or refs:
                cur = {"lines": [], "refs": refs, "prefix": prefix, "start": off, "line": li, "fix": fix}
                segs.append(cur)
                cur["lines"].append(rest if refs else line)
                cur["prefix_len"] = len(prefix) if refs else 0
            else:
                cur["lines"].append(line)
            off += len(line) + 1
        auto = (p["numbering"] or {}).get("value")
        # a paragraph that is only an alignment number applies to the next block
        if refs_mode != "none" and not spec.get("split_lines"):
            only, _, rest_ = parse_ref_prefix(p["text"].strip() + " x", ref_style)
            if only and rest_.strip() == "x":
                carry = (carry or []) + only
                carried_prefixes.append({"paragraph": p["index"], "text": p["text"]})
                continue
        for k, s in enumerate(segs):
            refs = s["refs"]
            if k == 0 and carry:
                refs = carry + [r for r in (refs or []) if r not in carry]
                carry = None
            if k == 0 and auto and refs_mode != "none":
                refs = [auto] + [r for r in (refs or []) if r != auto]
                n_auto += 1
            text = "\n".join(s["lines"])
            if not letters_only(text):
                continue
            end = s["start"] + len("\n".join(lines[s["line"]:s["line"] + len(s["lines"])]))
            ann = [dict(a, start=a["start"] - s["start"] - s["prefix_len"],
                        end=a["end"] - s["start"] - s["prefix_len"])
                   for a in runs if a["start"] >= s["start"] and a["end"] <= end]
            item = {"kind": "block", "text": text, "role": role,
                    "source": {"doc": spec["text"], "paragraph": p["index"], "line": p.get("line", s["line"]),
                               **({"typed_prefix": s["prefix"]} if s["prefix"] else {}),
                               **({"ref_correction": {"written": s["prefix"].strip(),
                                                      "read_as": s["refs"],
                                                      "reason": s["fix"]["reason"]}}
                                  if s.get("fix") else {}),
                               **({"auto_number": auto} if k == 0 and auto else {})},
                    "annotations": ann}
            new_c = [c for c in p.get("comment_ids") or [] if c in doc["comments"] and c not in seen_comments]
            if new_c:
                seen_comments.update(new_c)
                item["comments"] = [doc["comments"][c] for c in new_c]
            if refs:
                if refs_mode == "align" and ref_map is not None:
                    item["source"]["refs"] = refs
                    tg = []
                    for r in refs:
                        if r not in ref_map:
                            rep.setdefault("unresolved_refs", []).append(r)
                        tg += [t for t in ref_map.get(r, []) if t not in tg]
                    item["targets"] = sorted(tg, key=lambda x: int(x) if x.isdigit() else x)
                    n_refs += 1
                elif refs_mode == "align":
                    item["targets"] = [str(r) for r in refs]
                    n_refs += 1
                else:
                    item["source"]["candidate_refs"] = refs
                    candidates.append(refs)
                    if s["prefix"]:      # keep the number in the text: it is not confirmed markup
                        item["text"] = s["prefix"] + text
                        item["source"].pop("typed_prefix")
            items.append(item)
    known = {bid for bid, _ in ctx.works[spec["target"]]["blocks"]} if spec.get("target") else set()
    bad = sorted({t for it in items for t in it.get("targets", []) if t not in known})
    if bad:
        rep["warnings"] = rep.get("warnings", []) + [f"references to unknown target ids: {bad}"]
        for it in items:
            if "targets" in it:
                it["targets"] = [t for t in it["targets"] if t in known]
    rep.update({"blocks": sum(1 for i in items if i["kind"] == "block"),
                "headings": sum(1 for i in items if i["kind"] == "heading"),
                "blocks_with_refs": n_refs, "auto_numbered_refs": n_auto,
                "candidate_refs": len(candidates),
                "lemma_blocks": sum(1 for i in items if i.get("role") == "lemma")})
    extra = {}
    if carried_prefixes:
        extra["number_only_paragraphs"] = carried_prefixes
        rep["number_only_paragraphs"] = len(carried_prefixes)
    if ref_map is not None:
        extra["ref_map"] = {"doc": spec["ref_map"]["doc"], "style": spec["ref_map"].get("style", "typed"),
                            "map": {str(k): v for k, v in sorted(ref_map.items())}}
    if excluded:
        extra["excluded_paragraphs"] = excluded
        rep["excluded_paragraphs"] = len(excluded)
    if spec.get("tsadrel"):
        extra["tsadrel"] = tsadrel_crosscheck(ctx, spec, items, rep)
    if spec.get("overlays"):
        extra["overlay_summary"] = apply_overlays(ctx, spec, items, rep)
    return items, extra


def build_ref_map(ctx, rm, target, rep):
    """Concordance from a reference numbering to the target's block ids.

    rm = {doc: <docx whose paragraphs carry the numbers>,
          style: typed | auto}  — typed: '  12. text'; auto: Word list number.
    Each numbered paragraph is located in the target by its letters."""
    doc = ctx.docx(rm["doc"])
    idx = ctx.index(target)
    out, hint, missing = {}, 0, []
    for p in doc["paragraphs"]:
        if not p["text"].strip():
            continue
        if rm.get("style", "typed") == "auto":
            n = (p["numbering"] or {}).get("value")
            text = p["text"]
        else:
            refs, _, text = parse_ref_prefix(p["text"])
            n = refs[0] if refs and len(refs) == 1 else None
        if n is None:
            continue
        ids, hint = idx.find(text, hint)
        if ids:
            out[n] = ids
        else:
            missing.append(n)
    # A number that could not be located by its letters (its row carries a
    # later correction) but whose neighbours both were, takes the target ids
    # lying strictly between them. Recorded as inferred, never silent.
    order = [b for b, _ in ctx.works[target]["blocks"]]
    pos = {b: i for i, b in enumerate(order)}
    inferred = {}
    for n in list(missing):
        if n - 1 in out and n + 1 in out:
            lo = max(pos[b] for b in out[n - 1])
            hi = min(pos[b] for b in out[n + 1])
            between = order[lo + 1:hi]
            if between:
                out[n] = between
                inferred[n] = between
                missing.remove(n)
    key = f"ref_map:{rm['doc'].split('/')[-1]}"
    rep[key] = {"numbers": len(out), "unlocated": missing, "inferred_by_position": inferred}
    return out


def _item_text_index(items):
    """Concatenated block text with (item index, start, end) offsets."""
    parts, offs, pos = [], [], 0
    for i, it in enumerate(items):
        if it["kind"] != "block":
            continue
        t = it["text"]
        offs.append((i, pos, pos + len(t)))
        parts.append(t)
        pos += len(t) + 1
    return "\n".join(parts), offs


def _locate_span(offs, start, end):
    hits = []
    for i, s, e in offs:
        if s < end and e > start:
            hits.append((i, max(start, s) - s, min(end, e) - s))
    return hits


def apply_overlays(ctx, spec, items, rep):
    """Carry secondary human layers onto the built blocks (sidecar only):
      openpecha_alignment — an OpenPecha alignment of the same text
      openpecha_notes     — OpenPecha durchen (variant readings)
      refs_doc            — another doc of the same text with its own refs
      formatting          — runs (e.g. italics) from another version
    Every unplaced item is counted in the report, never guessed."""
    text, offs = _item_text_index(items)
    out = {}
    for ov in spec.get("overlays") or []:
        typ = ov["type"]
        if typ in ("openpecha_alignment", "openpecha_notes"):
            m = ctx.op(ov["text_id"])
            proj = Projector(m["content"], text)
            placed = lost = 0
            if typ == "openpecha_notes":
                for n in m["notes"]:
                    sp = proj.span(n["start"], n["end"])
                    hits = _locate_span(offs, *sp) if sp else []
                    if not hits:
                        lost += 1
                        continue
                    i, s, e = hits[0]
                    items[i].setdefault("annotations", []).append(
                        {"start": s, "end": e, "layer": "variant_note", "note": n["note"],
                         "reading": m["content"][n["start"]:n["end"]], "openpecha_id": n["id"],
                         "openpecha_text": ov["text_id"]})
                    placed += 1
            else:
                root_key = ov.get("root", spec.get("root_work"))
                root_text = "\n".join(t for _, t in ctx.works[root_key]["blocks"])
                rproj = Projector(ctx.op(m["alignment"]["parent_text"])["content"], root_text)
                roffs, pos = [], 0
                for bid, t in ctx.works[root_key]["blocks"]:
                    roffs.append((bid, pos, pos + len(t)))
                    pos += len(t) + 1
                agree = 0
                for pr in m["alignment"]["pairs"]:
                    sp = proj.span(pr["start"], pr["end"])
                    rsp = rproj.span(pr["target_start"], pr["target_end"])
                    hits = _locate_span(offs, *sp) if sp else []
                    rids = [b for b, s, e in roffs if rsp and s < rsp[1] and e > rsp[0]]
                    if not hits or not rids:
                        lost += 1
                        continue
                    for i, s, e in hits:
                        items[i].setdefault("overlays", []).append(
                            {"layer": "openpecha_alignment", "openpecha_id": pr["id"],
                             "root_ids": rids, "start": s, "end": e})
                        if set(rids) & set(items[i].get("targets") or []):
                            agree += 1
                    placed += 1
                out.setdefault("openpecha_alignment_agreement", agree)
            rep[f"overlay:{typ}:{ov['text_id']}"] = {"placed": placed, "unplaced": lost,
                                                      "projection": proj.stats}
        elif typ == "refs_doc":
            doc = ctx.docx(ov["doc"])
            rmap = build_ref_map(ctx, ov["ref_map"], spec["target"], rep)
            bidx = LetterIndex([(str(i), items[i]["text"]) for i, _, _ in offs])
            placed = lost = 0
            hint = 0
            for p in doc["paragraphs"]:
                refs, prefix, rest = parse_ref_prefix(p["text"], ov.get("ref_style", "dotted"))
                if not refs:
                    continue
                bids, hint = bidx.find(rest, hint)
                if not bids:
                    lost += 1
                    continue
                tg = sorted({t for r in refs for t in rmap.get(r, [])}, key=lambda x: int(x) if x.isdigit() else x)
                for b in bids:
                    items[int(b)].setdefault("overlays", []).append(
                        {"layer": ov.get("label", "refs_doc"), "refs": refs, "root_ids": tg,
                         "doc": ov["doc"], "paragraph": p["index"]})
                placed += 1
            rep[f"overlay:refs_doc:{ov.get('label', '')}"] = {"placed": placed, "unplaced": lost}
        elif typ == "docx_comments":
            # Word reviewer comments made on another copy of the same text:
            # each commented paragraph is projected onto the built blocks
            doc = ctx.docx(ov["doc"])
            src = "\n".join(p["text"] for p in doc["paragraphs"])
            proj = Projector(src, text)
            pos = placed = lost = 0
            seen = set()
            for p in doc["paragraphs"]:
                # a comment spanning several paragraphs is placed once, at its start
                cids = [c for c in p.get("comment_ids") or [] if c in doc["comments"] and c not in seen]
                seen.update(cids)
                if cids:
                    sp = proj.span(pos, pos + len(p["text"]))
                    hits = _locate_span(offs, *sp) if sp else []
                    if hits:
                        i, s, e = hits[0]
                        items[i].setdefault("comments", []).extend(
                            dict(doc["comments"][c], doc=ov["doc"], paragraph=p["index"]) for c in cids)
                        placed += len(cids)
                    else:
                        lost += len(cids)
                pos += len(p["text"]) + 1
            rep[f"overlay:docx_comments:{ov['doc'].split('/')[-1]}"] = {"placed": placed, "unplaced": lost}
        elif typ == "docx_footnotes":
            # a collation apparatus kept as Word footnotes on another copy of
            # the same text: "lemma]V1,V2: reading; V4: reading;" anchored
            # right after the lemma. Each note is projected onto the block
            # holding its lemma; the sigla legend comes from the manifest.
            doc = ctx.docx(ov["doc"])
            src = "\n".join(p["text"] for p in doc["paragraphs"])
            proj = Projector(src, text)
            pos = placed = lost = 0
            for p in doc["paragraphs"]:
                for ref in p.get("footnote_refs") or []:
                    note = doc["footnotes"].get(ref["id"], "")
                    lemma = note.split("]", 1)[0].strip() if "]" in note else ""
                    end = pos + ref["offset"]
                    start = max(pos, end - len(lemma)) if lemma else end - 1
                    sp = proj.span(start, end)
                    hits = _locate_span(offs, *sp) if sp else []
                    if not hits:
                        lost += 1
                        continue
                    i, s, e = hits[-1]
                    items[i].setdefault("annotations", []).append(
                        {"start": s, "end": e, "layer": ov.get("label", "footnote"), "note": note,
                         "reading": src[start:end], "footnote_id": ref["id"], "doc": ov["doc"]})
                    placed += 1
                pos += len(p["text"]) + 1
            rep[f"overlay:docx_footnotes:{ov.get('label', ov['doc'].split('/')[-1])}"] = {
                "placed": placed, "unplaced": lost, "projection": proj.stats}
            if ov.get("sigla"):
                out.setdefault("sigla", {}).update(ov["sigla"])
        elif typ == "formatting":
            doc = ctx.docx(ov["doc"])
            src = "\n".join(p["text"] for p in doc["paragraphs"])
            proj = Projector(src, text)
            keep = set(ov.get("keep") or ["italic"])
            pos = placed = lost = 0
            for p in doc["paragraphs"]:
                for r in formatted_runs(p, ov.get("legend")):
                    if not keep & {k for k in r if r[k] is True or k in ("color", "highlight")}:
                        continue
                    sp = proj.span(pos + r["start"], pos + r["end"])
                    hits = _locate_span(offs, *sp) if sp else []
                    if not hits:
                        lost += 1
                        continue
                    for i, s, e in hits:
                        items[i].setdefault("annotations", []).append(
                            dict({k: v for k, v in r.items() if k not in ("start", "end")},
                                 start=s, end=e, layer=f"formatting from {ov['doc'].split('/')[-1]}"))
                    placed += 1
                pos += len(p["text"]) + 1
            rep[f"overlay:formatting:{ov['doc'].split('/')[-1]}"] = {"placed": placed, "unplaced": lost,
                                                                    "projection": proj.stats}
    return out


def tsadrel_crosscheck(ctx, spec, items, rep):
    """Read a commentary's line-parallel Tsadrel pair (its own root split
    against its own commentary rows), locate every root row in the target
    and every commentary row in the built blocks, and record the row-level
    alignment. Agreement with the typed references is reported."""
    tgt_idx = ctx.index(spec["target"])
    blk = [(str(i), it["text"]) for i, it in enumerate(items) if it["kind"] == "block"]
    blk_idx = LetterIndex(blk)
    rows_r = _row_lines(ctx, spec["tsadrel"]["root_rows"])
    rows_c = _row_lines(ctx, spec["tsadrel"]["other"])
    if spec["tsadrel"].get("pair_by") == "number":
        # pair the two sides by their Word list numbers (row i <-> row i of
        # the list), for pairs where one side has extra unnumbered lines
        def by_num(rows):
            d = {}
            for r in rows:
                v = (r["numbering"] or {}).get("value")
                if v is not None:
                    d.setdefault(v, []).append(r["text"])
            return d
        nr, nc = by_num(rows_r), by_num(rows_c)
        keys = sorted(set(nr) | set(nc))
        rows_r = [{"text": "\n".join(nr.get(k, []))} for k in keys]
        rows_c = [{"text": "\n".join(nc.get(k, []))} for k in keys]
    out, hint_r, hint_c, agree, total = [], 0, 0, 0, 0
    for i in range(max(len(rows_r), len(rows_c))):
        rt = rows_r[i]["text"] if i < len(rows_r) else ""
        ct = rows_c[i]["text"] if i < len(rows_c) else ""
        if not rt.strip():
            continue
        tids, hint_r = tgt_idx.find(re.sub(r"_+", "", rt), hint_r)
        ct_clean = re.sub(r"_+|(?<=\S)-(?=\S)", "", ct)
        bids, hint_c = blk_idx.find(ct_clean, hint_c) if ct.strip() else (None, hint_c)
        row = {"row": i + 1, "root_text": rt, "target_ids": tids or [],
               "commentary_text": ct, "commentary_blocks": bids or []}
        out.append(row)
        if tids and bids:
            total += 1
            typed = {t for b in bids for t in (items_by_pos(items, int(b)).get("targets") or [])}
            if typed & set(tids):
                agree += 1
    rep["tsadrel_rows_with_root"] = len(out)
    rep["tsadrel_agreement_with_typed_refs"] = f"{agree}/{total}"
    return out


def items_by_pos(items, k):
    return items[k]


def adapt_op_translation(ctx, spec, rep):
    """A translation whose text, segmentation and alignment come from the
    OpenPecha API, aligned to an OpenPecha parent that is the same text as an
    already-built target work. Parent spans are located in the target by
    letter projection."""
    m = ctx.op(spec["openpecha_text"])
    parent = ctx.op(m["alignment"]["parent_text"])
    tgt = ctx.works[spec["target"]]
    tblocks = ([(TITLE_ID, tgt["title"])] if tgt.get("title") else []) + list(tgt["blocks"])
    tgt_text = "\n".join(t for _, t in tblocks)
    proj = Projector(parent["content"], tgt_text)
    # target block offsets in tgt_text (the title line first, as TITLE_ID)
    offs, pos = [], 0
    for bid, t in tblocks:
        offs.append((bid, pos, pos + len(t)))
        pos += len(t) + 1
    by_seg = {}
    for pr in m["alignment"]["pairs"]:
        sp = proj.span(pr["target_start"], pr["target_end"])
        ids = [b for b, s, e in offs if sp and s < sp[1] and e > sp[0]]
        by_seg.setdefault((pr["start"], pr["end"]), []).extend(x for x in ids if x not in by_seg.get((pr["start"], pr["end"]), []))
    blocks, order, unmapped, pending = {}, [], [], []
    heads, pending_head, n_head = [], None, 0
    title_re = spec.get("title_pattern")
    head_re = spec.get("heading_pattern")
    for sgm in m["segments"]:
        text = m["content"][sgm["start"]:sgm["end"]]
        if not text.strip():
            continue
        clean = text.strip().strip("\u200e")
        if title_re and re.fullmatch(title_re, clean):
            rep["title_segment"] = rep["title_text"] = clean
            continue
        if head_re and re.fullmatch(head_re, clean):
            n_head += 1
            pending_head = {"kind": "heading", "path": str(n_head), "title": clean,
                            "source": {"openpecha_segment": sgm["id"]}}
            continue
        ids = by_seg.get((sgm["start"], sgm["end"]), [])
        if ids and set(ids) == {TITLE_ID} and not order and "title_segment" not in rep:
            rep["title_segment"] = rep["title_text"] = clean   # aligned upstream to the parent's title
            continue
        ids = [t for t in ids if t != TITLE_ID]
        if not ids:
            # never drop text: keep it with the preceding block, flagged
            if not order:
                # before any aligned segment: kept with the following block
                pending.append((sgm, text))
                continue
            unmapped.append({"segment": sgm["id"], "text": text, "kept_in_block": order[-1]})
            b = blocks[order[-1]]
            b["lines"].append(text.strip())
            b["source"]["openpecha_segments"].append({"id": sgm["id"], "start": sgm["start"], "end": sgm["end"],
                                                      "flag": "no aligned counterpart; kept with the preceding block"})
            continue
        key = ids[0]
        if key not in blocks:
            blocks[key] = {"kind": "block", "id": key, "lines": [], "targets": [],
                           "source": {"openpecha_segments": []}}
            order.append(key)
            for psg, ptext in pending:
                blocks[key]["lines"].append(ptext.strip())
                blocks[key]["source"]["openpecha_segments"].append(
                    {"id": psg["id"], "start": psg["start"], "end": psg["end"],
                     "flag": "no aligned counterpart; kept with the following block"})
                unmapped.append({"segment": psg["id"], "text": ptext, "kept_in_block": key})
            pending = []
        if pending_head:
            heads.append((key, pending_head))
            pending_head = None
        b = blocks[key]
        b["lines"].append(text.strip())
        b["source"]["openpecha_segments"].append({"id": sgm["id"], "start": sgm["start"], "end": sgm["end"]})
        b["targets"] += [i for i in ids if i not in b["targets"]]
    items = []
    head_at = dict(heads)
    for key in sorted(order, key=lambda k: int(k) if k.isdigit() else k):
        b = blocks[key]
        b["text"] = "\n".join(b.pop("lines"))
        if key in head_at:
            items.append(head_at[key])
        items.append(b)
    rep["headings"] = len(heads)
    rep.update({"blocks": len(items) - len(heads), "openpecha_segments": len(m["segments"]),
                "unmapped_segments": unmapped, "projection": proj.stats})
    return items, {"openpecha": {"text_id": m["text_id"], "instance_id": m["instance_id"],
                                 "alignment_annotation": m["alignment"]["annotation_id"]}}


def adapt_op_text(ctx, spec, rep):
    """An OpenPecha text with no upstream alignment: one block per segment of
    its segmentation annotation, flat ids 1..n, no transclusions. A segment
    matching `title_pattern` becomes the title line."""
    m = ctx.op(spec["openpecha_text"])
    items, n = [], 0
    for sgm in m["segments"]:
        text = m["content"][sgm["start"]:sgm["end"]]
        if not text.strip():
            continue
        clean = text.strip().strip("\u200e")
        if spec.get("title_pattern") and not items and re.fullmatch(spec["title_pattern"], clean):
            rep["title_text"] = clean
            continue
        n += 1
        items.append({"kind": "block", "id": str(n), "text": text.strip(),
                      "source": {"openpecha_segment": sgm["id"], "start": sgm["start"], "end": sgm["end"]}})
    # text outside every segment (if any) is kept, never dropped
    covered = sum(s["end"] - s["start"] for s in m["segments"])
    rep.update({"blocks": len(items), "openpecha_segments": len(m["segments"]),
                "uncovered_chars": len(m["content"]) - covered})
    return items, {"openpecha": {"text_id": m["text_id"], "instance_id": m["instance_id"]}}


ADAPTERS = {
    "rows": adapt_rows,
    "numbered": adapt_numbered,
    "parallel": adapt_parallel,
    "ref_commentary": adapt_ref_commentary,
    "op_translation": adapt_op_translation,
    "op_text": adapt_op_text,
}


def register_adapter(name, fn):
    ADAPTERS[name] = fn


import md_adapter                                  # noqa: E402
register_adapter("md_rows", md_adapter.adapt_md_rows)


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def raw_files(spec):
    out = []
    for k in ("text", "toc", "segmentation", "citations", "meta"):
        if isinstance(spec.get(k), str):
            out.append(spec[k])
    if isinstance(spec.get("toc"), dict) and spec["toc"].get("doc"):
        out.append(spec["toc"]["doc"])
    for k in ("pair", "tsadrel"):
        if spec.get(k):
            out += [v for v in spec[k].values() if isinstance(v, str)]
    out += spec.get("extra_raw") or []
    return out


def write_pretoc(manifest_path, vault, only=None):
    """Write the pre-TOC text of every md_rows work whose headings come from a
    toc-generate tree: 0-INBOX/temp/TOC-<id>/source.md (what toc-generate
    chunks, and what its [[line]] pointers count) plus source.json (sha1 and
    line -> row). Works are built in order first, so this needs nothing but
    the raw data; it never touches 1-SOURCES/."""
    manifest = yaml.safe_load(pathlib.Path(manifest_path).read_text(encoding="utf-8"))
    ctx = Ctx(manifest, vault)
    for spec in manifest["works"]:
        toc = spec.get("toc") or {}
        if spec["adapter"] != "md_rows" or toc.get("kind") != "tree":
            continue
        if only and spec["key"] not in only:
            continue
        text, rows = md_adapter.pretoc_source(ctx, spec)
        d = ctx.vault / "0-INBOX" / "temp" / f"TOC-{toc['id']}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "source.md").write_text(text, encoding="utf-8")
        meta = {"work": spec["key"], "file": spec["path"], "sha1": md_adapter.sha1_text(text),
                "lines": text.count("\n"), "line_to_row": rows}
        (d / "source.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{spec['key']:34s} -> {d / 'source.md'}  sha1={meta['sha1']} lines={meta['lines']}", file=sys.stderr)


def build(manifest_path, vault, only=None, dry=False, out=None):
    manifest = yaml.safe_load(pathlib.Path(manifest_path).read_text(encoding="utf-8"))
    ctx = Ctx(manifest, vault)
    sidecar_dir = manifest.get("sidecar_dir", "1-SOURCES/Annotations")
    built = []
    for spec in manifest["works"]:
        key = spec["key"]
        rep = {"key": key, "path": spec["path"], "adapter": spec["adapter"]}
        items, extra = ADAPTERS[spec["adapter"]](ctx, spec, rep)
        sdir = spec.get("sidecar_dir", sidecar_dir)
        fm = dict(spec.get("frontmatter") or {})
        fm["raw_sources"] = provenance(ctx, raw_files(spec))
        if spec.get("openpecha_text"):
            fm.setdefault("openpecha_text_id", spec["openpecha_text"])
        fm["intake"] = {"skill": "aligned-corpus-intake", "adapter": spec["adapter"],
                        "date": datetime.date.today().isoformat(),
                        "annotations": f"{sdir}/{pathlib.Path(spec['path']).stem}.annotations.json"}
        target_path = ctx.works[spec["target"]]["path"] if spec.get("target") else None
        work = {"path": spec["path"], "frontmatter": fm, "title": rep.get("title_text") or spec["title"],
                "id_scheme": spec.get("id_scheme", "flat"), "target_file": target_path,
                "sidecar": f"{sdir}/{pathlib.Path(spec['path']).stem}.annotations.json",
                "items": items,
                "extra": {"legend": spec.get("legend"), "notes": spec.get("notes"), **extra}}
        built.append(work)
        # remember the rendered block ids for later works
        blocks = _rendered_blocks(work)
        ctx.works[key] = {"path": spec["path"], "blocks": blocks, "title": work["title"]}
        rep["ids"] = f"{blocks[0][0]}..{blocks[-1][0]}" if blocks else "-"
        rep["transclusions"] = sum(len(i.get("targets") or []) for i in items if i["kind"] == "block")
        ctx.report.append(rep)
        print(f"{key:28s} {spec['adapter']:15s} blocks={rep.get('blocks')} "
              f"transclusions={rep['transclusions']} -> {spec['path']}", file=sys.stderr)
    link_works(ctx, built)
    if not dry:
        for work in built:
            vault_writer.render(work, out or vault)
    return ctx


def link_works(ctx, built):
    """Fill the structural map About Sources.md §10 requires: related_* lists
    on every file something derives from, covers_verses on every derived file
    (first–last target id it transcludes, in the target's own order)."""
    by_path = {w["path"]: w for w in built}
    order = {w["path"]: {} for w in built}
    for key, w in ctx.works.items():
        order[w["path"]] = {b: i for i, (b, _) in enumerate(w["blocks"])}
    for w in built:
        fm = w["frontmatter"]
        root = fm.get("root_text")
        if not root or root not in by_path:
            continue
        rfm = by_path[root]["frontmatter"]
        field = "related_commentaries" if fm.get("file_type") == "commentary" else "related_translations"
        rfm.setdefault(field, [])
        if w["path"] not in rfm[field]:
            rfm[field].append(w["path"])
        if w.get("target_file") == root:
            pos = order[root]
            tg = sorted({t for it in w["items"] if it["kind"] == "block" for t in it.get("targets") or []
                         if t in pos}, key=lambda t: pos[t])
            if tg:
                fm["covers_verses"] = f"{tg[0]}–{tg[-1]}"


def _rendered_blocks(work):
    """Recompute the ids the writer assigns, in document order."""
    out, h2, counters, nxt = [], "0", {}, 1
    for it in work["items"]:
        if it["kind"] == "heading":
            if vault_writer.heading_level(it) == 1:
                h2 = vault_writer.top_label(it)
            continue
        if not vault_writer.clean_lines(it["text"]):
            continue
        if work["id_scheme"] == "flat":
            bid = str(it.get("id") or nxt)
            if bid.isdigit():
                nxt = int(bid) + 1
        else:
            counters[h2] = counters.get(h2, 0) + 1
            bid = f"{h2}-{counters[h2]}"
        out.append((bid, "\n".join(vault_writer.clean_lines(it["text"]))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--vault", default=".")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", help="write outputs under this root instead of the vault (for a test build)")
    ap.add_argument("--report", help="write the JSON intake report here")
    ap.add_argument("--stage", choices=["pre-toc", "full"], default="full",
                    help="pre-toc: only write the texts toc-generate reads (0-INBOX/temp/TOC-<id>/source.md)")
    ap.add_argument("--only", help="comma-separated work keys (pre-toc stage)")
    a = ap.parse_args()
    if a.stage == "pre-toc":
        write_pretoc(a.manifest, a.vault, only=set(a.only.split(",")) if a.only else None)
        return
    ctx = build(a.manifest, a.vault, dry=a.dry_run, out=a.out)
    if a.report:
        pathlib.Path(a.report).write_text(json.dumps(ctx.report, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
