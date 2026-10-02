#!/usr/bin/env python3
"""check_translation_alignment.py — prove that every translation mirrors its root text, structurally.

No API calls unless --live. Reads the root note and every translation note with
the SAME parser the uploader uses (4-SYSTEM/scripts/parser-root-text/parser.py),
so what is compared is exactly what would be uploaded:

  per note        segments (references, order, type, LINE COUNT per segment),
                  headings (level, reference, title), the TOC tree built from
                  them, and whether any heading text leaked into the content
  translation     every check above equal to the root's; transclusion above
  vs root         each block points at the block with the same id
  --payloads      the parser's <stem>.edition/.toc/.alignment.json for each note:
                  segment refs equal the note, content carries no '#' line and no
                  heading title, TOC spans are contiguous and cover the content,
                  alignment pairs are identity and cover every segment
  --live          the library's root segmentation and TOC (GET only): references
                  and TOC section count equal the root note's

Exit 0 when every check holds for every note, 1 otherwise. The report is a
table per note plus a list of every failed check with the offending ids.

Usage (from the vault root):
    python3 4-SYSTEM/scripts/check_translation_alignment.py                 # root + all machine tracks
    python3 4-SYSTEM/scripts/check_translation_alignment.py --payloads --live
    python3 4-SYSTEM/scripts/check_translation_alignment.py --root <root.md> <translation.md> ...
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import pathlib
import re
import sys
import urllib.request

# The skill folder ships its own parser, so the script works wherever the skill
# is installed. VAULT is only used to resolve the default translation glob.
SKILL_DIR = pathlib.Path(__file__).resolve().parent
VAULT = pathlib.Path(os.environ.get("VAULT_ROOT", pathlib.Path.cwd()))
PARSER = SKILL_DIR / "parser-root-text/parser.py"
PAYLOAD_DIR = pathlib.Path(
    os.environ.get("PAYLOAD_DIR", SKILL_DIR / "parser-root-text/output"))
BASE = os.environ.get("WEBUDDHIST_API_BASE", "https://library.webuddhist.com").rstrip("/")
TRANS_RE = re.compile(r"!\[\[.*?#\^([A-Za-z0-9-]+)\]\]")


def load_parser():
    spec = importlib.util.spec_from_file_location("wb_parser", PARSER)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(PARSER.parent))
    spec.loader.exec_module(mod)
    return mod


def nest(headings, content_len):
    """The same nesting the parser's build_toc applies: a section spans from its
    heading's content offset to the next heading of the same or higher level."""
    nodes = []
    for i, h in enumerate(headings):
        end = content_len
        for later in headings[i + 1:]:
            if later["level"] <= h["level"]:
                end = later["offset"]
                break
        nodes.append({"level": h["level"], "ref": h["reference"], "title": h["title"],
                      "start": h["offset"], "end": end})

    def _nest(idx, parent_level):
        out, i = [], idx
        while i < len(nodes):
            n = nodes[i]
            if n["level"] <= parent_level:
                break
            if n["level"] == parent_level + 1:
                sec = {"ref": n["ref"], "title": n["title"], "span": (n["start"], n["end"]), "subsections": []}
                sec["subsections"], i = _nest(i + 1, n["level"])
                out.append(sec)
            else:
                i += 1
        return out, i

    top = nodes[0]["level"] if nodes else 1
    tree, _ = _nest(0, top - 1)
    return tree


def shape(tree):
    """The TOC tree reduced to (ref, [children…]) — titles left out so trees
    in different languages compare equal."""
    return [(s["ref"], shape(s["subsections"])) for s in tree]


def analyse(P, path):
    fm, body = P._read_source(pathlib.Path(path))
    blocks = P._extract_blocks(body)
    doc_default = "verse"
    if fm.get("file_type") == "translation":
        doc_default = "verse"      # root-text translations; commentary translations are not in scope
    content, segs, headings = P._build_content_and_segmentation(blocks, doc_default)
    info = {
        "path": str(path), "fm": fm,
        "content": content, "segs": segs, "headings": headings,
        "refs": [s["reference"] for s in segs],
        "types": {s["reference"]: s["type"] for s in segs},
        "lines": {s["reference"]: len(s["lines"]) for s in segs},
        "heads": [(h["level"], h["reference"]) for h in headings],
        "head_titles": {h["reference"]: h["title"] for h in headings},
        "toc": nest(headings, len(content)),
        "leaks": [], "transclusions": {},
    }
    # heading text or a '#' line inside the content would mean the TOC leaked into the text
    for h in headings:
        if h["title"] and h["title"] in content:
            info["leaks"].append(f"heading {h['reference']} title found inside content")
    for line in body.split("\n"):
        pass
    # transclusion above each block: which root id does each translated block point at?
    pending = []
    for b in blocks:
        if b["is_header"]:
            pending = []
            continue
        targets = [m.group(1) for l in b["lines"] for m in [TRANS_RE.search(l)] if m]
        if targets and not b["ref"]:
            pending += targets
        elif b["ref"]:
            info["transclusions"][b["ref"].lstrip("^")] = pending + targets
            pending = []
    return info


