#!/usr/bin/env python3
"""upload_commentary.py — lint → parse → upload one commentary to the WeBuddhist library.

The commentary counterpart of `root-text-upload` and `translation-upload`. It
shells out to the vault's linter-commentary and parser-commentary (one copy, in
4-SYSTEM/scripts/ — this script finds it rather than carrying a second), then
sends the parser's payloads to the live v2 API:

    1. POST /v2/texts                                        <- <stem>.text.json       -> text_id
       (carries commentary_of = the root's text_id; settable only at creation)
    2. POST /v2/texts/{text_id}/editions                     <- <stem>.edition.json    -> edition_id
    3. POST /v2/editions/{edition_id}/table-of-contents      <- <stem>.toc.json        -> toc_id
    4. PUT  /v2/editions/{edition_id}/alignments/{root_edition_id}
                                                             <- <stem>.alignment.json  (as written)

Alignment direction. The COMMENTARY edition is the source side and the ROOT
edition the target, with the parser's pairs sent unchanged
(source_segment_reference = commentary block, target_segment_reference = root
block). That is how the commentaries already live on the library are stored
(e.g. the 21-taras commentaries: GET editions/<commentary>/alignments/<root>
returns the pairs, the reverse returns none). It is the opposite of
`translation-upload`, which puts the root on the source side.

A commentary is aligned to the ROOT TEXT only — never to another commentary,
even one it translates. Segment counts between two commentaries on the same
root may differ freely.

Footnotes. The backend has no footnote annotations yet, so `[^n]` markers and
`[^n]: …` notes must not reach the content, segmentation or TOC. The parser
drops them; the checks below confirm none leaked.

Dry-run is the DEFAULT: it lints, parses, runs the checks (read-only calls to
the live API unless --no-live), prints the plan and sends nothing. --execute
sends the calls, patches text_id / edition_id / toc_id / aligned_to_edition_id
into the note's frontmatter after each success, and appends a receipt to the
ledger after every call — so an interrupted run resumes instead of duplicating
(a step whose id is already in the frontmatter is skipped).

Nothing here is idempotent on the server: POST /v2/texts will happily create a
second copy of a text. The ledger, the frontmatter and the duplicate check
against the root's live `commentaries` list are what make re-running safe.

Credentials come from the environment and are never written to disk:
    WEBUDDHIST_API_KEY    X-API-Key      (required for --execute)
    WEBUDDHIST_APP        X-Application  (optional)
    WEBUDDHIST_API_BASE   default https://library.webuddhist.com

Usage (from the vault root):
    python3 4-SYSTEM/Skills/commentary-upload/scripts/upload_commentary.py "<commentary.md>"            # dry run
    python3 4-SYSTEM/Skills/commentary-upload/scripts/upload_commentary.py "<commentary.md>" --execute  # after confirmation
    python3 4-SYSTEM/Skills/commentary-upload/scripts/upload_commentary.py "<commentary.md>" --verify   # GET everything back
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

SKILL_DIR = pathlib.Path(__file__).resolve().parent
VAULT = pathlib.Path(os.environ.get("VAULT_ROOT", pathlib.Path.cwd()))
LEDGER = pathlib.Path(os.environ.get("LEDGER_PATH", SKILL_DIR / "upload_ledger.json"))
BASE = os.environ.get("WEBUDDHIST_API_BASE", "https://library.webuddhist.com").rstrip("/")

YAML_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
BLOCK_ID_RE = re.compile(r"\^([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\s*$", re.MULTILINE)
FOOTNOTE_DEF_RE = re.compile(r"^[ \t]*\[\^[^\]\s]+\]:[ \t]*(.*)$", re.MULTILINE)


class ApiError(RuntimeError):
    pass


def find_tools():
    """Locate linter-commentary and parser-commentary (one copy per vault)."""
    for base in [VAULT / "4-SYSTEM" / "scripts", SKILL_DIR, *SKILL_DIR.parents[:4]]:
        for linter in sorted(base.rglob("linter-commentary/lint_text_input.py")):
            parser = linter.parent.parent / "parser-commentary" / "parser.py"
            if parser.exists():
                return linter, parser
    sys.exit("could not find linter-commentary/lint_text_input.py and parser-commentary/parser.py — "
             "install them under 4-SYSTEM/scripts/")


# ---------------------------------------------------------------- helpers

def read_note(path):
    import yaml
    text = path.read_text(encoding="utf-8")
    m = YAML_RE.match(text)
    if not m:
        raise ValueError(f"no frontmatter in {path}")
    return (yaml.safe_load(m.group(1)) or {}), text[m.end():]


def resolve_vault_path(val, from_path):
    p = pathlib.Path(str(val))
    for base in [VAULT, from_path.parent, *from_path.parents]:
        if (base / p).exists():
            return base / p
    return None


def patch_fm(path, updates):
    """Set key: value pairs in the note's frontmatter (replace or append)."""
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines[0].strip() == "---"
    close = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    for key, value in updates.items():
        for i in range(1, close):
            if re.match(rf"^{re.escape(key)}\s*:", lines[i]):
                lines[i] = f"{key}: {value}"
                break
        else:
            lines.insert(close, f"{key}: {value}")
            close += 1
        print(f"  PATCHED {path.name}: {key} = {value}")
    path.write_text("\n".join(lines), encoding="utf-8")


