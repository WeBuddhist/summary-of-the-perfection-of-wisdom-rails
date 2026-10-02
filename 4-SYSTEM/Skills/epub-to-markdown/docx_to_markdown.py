#!/usr/bin/env python3
"""
Convert a .docx to Markdown, preserving the annotations that carry meaning
in this corpus. Standard library only — a .docx is a zip whose
`word/document.xml` holds the content.

What is preserved and why:

* **Word auto-numbering.** Most documents here number every segment through
  Word's numbering engine (`<w:numPr>`), so the numbers exist only as a
  numbering definition plus a counter — they are NOT in the text runs. Those
  numbers are the segmentation, and the Tibetan and Chinese witnesses of a
  work carry the *same* count, which is what aligns them. A converter that
  reads only `<w:t>` silently discards the entire alignment layer. This one
  reconstructs the counters the way Word does and emits each number both
  visibly (`3.`) and as an Obsidian block ID (`^s3`) so a segment can be
  addressed across files as `[[<other-file>#^s3]]`.
* **Footnotes.** Emitted as Obsidian footnotes (`[^3]` inline, definitions at
  the end) rather than dropped.
* **Highlighting.** Emitted as `==text==`; in these documents it marks
  passages someone flagged.
* **Tabs and explicit breaks** inside a paragraph.

Word splits one visible word across several `<w:t>` runs whenever formatting
changes mid-word, so runs are joined without separators.

There are no Heading styles or TOC fields anywhere in this corpus — the
structure is the numbered segmentation itself.
"""

import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ROMAN = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
         (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]


def _roman(n):
    out = []
    for v, s in ROMAN:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def _letter(n):
    out = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        out = chr(ord("a") + r) + out
    return out


def _fmt_number(n, fmt):
    if fmt == "decimal":
        return str(n)
    if fmt == "lowerLetter":
        return _letter(n)
    if fmt == "upperLetter":
        return _letter(n).upper()
    if fmt == "lowerRoman":
        return _roman(n)
    if fmt == "upperRoman":
        return _roman(n).upper()
    if fmt in ("bullet", "none"):
        return ""
    return str(n)


class _Numbering:
    """Word's numbering engine: numId -> abstractNum -> per-level format."""

    def __init__(self, zf):
        self.levels = {}      # (numId, ilvl) -> {fmt, text, start}
        self.counters = {}    # (numId, ilvl) -> current value
        try:
            root = ET.fromstring(zf.read("word/numbering.xml"))
        except KeyError:
            return
        abstract = {}
        for an in root.findall(W + "abstractNum"):
            aid = an.get(W + "abstractNumId")
            lv = {}
            for lvl in an.findall(W + "lvl"):
                il = int(lvl.get(W + "ilvl", "0"))
                fmt = lvl.find(W + "numFmt")
                txt = lvl.find(W + "lvlText")
                st = lvl.find(W + "start")
                lv[il] = {
                    "fmt": fmt.get(W + "val") if fmt is not None else "decimal",
                    "text": txt.get(W + "val") if txt is not None else "%1.",
                    "start": int(st.get(W + "val")) if st is not None else 1,
                }
            abstract[aid] = lv
        for n in root.findall(W + "num"):
            nid = n.get(W + "numId")
            aref = n.find(W + "abstractNumId")
            if aref is None:
                continue
            for il, spec in abstract.get(aref.get(W + "val"), {}).items():
                self.levels[(nid, il)] = spec

    def label(self, num_id, ilvl):
        """Advance the counter and return (visible_label, id_fragment)."""
        spec = self.levels.get((num_id, ilvl))
        if spec is None:
            spec = {"fmt": "decimal", "text": "%1.", "start": 1}
        key = (num_id, ilvl)
        self.counters[key] = self.counters.get(key, spec["start"] - 1) + 1
        # a deeper level restarts once its parent advances
        for (nid, il) in list(self.counters):
            if nid == num_id and il > ilvl:
                del self.counters[(nid, il)]

        parts = []
        for il in range(ilvl + 1):
            s = self.levels.get((num_id, il), {"fmt": "decimal", "start": 1})
            val = self.counters.get((num_id, il), s.get("start", 1))
            parts.append(_fmt_number(val, s.get("fmt", "decimal")))

        text = spec["text"]
        for i, val in enumerate(parts, start=1):
            text = text.replace("%%%d" % i, val)
        frag = "-".join(p for p in parts if p)
        return text, frag