def live_root(edition_id):
    def get(url):
        req = urllib.request.Request(url, headers={k: v for k, v in {
            "X-API-Key": os.environ.get("WEBUDDHIST_API_KEY", ""),
            "X-Application": os.environ.get("WEBUDDHIST_APP", "")}.items() if v})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    refs, off = [], 0
    while True:
        d = get(f"{BASE}/v2/editions/{edition_id}/segmentation/segments?limit=200&offset={off}")
        refs += [s["reference"] for s in d.get("items", [])]
        if not d.get("has_more"):
            break
        off += len(d.get("items", []))
    toc = get(f"{BASE}/v2/editions/{edition_id}/table-of-contents")
    return refs, toc


def check(root, tr, payload_dir=None):
    fails = []
    tag = tr["fm"].get("lang_tag", "?")

    def need(cond, msg):
        if not cond:
            fails.append(msg)

    need(tr["heads"] == root["heads"], f"headings differ: {tr['heads']} vs root {root['heads']}")
    need(tr["refs"] == root["refs"],
         f"segment references differ ({len(tr['refs'])} vs {len(root['refs'])}); "
         f"only-here {sorted(set(tr['refs']) - set(root['refs']))[:6]}, "
         f"only-root {sorted(set(root['refs']) - set(tr['refs']))[:6]}")
    bad_lines = [(r, root["lines"][r], tr["lines"].get(r)) for r in root["refs"] if tr["lines"].get(r) != root["lines"][r]]
    need(not bad_lines, f"line count differs in {len(bad_lines)} segment(s): {bad_lines[:8]}")
    bad_types = [(r, root["types"][r], tr["types"].get(r)) for r in root["refs"] if tr["types"].get(r) != root["types"][r]]
    need(not bad_types, f"segment type differs: {bad_types[:6]}")
    need(shape(tr["toc"]) == shape(root["toc"]), f"TOC tree differs: {shape(tr['toc'])} vs {shape(root['toc'])}")
    need(not tr["leaks"], f"TOC leaked into content: {tr['leaks']}")
    numerals = [(r, t) for r, t in tr["head_titles"].items() if re.match(r"^\s*\d+\s*[.．、]", t)]
    need(not numerals, f"heading title starts with a numeral: {numerals}")
    bad_tr = [(r, t) for r, t in tr["transclusions"].items() if t != [r]]
    need(not bad_tr, f"transclusion does not point at the same id: {bad_tr[:6]}")
    missing_tr = [r for r in tr["refs"] if r not in tr["transclusions"]]
    need(not missing_tr, f"blocks without a transclusion: {missing_tr[:6]}")
    placeholders = "*[not yet translated]*" in tr["content"]
    need(not placeholders, "untranslated placeholder in content")
    need(tr["fm"].get("file_type") == "translation", "file_type is not 'translation'")
    need(str(tr["fm"].get("root_text", "")).endswith(pathlib.Path(root["path"]).name), "root_text does not name the root note")

    if payload_dir:
        stem = pathlib.Path(tr["path"]).stem
        ed = payload_dir / f"{stem}.edition.json"
        toc = payload_dir / f"{stem}.toc.json"
        al = payload_dir / f"{stem}.alignment.json"
        if not (ed.exists() and toc.exists() and al.exists()):
            fails.append(f"payloads missing under {payload_dir} (run the dry-run upload first)")
        else:
            E = json.loads(ed.read_text(encoding="utf-8"))
            T = json.loads(toc.read_text(encoding="utf-8"))
            A = json.loads(al.read_text(encoding="utf-8"))
            prefs = [s["reference"] for s in E["segmentation"]["segments"]]
            need(prefs == tr["refs"], "edition.json segment references differ from the note")
            need(E["content"] == tr["content"], "edition.json content differs from the note's parse")
            need("#" not in E["content"], "edition.json content contains a '#'")
            for h in tr["headings"]:
                need(h["title"] not in E["content"], f"edition.json content contains heading title {h['reference']!r}")
            pos = 0
            for s in E["segmentation"]["segments"]:
                for sp in s["lines"]:
                    need(sp["start"] == pos, f"edition.json span gap/overlap at segment {s['reference']}")
                    pos = sp["end"]
            need(pos == len(E["content"]), "edition.json spans do not cover the whole content")
            secs = T.get("sections", [])
            need(len(secs) == 1, f"toc.json has {len(secs)} top sections, expected 1 (the H1)")
            if secs:
                lang = tr["fm"].get("lang_tag")
                subs = secs[0].get("subsections", [])
                want = tr["toc"][0]["subsections"] if tr["toc"] else []
                need(len(subs) == len(want), f"toc.json has {len(subs)} subsections, note has {len(want)}")
                need(secs[0]["span"] == {"start": 0, "end": len(E["content"])}, "toc.json root span is not the whole content")
                prev = 0
                for s, w in zip(subs, want):
                    need(s["title"].get(lang) == w["title"], f"toc.json title {s['title']} != note heading {w['title']!r}")
                    need((s["span"]["start"], s["span"]["end"]) == w["span"], f"toc.json span for {w['ref']} differs")
                    need(s["span"]["start"] == prev, f"toc.json subsections not contiguous at {w['ref']}")
                    prev = s["span"]["end"]
                need(prev == len(E["content"]), "toc.json subsections do not cover the whole content")
            pairs = A["alignments"]
            need([p["source_segment_reference"] for p in pairs] == tr["refs"], "alignment.json does not cover every segment in order")
            need(all(p["source_segment_reference"] == p["target_segment_reference"] for p in pairs), "alignment.json is not identity")
    return tag, fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("translations", nargs="*", help="translation files (default: every block-aligned translation under 3-TRANSFORMATIONS/Translations/)")
    ap.add_argument("--root", required=True,
                    help="the root text every translation is checked against")
    ap.add_argument("--payloads", action="store_true", help="also check the parser payloads in parser-root-text/output")
    ap.add_argument("--live", action="store_true", help="also compare the root note against the live library root")
    args = ap.parse_args()

    P = load_parser()
    root = analyse(P, args.root)
    notes = args.translations or sorted(
        glob.glob(str(VAULT / "3-TRANSFORMATIONS/Translations/*/*/" / f"{pathlib.Path(args.root).stem}-*.md")))
    if not notes:
        sys.exit("no translation notes found")

    print(f"root      : {pathlib.Path(args.root).name}")
    print(f"            {len(root['refs'])} segments, {len(root['heads'])} headings, {len(root['content'])} chars, "
          f"TOC {shape(root['toc'])}")
    print(f"            lines per segment: " + " ".join(f"{r}:{root['lines'][r]}" for r in root["refs"]))
    if root["leaks"]:
        print(f"            !! {root['leaks']}")
    numerals = [(r, t) for r, t in root["head_titles"].items() if re.match(r"^\s*\d+\s*[.．、]", t)]
    if numerals:
        print(f"            note: root heading title starts with a numeral: {numerals} (editorial; translations drop it)")

    problems = 0
    if args.live:
        eid = root["fm"].get("edition_id")
        try:
            refs, toc = live_root(eid)
            ok_refs = refs == root["refs"]
            live_subs = sum(len(s.get("subsections", [])) for t in toc for s in t.get("sections", []))
            note_subs = len(root["toc"][0]["subsections"]) if root["toc"] else 0
            print(f"live root : edition {eid}: {len(refs)} segments {'==' if ok_refs else '!='} note; "
                  f"TOC {len(toc)} annotation(s), {live_subs} subsections {'==' if live_subs == note_subs else '!='} note ({note_subs})")
            if not ok_refs or live_subs != note_subs:
                problems += 1
        except Exception as exc:  # noqa: BLE001
            print(f"live root : check failed: {exc}")
            problems += 1

    print(f"\n{'tag':<4} {'segs':>4} {'heads':>5} {'chars':>6}  {'TOC':<28} verdict")
    results = []
    for n in notes:
        tr = analyse(P, n)
        tag, fails = check(root, tr, PAYLOAD_DIR if args.payloads else None)
        results.append((tag, n, fails))
        toc_s = str(shape(tr["toc"]))
        print(f"{tag:<4} {len(tr['refs']):>4} {len(tr['heads']):>5} {len(tr['content']):>6}  "
              f"{(toc_s[:26] + '…') if len(toc_s) > 27 else toc_s:<28} {'OK' if not fails else f'{len(fails)} problem(s)'}")
        problems += len(fails)
    for tag, n, fails in results:
        for f in fails:
            print(f"  !! {tag}: {f}")
    print("\nRESULT:", "OK — every translation mirrors the root" if not problems else f"{problems} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
