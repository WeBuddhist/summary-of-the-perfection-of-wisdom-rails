#!/usr/bin/env python3
"""Replace the text of whole segments in a LIVE library edition, in place.

Used 2026-10-04 to fix seven Mipham Chinese segments (^1-94 … ^1-102) whose first
DharmaMitra run left Tibetan script in the text. Re-uploading would re-create the
edition and lose its alignment, so the new text is written through
PATCH /v2/editions/{id}/content instead, the route edition-spacing-fix uses
(Dzongsar-dolma-bumtsok-rails/3-SKILLS/edition-spacing-fix).

The target is the edition the parser builds from the vault file
(translation-upload's parser-root-text output, <stem>.edition.json): every live
segment line whose text differs from the target line is replaced, three ops per
line, sent highest position first:

    insert   new text at s+1          (strictly inside the line: stays in its span)
    delete   s+1+len(new) .. e+len    (the old remainder; the line is never emptied)
    delete   s .. s+1                 (the old first character)

Nothing is sent before the whole sequence has been replayed with the backend's own
span arithmetic (vendored below) and shown to give exactly the target content, every
line selecting its target text, the spans still tiling the content, and every TOC
span equal to the target TOC's. Segments, their ids, references and alignments stay
as they are. A segment whose number of lines changed is refused.

    python3 patch_live_segments.py <vault file> <parser edition.json> <parser toc.json>            # dry run
    python3 patch_live_segments.py <vault file> <parser edition.json> <parser toc.json> --execute  # send

Credentials: WEBUDDHIST_API_KEY (+ WEBUDDHIST_API_BASE, WEBUDDHIST_APP) in the environment.
"""
import argparse, datetime, json, os, pathlib, re, sys, urllib.error, urllib.request

BASE = (os.environ.get("WEBUDDHIST_API_BASE") or "https://library.webuddhist.com").rstrip("/")


# --- the backend's span arithmetic, copied from edition-spacing-fix/scripts/spacing_fix.py,
# --- itself vendored from openpecha-backend database/span_database.py @ 7fa2564 (2026-09-28).
def adjust_continuous_for_insert(start, end, insert_pos, insert_len):
    if insert_pos == 0 and start == 0:
        return (start, end + insert_len)
    if insert_pos <= start:
        return (start + insert_len, end + insert_len)
    if insert_pos <= end:
        return (start, end + insert_len)
    return (start, end)


def adjust_annotation_for_insert(start, end, insert_pos, insert_len):
    if insert_pos <= start:
        return (start + insert_len, end + insert_len)
    if insert_pos < end:
        return (start, end + insert_len)
    return (start, end)


def adjust_span_for_delete(start, end, del_start, del_end):
    del_len = del_end - del_start
    if del_end <= start:
        return (start - del_len, end - del_len)
    if del_start >= end:
        return (start, end)
    if del_start <= start and del_end >= end:
        return None
    if del_start <= start < del_end < end:
        return (del_start, end - del_len)
    if start < del_start < end <= del_end:
        return (start, del_start)
    if start < del_start and del_end < end:
        return (start, end - del_len)
    return (start, end)


def apply_spans(spans, op, continuous):
    out = []
    for s in spans:
        if s is None:
            out.append(None)
        elif op["type"] == "insert":
            f = adjust_continuous_for_insert if continuous else adjust_annotation_for_insert
            out.append(f(s[0], s[1], op["position"], len(op["text"])))
        else:
            out.append(adjust_span_for_delete(s[0], s[1], op["start"], op["end"]))
    return out


def apply_text(text, op):
    if op["type"] == "insert":
        return text[:op["position"]] + op["text"] + text[op["position"]:]
    return text[:op["start"]] + text[op["end"]:]


# --- api
def call(method, path, body=None):
    h = {"Accept": "application/json", "X-Application": os.environ.get("WEBUDDHIST_APP") or "webuddhist",
         "X-API-Key": os.environ["WEBUDDHIST_API_KEY"]}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:800]


def get(path):
    st, d = call("GET", path)
    if st != 200:
        sys.exit(f"GET {path} -> {st} {d}")
    return d


def live_state(eid):
    c = get(f"/v2/editions/{eid}/content")
    content = c if isinstance(c, str) else c.get("content", "")
    segs, off = [], 0
    while True:
        d = get(f"/v2/editions/{eid}/segmentation/segments?limit=500&offset={off}")
        segs += d["items"]
        if not d.get("has_more") or not d["items"]:
            break
        off += len(d["items"])
    tocs = get(f"/v2/editions/{eid}/table-of-contents")
    return content, segs, (tocs if isinstance(tocs, list) else [tocs])


