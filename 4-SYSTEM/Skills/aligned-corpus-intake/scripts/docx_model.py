#!/usr/bin/env python3
"""Lossless .docx reader (stdlib only).

Reads a Word document into a plain JSON-able model that keeps every piece of
human annotation a parser could need: paragraph order, paragraph style,
numbering, bookmarks, comment anchors, and — per run — the text with its
colour, highlight, shading, bold, italic, underline, strike and vertical
alignment. Nothing is normalised here; interpretation happens downstream.

    python3 docx_model.py <file.docx>            # print a summary
    python3 docx_model.py <file.docx> --json     # dump the full model

Model shape:
    {"paragraphs": [{"index", "style", "numbering", "bookmarks",
                     "comment_ids", "text",
                     "runs": [{"text", "color", "highlight", "shading",
                               "bold", "italic", "underline", "strike",
                               "vert_align"}]}],
     "comments": {id: {"author", "date", "text"}},
     "footnotes": {id: text},     # paragraphs carry "footnote_refs": [{id, offset}]
     "sha1": <hash of the .docx bytes>}

A paragraph's "text" is the exact concatenation of its runs' text. Line
breaks inside a paragraph are kept as "\n" and tabs as "\t".
"""
import hashlib
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Colours that carry no annotation: Word's "automatic" and the near-black
# body-text colours the source documents use for plain prose.
NEUTRAL_COLOURS = {None, "auto", "000000", "0a0a0a", "222222", "2f2f2f", "333333"}


def _on(el, tag):
    """True when a toggle property (w:b, w:i, …) is present and not switched off."""
    x = el.find(W + tag) if el is not None else None
    return x is not None and x.get(W + "val", "true").lower() not in ("0", "false", "none")


def _val(el, tag, attr="val"):
    x = el.find(W + tag) if el is not None else None
    return x.get(W + attr) if x is not None else None


def _run_props(rpr):
    shading = _val(rpr, "shd", "fill")
    if shading and shading.lower() in ("auto", "ffffff"):
        shading = None
    underline = _val(rpr, "u")
    color = _val(rpr, "color")
    return {
        "color": color.lower() if color else None,
        "highlight": _val(rpr, "highlight"),
        "shading": shading.lower() if shading else None,
        "bold": _on(rpr, "b"),
        "italic": _on(rpr, "i"),
        "underline": underline if underline and underline != "none" else None,
        "strike": _on(rpr, "strike"),
        "vert_align": _val(rpr, "vertAlign"),
    }


def _run_text(r):
    out = []
    for x in r:
        if x.tag == W + "footnoteReference":
            # zero-width marker, turned into a footnote_refs entry by read();
            # never part of the paragraph text
            out.append("\x00FN" + (x.get(W + "id") or "") + "\x00")
            continue
        if x.tag == W + "t":
            out.append(x.text or "")
        elif x.tag == W + "tab":
            out.append("\t")
        elif x.tag in (W + "br", W + "cr"):
            out.append("\n")
        elif x.tag == W + "noBreakHyphen":
            out.append("‑")
    return "".join(out)


def _iter_runs(p):
    """Yield w:r elements in document order, including those nested in
    hyperlinks, smart tags, inserted-text and simple fields. Deleted text
    (w:del) is skipped: it is not part of the visible document."""
    for child in p:
        tag = child.tag
        if tag == W + "r":
            yield child
        elif tag in (W + "hyperlink", W + "smartTag", W + "ins", W + "fldSimple",
                     W + "customXml", W + "sdt", W + "sdtContent"):
            yield from _iter_runs(child)
        elif tag == W + "del":
            continue


def _comments(z):
    if "word/comments.xml" not in z.namelist():
        return {}
    root = ET.fromstring(z.read("word/comments.xml"))
    out = {}
    for c in root.findall(W + "comment"):
        text = "\n".join("".join(t.text or "" for t in p.iter(W + "t")) for p in c.iter(W + "p"))
        out[c.get(W + "id")] = {"author": c.get(W + "author"), "date": c.get(W + "date"), "text": text}
    return out


def _footnotes(z):
    """Word footnotes (id -> text), e.g. a collation apparatus. Separator
    footnotes (w:type set) are skipped."""
    if "word/footnotes.xml" not in z.namelist():
        return {}
    root = ET.fromstring(z.read("word/footnotes.xml"))
    out = {}
    for f in root.findall(W + "footnote"):
        if f.get(W + "type"):
            continue
        out[f.get(W + "id")] = "\n".join("".join(t.text or "" for t in p.iter(W + "t")) for p in f.iter(W + "p")).strip()
    return out


_FN = re.compile("\x00FN([^\x00]*)\x00")


def _pull_footnote_refs(para):
    """Move footnote markers out of the runs into para["footnote_refs"]
    (id + offset into the paragraph text, i.e. right after the lemma)."""
    refs, pos = [], 0
    for r in para["runs"]:
        clean, last = [], 0
        for m in _FN.finditer(r["text"]):
            clean.append(r["text"][last:m.start()])
            refs.append({"id": m.group(1), "offset": pos + sum(len(x) for x in clean)})
            last = m.end()
        clean.append(r["text"][last:])
        r["text"] = "".join(clean)
        pos += len(r["text"])
    para["runs"] = [r for r in para["runs"] if r["text"]]
    if refs:
        para["footnote_refs"] = refs