def _footnotes(zf):
    out = {}
    try:
        root = ET.fromstring(zf.read("word/footnotes.xml"))
    except KeyError:
        return out
    for fn in root.findall(W + "footnote"):
        fid = fn.get(W + "id")
        if fn.get(W + "type") in ("separator", "continuationSeparator"):
            continue
        text = "".join(t.text or "" for t in fn.iter(W + "t")).strip()
        if text:
            out[fid] = re.sub(r"\s+", " ", text)
    return out


def _run_text(r):
    """Text of one <w:r>, with highlighting marked and footnote refs kept."""
    rPr = r.find(W + "rPr")
    highlighted = False
    if rPr is not None:
        h = rPr.find(W + "highlight")
        if h is not None and h.get(W + "val") not in (None, "none"):
            highlighted = True

    buf, refs = [], []
    for node in r.iter():
        if node.tag == W + "t":
            buf.append(node.text or "")
        elif node.tag == W + "tab":
            buf.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            buf.append("\n")
        elif node.tag == W + "footnoteReference":
            refs.append(node.get(W + "id"))
    text = "".join(buf)
    if highlighted and text.strip():
        lead = text[:len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        text = "%s==%s==%s" % (lead, text.strip(), trail)
    for fid in refs:
        text += "[^%s]" % fid
    return text


def _para(p, numbering):
    """Return (markdown_line, used_footnote_ids) for one <w:p>."""
    buf = []
    for r in p.iter(W + "r"):
        buf.append(_run_text(r))
    text = "".join(buf).strip()

    used = re.findall(r"\[\^(\d+)\]", text)

    pPr = p.find(W + "pPr")
    numPr = pPr.find(W + "numPr") if pPr is not None else None
    if numPr is not None:
        nid_el = numPr.find(W + "numId")
        ilvl_el = numPr.find(W + "ilvl")
        if nid_el is not None:
            nid = nid_el.get(W + "val")
            ilvl = int(ilvl_el.get(W + "val", "0")) if ilvl_el is not None else 0
            label, frag = numbering.label(nid, ilvl)
            indent = "    " * ilvl
            if not text:
                # a numbered but empty paragraph still consumes a number —
                # keep it so the segment count stays aligned with the source
                return "%s%s ^s%s" % (indent, label, frag), used
            return "%s%s %s ^s%s" % (indent, label, text, frag), used

    return text, used


def docx_to_markdown(path):
    with zipfile.ZipFile(path) as z:
        if "word/document.xml" not in z.namelist():
            raise ValueError("not a Word document (no word/document.xml): %s" % path)
        numbering = _Numbering(z)
        notes = _footnotes(z)
        root = ET.fromstring(z.read("word/document.xml"))

    body = root.find(W + "body")
    if body is None:
        return ""

    lines, used_notes = [], []
    for p in body.iter(W + "p"):
        line, used = _para(p, numbering)
        used_notes.extend(used)
        lines.append(line)

    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()

    seen = []
    for fid in used_notes:
        if fid in notes and fid not in seen:
            seen.append(fid)
    if seen:
        out += "\n\n" + "\n".join("[^%s]: %s" % (f, notes[f]) for f in seen)
    return out + "\n"


def segment_count(path):
    """How many numbered segments the document has — the alignment unit."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    return xml.count("<w:numPr")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: docx_to_markdown.py <file.docx> [more.docx ...]")
    for p in sys.argv[1:]:
        sys.stdout.write(docx_to_markdown(p))
