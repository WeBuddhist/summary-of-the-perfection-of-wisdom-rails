#!/usr/bin/env python3
"""upload_root_text.py — lint → parse → upload one root text to the WeBuddhist library.

The root-text half of the chain whose translation half is `translation-upload`.
It shells out to that skill's bundled linter-root-text and parser-root-text
(there is only ever one copy of those in a vault — this script finds it rather
than carrying a second), then sends the parser's payloads to the live v2 API:

    1. POST /v2/texts                                   <- <stem>.text.json     -> text_id
    2. POST /v2/texts/{text_id}/editions                <- <stem>.edition.json  -> edition_id
    3. POST /v2/editions/{edition_id}/table-of-contents <- <stem>.toc.json      -> toc_id

No alignment step: a root text is the alignment target, not a side of one. Its
translations are attached afterwards, each by `translation-upload`, which needs
this file's `text_id` and `edition_id` — so the root is always published first.

Dry-run is the DEFAULT: it lints, parses, checks, prints the plan and sends
nothing. --execute sends the calls, patches `text_id` / `edition_id` / `toc_id`
into the note's frontmatter after each success, and appends a receipt to the
ledger after every call — so an interrupted run resumes instead of duplicating
(a step whose id is already in the frontmatter is skipped).

Nothing here is idempotent on the server: POST /v2/texts will happily create a
second copy of a text that is already there. The ledger and the frontmatter are
what make re-running safe.

Credentials come from the environment and are never written to disk:
    WEBUDDHIST_API_KEY    X-API-Key      (required for --execute and the live checks)
    WEBUDDHIST_APP        X-Application  (optional)
    WEBUDDHIST_API_BASE   default https://library.webuddhist.com

Usage (from the vault root):
    python3 <skill>/scripts/upload_root_text.py "<root-text.md>"            # dry run
    python3 <skill>/scripts/upload_root_text.py "<root-text.md>" --execute  # after human confirmation
    python3 <skill>/scripts/upload_root_text.py "<root-text.md>" --verify   # GET everything back
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

ROOT_FILE_TYPES = ("root-text", "edition")


class ApiError(RuntimeError):
    pass


def find_tools():
    """Locate the shared linter-root-text and parser-root-text.

    They ship inside whichever skill installed them (translation-upload in this
    vault). Duplicating them here would let the two copies drift, so this script
    searches for the one copy: first beside itself, then across sibling skills,
    then under 4-SYSTEM/scripts/.
    """
    roots = [SKILL_DIR, *SKILL_DIR.parents[:4]]
    for base in roots:
        for linter in sorted(base.rglob("linter-root-text/lint_text_input.py")):
            parser = linter.parent.parent / "parser-root-text" / "parser.py"
            if parser.exists():
                return linter, parser
    sys.exit("could not find linter-root-text/lint_text_input.py and parser-root-text/parser.py "
             "in this vault — install the translation-upload skill, or set them up under 4-SYSTEM/scripts/")


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


def headers():
    key = os.environ.get("WEBUDDHIST_API_KEY", "")
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if key:
        h["X-API-Key"] = key
    app = os.environ.get("WEBUDDHIST_APP", "")
    if app:
        h["X-Application"] = app
    return h


def run_tool(argv):
    """Run a bundled tool, keeping its output in order with ours.

    Our prints go through Python's buffered stdout while the child writes
    straight to the same fd, so without the flush the child's output lands
    above the header that introduces it.
    """
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
    ap.add_argument("note", help="the root-text note (file_type: root-text)")
    ap.add_argument("--execute", action="store_true", help="send the requests (default: dry run)")
    ap.add_argument("--skip-lint", action="store_true", help="reuse the existing lint output")
    ap.add_argument("--no-live", action="store_true", help="skip the read-only checks against the live API")
    ap.add_argument("--verify", action="store_true", help="only GET the live state of this text and exit")
    args = ap.parse_args(argv)

    linter, parser_py = find_tools()
    lint_out = linter.parent / "output"
    parse_out = parser_py.parent / "output"

    note = pathlib.Path(args.note)
    if not note.exists():
        sys.exit(f"not found: {note}")
    stem = note.stem
    fm = read_fm(note)
    if fm.get("file_type") not in ROOT_FILE_TYPES:
        ft = fm.get("file_type")
        hint = ("send it through translation-upload instead" if ft == "translation" else
                f"set file_type to one of {ROOT_FILE_TYPES} if this really is the root text — note that the "
                f"linter validates the body and the table of contents only for those types, so a wrong "
                f"file_type makes it pass without ever checking the edition")
        sys.exit(f"{note.name}: file_type is {ft!r}, not one of {ROOT_FILE_TYPES} — {hint}.")
    lang = fm.get("lang_tag")
    key = stem

    if args.verify:
        tid, eid, toc_id = fm.get("text_id"), fm.get("edition_id"), fm.get("toc_id")
        print(f"text_id {tid}  edition_id {eid}  toc_id {toc_id}")
        if tid:
            t = call("GET", f"{BASE}/v2/texts/{tid}")
            print(f"  text: title={t.get('title')} lang={t.get('language')} "
                  f"category={t.get('category_id')} editions={t.get('editions')}")
        if eid:
            refs = live_segment_refs(eid)
            print(f"  edition segments: {len(refs)}  {refs[:4]} … {refs[-2:]}")
            toc = call("GET", f"{BASE}/v2/editions/{eid}/table-of-contents")
            for t in toc or []:
                secs = t.get("sections", [])
                print(f"  toc {t.get('id')}: {len(secs)} root section(s), "
                      f"{sum(len(s.get('subsections', [])) for s in secs)} subsections: "
                      + " | ".join(ss["title"].get(lang, "?") for s in secs for ss in s.get("subsections", [])))
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

    # ---- 2. parse
    print("\n== parse ==")
    r = run_tool([sys.executable, str(parser_py), str(note), str(lint_json)])
    if r.returncode != 0:
        sys.exit("ABORT: parse failed (see above)")
    payloads = {}
    for kind in ("text", "edition", "toc"):
        p = parse_out / f"{stem}.{kind}.json"
        if not p.exists():
            sys.exit(f"ABORT: parser did not write {p.name}")
        payloads[kind] = json.loads(p.read_text(encoding="utf-8"))

    edition = payloads["edition"]
    segs = edition["segmentation"]["segments"]
    refs = [s["reference"] for s in segs]
    toc = payloads["toc"]

    # ---- 3. checks
    print("\n== checks ==")
    problems = []
    if not edition["content"].strip():
        problems.append("edition content is empty")
    if len(refs) != len(set(refs)):
        dupes = sorted({r for r in refs if refs.count(r) > 1})[:6]
        problems.append(f"duplicate segment references: {dupes}")
    for s in segs:
        for sp in s["lines"]:
            if not 0 <= sp["start"] <= sp["end"] <= len(edition["content"]):
                problems.append(f"segment {s['reference']} span out of range")
    n_sections = len(toc.get("sections", []))
    n_sub = sum(len(s.get("subsections", [])) for s in toc.get("sections", []))
    if n_sections != 1:
        problems.append(f"toc has {n_sections} root sections, expected 1 (the H1)")
    if (parse_out / f"{stem}.alignment.json").exists():
        print(f"  note: a stale {stem}.alignment.json is present and will be ignored "
              f"(a root text has no alignment side)")
    if not args.no_live and fm.get("text_id"):
        try:
            t = call("GET", f"{BASE}/v2/texts/{fm['text_id']}")
            if t.get("editions"):
                problems.append(f"live text {fm['text_id']} already has editions {t.get('editions')} — "
                                f"set edition_id in the note or remove the stale edition first; "
                                f"re-creating would orphan every alignment that referenced it")
            else:
                print(f"  live text {fm['text_id']}: exists ✓, no edition yet ✓")
        except ApiError as exc:
            problems.append(f"live check failed: {exc}")
    print(f"  {len(edition['content'])} chars, {len(segs)} segments, "
          f"toc: 1 root section + {n_sub} subsections")
    for p in problems:
        print(f"  !! {p}")
    if problems:
        sys.exit("ABORT: checks failed")

    # ---- 4. plan / execute
    tid = fm.get("text_id") or None
    eid = fm.get("edition_id") or None
    toc_id = fm.get("toc_id") or None
    plan = [
        ("text", "POST", f"{BASE}/v2/texts",
         payloads["text"], "skip (text_id present)" if tid else "create"),
        ("edition", "POST", f"{BASE}/v2/texts/{tid or '{text_id}'}/editions",
         edition, "skip (edition_id present)" if eid else "create"),
        ("toc", "POST", f"{BASE}/v2/editions/{eid or '{edition_id}'}/table-of-contents",
         toc, "skip (toc_id present)" if toc_id else "create"),
    ]

    print(f"\n== {'EXECUTE' if args.execute else 'DRY RUN'} ==")
    for step, method, url, body, action in plan:
        nbytes = len(json.dumps(body, ensure_ascii=False).encode("utf-8"))
        print(f"  {step:<8} {method:<4} {url}  ({nbytes} bytes)  -> {action}")
    if not args.execute:
        print("\ndry run: nothing sent, frontmatter untouched. Re-run with --execute after confirmation.")
        return 0
    if not os.environ.get("WEBUDDHIST_API_KEY"):
        sys.exit("WEBUDDHIST_API_KEY is not set")

    ledger = load_ledger()
    entry = ledger.setdefault(key, {})
    entry.update({"lang_tag": lang, "file_type": fm.get("file_type"), "source_file": str(note)})

    def receipt(step, **kw):
        entry.setdefault("log", []).append(
            {"step": step, "ts": _dt.datetime.now().isoformat(timespec="seconds"), **kw})
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
    print(f"the translations of this text can now be uploaded: they read text_id={tid} "
          f"and edition_id={eid} from this file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
