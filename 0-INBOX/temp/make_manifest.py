#!/usr/bin/env python3
"""Generate 0-INBOX/raw-data/intake-manifest.yaml and the Wikisource outline
files for the Phakpa Düpa (Ratnaguṇasañcayagāthā) intake, from:
  - the raw data (rows, CSV metadata),
  - the placed Wikisource outlines in 0-INBOX/temp/wiki-toc-*/outline.placed.md,
  - the numbered TOC-doc labels and their path corrections (0-INBOX/temp/numbered-label*.json),
  - the root heading renderings (0-INBOX/temp/root-labels.json),
  - a previous scratch build's sidecars (--prev), for each split row's own targets,
  - label row splits computed from a previous build (0-INBOX/temp/label-splits.json, optional).
Every human decision is written with reason, who and date. Run from the vault root:
    python3 0-INBOX/temp/make_manifest.py --prev <scratch build root>
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

import yaml

V = pathlib.Path(".")
RAW = V / "0-INBOX/raw-data"
TMP = V / "0-INBOX/temp"
sys.path.insert(0, str(V / "4-SYSTEM/Skills/aligned-corpus-intake/scripts"))
from md_export import read_rows, read_meta   # noqa: E402
from project import letters                  # noqa: E402

TODAY = "2026-10-03"
STANDING = "vault owner — standing decision carried over from heart-sutra-rails (2026-10-03)"
D7 = f"{STANDING}, D7 \"split the rows\"; positions from Wikisource; applied by Claude"
D8 = f"{STANDING}, D8 \"add the missing TOC section's text from Wikisource\"; applied by Claude"
D10 = f"{STANDING}, D10 \"remove brackets, keep words\""
D12 = ('Claude (standing instruction "read it and fix if it really makes sense", carried over from '
       'heart-sutra-rails 2026-10-03) — for the text expert to check')
ROOT_FILE = "1-SOURCES/Translations/bo-ratnagunasancayagatha.md"


def rows(f):
    return {r["row"]: r["text"] for r in read_rows(RAW / f)}


def sha1(f):
    return hashlib.sha1((RAW / f).read_bytes()).hexdigest()


def placed(oid):
    t = (TMP / f"wiki-toc-{oid}/outline.placed.md").read_text(encoding="utf-8")
    fm = yaml.safe_load(re.match(r"\A---\n(.*?)\n---\n", t, re.S).group(1))
    nodes = yaml.safe_load(re.search(r"```yaml\n(.*?)\n```", t, re.S).group(1))["nodes"]
    splits = yaml.safe_load(re.search(r"```text\n(.*?)```", t, re.S).group(1))["row_splits"]
    return fm, nodes, splits


# --------------------------------------------------------------------------
# targets per part of a split row: each target segment goes to the first part
# that quotes it (8-letter runs of the segment found in the part), never
# before the part of the target before it; a target no part quotes goes with
# the part of the target before it (the first part for the first target)
# --------------------------------------------------------------------------

def _shingles(s, k=8):
    la = letters(s.replace("༷", ""))[0]
    return {la[i:i + k] for i in range(len(la) - k + 1)}


def part_targets(parts, seg_texts):
    out, last = [[] for _ in parts], 0
    for j, seg in enumerate(seg_texts):
        sh = _shingles(seg)
        best = None
        for i in range(last, len(parts)):
            hits = len(sh & _shingles(parts[i]))
            if hits >= 3:
                best = i
                break
        i = best if best is not None else last
        out[i].append(j)
        last = i
    return out


def split_parts(text, at):
    cuts = [text.index(c) for c in at]
    b = [0] + cuts + [len(text)]
    return [text[b[i]:b[i + 1]] for i in range(len(b) - 1)]


class Prev:
    """A previous scratch build: each row's own targets and the target texts."""
    def __init__(self, root):
        self.root = pathlib.Path(root)
        self.cache = {}

    def sidecar(self, stem):
        if stem not in self.cache:
            self.cache[stem] = json.loads((self.root / f"1-SOURCES/Annotations/{stem}.annotations.json")
                                          .read_text(encoding="utf-8"))
        return self.cache[stem]

    def block_texts(self, path):
        out = {}
        for line in (self.root / path).read_text(encoding="utf-8").splitlines():
            m = re.match(r"^(?!#|!\[\[)(.*\S)\s+\^([0-9-]+)$", line)
            if m:
                out[m.group(2)] = m.group(1)
        return out

    def row_targets(self, stem, row):
        tg = []
        for b in self.sidecar(stem)["blocks"].values():
            if b.get("source", {}).get("row") == row:
                for t in (b.get("alignment") or {}).get("row_targets") or b.get("targets") or []:
                    if t not in tg:
                        tg.append(t)
        return tg


def with_targets(splits, row_text, stem, target_path, prev, reason_of):
    out = []
    tt = prev.block_texts(target_path)
    for s in splits:
        r = s["row"]
        tg = prev.row_targets(stem, r)
        parts = split_parts(row_text[r], s["at"])
        per = part_targets(parts, [tt.get(t, "") for t in tg])
        out.append({"row": r, "at": s["at"], "targets": per, "reason": reason_of(s, tg, per),
                    "decided_by": D7, "date": TODAY})
    return out


# --------------------------------------------------------------------------
# metadata
# --------------------------------------------------------------------------

def meta(f):
    return read_meta(RAW / f)


def g(m, field, lang="bo"):
    return (m.get(field) or {}).get(lang)


def alts(m, *extra):
    out = []
    for k in ["title_long_clean", "title_alt_1", "title_alt_2", "title_alt_3", "title_alt_4", "title_short"]:
        v = g(m, k)
        if v and v not in out:
            out.append(v)
    for v in extra:
        if v and v not in out:
            out.append(v)
    return out


def brackets(text_rows, reason):
    """D10: every [ … ] pair in a row -> the words; a bracket whose partner is
    in another row is removed on its own."""
    out = []
    for r, t in sorted(text_rows.items()):
        work = t
        for m in re.finditer(r"\[([^\[\]\n]*)\]", t):
            glued = m.end() < len(t) and t[m.end()].isalpha()
            out.append({"row": r, "find": m.group(0), "replace": m.group(1) + (" " if glued else ""),
                        "reason": reason + (" The bracket was the only separator before the next word, "
                                            "so a space takes its place." if glued else ""),
                        "decided_by": D10, "date": TODAY})
            work = work.replace(m.group(0), "", 1)
        for ch in "[]":
            if ch in work:
                assert work.count(ch) == 1 and t.count(ch) == 1 + len(re.findall(r"\[[^\[\]\n]*\]", t)), (r, t)
                # the bracket pairs with one in a neighbouring row
                k = t.index(ch)
                find = t[k:k + 12] if ch == "[" else t[max(0, k - 12):k + 1]
                if t.count(find) != 1:
                    find = ch
                out.append({"row": r, "find": find, "replace": find.replace(ch, ""),
                            "reason": reason + " This bracket's partner is in the "
                                      + ("next" if ch == "[" else "previous") + " row.",
                            "decided_by": D10, "date": TODAY})
    return out