def toc_spans(sections):
    out = []
    for s in sections:
        out.append((s["span"]["start"], s["span"]["end"]))
        out += toc_spans(s.get("subsections") or s.get("sections") or [])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("note"); ap.add_argument("edition_json"); ap.add_argument("toc_json")
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args()

    fm = re.match(r"---\n(.*?)\n---\n", pathlib.Path(a.note).read_text(encoding="utf-8"), re.S).group(1)
    eid = re.search(r"(?m)^edition_id:\s*(\S+)", fm).group(1)
    target = json.loads(pathlib.Path(a.edition_json).read_text(encoding="utf-8"))
    tcontent = target["content"]
    tsegs = {s["reference"]: s for s in target["segmentation"]["segments"]}
    ttoc = json.loads(pathlib.Path(a.toc_json).read_text(encoding="utf-8"))
    ttoc_spans = sorted(toc_spans(ttoc.get("sections") or []))

    live, segs, tocs = live_state(eid)
    print(f"edition {eid} @ {BASE}: live {len(live)} chars, {len(segs)} segments; target {len(tcontent)} chars, {len(tsegs)} segments")
    if sorted(tsegs) != sorted(s["reference"] for s in segs):
        sys.exit("ABORT: the target's segment references differ from the live segmentation")

    rows, changes = [], []          # rows: every live line (ref, idx, start, end, target text)
    for s in segs:
        t = tsegs[s["reference"]]
        if len(t["lines"]) != len(s["lines"]):
            sys.exit(f"ABORT: ^{s['reference']} has {len(s['lines'])} live lines, {len(t['lines'])} in the target")
        for i, (ll, tl) in enumerate(zip(s["lines"], t["lines"])):
            want = tcontent[tl["start"]:tl["end"]]
            rows.append((s["reference"], i, ll["start"], ll["end"], want))
            if live[ll["start"]:ll["end"]] != want:
                changes.append((s["reference"], i, ll["start"], ll["end"], want))
    if not changes:
        print("nothing to do: every live line already equals the target"); return
    print(f"lines to replace: {len(changes)} in segments {sorted({c[0] for c in changes}, key=lambda r: [int(x) for x in r.split('-')])}")

    ops = []
    for ref, i, s, e, new in sorted(changes, key=lambda c: c[2], reverse=True):
        if e - s < 2 or not new:
            sys.exit(f"ABORT: ^{ref}[{i}] too short to replace in place ({e - s} → {len(new)} chars)")
        L = len(new)
        ops += [{"type": "insert", "position": s + 1, "text": new, "_l": f"^{ref}[{i}]"},
                {"type": "delete", "start": s + 1 + L, "end": e + L, "_l": f"^{ref}[{i}]"},
                {"type": "delete", "start": s, "end": s + 1, "_l": f"^{ref}[{i}]"}]

    # replay the backend before sending anything
    sim = live
    lspans = [(r[2], r[3]) for r in rows]
    tspans = [sp for t in tocs for sp in toc_spans(t.get("sections") or [])]
    for op in ops:
        o = {k: v for k, v in op.items() if not k.startswith("_")}
        lspans = apply_spans(lspans, o, True); tspans = apply_spans(tspans, o, False); sim = apply_text(sim, o)
    problems = []
    if sim != tcontent:
        problems.append("replayed content differs from the target content")
    if any(sp is None for sp in lspans):
        problems.append("a line span would be dropped")
    else:
        bad = [f"^{r[0]}[{r[1]}]" for r, sp in zip(rows, lspans) if sim[sp[0]:sp[1]] != r[4]]
        if bad:
            problems.append(f"{len(bad)} lines would not select their target text: {bad[:5]}")
        cov = sorted(lspans)
        if cov[0][0] != 0 or cov[-1][1] != len(sim) or any(cov[k][1] != cov[k + 1][0] for k in range(len(cov) - 1)):
            problems.append("line spans would no longer tile the content")
    if any(sp is None for sp in tspans) or sorted(tspans) != ttoc_spans:
        problems.append("TOC spans would not equal the target TOC's")
    if problems:
        for p in problems:
            print("  ✗", p)
        sys.exit("ABORT: simulation failed — nothing sent")
    print(f"simulation: content == target ✓  all {len(rows)} lines select their target text ✓  "
          f"spans tile ✓  {len(tspans)} TOC spans == target ✓")
    print(f"plan: {len(ops)} PATCH calls, highest position first; length {len(live)} → {len(sim)}")

    if not a.execute:
        print("dry run: nothing sent. Re-run with --execute."); return

    log = pathlib.Path("0-INBOX/temp") / f"patch-live-{eid}.log.jsonl"
    with log.open("a", encoding="utf-8") as fh:
        for k, op in enumerate(ops, 1):
            body = {x: v for x, v in op.items() if not x.startswith("_")}
            st, d = call("PATCH", f"/v2/editions/{eid}/content", body)
            fh.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "line": op["_l"],
                                 "op": {x: (v if x != "text" else v[:40] + "…") for x, v in body.items()},
                                 "status": st}, ensure_ascii=False) + "\n")
            if st not in (200, 204):
                sys.exit(f"op {k}/{len(ops)} {op['_l']} -> {st} {d}\nStopped; ops before this one landed (see {log}).")
            print(f"  {k}/{len(ops)} {op['_l']} {body['type']} ok")
    live2, segs2, tocs2 = live_state(eid)
    ok_c = live2 == tcontent
    ok_l = all(live2[ll["start"]:ll["end"]] == tcontent[tl["start"]:tl["end"]]
               for s in segs2 for ll, tl in zip(s["lines"], tsegs[s["reference"]]["lines"]))
    ok_t = sorted(sp for t in tocs2 for sp in toc_spans(t.get("sections") or [])) == ttoc_spans
    print(f"verify: content == target {ok_c}; every line == target {ok_l}; segments {len(segs2)}; TOC spans == target {ok_t}")
    if not (ok_c and ok_l and ok_t):
        sys.exit("VERIFY FAILED — inspect before doing anything else")


if __name__ == "__main__":
    main()
