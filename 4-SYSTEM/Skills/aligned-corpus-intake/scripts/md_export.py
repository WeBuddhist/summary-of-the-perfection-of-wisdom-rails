#!/usr/bin/env python3
"""Read Google-Docs Markdown exports of human-made alignment documents.

    python3 md_export.py <file.md>            # rows, with emphasis runs
    python3 md_export.py <file.csv> --meta    # a metadata sheet

The Dzongsar team aligns a text by keeping two Google Docs whose paragraphs are
an auto-numbered list: row N of one document is paired with row N of the other
(see ../references/md-export-format.md). Exported with "Download → Markdown",
each row becomes one numbered list item:

    12. རིགས་ཀྱི་བུ་གང་ལ་ལ་ … ཇི་ལྟར་བསླབ་པར་བྱ།␠␠
    13.␠␠
       ***continuation line of row 13 (indented, verse)***␠␠

The number in front of a row is the row number, i.e. the alignment key. An
empty item is a row with no text on this side (its counterpart has no
equivalent here). Anything before the first numbered item is row 0 (typically
the document's own title line).

The reader never alters wording. It only:
  * splits rows at the list numbers and keeps every other line inside its row;
  * removes the export's Markdown markup — the two-space hard break, the
    indentation of continuation lines, backslash escapes (``\\[`` → ``[``) and
    the ``*``/``**``/``***`` emphasis markers — recording each emphasised span
    (offsets into the clean text) so nothing the humans marked is lost.
"""
import csv
import json
import re
import sys

ROW_RE = re.compile(r"^(\d+)\.(?:[ \t ]+(.*))?$")
_ESCAPABLE = set("\\`*_{}[]()#+-.!|<>~=")
STYLES = {1: "italic", 2: "bold", 3: "bold_italic"}


def strip_markup(line):
    """Return (clean_text, runs). runs = [{"start", "end", "style"}] in clean
    offsets. Unbalanced markers are removed too and reported as a run with
    "unclosed": True."""
    out, runs = [], []
    open_runs = {}                     # marker length -> start offset
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if ch == "\\" and i + 1 < n and line[i + 1] in _ESCAPABLE:
            out.append(line[i + 1])
            i += 2
            continue
        if ch == "*":
            j = i
            while j < n and line[j] == "*":
                j += 1
            k = j - i
            pos = len("".join(out))
            # close the most recent open run of the same marker length, or of
            # a combination that adds up (*** closing ** + *)
            if k in open_runs:
                start = open_runs.pop(k)
                if pos > start:
                    runs.append({"start": start, "end": pos, "style": STYLES.get(k, f"{k}*")})
            elif k == 3 and 1 in open_runs and 2 in open_runs:
                for kk in (1, 2):
                    start = open_runs.pop(kk)
                    if pos > start:
                        runs.append({"start": start, "end": pos, "style": STYLES[kk]})
            else:
                open_runs[k] = pos
            i = j
            continue
        out.append(ch)
        i += 1
    text = "".join(out)
    for k, start in open_runs.items():
        if len(text) > start:
            runs.append({"start": start, "end": len(text), "style": STYLES.get(k, f"{k}*"), "unclosed": True})
    runs.sort(key=lambda r: (r["start"], r["end"]))
    return text, runs


def read_rows(path):
    """Rows of a numbered-list export, in document order.

    Returns a list of dicts {"row", "text", "raw", "runs"} with row 0 holding
    any text before the first numbered item. `text` keeps the row's line
    structure (one line per non-blank source line, outer whitespace and the
    two-space hard break trimmed); `raw` is the row exactly as exported."""
    rows = []
    cur = {"row": 0, "raw": []}
    for line in open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n"):
        m = ROW_RE.match(line)
        if m:
            rows.append(cur)
            cur = {"row": int(m.group(1)), "raw": [m.group(2) or ""]}
        else:
            cur["raw"].append(line)
    rows.append(cur)
    out = []
    for r in rows:
        lines, runs, off = [], [], 0
        for raw_line in r["raw"]:
            clean, rr = strip_markup(raw_line)
            lead = len(clean) - len(clean.lstrip(" \t "))
            clean = clean.strip(" \t ")
            if not clean:
                continue
            if lines:
                off += 1                                   # the joining "\n"
            for x in rr:
                s, e = max(0, x["start"] - lead), min(len(clean), x["end"] - lead)
                if e > s:
                    runs.append(dict(x, start=s + off, end=e + off))
            lines.append(clean)
            off += len(clean)
        text = "\n".join(lines)
        if r["row"] == 0 and not text:
            continue
        out.append({"row": r["row"], "text": text, "raw": "\n".join(r["raw"]), "runs": runs})
    nums = [r["row"] for r in out if r["row"]]
    if nums != sorted(nums) or len(set(nums)) != len(nums):
        raise ValueError(f"{path}: row numbers are not strictly increasing")
    return out


def read_meta(path):
    """A Dzongsar metadata sheet exported as CSV: rows `field,BO,EN[,ZH]`
    under an `Entries,…` header (an optional banner row above it is
    skipped). Returns {field: {"bo": …, "en": …, "zh": …}} with empty cells
    dropped — cell text only, never hyperlinks."""
    meta, header = {}, None
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh):
            if not row:
                continue
            if header is None:
                if row[0].strip() == "Entries":
                    header = [h.strip().lower() for h in row[1:]]
                continue
            vals = {h: v.strip() for h, v in zip(header, row[1:]) if v.strip()}
            if vals:
                meta[row[0].strip()] = vals
    if header is None:
        raise ValueError(f"{path}: no 'Entries,…' header row")
    return meta


if __name__ == "__main__":
    p = sys.argv[1]
    if "--meta" in sys.argv:
        print(json.dumps(read_meta(p), ensure_ascii=False, indent=1))
    else:
        for r in read_rows(p):
            flag = f" runs={len(r['runs'])}" if r["runs"] else ""
            print(f"{r['row']:4d}{flag} {r['text'][:100]!r}")