def renumber(paths):
    """Wikisource heading numbers with slips -> a consistent tree, in order.
    A prefix already remapped is carried to later nodes; a node whose parent
    is not on the current ancestor chain hangs under the deepest open
    ancestor; an ordinal that repeats or runs back takes the next free one
    (gaps up to 3 are kept). Returns (new paths, {index: (old, new, why)})."""
    remap, chain, last, out, changes, skipped = {}, [], {}, [], {}, []
    for i, old in enumerate(paths):
        p, why = old, []
        for k in sorted(remap, key=len, reverse=True):          # carry an earlier correction
            if p == k or p.startswith(k + "."):
                p = remap[k] + p[len(k):]
                why.append("under a renumbered heading")
                break
        parent, n = p.rpartition(".")[0], int(p.rpartition(".")[2])
        gp, pn = parent.rpartition(".")[0], int(parent.rpartition(".")[2] or 0)
        if parent and parent not in chain and (not gp or gp in chain) and last.get(gp, 0) < pn <= last.get(gp, 0) + 1:
            # the source omits this heading's parent (a level skipped): kept as the source numbers it
            skipped.append(parent)
            last[gp] = pn
            chain = [c for c in chain if c.count(".") < parent.count(".")] + [parent]
        if parent and parent not in chain:
            depth = p.count(".")                                 # the parent's depth (1-based) would be this
            missing, parent = parent, next((c for c in reversed(chain) if c.count(".") + 1 <= depth), "")
            remap[missing] = parent                              # its siblings follow it there
            why.append("its number's parent is not the heading above it")
        prev = last.get(parent, 0 if n else -1)       # a section may be numbered from 0
        if not (prev < n <= prev + 3):
            n = prev + 1
            why.append("its ordinal repeats or runs back on a sibling's")
        new = f"{parent}.{n}" if parent else str(n)
        if new != old:
            remap[old] = new
            changes[i] = (old, new, "; ".join(dict.fromkeys(why)))
        last[parent] = n
        d = new.count(".")
        chain = [c for c in chain if c.count(".") < d] + [new]
        out.append(new)
    return out, changes, skipped


# --------------------------------------------------------------------------