def read(path):
    data = open(path, "rb").read()
    z = zipfile.ZipFile(path)
    doc = ET.fromstring(z.read("word/document.xml"))
    body = doc.find(W + "body")
    paragraphs = []
    open_comments = set()
    # Body-level paragraphs and table cells, in document order.
    for p in body.iter(W + "p"):
        ppr = p.find(W + "pPr")
        numpr = ppr.find(W + "numPr") if ppr is not None else None
        para = {
            "index": len(paragraphs),
            "style": _val(ppr, "pStyle"),
            "numbering": ({"level": _val(numpr, "ilvl"), "id": _val(numpr, "numId")}
                          if numpr is not None else None),
            "bookmarks": [b.get(W + "name") for b in p.iter(W + "bookmarkStart")
                          if not (b.get(W + "name") or "").startswith("_")],
            "comment_ids": [],
            "runs": [],
        }
        for el in p.iter():
            if el.tag == W + "commentRangeStart":
                open_comments.add(el.get(W + "id"))
            elif el.tag == W + "commentReference":
                open_comments.add(el.get(W + "id"))
        para["comment_ids"] = sorted(open_comments)
        for el in p.iter():
            if el.tag == W + "commentRangeEnd":
                open_comments.discard(el.get(W + "id"))
        for r in _iter_runs(p):
            text = _run_text(r)
            if not text:
                continue
            props = _run_props(r.find(W + "rPr"))
            prev = para["runs"][-1] if para["runs"] else None
            if prev and all(prev[k] == v for k, v in props.items()):
                prev["text"] += text          # merge identical neighbours
            else:
                para["runs"].append({"text": text, **props})
        _pull_footnote_refs(para)
        para["text"] = "".join(r["text"] for r in para["runs"])
        paragraphs.append(para)
    _render_numbers(z, paragraphs)
    return {"paragraphs": paragraphs, "comments": _comments(z), "footnotes": _footnotes(z),
            "sha1": hashlib.sha1(data).hexdigest()}


def _render_numbers(z, paragraphs):
    """Add numbering["rendered"]: the label Word displays for an auto-numbered
    paragraph (e.g. "12."). Human references are often typed as these
    numbers, so the rendered value is part of the text a reader saw."""
    if "word/numbering.xml" not in z.namelist():
        return
    root = ET.fromstring(z.read("word/numbering.xml"))
    abstract = {}
    for an in root.findall(W + "abstractNum"):
        lv = {}
        for l in an.findall(W + "lvl"):
            lv[l.get(W + "ilvl")] = {"start": int(_val(l, "start") or 1),
                                     "fmt": _val(l, "numFmt"), "text": _val(l, "lvlText")}
        abstract[an.get(W + "abstractNumId")] = lv
    nums = {n.get(W + "numId"): abstract.get(_val(n, "abstractNumId"), {})
            for n in root.findall(W + "num")}
    counters = {}
    for p in paragraphs:
        n = p["numbering"]
        if not n:
            continue
        lv = nums.get(n["id"], {}).get(n["level"] or "0")
        if not lv:
            continue
        key = (n["id"], n["level"])
        counters[key] = counters.get(key, lv["start"] - 1) + 1
        # deeper levels restart when a shallower one advances
        for k in list(counters):
            if k[0] == n["id"] and int(k[1] or 0) > int(n["level"] or 0):
                del counters[k]
        value = counters[key]
        n["value"] = value
        n["format"] = lv["fmt"]
        n["rendered"] = (lv["text"] or "%1.").replace(f"%{int(n['level'] or 0) + 1}", str(value)) \
            if lv["fmt"] == "decimal" else None


def marked(para, neutral=NEUTRAL_COLOURS):
    """Render a paragraph with its non-neutral formatting made visible, for
    human inspection: {color:text}, **bold**, _italic_, [[hl:x|text]]."""
    out = []
    for r in para["runs"]:
        t = r["text"]
        if r["bold"]:
            t = f"**{t}**"
        if r["italic"]:
            t = f"_{t}_"
        if r["color"] not in neutral:
            t = "{" + r["color"] + ":" + t + "}"
        if r["highlight"] and r["highlight"] != "white":
            t = f"[[hl:{r['highlight']}|{t}]]"
        out.append(t)
    return "".join(out)


if __name__ == "__main__":
    m = read(sys.argv[1])
    if "--json" in sys.argv:
        json.dump(m, sys.stdout, ensure_ascii=False, indent=1)
    else:
        print(f"paragraphs={len(m['paragraphs'])} comments={len(m['comments'])} sha1={m['sha1']}")
        for p in m["paragraphs"][:40]:
            print(f"{p['index']:4d} {p['style'] or '':10s} {marked(p)[:160]}")
