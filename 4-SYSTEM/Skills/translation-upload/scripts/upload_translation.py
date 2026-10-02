#!/usr/bin/env python3
"""upload_translation.py — lint → parse → upload one translation note to the WeBuddhist library.

The translation-side counterpart of the root-text chain this vault already
has (the bundled linter-root-text + parser-root-text). It shells out to
both, then sends the parser's payloads to the live v2 API:

    1. POST /v2/texts                                     <- <stem>.text.json      (SKIPPED when the
                                                             note already carries text_id — a translation
                                                             text that exists is reused, never re-created:
                                                             `translation_of` is settable only at creation)
    2. POST /v2/texts/{text_id}/editions                  <- <stem>.edition.json   -> edition_id
    3. PUT  /v2/editions/{root_edition}/alignments/{edition_id}
                                                          <- <stem>.alignment.json (pairs re-oriented so
                                                             the ROOT edition is the source, the same
                                                             direction the library already displays)
    4. POST /v2/editions/{edition_id}/table-of-contents   <- <stem>.toc.json       -> toc_id

Dry-run is the DEFAULT: it lints, parses, checks the payloads against the
live root segmentation (GET only), prints the plan and sends nothing.
--execute sends the calls, patches `edition_id` / `toc_id` /
`aligned_to_edition_id` into the note's frontmatter after each success, and
appends a receipt to the upload ledger after every call —
so an interrupted run resumes instead of duplicating (a step whose id is
already in the frontmatter is skipped).

Credentials come from the environment and are never written to disk:
    WEBUDDHIST_API_KEY    X-API-Key      (required for --execute and for the live checks)
    WEBUDDHIST_APP        X-Application  (optional)
    WEBUDDHIST_API_BASE   default https://library.webuddhist.com

Usage (from the vault root):
    python3 <skill>/scripts/upload_translation.py "<translation.md>"              # dry run
    python3 <skill>/scripts/upload_translation.py "<translation.md>" --execute    # after human confirmation
    python3 <skill>/scripts/upload_translation.py "<translation.md>" --verify     # GET everything back
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

# The linter and parser ship inside this skill folder, so the script works
# wherever the skill is installed. The ledger stays with them so that receipts
# travel with the tool that wrote them; override with LEDGER_PATH if a vault
# prefers to keep it elsewhere.
SKILL_DIR = pathlib.Path(__file__).resolve().parent
VAULT = pathlib.Path(os.environ.get("VAULT_ROOT", pathlib.Path.cwd()))
LINTER = SKILL_DIR / "linter-root-text" / "lint_text_input.py"
LINT_OUT = SKILL_DIR / "linter-root-text" / "output"
PARSER = SKILL_DIR / "parser-root-text" / "parser.py"
PARSE_OUT = SKILL_DIR / "parser-root-text" / "output"
LEDGER = pathlib.Path(os.environ.get("LEDGER_PATH", SKILL_DIR / "upload_ledger.json"))
BASE = os.environ.get("WEBUDDHIST_API_BASE", "https://library.webuddhist.com").rstrip("/")

YAML_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


class ApiError(RuntimeError):
    pass


# ---------------------------------------------------------------- helpers

def read_fm(path):
    import yaml
    text = path.read_text(encoding="utf-8")
    m = YAML_RE.match(text)
    if not m:
        raise ValueError(f"no frontmatter in {path}")
    return yaml.safe_load(m.group(1)) or {}


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


def resolve_vault_path(val, from_path):
    p = pathlib.Path(val)
    for base in [from_path.parent, *from_path.parents]:
        if (base / p).exists():
            return base / p
    for base in from_path.parents:
        hits = list(base.rglob(p.name))
        if hits:
            return hits[0]
    return None


def headers():
    key = os.environ.get("WEBUDDHIST_API_KEY", "")
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if key:
        h["X-API-Key"] = key
    app = os.environ.get("WEBUDDHIST_APP", "")
    if app:
        h["X-Application"] = app
    return h


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


def load_ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}


def save_ledger(ledger):
    tmp = LEDGER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, LEDGER)


def live_segment_refs(edition_id):
    out, offset = [], 0
    while True:
        d = call("GET", f"{BASE}/v2/editions/{edition_id}/segmentation/segments?limit=200&offset={offset}")
        items = d.get("items", []) if isinstance(d, dict) else d
        out += [s["reference"] for s in items]
        if not (isinstance(d, dict) and d.get("has_more")):
            return out
        offset += len(items)


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("note", help="the translation note (file_type: translation)")
    ap.add_argument("--execute", action="store_true", help="send the requests (default: dry run)")
    ap.add_argument("--skip-lint", action="store_true", help="reuse the existing lint output")
    ap.add_argument("--no-live", action="store_true", help="skip the read-only check against the live root")
    ap.add_argument("--verify", action="store_true", help="only GET the live state of this translation and exit")
    args = ap.parse_args(argv)

    note = pathlib.Path(args.note)
    if not note.exists():
        sys.exit(f"not found: {note}")
    stem = note.stem
    fm = read_fm(note)
    if fm.get("file_type") != "translation":
        sys.exit(f"{note.name}: file_type is {fm.get('file_type')!r}, not 'translation'")
    root_path = resolve_vault_path(str(fm.get("root_text", "")), note)
    if not root_path:
        sys.exit(f"{note.name}: root_text {fm.get('root_text')!r} does not resolve")
    root_fm = read_fm(root_path)
    root_text_id, root_edition_id = root_fm.get("text_id"), root_fm.get("edition_id")
    if not (root_text_id and root_edition_id):
        sys.exit(f"{root_path.name}: root text has no text_id/edition_id — upload the root first")
    lang = fm.get("lang_tag")
    key = f"{stem}"

    if args.verify:
        tid, eid = fm.get("text_id"), fm.get("edition_id")
        print(f"text_id {tid}  edition_id {eid}")
        if tid:
            t = call("GET", f"{BASE}/v2/texts/{tid}")
            print(f"  text: title={t.get('title')} lang={t.get('language')} translation_of={t.get('translation_of')} editions={t.get('editions')}")
        if eid:
            refs = live_segment_refs(eid)
            print(f"  edition segments: {len(refs)}  {refs[:4]} … {refs[-2:]}")
            # the GET is paginated: {items: [{source_segment: {...reference}, target_segment: {...}}], has_more}
            pairs, off = [], 0
            while True:
                al = call("GET", f"{BASE}/v2/editions/{root_edition_id}/alignments/{eid}?limit=200&offset={off}")
                items = al.get("items", []) if isinstance(al, dict) else al
                pairs += [(i["source_segment"]["reference"], i["target_segment"]["reference"]) for i in items]
                if not (isinstance(al, dict) and al.get("has_more")):
                    break
                off += len(items)
            identity = all(a == b for a, b in pairs) and [a for a, _ in pairs] == refs
            print(f"  alignment root->this: {len(pairs)} pairs, identity over every segment: {identity}")
            toc = call("GET", f"{BASE}/v2/editions/{eid}/table-of-contents")
            for t in toc or []:
                secs = t.get("sections", [])
                print(f"  toc {t.get('id')}: {len(secs)} root section(s), "
                      f"{sum(len(s.get('subsections', [])) for s in secs)} subsections: "
                      + " | ".join(ss['title'].get(lang, '?') for s in secs for ss in s.get('subsections', [])))
        return 0

    # ---- 1. lint
    lint_json = LINT_OUT / f"{stem}.lint.json"
    lint_err = LINT_OUT / f"{stem}.lint.errors.json"
    if args.skip_lint:
        if not lint_json.exists():
            sys.exit(f"--skip-lint but {lint_json} does not exist")
        print(f"== lint == (skipped, reusing {lint_json.name})")
    else:
        print("== lint ==")
        if lint_err.exists():
            lint_err.unlink()
        r = subprocess.run([sys.executable, str(LINTER), str(note)], cwd=VAULT)
        if lint_err.exists() or r.returncode != 0 or not lint_json.exists():
            sys.exit("ABORT: lint failed (see above)")

    # ---- 2. parse
    print("\n== parse ==")
    r = subprocess.run([sys.executable, str(PARSER), str(note), str(lint_json)], cwd=VAULT)
    if r.returncode != 0:
        sys.exit("ABORT: parse failed (see above)")
    payloads = {}
    for kind in ("text", "edition", "toc", "alignment"):
        p = PARSE_OUT / f"{stem}.{kind}.json"
        if not p.exists():
            sys.exit(f"ABORT: parser did not write {p.name}")
        payloads[kind] = json.loads(p.read_text(encoding="utf-8"))

    edition = payloads["edition"]
    segs = edition["segmentation"]["segments"]
    refs = [s["reference"] for s in segs]
    # the parser's pairs are (source=this translation's block, target=the root block);
    # the library is fed root->translation, so re-orient them.
    pairs = [{"source_segment_reference": a["target_segment_reference"],
              "target_segment_reference": a["source_segment_reference"]}
             for a in payloads["alignment"]["alignments"]]
    align_body = {"alignments": pairs}
    toc = payloads["toc"]

    # ---- 3. checks
    print("\n== checks ==")
    problems = []
    if not edition["content"].strip():
        problems.append("edition content is empty")
    if len(refs) != len(set(refs)):
        problems.append("duplicate segment references")
    if [p["target_segment_reference"] for p in pairs] != refs:
        problems.append(f"alignment pairs ({len(pairs)}) do not cover the edition segments ({len(refs)}) one for one, in order")
    if [p["source_segment_reference"] for p in pairs] != refs:
        problems.append("alignment is not identity (translation ids differ from root ids)")
    for s in segs:
        for sp in s["lines"]:
            if not 0 <= sp["start"] <= sp["end"] <= len(edition["content"]):
                problems.append(f"segment {s['reference']} span out of range")
    n_sections = len(toc.get("sections", []))
    n_sub = sum(len(s.get("subsections", [])) for s in toc.get("sections", []))
    if n_sections != 1:
        problems.append(f"toc has {n_sections} root sections, expected 1 (the H1)")
    if not args.no_live:
        try:
            live = live_segment_refs(root_edition_id)
            if live != refs:
                only_live = sorted(set(live) - set(refs))[:6]
                only_here = sorted(set(refs) - set(live))[:6]
                problems.append(f"segment refs differ from the LIVE root ({len(live)} live vs {len(refs)} here); "
                                f"live-only {only_live}, here-only {only_here}")
            else:
                print(f"  live root {root_edition_id}: {len(live)} segments, references identical to this edition ✓")
            if fm.get("text_id"):
                t = call("GET", f"{BASE}/v2/texts/{fm['text_id']}")
                if t.get("translation_of") != root_text_id:
                    problems.append(f"live text {fm['text_id']} has translation_of={t.get('translation_of')!r}, not the root {root_text_id}")
                if t.get("editions"):
                    problems.append(f"live text {fm['text_id']} already has editions {t.get('editions')} — set edition_id in the note or delete the stale edition first")
                else:
                    print(f"  live text {fm['text_id']}: translation_of={root_text_id} ✓, no edition yet ✓")
        except ApiError as exc:
            problems.append(f"live check failed: {exc}")
    print(f"  {len(edition['content'])} chars, {len(segs)} segments, {len(pairs)} alignment pairs, "
          f"toc: 1 root section + {n_sub} subsections")
    for p in problems:
        print(f"  !! {p}")
    if problems:
        sys.exit("ABORT: checks failed")

    # ---- 4. plan / execute
    tid = fm.get("text_id") or None
    eid = fm.get("edition_id") or None
    toc_id = fm.get("toc_id") or None
    aligned = fm.get("aligned_to_edition_id") == root_edition_id
    plan = []
    plan.append(("text", "POST", f"{BASE}/v2/texts", payloads["text"], "skip (text_id present)" if tid else "create"))
    plan.append(("edition", "POST", f"{BASE}/v2/texts/{tid or '{text_id}'}/editions", edition, "skip (edition_id present)" if eid else "create"))
    plan.append(("alignment", "PUT", f"{BASE}/v2/editions/{root_edition_id}/alignments/{eid or '{edition_id}'}", align_body, "skip (already aligned)" if aligned else "put"))
    plan.append(("toc", "POST", f"{BASE}/v2/editions/{eid or '{edition_id}'}/table-of-contents", toc, "skip (toc_id present)" if toc_id else "create"))

    print(f"\n== {'EXECUTE' if args.execute else 'DRY RUN'} ==")
    for step, method, url, body, action in plan:
        nbytes = len(json.dumps(body, ensure_ascii=False).encode("utf-8"))
        print(f"  {step:<9} {method:<4} {url}  ({nbytes} bytes)  -> {action}")
    if not args.execute:
        print("\ndry run: nothing sent, frontmatter untouched. Re-run with --execute after confirmation.")
        return 0
    if not os.environ.get("WEBUDDHIST_API_KEY"):
        sys.exit("WEBUDDHIST_API_KEY is not set")

    ledger = load_ledger()
    entry = ledger.setdefault(key, {})
    entry.update({"lang_tag": lang, "root_text_id": root_text_id, "root_edition_id": root_edition_id})

    def receipt(step, **kw):
        entry.setdefault("log", []).append({"step": step, "ts": _dt.datetime.now().isoformat(timespec="seconds"), **kw})
        save_ledger(ledger)

    try:
        if not tid:
            res = call("POST", f"{BASE}/v2/texts", payloads["text"])
            tid = res["id"]
            entry["text_id"] = tid
            receipt("text", text_id=tid)
            patch_fm(note, {"text_id": tid})
            print(f"  text_id    {tid}")
        else:
            entry["text_id"] = tid
        if not eid:
            res = call("POST", f"{BASE}/v2/texts/{tid}/editions", edition)
            eid = res["id"]
            entry["edition_id"] = eid
            receipt("edition", edition_id=eid, segments=len(segs), chars=len(edition["content"]))
            patch_fm(note, {"edition_id": eid})
            print(f"  edition_id {eid}  ({len(edition['content'])} chars, {len(segs)} segments)")
        else:
            entry["edition_id"] = eid
        if not aligned:
            call("PUT", f"{BASE}/v2/editions/{root_edition_id}/alignments/{eid}", align_body)
            entry["aligned_to_edition_id"] = root_edition_id
            receipt("alignment", pairs=len(pairs), root_edition_id=root_edition_id)
            patch_fm(note, {"aligned_to_edition_id": root_edition_id})
            print(f"  aligned    {len(pairs)} pairs -> {root_edition_id}")
        if not toc_id:
            res = call("POST", f"{BASE}/v2/editions/{eid}/table-of-contents", toc)
            toc_id = res.get("id") or res.get("toc_id")
            entry["toc_id"] = toc_id
            receipt("toc", toc_id=toc_id, subsections=n_sub)
            patch_fm(note, {"toc_id": toc_id})
            print(f"  toc_id     {toc_id}  (1 root section + {n_sub} subsections)")
    except ApiError as exc:
        receipt("error", error=str(exc)[:400])
        print(f"\nFAIL {exc}\nledger: {LEDGER}  — the ids already assigned are in the note; re-run to resume.",
              file=sys.stderr)
        return 1
    save_ledger(ledger)
    print(f"\ndone. ledger: {LEDGER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