def headers():
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    key = os.environ.get("WEBUDDHIST_API_KEY", "")
    if key:
        h["X-API-Key"] = key
    app = os.environ.get("WEBUDDHIST_APP", "")
    if app:
        h["X-Application"] = app
    return h


def run_tool(argv):
    # flush so the child's output lands below the header that introduces it
    sys.stdout.flush()
    return subprocess.run(argv, cwd=VAULT)


def call(method, url, body=None, timeout=60):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:800]
        raise ApiError(f"HTTP {exc.code} {method} {url}\n         {detail}") from None
    except urllib.error.URLError as exc:
        raise ApiError(f"network error {method} {url}: {exc.reason}") from None


def paged(url):
    out, offset = [], 0
    sep = "&" if "?" in url else "?"
    while True:
        d = call("GET", f"{url}{sep}limit=200&offset={offset}")
        items = d.get("items", []) if isinstance(d, dict) else (d or [])
        out += items
        if not (isinstance(d, dict) and d.get("has_more")) or not items:
            return out
        offset += len(items)


def live_segment_refs(edition_id):
    return [s["reference"] for s in paged(f"{BASE}/v2/editions/{edition_id}/segmentation/segments")]


def live_alignment_pairs(src_edition, tgt_edition):
    items = paged(f"{BASE}/v2/editions/{src_edition}/alignments/{tgt_edition}")
    return [(i["source_segment"]["reference"], i["target_segment"]["reference"]) for i in items]


def load_ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}


def save_ledger(ledger):
    tmp = LEDGER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, LEDGER)


