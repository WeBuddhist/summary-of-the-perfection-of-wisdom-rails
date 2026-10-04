#!/usr/bin/env python3
"""Fetch a text's table of contents from Wikisource or Wikipedia and write a
draft outline file for aligned-corpus-intake (`toc.kind: outline`).

    python3 fetch_wiki_outline.py wikisource "<Index:… .pdf title or URL>" --id <outline-id>
            --placed-on <work key> [--manifest 0-INBOX/raw-data/intake-manifest.yaml] [--vault .]
    python3 fetch_wiki_outline.py sections <page title or URL> [--wiki bo]
    python3 fetch_wiki_outline.py draft <page title or URL> --section N --id <outline-id>
            [--wiki bo] [--placed-on <work key>] [--manifest …] [--vault .]
    python3 fetch_wiki_outline.py sha1 <work key> [--manifest …] [--vault .]

wikisource  (the usual route) A proofread Wikisource Index page. Its table of
          contents is the page the Index embeds ({{:<title>}}); the headings
          stand inline in the Index's Page: pages, right before the text they
          open. The text after each heading is matched, by letters, to the rows
          of the --placed-on work's raw text: a heading at the start of a row
          gets start_row "N"; one inside a row gets "N.k" (part k of that row)
          and a suggested row_splits entry with the verbatim clause to cut
          before. Writes 0-INBOX/temp/wiki-toc-<id>/outline.draft.md (Index and
          page revisions pinned) and pages.json (the Page: wikitext read).
sections  List a Wikipedia article's sections (number, level, title).
draft     Wikipedia: write a draft outline from one section of an article —
          every sub-heading and bold-led list item / numbered line becomes a
          candidate node with an empty start_row (the placement pass fills it).
sha1      Print the sha1 of a manifest work's raw text, for placed_on_sha1.

Only the MediaWiki APIs of wikisource.org and <wiki>.wikipedia.org are
contacted, one request at a time, with a pause between and backoff on 429.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

UA = {"User-Agent": "railroads-vault/1.0 (wiki-toc-import)"}
INTAKE = pathlib.Path(__file__).resolve().parents[2] / "aligned-corpus-intake" / "scripts"
BOLD = "'" * 3


def api(wiki, **params):
    """wiki: 'bo' (-> bo.wikipedia.org) or a host such as 'wikisource.org'."""
    params |= {"format": "json", "formatversion": 2, "maxlag": 5}
    host = wiki if "." in wiki else f"{wiki}.wikipedia.org"
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        time.sleep(1.5)
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA)))
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 4:
                raise
            time.sleep(15 * (attempt + 1))
    if "error" in d:
        sys.exit(f"MediaWiki API error: {d['error'].get('info')}")
    return d


def page_title(arg):
    if arg.startswith("http"):
        return urllib.parse.unquote(arg.rsplit("/wiki/", 1)[-1]).replace("_", " ")
    return arg


def clean(label):
    s = re.sub(r"'''?|</?b>|</?u>|<small>.*?</small>|<nowiki>|</nowiki>", "", label)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    return s.strip(" :")


def manifest_work(args, key):
    man = yaml.safe_load((pathlib.Path(args.vault) / args.manifest).read_text(encoding="utf-8"))
    for w in man["works"]:
        if w["key"] == key:
            return man, w
    sys.exit(f"no work {key!r} in {args.manifest}")


# --------------------------------------------------------------------------
# Wikisource Index pages
# --------------------------------------------------------------------------

def _letters(s):
    return "".join(ch for ch in s if "ཀ" <= ch <= "ྼ" or ch.isalpha())


def _plain(wt):
    """Proofread-page wikitext -> roughly the text a reader sees."""
    wt = re.sub(r"<noinclude>.*?</noinclude>", "", wt, flags=re.S)
    wt = re.sub(r"\{\{[Hh]w/bo\|[^|}]*\|\|([^}]*)\}\}", r"\1", wt)
    wt = re.sub(r"\{\{[^{}]*\}\}", "", wt)
    return re.sub(r"<[^>]+>", "", wt)


HEAD = re.compile(r"=+\s*(?:<center>)?\s*((\d+(?:\.\d+)*)\s+[^<=\n]+?)\s*(?:</center>)?\s*(?:<br\s*/?>)?\s*=+")


def _toc_entries(wikitext):
    out = []
    for line in wikitext.splitlines():
        line = re.sub(r"\[\[[^|\]]*\|([^\]]*)\]\]", r"\1", line)
        line = re.sub(r"<[^>]+>|\{\{[^}]*\}\}", "", line).replace(BOLD, "").strip(" :")
        m = re.match(r"^(\d+(?:\.\d+)*)\s+(.+)$", line)
        if m:
            out.append((m.group(1), m.group(2).strip()))
    return out


def _find(rows, after):
    key = _letters(after)
    for n in (40, 25, 15):
        if len(key) < n:
            continue
        for r, t in rows:
            i = _letters(t).find(key[:n])
            if i >= 0:
                return r, i, t
    return None


def _char_at_letter(text, k):
    n = 0
    for j, ch in enumerate(text):
        if _letters(ch):
            if n == k:
                return j
            n += 1
    return len(text)


def cmd_wikisource(args):
    host = "wikisource.org"
    index = page_title(args.page)
    q = api(host, action="query", titles=index, prop="revisions", rvprop="ids|timestamp|content",
            rvslots="main", redirects=1)
    pg = q["query"]["pages"][0]
    if "missing" in pg:
        sys.exit(f"no such page: {index}")
    irev = pg["revisions"][0]
    m = re.search(r"\{\{:([^}|]+)\}\}", irev["slots"]["main"]["content"])
    toc_page = m.group(1).strip() if m else None
    toc = []
    if toc_page:
        t = api(host, action="query", titles=toc_page, prop="revisions", rvprop="ids|content", rvslots="main")
        toc = _toc_entries(t["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"])
    ns = api(host, action="query", meta="siteinfo", siprop="namespaces")["query"]["namespaces"]
    pns = next(v["id"] for v in ns.values() if v.get("canonical") == "Page")
    fname = pg["title"].split(":", 1)[1]
    listing = api(host, action="query", list="allpages", apnamespace=pns, apprefix=fname + "/", aplimit=500)
    titles = sorted((p["title"] for p in listing["query"]["allpages"]), key=lambda t: int(t.rsplit("/", 1)[1]))
    pages = []
    for i in range(0, len(titles), 4):
        r = api(host, action="query", titles="|".join(titles[i:i + 4]), prop="revisions",
                rvprop="ids|content", rvslots="main")
        for p in r["query"]["pages"]:
            if "revisions" in p:
                pages.append({"title": p["title"], "revid": p["revisions"][0]["revid"],
                              "content": p["revisions"][0]["slots"]["main"]["content"]})
    pages.sort(key=lambda p: int(p["title"].rsplit("/", 1)[1]))
    stream, starts = "", []
    for p in pages:
        starts.append((len(stream), p))
        stream += p["content"]
    heads = []
    for m in HEAD.finditer(stream):
        page = [p for o, p in starts if o <= m.start()][-1]
        heads.append({"number": m.group(2), "label": re.sub(r"^\d+(?:\.\d+)*\s+", "", m.group(1)).strip(),
                      "page": page["title"].rsplit("/", 1)[1], "revid": page["revid"],
                      "after": _plain(stream[m.end():m.end() + 2000])})
    man, w = manifest_work(args, args.placed_on)
    raw = pathlib.Path(args.vault) / man["raw_root"] / w["text"]
    sys.path.insert(0, str(INTAKE))
    from md_export import read_rows
    rows = [(int(r["row"]), r["text"]) for r in read_rows(raw)]
    nodes, splits = [], {}
    for h in heads:
        node = {"path": h["number"], "start_row": None, "labels": {"bo": h["label"]},
                "page": h["page"], "page_revid": h["revid"]}
        hit = _find(rows, h["after"])
        if not hit:
            node["unmatched"] = h["after"].strip()[:80]
        else:
            r, i, t = hit
            pos = _char_at_letter(t, i)
            if i == 0:
                node["start_row"] = str(r)
            else:
                clause = t[pos:pos + 200].split("།")[0] + "།"
                splits.setdefault(r, []).append(clause.strip())
                node["start_row"] = f"{r}.{len(splits[r]) + 1}"
                node["mid_row"] = True
            node["clause"] = t[pos:pos + 60].strip()
        nodes.append(node)
    numbers = {h["number"] for h in heads}
    missing = [f"{n} {l}" for n, l in toc if n not in numbers]
    fm = {"outline_id": args.id, "source": host, "index_page": pg["title"],
          "index_url": f"https://{host}/wiki/" + urllib.parse.quote(pg["title"].replace(" ", "_")),
          "index_revid": irev["revid"], "toc_page": toc_page,
          "retrieved": datetime.date.today().isoformat(),
          "placed_on": args.placed_on, "placed_on_text": f"{man['raw_root']}/{w['text']}",
          "placed_on_sha1": hashlib.sha1(raw.read_bytes()).hexdigest(),
          "toc_entries": [f"{n} {l}" for n, l in toc],
          "toc_entries_without_inline_heading": missing, "status": "draft"}
    out = pathlib.Path(args.vault) / "0-INBOX" / "temp" / f"wiki-toc-{args.id}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
    split_yaml = [{"row": r, "at": c, "targets": "<per part: indices into the row's own targets>",
                   "reason": "…", "decided_by": "…", "date": datetime.date.today().isoformat()}
                  for r, c in sorted(splits.items())]
    body = ("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n\n"
            f"# Draft outline — {pg['title']}\n\nNodes from the inline headings of the Index's pages, placed by "
            "matching the text after each heading to the rows by letters. Check every node, add a label per "
            "language of every work the outline applies to, and — if any node is `mid_row` — get the human "
            "decision on splitting those rows before copying `row_splits` into the manifest.\n\n"
            "```yaml\n" + yaml.safe_dump({"nodes": nodes}, allow_unicode=True, sort_keys=False) + "```\n\n"
            "Suggested manifest `row_splits` for the work it is placed on (not read by the build from here):\n\n"
            "```text\n" + yaml.safe_dump({"row_splits": split_yaml}, allow_unicode=True, sort_keys=False) + "```\n")
    (out / "outline.draft.md").write_text(body, encoding="utf-8")
    print(f"Index revision {irev['revid']}; TOC page {toc_page}: {len(toc)} entries; "
          f"{len(heads)} inline headings in {len(pages)} pages -> {out / 'outline.draft.md'}")
    for n in nodes:
        print(f"  {n['path']:6s} row {str(n['start_row']):6s} {'MID ' if n.get('mid_row') else '    '}"
              f"{n['labels']['bo']}  (page {n['page']}){'  UNMATCHED' if n.get('unmatched') else ''}")
    if missing:
        print("  TOC entries with no inline heading:", missing)


TOKEN = re.compile(r"<noinclude>.*?</noinclude>"
                   r"|(?P<eq>={2,})[ \t]*(?P<head>[^=\n]+?)[ \t]*(?P=eq)"
                   r"|<section\s+begin=\"(?P<sec>[^\"]+)\"\s*/>"
                   r"|\{\{[Hh]w[-/]bo\|(?P<hwa>[^|}]*)\|\|(?P<hwb>[^}]*)\}\}"
                   r"|\{\{[^{}]*\}\}|<[^>]+>", re.S | re.M)


def _stream(pages):
    """Proofread pages -> (plain text, markers). Headings and <section> tags
    are removed from the text and kept as markers at the offset where they
    stood: {"kind": "heading"|"section", "number", "label", "name", "page",
    "revid", "at"}."""
    text, marks = [], []
    n = 0
    for p in pages:
        c, last = p["content"], 0
        for m in TOKEN.finditer(c):
            piece = c[last:m.start()]
            text.append(piece)
            n += len(piece)
            last = m.end()
            base = {"page": p["title"].rsplit("/", 1)[1], "revid": p["revid"], "at": n}
            if m.group("head") is not None:
                h = re.sub(r"<[^>]+>|\{\{[^{}]*\}\}|'''?", "", m.group("head")).strip()
                hm = re.match(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$", h)
                if hm:
                    marks.append(dict(base, kind="heading", number=hm.group(1), label=hm.group(2).strip()))
            elif m.group("sec"):
                marks.append(dict(base, kind="section", name=m.group("sec")))
            elif m.group("hwa") is not None:
                piece = m.group("hwa") + m.group("hwb")
                text.append(piece)
                n += len(piece)
        text.append(c[last:])
        n += len(c) - last
    return "".join(text), marks


def _fixed(text, corrections):
    for x in corrections:
        if text.count(x["find"]) != 1:
            sys.exit(f"text_correction for row {x['row']} does not match exactly once: {x['find']!r}")
        text = text.replace(x["find"], x["replace"])
    return text


def _anchor_chain(la, lb, k=12):
    """Pairs (i, j): la[i:i+k] == lb[j:j+k], each run unique in both texts,
    reduced to the longest chain increasing in both (so order is kept)."""
    def uniq(s):
        seen, dup = {}, set()
        for i in range(len(s) - k + 1):
            g = s[i:i + k]
            if g in seen:
                dup.add(g)
            else:
                seen[g] = i
        return {g: i for g, i in seen.items() if g not in dup}
    ua, ub = uniq(la), uniq(lb)
    pairs = sorted((i, ub[g]) for g, i in ua.items() if g in ub)
    import bisect
    tails, idx, back = [], [], [-1] * len(pairs)
    for n, (_, j) in enumerate(pairs):
        p = bisect.bisect_left(tails, j)
        if p == len(tails):
            tails.append(j)
            idx.append(n)
        else:
            tails[p], idx[p] = j, n
        back[n] = idx[p - 1] if p else -1
    out, n = [], idx[-1] if idx else -1
    while n != -1:
        out.append(pairs[n])
        n = back[n]
    return out[::-1]


def cmd_place(args):
    """Place the inline headings (or <section> tags) of an already-fetched
    Index on the rows of a work by projecting the whole proofread-page stream
    onto the rows' letters (aligned-corpus-intake's Projector): tolerant of
    edition variants, where the `wikisource` command's prefix match fails.
    --sections FILE (json {section name: {path, label}}) places a TOC whose
    entries are named <section>s rather than inline headings."""
    vault = pathlib.Path(args.vault)
    out = vault / "0-INBOX" / "temp" / f"wiki-toc-{args.id}"
    pages = json.loads((out / "pages.json").read_text(encoding="utf-8"))
    draft = (out / "outline.draft.md").read_text(encoding="utf-8")
    fm = yaml.safe_load(re.match(r"\A---\n(.*?)\n---\n", draft, re.S).group(1))
    stream, marks = _stream(pages)
    if args.sections:
        want = json.loads(pathlib.Path(args.sections).read_text(encoding="utf-8"))
        first = {}
        for mk in marks:
            if mk["kind"] == "section" and mk["name"] in want:
                first.setdefault(mk["name"], mk)
        missing = [s for s in want if s not in first]
        if missing:
            sys.exit(f"sections not found on the pages: {missing}")
        marks = sorted((dict(first[s], number=str(v["path"]), label=v["label"]) for s, v in want.items()),
                       key=lambda m: m["at"])
    else:
        marks = [mk for mk in marks if mk["kind"] == "heading"]
    man, w = manifest_work(args, args.placed_on)
    raw = vault / man["raw_root"] / w["text"]
    sys.path.insert(0, str(INTAKE))
    from md_export import read_rows
    from project import is_letter
    rows = [(int(r["row"]), r["text"]) for r in read_rows(raw)]
    fixes = {}
    for x in w.get("text_corrections") or []:          # human-decided fixes, as the build applies them
        fixes.setdefault(int(x["row"]), []).append(x)
    rows = [(r, _fixed(t, fixes.get(r, []))) for r, t in rows]
    comm, spans = "", []
    for r, t in rows:
        spans.append((len(comm), len(comm) + len(t), r, t))
        comm += t + "\n"
    import bisect
    from project import letters as _lt
    la, ia = _lt(stream)
    lb, ib = _lt(comm)
    chain = _anchor_chain(la, lb)
    ca = [x for x, _ in chain]
    stats = {"letters_wikisource": len(la), "letters_rows": len(lb), "anchors": len(chain)}
    nodes, splits, prev = [], {}, (-1, -1)
    for mk in marks:
        node = {"path": mk["number"], "start_row": None, "labels": {"bo": mk["label"]},
                "page": mk["page"], "page_revid": mk["revid"]}
        h = bisect.bisect_left(ia, mk["at"])          # first Wikisource letter after the marker
        pos, gap = None, 0
        k = bisect.bisect_left(ca, h)
        if k < len(chain):
            # walk back from the next anchor while the letters agree
            x, y = chain[k]
            while x > h and y > 0 and la[x - 1] == lb[y - 1] and (k == 0 or x - 1 >= chain[k - 1][0]):
                x, y = x - 1, y - 1
            gap = x - h
            if gap and k > 0:
                # or walk forward from the previous anchor
                x0, y0 = chain[k - 1]
                x0, y0 = x0 + 12, y0 + 12
                while x0 < h and y0 < len(lb) and la[x0] == lb[y0]:
                    x0, y0 = x0 + 1, y0 + 1
                if x0 == h:
                    y, gap = y0, 0
            pos = ib[min(y, len(ib) - 1)]
        if pos is None:
            node["unmatched"] = re.sub(r"\s+", " ", stream[mk["at"]:mk["at"] + 80]).strip()
            nodes.append(node)
            continue
        s, e, r, t = next(x for x in spans if x[0] <= pos <= x[1])
        off = pos - s
        # an in-text label the heading duplicates (e.g. ༈ …) stays with its section
        lab = "".join(c for c in mk["label"] if is_letter(c))
        before = "".join(c for c in t[:off] if is_letter(c))
        if lab and before.endswith(lab):
            k, seen = off, 0
            while seen < len(lab):
                k -= 1
                if is_letter(t[k]):
                    seen += 1
            while k > 0 and t[k - 1] in "༈༄༅།་ \t":
                k -= 1
            off = k
            node["label_in_row"] = True
        if gap > 5:
            node["unplaced_letters_before"] = gap
        if not any(is_letter(c) for c in t[:off]):
            node["start_row"] = str(r)
            here = (r, 0)
        else:
            cuts = splits.setdefault(r, [])
            if off not in cuts:
                cuts.append(off)
            if cuts != sorted(cuts):
                node["out_of_order"] = True
            node["start_row"] = f"{r}.{sorted(cuts).index(off) + 2}"
            node["mid_row"] = True
            here = (r, off)
        if here < prev:
            node["out_of_order"] = True
        prev = here
        node["clause"] = t[off:off + 60].strip()
        nodes.append(node)
    # verbatim clauses, each found once in its row, cut in order
    split_yaml = []
    for r, cuts in sorted(splits.items()):
        t = dict((x[2], x[3]) for x in spans)[r]
        at = []
        for off in sorted(cuts):
            n = 8
            while t.count(t[off:off + n]) > 1 and off + n < len(t):
                n += 4
            j = t.find("།", off + n - 1)
            clause = t[off:j + 1] if j != -1 and j - off < 120 and t.count(t[off:j + 1]) == 1 else t[off:off + n]
            at.append(clause)
        split_yaml.append({"row": r, "at": at})
    fm.update({"placed_on": args.placed_on, "placed_on_text": f"{man['raw_root']}/{w['text']}",
               "placed_on_sha1": hashlib.sha1(raw.read_bytes()).hexdigest(),
               "placement": f"letters of the whole proofread-page stream matched to the rows by a monotonic chain of unique 12-letter anchors ({stats})"})
    body = ("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n\n"
            f"# Placed outline — {fm.get('index_page')}\n\n"
            "```yaml\n" + yaml.safe_dump({"nodes": nodes}, allow_unicode=True, sort_keys=False) + "```\n\n"
            "```text\n" + yaml.safe_dump({"row_splits": split_yaml}, allow_unicode=True, sort_keys=False) + "```\n")
    (out / "outline.placed.md").write_text(body, encoding="utf-8")
    bad = [n for n in nodes if n.get("unmatched") or n.get("out_of_order")]
    print(f"{len(nodes)} nodes, {sum(1 for n in nodes if n.get('mid_row'))} inside rows "
          f"({len(splits)} rows to split), {len(bad)} unmatched/out of order; {stats}"
          f" -> {out / 'outline.placed.md'}")
    for n in bad:
        print("  ", n["path"], n["labels"]["bo"], n.get("unmatched", ""), "OUT OF ORDER" if n.get("out_of_order") else "")


# --------------------------------------------------------------------------
# Wikipedia articles
# --------------------------------------------------------------------------

def candidates(wikitext):
    """(depth, label, kind) for every heading and bold-led list item / numbered line."""
    out, base = [], None
    for line in wikitext.splitlines():
        h = re.match(r"^(=+)\s*(.*?)\s*\1\s*$", line)
        if h:
            lvl = len(h.group(1))
            if base is None:
                base = lvl                       # the outline section's own heading
                continue
            out.append((lvl - base, clean(h.group(2)), "heading"))
            continue
        b = re.match(r"^([*#]+)\s*(?:[^']{0,12}?)'''(.+?)'''", line)
        if b:
            out.append((len(b.group(1)), clean(b.group(2)), "item"))
            continue
        n = re.match(r"^[༠-༩0-9ཀ-ཿ]+\s*[།༽.)]\s*'''(.+?)'''", line)
        if n:
            out.append((1, clean(n.group(1)), "numbered"))
    return out


def paths(cands):
    """Depths -> decimal paths: items under a heading nest below it."""
    res, stack, counters = [], [], {}
    for depth, label, kind in cands:
        depth = max(1, depth)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        parent = stack[-1][1] if stack else ""
        counters[parent] = counters.get(parent, 0) + 1
        path = f"{parent}.{counters[parent]}" if parent else str(counters[parent])
        res.append({"path": path, "label": label, "kind": kind})
        stack.append((depth, path))
    return res


def cmd_sections(args):
    d = api(args.wiki, action="parse", page=page_title(args.page), prop="sections", redirects=1)
    print(d["parse"]["title"])
    for s in d["parse"]["sections"]:
        print(f"  {s['index']:>3}  {'  ' * (int(s['level']) - 2)}{s['number']} {clean(s['line'])}")


def cmd_draft(args):
    title = page_title(args.page)
    q = api(args.wiki, action="query", titles=title, prop="revisions", rvprop="ids|timestamp", redirects=1)
    pg = q["query"]["pages"][0]
    rev = pg["revisions"][0]
    d = api(args.wiki, action="parse", oldid=rev["revid"], prop="wikitext", section=args.section)
    wt = d["parse"]["wikitext"]
    sec = next((s for s in api(args.wiki, action="parse", oldid=rev["revid"], prop="sections")["parse"]["sections"]
                if str(s["index"]) == str(args.section)), {})
    out = pathlib.Path(args.vault) / "0-INBOX" / "temp" / f"wiki-toc-{args.id}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "section.wiki").write_text(wt, encoding="utf-8")
    fm = {"outline_id": args.id, "source": f"{args.wiki}.wikipedia.org", "page_title": pg["title"],
          "page_url": f"https://{args.wiki}.wikipedia.org/wiki/" + urllib.parse.quote(pg["title"].replace(" ", "_")),
          "page_id": pg["pageid"], "revid": rev["revid"], "revision_timestamp": rev["timestamp"],
          "retrieved": datetime.date.today().isoformat(),
          "section": f"{sec.get('number', args.section)} {clean(sec.get('line', ''))}".strip(),
          "placed_on": args.placed_on, "placed_on_text": None, "placed_on_sha1": None, "status": "draft"}
    if args.placed_on:
        man, w = manifest_work(args, args.placed_on)
        p = pathlib.Path(args.vault) / man["raw_root"] / w["text"]
        fm["placed_on_text"] = f"{man['raw_root']}/{w['text']}"
        fm["placed_on_sha1"] = hashlib.sha1(p.read_bytes()).hexdigest()
    nodes = [{"path": n["path"], "start_row": None, "labels": {args.wiki: n["label"]}, "candidate": n["kind"]}
             for n in paths(candidates(wt))]
    body = ("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---\n\n"
            f"# Draft outline — {pg['title']}\n\nCandidates from the section's headings and bold-led items. "
            "Keep, drop or re-nest them, fill `start_row`, add a label per language of every work the "
            "outline applies to, then promote it.\n\n"
            "```yaml\n" + yaml.safe_dump({"nodes": nodes}, allow_unicode=True, sort_keys=False) + "```\n")
    (out / "outline.draft.md").write_text(body, encoding="utf-8")
    print(f"revision {rev['revid']} ({rev['timestamp']}); {len(nodes)} candidate nodes -> {out / 'outline.draft.md'}")
    for n in nodes:
        print(f"  {n['path']:8s} {n['labels'][args.wiki]}")


def cmd_sha1(args):
    man, w = manifest_work(args, args.work)
    p = pathlib.Path(args.vault) / man["raw_root"] / w["text"]
    print(hashlib.sha1(p.read_bytes()).hexdigest(), p)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("wikisource", "place", "sections", "draft", "sha1"):
        p = sub.add_parser(name)
        if name == "place":
            p.add_argument("id")
            p.add_argument("--placed-on", dest="placed_on", required=True)
            p.add_argument("--sections", help="json {section name: {path, label}} for a TOC of named <section>s")
            p.add_argument("--vault", default=".")
            p.add_argument("--manifest", default="0-INBOX/raw-data/intake-manifest.yaml")
            continue
        p.add_argument("work" if name == "sha1" else "page")
        p.add_argument("--wiki", default="bo")
        p.add_argument("--vault", default=".")
        p.add_argument("--manifest", default="0-INBOX/raw-data/intake-manifest.yaml")
        if name == "draft":
            p.add_argument("--section", required=True, help="section index from `sections`")
        if name in ("draft", "wikisource"):
            p.add_argument("--id", required=True)
            p.add_argument("--placed-on", dest="placed_on", required=name == "wikisource")
    a = ap.parse_args()
    {"wikisource": cmd_wikisource, "place": cmd_place, "sections": cmd_sections, "draft": cmd_draft,
     "sha1": cmd_sha1}[a.cmd](a)


if __name__ == "__main__":
    main()