def outline_file(oid, fm, nodes, lang_labels, applied_to, extra):
    """Write 2-RAILS/Sections/Raw/toc-wikisource/<oid>.md."""
    pages = {}
    for n in nodes:
        p = pages.setdefault(n["page"], {"page": f"Page:{fm['index_page'].split(':', 1)[1]}/{n['page']}",
                                         "revid": n["page_revid"], "headings": []})
        p["headings"].append(n["path"])
    head = {"outline_id": oid, **({"registered_id": extra["registered_id"]} if extra.get("registered_id") else {}),
            "source": "wikisource.org", "index_page": fm["index_page"], "index_url": fm["index_url"],
            "index_revid": fm["index_revid"], **({"toc_page": extra["toc_page"]} if extra.get("toc_page") else {}),
            "edition": extra["edition"],
            "heading_pages": sorted(pages.values(), key=lambda p: int(p["page"].rsplit("/", 1)[1])),
            "retrieved": fm["retrieved"], "placed_on": fm["placed_on"], "placed_on_text": fm["placed_on_text"],
            "placed_on_sha1": fm["placed_on_sha1"], "applied_to": applied_to, "labels": extra["labels"],
            "placement": extra["placement"], **({"replaces": extra["replaces"]} if extra.get("replaces") else {}),
            "status": "complete"}
    new_paths, changes, skipped = renumber([str(n["path"]) for n in nodes])
    out_nodes = []
    for i, n in enumerate(nodes):
        lab = {"bo": n["labels"]["bo"]}
        for lang, table in lang_labels.items():
            lab[lang] = table[n["path"]]
        out_nodes.append({"path": new_paths[i], **({"path_in_source": str(n["path"])} if i in changes else {}),
                          "start_row": str(n["start_row"]), "labels": lab, "clause": n.get("clause", "")})
    if changes:
        head["path_corrections"] = {
            "decided_by": D12, "date": TODAY,
            "reason": ("The Index's own heading numbers repeat, skip a level or carry a stale prefix at these "
                       "nodes, which would give duplicate or orphaned block ids; each takes the consistent "
                       "number shown, and keeps the source's in path_in_source."),
            "nodes": [{"source": o, "path": nw, "why": w} for o, nw, w in changes.values()]}
        extra = dict(extra, body=extra["body"] + f"\n\n{len(changes)} heading numbers corrected (frontmatter "
                     "`path_corrections`; the Index's own number stays in `path_in_source`).")
    if skipped:
        head["levels_skipped_in_source"] = skipped
        extra = dict(extra, body=extra["body"] + "\n\nThe Index has no heading for " + ", ".join(skipped)
                     + " although it numbers headings under it; those keep the Index's numbers (a level is skipped).")
    body = ("---\n" + yaml.safe_dump(head, allow_unicode=True, sort_keys=False, width=1000) + "---\n\n"
            + extra["body"] + "\n\n```yaml\n"
            + yaml.safe_dump({"nodes": out_nodes}, allow_unicode=True, sort_keys=False, width=1000) + "```\n")
    p = V / f"2-RAILS/Sections/Raw/toc-wikisource/{oid}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return f"2-RAILS/Sections/Raw/toc-wikisource/{oid}.md"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", required=True, help="a previous scratch build root (for row targets)")
    a = ap.parse_args()
    prev = Prev(a.prev)
    works = []

    # ---------------------------------------------------------------- root
    sa_rows = rows("phakpadoepa-root-sa(sa-bo).md")
    bo_rows = rows("phakpadoepa-root-bo(display).md")
    zh_rows = rows("phakpadoepa-root-zh(bo-zh).md")
    rfm, rnodes, rsplits = placed("ratnagunasancayagatha")
    rlab = json.loads((TMP / "root-labels.json").read_text(encoding="utf-8")) \
        if (TMP / "root-labels.json").exists() else None
    dk = json.loads((TMP / "wiki-toc-ratnagunasancayagatha/dkarchag-pages.json").read_text(encoding="utf-8"))
    root_outline = outline_file(
        "ratnagunasancayagatha", rfm, rnodes,
        {"sa": rlab["sa"], "zh": rlab["zh"]} if rlab else {"sa": {n["path"]: n["labels"]["bo"] for n in rnodes},
                                                           "zh": {n["path"]: n["labels"]["bo"] for n in rnodes}},
        ["sa-root", "bo-display", "zh-translation"],
        {"edition": "Derge Kangyur (སྡེ་དགེ་དཔར་ཁང་།, 1727; Index: པོད་སོ་བཞི། ༡བ༡-༡༩བ༧)",
         "toc_page": {"title": dk[0]["title"], "revid": dk[0]["revid"],
                      "subpages": [{"title": x["title"], "revid": x["revid"], "pages": x["pages"]} for x in dk[1:]]},
         "labels": {"bo": "verbatim from the དཀར་ཆག on the Wikisource transclusion page (outer whitespace trimmed)",
                    "sa": "editorial renderings in the Sanskrit text's own vocabulary — 0-INBOX/temp/pair-review/root-toc-labels.md (Claude, for the text expert to check)",
                    "zh": "editorial renderings in the Chinese text's own vocabulary — 0-INBOX/temp/pair-review/root-toc-labels.md (Claude, for the text expert to check)"},
         "placement": ("The Index's proofread pages carry no inline headings; the TOC is the nine-entry དཀར་ཆག of the "
                       "transclusion page, whose subpages transclude the named <section>s part1–part9 of the pages. "
                       "Each node starts where its section's begin tag stands, found in the display Tibetan by "
                       "letters (fetch_wiki_outline.py place --sections; unique-letter-run anchor chain). Spot-checked: "
                       "every node's start row against the raw text."),
         "body": ("# ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པ། — outline from the Wikisource dkar chag\n\n"
                  "Nine sections: the opening (ཀླད་ཀྱི་དོན།) and the eight topics (སྐབས་) that the Derge text marks inline. "
                  "Row 1 (the document's own title line) precedes node 0. Wikisource opens section 2 *after* the inline marker "
                  "སྐབས་གཉིས་པ་ལམ་ཐམས་ཅད་ཤེས་པ་ཉིད་བསྟན། (display row 34 stays at the end of section 1), whereas every other "
                  "section opens *with* its marker — kept as Wikisource has it and listed for review. Section 8 opens inside "
                  "row 367 (at སྐབས་བརྒྱད་པ་ཆོས་ཀྱི་སྐུ་བསྟན།), so that row is split (manifest `row_splits`, D7).\n\n"
                  "| node | bo | start row | text after the heading |\n|---|---|---|---|\n"
                  + "\n".join(f"| {n['path']} | {n['labels']['bo']} | {n['start_row']} | {n.get('clause', '')[:40]}… |"
                              for n in rnodes))})
    root_toc_note = ("The root's TOC is the nine-entry དཀར་ཆག of the Derge Kangyur text on Wikisource (transclusion page "
                     f"revision {dk[0]['revid']}; Index:{rfm['index_page'].split(':', 1)[1]} revision {rfm['index_revid']}): "
                     "ཀླད་ཀྱི་དོན། and the eight སྐབས་, each placed where the Index's proofread pages open its <section>, "
                     "found by letters in the display Tibetan and carried onto the Sanskrit and the Chinese through their "
                     "row pairings, with headings in each file's own language (Tibetan verbatim; Sanskrit and Chinese "
                     "editorial). D4/D5, standing decisions carried over from heart-sutra-rails (2026-10-03); the vault "
                     "owner confirmed on 2026-10-03 that the dkar chag be used, as the Index has no inline headings.")
    toc_root = {"kind": "outline", "file": root_outline, "note": root_toc_note}

    sa_reason = ("The Sanskrit edition's square brackets (editor-supplied chapter titles, restored words and the "
                 "editor's labels for the praśastis) are removed and the words kept, because Obsidian renders "
                 "bracketed text like link syntax. The bracketed form stays here and in the block's sidecar entry "
                 "(source.corrections).")
    DEV = str.maketrans("०१२३४५६७८९", "0123456789")
    num_re = re.compile(r"॥\s*(?:([०-९]+)[,.]\s*([०-९]+)|([हल])्प्र्\s*([०-९]+))\s*॥")
    sa_numbers = []
    for r, t in sorted(sa_rows.items()):
        for m in num_re.finditer(t):
            if m.group(1):
                verse = f"{m.group(1).translate(DEV)}.{m.group(2).translate(DEV)}"
                what = f"chapter {verse.split('.')[0]}, verse {verse.split('.')[1]}"
            else:
                verse = ("Haribhadra's praśasti " if m.group(3) == "ह" else "scribe's praśasti ") + m.group(4).translate(DEV)
                what = verse
            sa_numbers.append({"row": r, "find": m.group(0), "replace": "॥", "verse": verse,
                               "reason": (f"The edition's verse number ({what}) is the modern editor's numbering of "
                                          "Vaidya's edition (GRETIL marks the same numbering, Rgs_<chapter>.<verse>, as added "
                                          "in digitisation), not root text, and follows the edition's 32 chapters rather than "
                                          "this file's TOC. Removed from the text; kept here and in the block's sidecar entry "
                                          "(source.corrections[].verse)."),
                               "decided_by": "the vault owner (\"Remove, keep as metadata\")", "date": "2026-10-04"})
    pada = json.loads((TMP / "sa-pada-breaks.json").read_text(encoding="utf-8"))
    works.append({
        "key": "sa-root", "path": "1-SOURCES/Text/sa-ratnagunasancayagatha.md", "adapter": "md_rows",
        "id_scheme": "h2", "text": "phakpadoepa-root-sa(sa-bo).md",
        "text_corrections": sa_numbers + brackets(sa_rows, sa_reason),
        "line_breaks": {
            "before": {int(k): v for k, v in pada.items()},
            "source": ("Digital Sanskrit Buddhist Canon, Devanāgarī edition, book 402 "
                       "(https://dsbcproject.org/canon-text/book/402), one pāda per line; copy in "
                       "0-INBOX/raw-data/dsbc-ratnagunasancayagatha/; matched by letters "
                       "(0-INBOX/temp/sa_pada_breaks.py), five rows read off the metre by Claude"),
            "reason": ("One verse line (pāda) per line, four per verse, like the Tibetan. The edition marks only the "
                       "half-verse (।), so the pāda boundaries are taken from the DSBC edition of the same text."),
            "decided_by": "the vault owner (\"break each verse into four lines … also the Sanskrit\"; \"4 lines via DSBC\")",
            "date": "2026-10-04"},
        "title": "रत्नगुणसंचयगाथा",
        "notes": ("The Sanskrit is the root of this vault (D1); the Tibetan is its translation. Rows are the Dzongsar "
                  "team's segmentation of the Sanskrit-Tibetan pair (373 rows; the Sanskrit's chapter titles and "
                  "chapter colophons have empty Tibetan rows). Read in full against the Tibetan: no pairing errors."),
        "frontmatter": {"title": "रत्नगुणसंचयगाथा", "language": "Sanskrit", "lang_tag": "sa", "file_type": "root-text",
                        "verse_id_format": "section-paragraph", "category_id": None, "license": "unknown",
                        "source": None,
                        "other_ids": ["Dzongsar: phakpadoepa Sanskrit-Tibetan alignment doc"],
                        "source_description": ("Dzongsar Google Doc (Sanskrit side of the Sanskrit-Tibetan row alignment), "
                                               "exported as phakpadoepa-root-sa(sa-bo).md. Title from its first row. No "
                                               "metadata sheet for the Sanskrit is in the raw data, so source URL and "
                                               "licence are not recorded. One block per row."),
                        "text_id": None, "edition_id": None, "toc_id": None},
        "toc": toc_root})

    bom = meta("phakpadoepa-root-bo.csv")
    r367 = [s for s in rsplits]
    works.append({
        "key": "bo-display", "path": ROOT_FILE, "adapter": "md_rows", "id_scheme": "h2",
        "text": "phakpadoepa-root-bo(display).md",
        "pair": {"own_side": "phakpadoepa-root-bo(sa-bo).md", "target_side": "phakpadoepa-root-sa(sa-bo).md"},
        "target": "sa-root",
        "row_splits": with_targets(
            r367, bo_rows, "bo-ratnagunasancayagatha", "1-SOURCES/Text/sa-ratnagunasancayagatha.md", prev,
            lambda s, tg, per: ("Row 367 holds the last verse-opening of section 7 (སྐད་ཅིག་མ་གཅིག་ལ་མངོན་པར་རྫོགས་པར་"
                                "བྱང་ཆུབ་པ།) and the opening of section 8 (ཆོས་སྐུ།) of the Wikisource dkar chag; it is "
                                "cut where the Index's page 37 opens <section> part9. The row's Sanskrit segment is "
                                "shown with the part that translates it.")),
        "line_breaks": {
            "after": "། ?།",
            "reason": ("One verse line per line (a line ends with its shad pair, ། །), so each block shows its verse "
                       "as four lines; a topic marker (སྐབས་…བསྟན། །) stands on its own line. Letters unchanged."),
            "decided_by": "the vault owner (\"break each segment into four lines … one block ID per verse\")",
            "date": "2026-10-04"},
        "title": "ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པ།",
        "notes": ("The display segmentation: the one Tibetan text the library stores (D2). "
                  "phakpadoepa-root-bo(sa-bo).md and phakpadoepa-root-bo(bo-zh).md are byte-identical to it. Every "
                  "commentary's own cut of the root is carried onto these blocks by letters."),
        "meta": "phakpadoepa-root-bo.csv",
        "frontmatter": {
            "title": "ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པ།",
            "alt_titles": alts(bom),
            "title_in_english": g(bom, "title_long_clean", "en"),
            "alt_titles_in_english": [x for x in (g(bom, "title_short", "en"), g(bom, "title_alt_1", "en")) if x],
            "author": g(bom, "author"),
            "translator": "རྒྱ་གར་གྱི་མཁན་པོ་བིདྷ་ཀ་ར་སིང་ཧ། · ཞུ་ཆེན་གྱི་ལོཙཚ་བ་བན་དེ་དཔལ་བརྩེགས།",
            "language": "Tibetan", "lang_tag": "bo", "file_type": "translation",
            "root_text": "1-SOURCES/Text/sa-ratnagunasancayagatha.md", "verse_id_format": "section-paragraph",
            "category_id": None, "license": "unknown", "source": g(bom, "source"),
            "bdrc_work_id": "WA0RK0013",
            "other_ids": ["Dzongsar: phakpadoepa display doc"],
            "source_description": ("Dzongsar Google Doc (the display segmentation), exported as "
                                   "phakpadoepa-root-bo(display).md. Titles, author and source from "
                                   "phakpadoepa-root-bo.csv (whose English author cell reads 'Peltsek Rakṣita', the "
                                   "translator's name, so it is not used as author_in_english); translator from the "
                                   "text's own colophon (row 373). A translation of the Sanskrit root, aligned by the "
                                   "Dzongsar team's row pairing (read in full: no pairing errors)."),
            "text_id": None, "edition_id": None, "toc_id": None},
        "toc": toc_root})

    zh_pairs = [
        (27, [26, 27], "ZH 27 repeats the last two lines of ZH 26 (Tibetan row 26: …如火滅 是故名為入涅盤) and then renders the first half of Tibetan row 27 (菩薩所行不可得 初後現在三清淨). A half-verse slip in the doc's pairing; the row covers Tibetan rows 26 and 27."),
        (28, [27, 28], "ZH 28 opens with the rest of Tibetan row 27 (清淨無畏無戲論 是行最上般若行 — འདུས་མ་བྱས་ཡིན་སྤྲོས་མེད་… ཤེར་ཕྱིན་མཆོག་སྤྱོད་པ་ཡིན།) and continues with row 28 (大智菩薩行行時 發大慈悲為眾生). A half-verse slip; the row covers Tibetan rows 27 and 28."),
        (29, [28, 29], "ZH 29 opens with the end of Tibetan row 28 (為已不起眾生相 是行最上般若行 — སེམས་ཅན་འདུ་ཤེས་མེད།) and continues with row 29. A half-verse slip; the row covers Tibetan rows 28 and 29; the pairing resyncs at row 30."),
        (36, [36, 37], "ZH 36 renders Tibetan row 36 (常與無常苦樂等 我及無我 — རྟག་དང་མི་རྟག་བདེ་དང་སྡུག་བསྔལ་… བདག་དང་བདག་མེད་) and row 37 (不住有為及無為 — འདུས་མ་བྱས་ཁམས་མི་གནས་… འདུས་བྱས་ལ་ཡང་མི་གནས་). The Chinese compresses Tibetan rows 36–39 into rows 36–37; ZH 38 and 39 are empty."),
        (37, [38, 39], "ZH 37 renders Tibetan row 38 (不住此忍不可得 如渡大河不見岸 — བཟོད་པ་འདི་ལ་མ་བརྟེན་ཐོབ་པར་མི་ནུས་… ཚུ་རོལ་ཕ་རོལ་) and, loosely, row 39, not row 37, whose content is in ZH 36."),
        (135, [136], "ZH 135 is a verbatim duplicate of ZH 136 (如是世間諸如來 乃至緣覺及羅漢 …), which renders Tibetan row 136 (འཇིག་རྟེན་དེ་བཞིན་ཉིད་དང་དགྲ་བཅོམ་དེ་བཞིན་ཉིད།…); Tibetan row 135 has no Chinese counterpart. Likely a copy-paste slip in the Chinese doc; the duplicate text is kept as it is."),
        (210, [209, 210], "ZH 210 renders both Tibetan row 209 (如人有德力最勝 善解一切幻化法 — སྐྱེས་བུ་མཁས་པ་ཡོན་ཏན་ཀུན་ལྡན་… སྒྱུ་མ་སྒྲུབ་ཤེས་) and row 210 (彼人父母妻及子 遊行遠路多冤中 — ཕ་དང་མ་དང་ཆུང་མ་… དགྲ་བྱེད་མང་བ་དགོན་པའི་ལམ་); ZH 209 is empty."),
    ]
    works.append({
        "key": "zh-translation", "path": "1-SOURCES/Translations/zh-ratnagunasancayagatha.md", "adapter": "md_rows",
        "id_scheme": "h2", "text": "phakpadoepa-root-zh(bo-zh).md",
        "pair": {"own_side": "phakpadoepa-root-zh(bo-zh).md", "target_side": "phakpadoepa-root-bo(bo-zh).md"},
        "target": "bo-display",
        "pair_corrections": [{"row": r, "target_side_rows": t, "reason": why, "decided_by": D12, "date": TODAY}
                             for r, t, why in zh_pairs],
        "line_breaks": {
            "phrases": 7,
            "reason": ("One verse line per line: the Chinese verse lines are seven-character phrases, separated by a "
                       "space in the doc (a run of 14, 21 or 28 characters without a space is cut every 7). Letters "
                       "unchanged."),
            "decided_by": "the vault owner (\"if that can be also replicated on the Chinese … then also do that\")",
            "date": "2026-10-04"},
        "title": "佛母寶德藏般若波羅蜜經",
        "notes": ("Aligned row for row (373 rows) by the Dzongsar team with a Tibetan text byte-identical to the "
                  "display. Cut like the Tibetan (one row per verse), so no merge (D9) is needed. Read in full: seven "
                  "local pairing slips corrected (pair_corrections), the rest sound. Chinese-only material (fascicle "
                  "markers 卷上/卷中/卷下, editorial notes, extra verses in rows 105, 122, 133, 138, 201, 257–258) stays "
                  "unaligned, as made."),
        "frontmatter": {"title": "佛母寶德藏般若波羅蜜經", "language": "Chinese", "lang_tag": "zh",
                        "file_type": "translation", "root_text": ROOT_FILE, "verse_id_format": "section-paragraph",
                        "category_id": None, "license": "unknown", "source": None,
                        "other_ids": ["Dzongsar: phakpadoepa Tibetan-Chinese alignment doc"],
                        "source_description": ("Dzongsar Google Doc (Chinese side of the Tibetan-Chinese row alignment), "
                                               "exported as phakpadoepa-root-zh(bo-zh).md. Title from its first row "
                                               "(佛母寶德藏般若波羅蜜經卷上, without the fascicle marker 卷上). A translation "
                                               "aligned to the Tibetan; no metadata sheet, translator not recorded "
                                               "upstream."),
                        "text_id": None, "edition_id": None, "toc_id": None},
        "toc": toc_root})

    # ---------------------------------------------------------------- comm-1
    c1 = rows("phakpadoepa-comm-1(root-comm).md")
    m1 = meta("phakpadoepa-comm-1.csv")
    fm1, n1, s1 = placed("rangjung-dorje-tika")
    o1 = outline_file(
        "rangjung-dorje-tika", fm1, n1, {}, ["bo-rangjung-dorje-tika"],
        {"registered_id": "rangjung-dorje-tika",
         "edition": "ལྕགས་པར། — དཔལ་བརྩེགས་བོད་ཡིག་དཔེ་རྙིང་ཞིབ་འཇུག་ཁང་།, ལྷ་ས།, 2013 (Index: པོད། ༡༥ པར་གྲངས། ༢༥༨ - ༤༠༦)",
         "labels": {"bo": "verbatim from the inline headings of the Index's proofread pages (section numbers dropped)"},
         "placement": ("fetch_wiki_outline.py place: the whole proofread-page stream matched to the commentary's rows "
                       "by a monotonic chain of unique 12-letter anchors. The Wikisource edition interpolates the sa "
                       "bcad enumeration sentences (e.g. བཞི་པ་ཆོས་ཀྱི་རང་བཞིན་ལ་གཉིས་ཏེ།…) that the Dzongsar text does "
                       "not have; such a heading stands where the shared text resumes, and headings with no shared text "
                       "between them stand together. Spot-checked by Claude."),
         "body": ("# སྡུད་པ་ཚིགས་སུ་བཅད་པའི་ཊཱིཀ་ཡིད་བཞིན་གྱི་ནོར་བུ། — outline from the Wikisource Index\n\n"
                  f"{len(n1)} inline headings of the Index (depth up to {max(str(n['path']).count('.') + 1 for n in n1)}), "
                  f"{sum(1 for n in n1 if '.' in str(n['start_row']))} of them inside a Dzongsar row; those "
                  f"{len(s1)} rows are split (manifest `row_splits`, D7). "
                  f"{sum(1 for n in n1 if n.get('unplaced_letters_before'))} headings are followed in Wikisource by "
                  "a sa bcad sentence the Dzongsar text lacks; they stand before the first shared words.")})
    works.append({
        "key": "bo-rangjung-dorje-tika", "path": "1-SOURCES/Commentaries/bo-rangjung-dorje-tika.md",
        "adapter": "md_rows", "id_scheme": "h2", "text": "phakpadoepa-comm-1(root-comm).md",
        "pair": {"own_side": "phakpadoepa-comm-1(root-comm).md", "target_side": "phakpadoepa-root-1(root-comm).md"},
        "target": "bo-display",
        "title": c1[2].removesuffix("ཞེས་བྱ་བ་བཞུགས་སོ།།").strip() + "།" if False else
        "འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པའི་ཊཱི་ཀ་ཡིད་བཞིན་གྱི་ནོར་བུ་རིན་པོ་ཆེ་ལྟ་བུ་ཕ་རོལ་ཏུ་ཕྱིན་པ་རྒྱ་མཚོའི་སྡེ།",
        "meta": "phakpadoepa-comm-1.csv",
        "text_corrections": brackets({8: c1[8]}, "A square-bracketed Sanskrit word in the text is unbracketed and kept, "
                                     "because Obsidian renders bracketed text like link syntax. The bracketed form stays "
                                     "here and in the block's sidecar entry (source.corrections)."),
        "toc": {"kind": "outline", "file": o1,
                "note": (f"The commentary's table of contents on its Wikisource Index page "
                         f"({fm1['index_page']}, revision {fm1['index_revid']}; the Lhasa 2013 ལྕགས་པར། edition), "
                         "placed where its proofread pages put each heading (D6a, standing decision carried over from "
                         "heart-sutra-rails, 2026-10-03).")},
        "row_splits": with_targets(s1, c1, "bo-rangjung-dorje-tika", ROOT_FILE, prev,
                                   lambda s, tg, per: (f"Wikisource puts {len(s['at'])} heading(s) of the commentary's "
                                                       "table of contents inside this alignment row; it is cut there. "
                                                       "Each root segment the row transcludes is shown once, with the "
                                                       "first part that quotes it (the first part if none does).")),
        "toc_doc_not_used": "phakpadoepa-comm-1(toc).md",
        "notes": ("The TOC doc phakpadoepa-comm-1(toc).md is a 2.7× larger published volume (a publisher's preface and "
                  "life of the author, then this commentary and other material); it carries no heading labels and is "
                  "not used (Wikisource TOC preferred, D6a)."),
        "frontmatter": {
            "title": "འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པའི་ཊཱི་ཀ་ཡིད་བཞིན་གྱི་ནོར་བུ་རིན་པོ་ཆེ་ལྟ་བུ་ཕ་རོལ་ཏུ་ཕྱིན་པ་རྒྱ་མཚོའི་སྡེ།",
            "alt_titles": alts(m1, "སྡུད་པ་ཚིགས་སུ་བཅད་པའི་ཊིཀྐ་ཡིད་བཞིན་གྱི་ནོར་བུ།"),
            "title_in_english": g(m1, "title_alt_1", "en"),
            "author": None,
            "registered_id": "rangjung-dorje-tika", "language": "Tibetan", "lang_tag": "bo",
            "file_type": "commentary", "root_text": ROOT_FILE, "verse_id_format": "section-paragraph",
            "category_id": None, "license": "unknown", "source": g(m1, "source"),
            "other_ids": ["Dzongsar: phakpadoepa comm-1"],
            "source_description": ("Dzongsar alignment doc exported as phakpadoepa-comm-1(root-comm).md, paired row for "
                                   "row with phakpadoepa-root-1(root-comm).md (the team's own cut of the Tibetan root), "
                                   "carried onto the display Tibetan by letters. Title from the text's own title line "
                                   "(row 2); alternative titles and source from phakpadoepa-comm-1.csv. Author left empty "
                                   "on the vault owner's instruction (2026-10-03): the text names its author "
                                   "(བདག་འདྲའི་སེམས་དཔའ་རང་བྱུང་རྡོ་རྗེ་ཡིས།, row 3) and the text sheet gives "
                                   "ཀརྨ་པ་རང་བྱུང་རྡོ་རྗེ།, but the metadata sheet gives ཀརྨ་པ་མི་བསྐྱོད་རྡོ་རྗེ། / Karmapa "
                                   "Mikyo Dorje; to be settled by the text expert, together with the sheet's source "
                                   "(MW4CZ295070)."),
            "text_id": None, "edition_id": None, "toc_id": None}})

    # ---------------------------------------------------------------- comm-2
    c2 = rows("phakpadoepa-comm-2(root-comm).md")
    m2 = meta("phakpadoepa-comm-2.csv")
    ws_missing = ("རྩ་བའི་ས་བཅད་ལྔ་པ་སྤྱད་བྱ་ཆོས་ཀྱི་ཆེ་བ་ལ། འབྲས་བུ་བགྲོད་གཅིག་ལམ་དུ་ཚུད་པ་དང་། ལམ་གནས་པ་རྣམས་ཀྱི་མཆོག་ཏུ་"
                  "གྱུར་པ་དང་། ཤེས་བྱ་བསླབ་པ་ཐམས་ཅད་ཀྱི་མཆོག་ཡིན་པའི་ཆེ་བ་བསྟན་པ་གསུམ། དང་པོ། དེ་བཞིན་གཤེགས་ཡུམ་སོགས་"
                  "ཚིགས་བཅད་གཅིག་སྟེ། དེ༷་བཞིན༷་གཤེ༷གས་པ་ཐམས་ཅད་ཀྱི་ཡུམ༷་ཤེས༷་རབ༷་ཀྱི་ཕ༷་རོལ༷་ཏུ་ཕྱིན༷་པ༷་འདི༷་འཆ༷ད་པར་བྱེད་"
                  "པའི་ཚེ༷་ན་བྱང༷་ཆུབ༷་སེམ༷ས་དཔའ༷་གང༷་ཞིག༷་ཚུལ་འདི་ལ་སྙིང་ནས་མོས༷་པ་བྱེ༷ད་ཅིང༷་། བས༷མ་པ༷་ཐག༷་པས༷་འདི་ཉིད་"
                  "ཉམས་སུ་ལེན་པའམ་བསྒྲུབ༷་པ༷་ལ་མངོ༷ན་པར༷་བརྩོན༷་པར་བྱེ༷ད་ན༷། སྒོ་གསུམ་ཞི་ཞིང་དུལ་བའི་དེས༷་པ༷་སྟེ་བྱང་ཆུབ་"
                  "སེམས་དཔའ་དེ་ནི་ཐམ༷ས་ཅ༷ད་མཁྱེན༷་པ༷་ཉི༷ད་ཀྱི་ཚུལ་ལ༷་ཞུགས༷་པ་ཉིད་དུ་རིག༷་པར་བྱ༷་སྟེ། འདི་ནི་འབྲས་བུ་ཐམས་"
                  "ཅད་མཁྱེན་པའི་ཡེ་ཤེས་ལ་བགྲོད་པའི་ལམ་གཅིག་པུ་སྟེ་གཉིས་སུ་")
    fm2, n2, s2 = placed("mipham-lekshe")
    o2 = outline_file(
        "mipham-lekshe", fm2, n2, {}, ["bo-mipham-lekshe"],
        {"registered_id": "mipham-lekshe",
         "edition": "ལག་བྲིས་དབུ་ཅན། — a dbu can manuscript, 1892 (Index Year)",
         "labels": {"bo": "verbatim from the inline headings of the Index's proofread pages (section numbers dropped)"},
         "placement": ("fetch_wiki_outline.py place: the whole proofread-page stream matched to the commentary's rows by "
                       "a monotonic chain of unique 12-letter anchors, after the manifest's text_corrections. The "
                       "Dzongsar text carries most headings inline as ༈ labels; a heading stands before its ༈ label, "
                       "which stays in the text. Spot-checked by Claude."),
         "body": ("# ཡོན་ཏན་རིན་ཆེན་སྡུད་པའི་འགྲེལ་པ་རྒྱལ་བའི་ཡུམ་གྱི་དགོངས་དོན་ལ་ཕྱིན་ཅི་མ་ལོག་པར་འཇུག་པའི་ལེགས་བཤད། — outline from the Wikisource Index\n\n"
                  f"{len(n2)} inline headings of the Index (depth up to {max(str(n['path']).count('.') + 1 for n in n2)}), "
                  f"{sum(1 for n in n2 if '.' in str(n['start_row']))} of them inside a Dzongsar row; those {len(s2)} rows "
                  "are split (manifest `row_splits`, D7). The Dzongsar text lacks the opening of section 1.3.2.2.1.1.3.5 "
                  "and the body of 1.3.2.2.1.1.3.5.1 (row 209 keeps only its last words, མེད་པ་ཡིན་པའི་ཕྱིར་རོ། །); the "
                  "missing text is added from Wikisource pages 182 (revision 1247289), D8, recorded as a text_correction "
                  "of row 209.")})
    works.append({
        "key": "bo-mipham-lekshe", "path": "1-SOURCES/Commentaries/bo-mipham-lekshe.md", "adapter": "md_rows",
        "id_scheme": "h2", "text": "phakpadoepa-comm-2(root-comm).md",
        "pair": {"own_side": "phakpadoepa-comm-2(root-comm).md", "target_side": "phakpadoepa-root-2(root-comm).md"},
        "target": "bo-display",
        "title": "ཡོན་ཏན་རིན་ཆེན་སྡུད་པའི་འགྲེལ་པ་རྒྱལ་བའི་ཡུམ་གྱི་དགོངས་དོན་ལ་ཕྱིན་ཅི་མ་ལོག་པར་འཇུག་པའི་ལེགས་བཤད།",
        "meta": "phakpadoepa-comm-2.csv",
        "text_corrections": [{
            "row": 209, "find": "ནུས་སོ། །མེད་པ་ཡིན་པའི་ཕྱིར་རོ། །",
            "replace": "ནུས་སོ། །" + ws_missing + "མེད་པ་ཡིན་པའི་ཕྱིར་རོ། །",
            "source": ("Wikisource, Page:ཡོན་ཏན་རིན་ཆེན་སྡུད་པའི་འགྲེལ་པ་རྒྱལ་བའི་ཡུམ་གྱི་དགོངས་དོན་ལག་བྲིས་དབུ་ཅན།.pdf/182 "
                       "(revision 1247289), proofread; Index revision 1132490; the page's heading markup dropped"),
            "edition": "ལག་བྲིས་དབུ་ཅན། manuscript (1892) on Wikisource",
            "reason": ("The Dzongsar text lacks the opening of TOC section 1.3.2.2.1.1.3.5 (དེས་བསླབ་བྱ་ཆོས་ཀྱི་ཆེ་བ།) and "
                       "the body of 1.3.2.2.1.1.3.5.1 (འབྲས་བུ་བགྲོད་གཅིག་ལམ་དུ་ཚུད་པ།): row 209 runs from …ཕམ་པར་བྱེད་ནུས་སོ། "
                       "straight to that section's last words, མེད་པ་ཡིན་པའི་ཕྱིར་རོ། ། — a copying gap. The missing "
                       "text is added verbatim from Wikisource so both sections have their text (D8). Supplement rows "
                       "can only follow the last row, so it is written as a correction of row 209; the original row "
                       "stays in the sidecar."),
            "decided_by": D8, "date": TODAY}],
        "toc": {"kind": "outline", "file": o2,
                "note": (f"The commentary's table of contents on its Wikisource Index page ({fm2['index_page']}, "
                         f"revision {fm2['index_revid']}), placed where its proofread pages put each heading (D6a, "
                         "standing decision carried over from heart-sutra-rails, 2026-10-03).")},
        "row_splits": with_targets(s2, {**c2, 209: c2[209].replace("ནུས་སོ། །མེད་པ་ཡིན་པའི་ཕྱིར་རོ། །",
                                                                   "ནུས་སོ། །" + ws_missing + "མེད་པ་ཡིན་པའི་ཕྱིར་རོ། །")},
                                   "bo-mipham-lekshe", ROOT_FILE, prev,
                                   lambda s, tg, per: (f"Wikisource puts {len(s['at'])} heading(s) of the commentary's "
                                                       "table of contents inside this alignment row; it is cut there "
                                                       "(before the heading's own ༈ label where the row carries one). "
                                                       "Each root segment the row transcludes is shown once, with the "
                                                       "first part that quotes it (the first part if none does).")),
        "toc_doc_not_used": "phakpadoepa-comm-2(toc).md",
        "frontmatter": {
            "title": "ཡོན་ཏན་རིན་ཆེན་སྡུད་པའི་འགྲེལ་པ་རྒྱལ་བའི་ཡུམ་གྱི་དགོངས་དོན་ལ་ཕྱིན་ཅི་མ་ལོག་པར་འཇུག་པའི་ལེགས་བཤད།",
            "alt_titles": [x for x in alts(m2) if x.rstrip(" །") != "ཡོན་ཏན་རིན་ཆེན་སྡུད་པའི་འགྲེལ་པ་རྒྱལ་བའི་ཡུམ་གྱི་དགོངས་དོན་ལ་ཕྱིན་ཅི་མ་ལོག་པར་འཇུག་པའི་ལེགས་བཤད།"],
            "title_in_english": g(m2, "title_long_clean", "en"),
            "author": g(m2, "author"), "author_in_english": g(m2, "author", "en"),
            "registered_id": "mipham-lekshe", "language": "Tibetan", "lang_tag": "bo", "file_type": "commentary",
            "root_text": ROOT_FILE, "verse_id_format": "section-paragraph", "category_id": None, "license": "unknown",
            "source": g(m2, "source"), "other_ids": ["Dzongsar: phakpadoepa comm-2"],
            "source_description": ("Dzongsar alignment doc exported as phakpadoepa-comm-2(root-comm).md, paired row for "
                                   "row with phakpadoepa-root-2(root-comm).md (the team's own cut of the Tibetan root), "
                                   "carried onto the display Tibetan by letters. Title, author and source from "
                                   "phakpadoepa-comm-2.csv. One passage the Dzongsar text lacks (row 209) is added "
                                   "from the Wikisource manuscript (see the manifest)."),
            "text_id": None, "edition_id": None, "toc_id": None}})

    # ---------------------------------------------------------------- comm-3, comm-4
    labs = json.loads((TMP / "numbered-labels.json").read_text(encoding="utf-8"))
    fixes = json.loads((TMP / "numbered-label-fixes.json").read_text(encoding="utf-8"))
    lsplits = json.loads((TMP / "label-splits.json").read_text(encoding="utf-8")) \
        if (TMP / "label-splits.json").exists() else {}

    def fix_reason(f, L):
        was, new = f["was"], f["path"]
        if was.split(".")[:-1] != new.split(".")[:-1]:
            return (f"The TOC doc numbers this label {was}, but it stands under {new.rsplit('.', 1)[0]} (the "
                    f"label before it at that depth); its parent prefix is corrected, its own ordinal kept.")
        if len(was.split(".")[-1]) > 1 and int(was.split(".")[-1]) > int(new.split(".")[-1]) + 3:
            return (f"The TOC doc numbers this label {was}; its last part ({was.split('.')[-1]}) reads as two "
                    f"ordinals run together (one label covering two items). It takes the next free ordinal, {new}.")
        return (f"The TOC doc numbers this label {was}, which repeats or runs back on a sibling's number under the "
                f"same parent; it takes the next free ordinal, {new}.")

    for key, i, rid, title_row, toc_note in (
        ("bo-shasana-dibam-bedon-dronme", "3", "shasana-dibam-bedon-dronme", 2,
         "The Dzongsar TOC doc's own decimal-numbered heading labels (140), verbatim and in order; each label's number gives its place in the tree (toc.numbered, agreed by the vault owner on 2026-10-03). D6b."),
        ("bo-khenrab-jamyang-norbu-dronme", "4", "khenrab-jamyang-norbu-dronme", 2,
         "The Dzongsar TOC doc's own decimal-numbered heading labels (143), verbatim and in order; each label's number gives its place in the tree (toc.numbered, agreed by the vault owner on 2026-10-03). D6b."),
    ):
        c = rows(f"phakpadoepa-comm-{i}(root-comm).md")
        m = meta(f"phakpadoepa-comm-{i}.csv")
        L = labs[i]
        own_title = c[title_row].strip().rstrip("།").strip()
        own_title = re.sub(r"^༄༅།\s*།", "", own_title).removesuffix("ཞེས་བྱ་བ་བཞུགས་སོ").strip(" །") + "།"
        w = {"key": key, "path": f"1-SOURCES/Commentaries/{key}.md", "adapter": "md_rows", "id_scheme": "h2",
             "text": f"phakpadoepa-comm-{i}(root-comm).md",
             "pair": {"own_side": f"phakpadoepa-comm-{i}(root-comm).md",
                      "target_side": f"phakpadoepa-root-{i}(root-comm).md"},
             "target": "bo-display",
             # comm-3's sheet title drops the initial འ (ཕགས་པ…): the text's own title line is used instead
             "title": own_title if i == "3" else g(m, "title_long_clean").strip(" །") + "།",
             "meta": f"phakpadoepa-comm-{i}.csv",
             "toc": {"kind": "labels", "doc": f"phakpadoepa-comm-{i}(toc).md", "numbered": True, "labels": L,
                     "path_corrections": [{"n": f["n"], "label": f["label"], "path": f["path"],
                                           "reason": fix_reason(f, L), "decided_by": D12, "date": TODAY}
                                          for f in fixes[i]],
                     "note": toc_note}}
        if lsplits.get(key):
            w["row_splits"] = lsplits[key]
        if i == "4":
            w["pair_corrections"] = [{
                "row": 277, "target_side_rows": [],
                "reason": ("Commentary row 277 explains the translators' colophon (ལོ་ཙཱ་བའི་འགྱུར་བྱང་། … རྒྱ་གར་གྱི་མཁན་པོ་"
                           "བིདྱཱ་ཀ་ར་སིཧཾ་…), but the doc pairs it with row 277 of this commentary's own copy of the root, "
                           "which holds a different colophon — Zhalu Lotsāwa's revision note (…ཞྭ་ལུ་ལོ་ཙཱ་བ་དགེ་སློང་"
                           "དྷརྨ་པཱ་ལ་བྷ་དྲས་སླར་ཡང་དག་པར་བྱས་པའོ།), absent from the display text. Only 10 % of that row's "
                           "letters are in the display segment the letters pointed to, so the pairing gives no "
                           "transclusion. The passage it does comment on is the display's translators' colophon "
                           "(bo-ratnagunasancayagatha ^8-4); the text expert may add that link."),
                "decided_by": D12, "date": TODAY}]
        w["frontmatter"] = {
            "title": w["title"], "alt_titles": [x for x in alts(m, own_title) if x.strip(" །") + "།" != w["title"]],
            "title_in_english": g(m, "title_long_clean", "en") or g(m, "title_short", "en"),
            "author": g(m, "author"), "author_in_english": g(m, "author", "en"),
            "registered_id": rid, "language": "Tibetan", "lang_tag": "bo", "file_type": "commentary",
            "root_text": ROOT_FILE, "verse_id_format": "section-paragraph", "category_id": None, "license": "unknown",
            "source": g(m, "source"), "other_ids": [f"Dzongsar: phakpadoepa comm-{i}"],
            **({"title_note": "Title from the text's own title line (row 2); the metadata sheet's form, which lacks the initial འ, is kept in alt_titles."} if i == "3" else {}),
            "source_description": (f"Dzongsar alignment doc exported as phakpadoepa-comm-{i}(root-comm).md, paired row "
                                   f"for row with phakpadoepa-root-{i}(root-comm).md (the team's own cut of the Tibetan "
                                   f"root), carried onto the display Tibetan by letters. Title, author and source from "
                                   f"phakpadoepa-comm-{i}.csv. Not listed in the text sheet (phakpadoepa.csv); ingested "
                                   f"on the vault owner's instruction of 2026-10-03."),
            "text_id": None, "edition_id": None, "toc_id": None}
        works.append(w)

    man = {"raw_root": "0-INBOX/raw-data", "sidecar_dir": "1-SOURCES/Annotations", "works": works}
    head = ("# Intake manifest — Ratnaguṇasañcayagāthā / ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པ། (Phakpa Düpa)\n"
            "#\n# Read by 4-SYSTEM/Skills/aligned-corpus-intake/scripts/build_sources.py and verify.py.\n"
            "# Raw data: Dzongsar Google Docs exported as Markdown (row-aligned pairs) and metadata sheets as CSV,\n"
            "# named phakpadoepa-* by the vault owner (format: 4-SYSTEM/Skills/aligned-corpus-intake/references/\n"
            "# md-export-format.md). Built following the heart-sutra-rails handoff (HANDOFF.md, 2026-10-03); the\n"
            "# standing decisions D1–D13 are cited where applied.\n#\n"
            "# Build order = dependency order: the Sanskrit root, the Tibetan display text (its translation), then\n"
            "# what aligns to the Tibetan: the Chinese and the four commentaries.\n#\n"
            "# GENERATED by 0-INBOX/temp/make_manifest.py — change that script (or its inputs) and re-run it,\n"
            "# rather than editing this file by hand.\n\n")
    (RAW / "intake-manifest.yaml").write_text(
        head + yaml.safe_dump(man, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    print("manifest:", len(works), "works;",
          {w["key"]: len(w.get("row_splits") or []) for w in works}, "row splits")


if __name__ == "__main__":
    main()