def count_toc(toc):
    def walk(nodes):
        return sum(1 + walk(n.get("subsections", [])) for n in nodes)
    return walk(toc.get("sections", []))


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("note", help="the commentary note (file_type: commentary)")
    ap.add_argument("--execute", action="store_true", help="send the requests (default: dry run)")
    ap.add_argument("--skip-lint", action="store_true", help="reuse the existing lint output")
    ap.add_argument("--no-live", action="store_true", help="skip the read-only checks against the live API")
    ap.add_argument("--verify", action="store_true", help="only GET the live state of this commentary and exit")
    args = ap.parse_args(argv)

    linter, parser_py = find_tools()
    lint_out = linter.parent / "output"
    parse_out = parser_py.parent / "output"

    note = pathlib.Path(args.note)
    if not note.exists():
        sys.exit(f"not found: {note}")
    stem = note.stem
    fm, body = read_note(note)
    if fm.get("file_type") != "commentary":
        sys.exit(f"{note.name}: file_type is {fm.get('file_type')!r}, not 'commentary'.")
    if fm.get("translation_of"):
        sys.exit(f"{note.name}: carries translation_of — a commentary is uploaded as a commentary of the "
                 f"root text only; remove translation_of first.")
    root_path = resolve_vault_path(fm.get("root_text", ""), note)
    if not root_path:
        sys.exit(f"{note.name}: root_text {fm.get('root_text')!r} does not resolve")
    root_fm, root_body = read_note(root_path)
    root_tid, root_eid = root_fm.get("text_id"), root_fm.get("edition_id")
    if not (root_tid and root_eid):
        sys.exit(f"root {root_path.name} has no text_id/edition_id — upload the root text first")
    lang = fm.get("lang_tag")

    if args.verify:
        tid, eid, toc_id = fm.get("text_id"), fm.get("edition_id"), fm.get("toc_id")
        print(f"text_id {tid}  edition_id {eid}  toc_id {toc_id}  root {root_tid}/{root_eid}")
        if tid:
            t = call("GET", f"{BASE}/v2/texts/{tid}")
            print(f"  text: lang={t.get('language')} commentary_of={t.get('commentary_of')} "
                  f"translation_of={t.get('translation_of')} editions={t.get('editions')}")
        if eid:
            refs = live_segment_refs(eid)
            print(f"  edition segments: {len(refs)}  {refs[:4]} … {refs[-2:]}")
            pairs = live_alignment_pairs(eid, root_eid)
            print(f"  alignment {eid} -> root {root_eid}: {len(pairs)} pairs  {pairs[:3]}")
            for t in call("GET", f"{BASE}/v2/editions/{eid}/table-of-contents") or []:
                print(f"  toc {t.get('id')}: {count_toc(t)} nodes")
        return 0

    # ---- 1. lint
    lint_json = lint_out / f"{stem}.lint.json"
    lint_err = lint_out / f"{stem}.lint.errors.json"
    if args.skip_lint:
        if not lint_json.exists():
            sys.exit(f"--skip-lint but {lint_json} does not exist")
        print(f"== lint == (skipped, reusing {lint_json.name})")
    else:
        print("== lint ==")
        if lint_err.exists():
            lint_err.unlink()
        r = run_tool([sys.executable, str(linter), str(note)])
        if lint_err.exists() or r.returncode != 0 or not lint_json.exists():
            sys.exit("ABORT: lint failed (see above)")
        fm, body = read_note(note)  # the linter may normalise frontmatter

    # ---- 2. parse
    print("\n== parse ==")
    r = run_tool([sys.executable, str(parser_py), str(note), str(lint_json)])
    if r.returncode != 0:
        sys.exit("ABORT: parse failed (see above)")
    payloads = {}
    for kind in ("text", "edition", "toc", "alignment"):
        p = parse_out / stem / f"{stem}.{kind}.json"
        if not p.exists():
            sys.exit(f"ABORT: parser did not write {p}")
        payloads[kind] = json.loads(p.read_text(encoding="utf-8"))

    text = payloads["text"]
    edition = payloads["edition"]
    content = edition["content"]
    segs = edition["segmentation"]["segments"]
    refs = [s["reference"] for s in segs]
    toc = payloads["toc"]
    pairs = payloads["alignment"]["alignments"]
    align_body = {"alignments": pairs}

    # ---- 3. checks
    print("\n== checks ==")
    problems = []
    if text.get("commentary_of") != root_tid:
        problems.append(f"text payload commentary_of={text.get('commentary_of')!r}, expected the root {root_tid}")
    if text.get("translation_of"):
        problems.append("text payload carries translation_of")
    # The library copies alt_titles into the text's title map, and a title must be
    # unique per language: a cross-language alt title (e.g. the English title on
    # the Tibetan commentary) claims that title and blocks the other commentary.
    # It cannot be removed afterwards (PATCH ignores [] and rejects null).
    foreign = sorted({k for a in text.get("alt_titles") or [] for k in a} - {text.get("language")})
    if foreign:
        problems.append(f"alt_titles in other languages {foreign} would become titles of this text on the "
                        f"library and can block another commentary with that title — drop them")
    if not content.strip():
        problems.append("edition content is empty")
    if len(refs) != len(set(refs)):
        problems.append(f"duplicate segment references: {sorted({r for r in refs if refs.count(r) > 1})[:6]}")
    spans = [sp for s in segs for sp in s["lines"]]
    if not spans or spans[0]["start"] != 0 or spans[-1]["end"] != len(content) or \
            any(a["end"] != b["start"] for a, b in zip(spans, spans[1:])):
        problems.append("segment spans do not cover the content contiguously")
    # footnotes must not leak into content, segmentation or TOC
    toc_str = json.dumps(toc, ensure_ascii=False)
    notes = [n.strip() for n in FOOTNOTE_DEF_RE.findall(body) if n.strip()]
    leaked = [n[:40] for n in notes if n[:35] in content or n[:35] in toc_str]
    if re.search(r"\[\^[^\]\s]+\]", content + toc_str):
        problems.append("footnote markers ([^n]) found in edition content or TOC")
    if leaked:
        problems.append(f"footnote notes leaked into content/TOC: {leaked[:3]}")
    for art in ("![[", "<small>", "**"):
        if art in content:
            problems.append(f"markup {art!r} left in edition content")
    n_roots, n_nodes = len(toc.get("sections", [])), count_toc(toc)
    if n_roots != 1:
        problems.append(f"toc has {n_roots} root sections, expected 1 (the H1)")
    # alignment: commentary blocks -> root blocks
    if not pairs:
        problems.append("alignment is empty")
    src_bad = sorted({p["source_segment_reference"] for p in pairs} - set(refs))
    root_local = set(BLOCK_ID_RE.findall(root_body))
    tgt_bad = sorted({p["target_segment_reference"] for p in pairs} - root_local)
    if src_bad:
        problems.append(f"alignment sources not in this edition: {src_bad[:6]}")
    if tgt_bad:
        problems.append(f"alignment targets not in the root file: {tgt_bad[:6]}")

    if not args.no_live:
        try:
            rt = call("GET", f"{BASE}/v2/texts/{root_tid}")
            if root_eid not in (rt.get("editions") or []):
                problems.append(f"live root {root_tid} does not list edition {root_eid}")
            live_root = set(live_segment_refs(root_eid))
            missing = sorted({p["target_segment_reference"] for p in pairs} - live_root)
            if missing:
                problems.append(f"alignment targets not in the LIVE root segmentation: {missing[:6]}")
            else:
                print(f"  live root {root_eid}: {len(live_root)} segments, every alignment target present ✓")
            # duplicate guard: an existing commentary on this root in the same language and title
            my_title = (text.get("title") or {}).get(text.get("language"), "")
            for cid in rt.get("commentaries") or []:
                if cid == fm.get("text_id"):
                    continue
                c = call("GET", f"{BASE}/v2/texts/{cid}")
                if c.get("language") == text.get("language") and \
                        (c.get("title") or {}).get(c.get("language")) == my_title:
                    problems.append(f"live commentary {cid} on this root already has this language and title — "
                                    f"set text_id: {cid} in the note instead of creating a duplicate")
            print(f"  live root {root_tid}: {len(rt.get('commentaries') or [])} existing commentar(ies), "
                  f"no duplicate of this one ✓" if not any('already has this language' in p for p in problems)
                  else "")
            if fm.get("text_id"):
                t = call("GET", f"{BASE}/v2/texts/{fm['text_id']}")
                if t.get("commentary_of") != root_tid:
                    problems.append(f"live text {fm['text_id']} has commentary_of={t.get('commentary_of')!r}, "
                                    f"not the root {root_tid}")
                if t.get("editions") and not fm.get("edition_id"):
                    problems.append(f"live text {fm['text_id']} already has editions {t.get('editions')} — "
                                    f"set edition_id in the note or remove the stale edition first")
        except ApiError as exc:
            problems.append(f"live check failed: {exc}")

    n_verse = sum(1 for s in segs if s.get("type") == "verse")
    print(f"  {len(content)} chars, {len(segs)} segments ({len(segs) - n_verse} paragraph, {n_verse} verse)")
    print(f"  toc: 1 root section, {n_nodes} nodes; alignment: {len(pairs)} pairs "
          f"({len({p['source_segment_reference'] for p in pairs})} commentary segments -> "
          f"{len({p['target_segment_reference'] for p in pairs})} root segments)")
    print(f"  footnotes: {len(notes)} notes in the source, none in the payloads" if notes and not leaked
          else "  footnotes: none in the source")
    for p in problems:
        print(f"  !! {p}")
    if problems:
        sys.exit("ABORT: checks failed")

    # ---- 4. plan / execute
    tid = fm.get("text_id") or None
    eid = fm.get("edition_id") or None
    toc_id = fm.get("toc_id") or None
    aligned = fm.get("aligned_to_edition_id") == root_eid
    plan = [
        ("text", "POST", f"{BASE}/v2/texts", text, "skip (text_id present)" if tid else "create"),
        ("edition", "POST", f"{BASE}/v2/texts/{tid or '{text_id}'}/editions", edition,
         "skip (edition_id present)" if eid else "create"),
        ("toc", "POST", f"{BASE}/v2/editions/{eid or '{edition_id}'}/table-of-contents", toc,
         "skip (toc_id present)" if toc_id else "create"),
        ("alignment", "PUT", f"{BASE}/v2/editions/{eid or '{edition_id}'}/alignments/{root_eid}", align_body,
         "skip (already aligned)" if aligned else "put"),
    ]

    print(f"\n== {'EXECUTE' if args.execute else 'DRY RUN'} ==  host {BASE}")
    print(f"  commentary of root text {root_tid} (edition {root_eid}); language {text.get('language')}")
    for step, method, url, payload, action in plan:
        nbytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        print(f"  {step:<9} {method:<4} {url}  ({nbytes} bytes)  -> {action}")
    if not args.execute:
        print("\ndry run: nothing sent, frontmatter untouched by this script. "
              "Re-run with --execute after confirmation.")
        return 0
    if not os.environ.get("WEBUDDHIST_API_KEY"):
        sys.exit("WEBUDDHIST_API_KEY is not set")

    ledger = load_ledger()
    entry = ledger.setdefault(stem, {})
    entry.update({"lang_tag": lang, "file_type": "commentary", "source_file": str(note),
                  "root_text_id": root_tid, "root_edition_id": root_eid})

    def receipt(step, **kw):
        entry.setdefault("log", []).append(
            {"step": step, "ts": _dt.datetime.now().isoformat(timespec="seconds"), **kw})
        save_ledger(ledger)

    try:
        if not tid:
            tid = call("POST", f"{BASE}/v2/texts", text)["id"]
            entry["text_id"] = tid
            receipt("text", text_id=tid)
            patch_fm(note, {"text_id": tid})
            print(f"  text_id    {tid}")
        entry["text_id"] = tid
        if not eid:
            eid = call("POST", f"{BASE}/v2/texts/{tid}/editions", edition)["id"]
            entry["edition_id"] = eid
            receipt("edition", edition_id=eid, segments=len(segs), chars=len(content))
            patch_fm(note, {"edition_id": eid})
            print(f"  edition_id {eid}  ({len(content)} chars, {len(segs)} segments)")
        entry["edition_id"] = eid
        if not toc_id:
            res = call("POST", f"{BASE}/v2/editions/{eid}/table-of-contents", toc)
            toc_id = res.get("id") or res.get("toc_id")
            entry["toc_id"] = toc_id
            receipt("toc", toc_id=toc_id, nodes=n_nodes)
            patch_fm(note, {"toc_id": toc_id})
            print(f"  toc_id     {toc_id}  ({n_nodes} nodes)")
        if not aligned:
            call("PUT", f"{BASE}/v2/editions/{eid}/alignments/{root_eid}", align_body)
            entry["aligned_to_edition_id"] = root_eid
            receipt("alignment", pairs=len(pairs), root_edition_id=root_eid)
            patch_fm(note, {"aligned_to_edition_id": root_eid})
            print(f"  aligned    {len(pairs)} pairs -> root edition {root_eid}")
    except ApiError as exc:
        receipt("error", error=str(exc)[:400])
        print(f"\nFAIL {exc}\nledger: {LEDGER}  — the ids already assigned are in the note; re-run to resume.",
              file=sys.stderr)
        return 1
    save_ledger(ledger)
    print(f"\ndone. ledger: {LEDGER}\nverify with: --verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
