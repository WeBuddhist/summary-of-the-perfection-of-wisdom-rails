#!/usr/bin/env python3
"""Render an intermediate *work* model as a vault source file plus a
lossless annotation sidecar.

A work model is built by an adapter (see build_sources.py) and looks like:

    {"path": "1-SOURCES/Commentaries/bo-xxx.md",       # vault-relative
     "sidecar": "1-SOURCES/Annotations/bo-xxx.annotations.json",
     "frontmatter": {...},                              # ordered dict
     "title": "…",                                      # the '# ' line
     "id_scheme": "flat" | "h2",
     "target_file": "1-SOURCES/Text/bo-….md" | None,     # what transclusions point at
     "items": [
        {"kind": "heading", "path": "1.2.3", "title": "…", "source": {…}},
        {"kind": "block", "text": "…", "id": "12" | None,
         "targets": ["12", "13"], "source": {…},
         "annotations": [{"start", "end", "layer", …}],   # offsets into "text"
         "notes": ["[Ed: …]"]},
     ],
     "extra": {...}}                                    # copied into the sidecar

ID rules (4-SYSTEM/Guidelines/annotation-conventions.md):
  * '# title ^0' always.
  * heading at tree path "1.2.3" -> '### title ^1-2-3-0' (one '#' per depth,
    capped at six, deeper titles wrapped in **bold**). Headings never take
    content counters.
  * id_scheme "flat": a block keeps the id the adapter gave it (row number of
    the human segmentation), else the next integer.
  * id_scheme "h2": body blocks are ^<H2 label>-<n>; n restarts at every
    top-level heading and runs through deeper headings; blocks before the
    first top-level heading are section 0.
Transclusions are written on their own lines immediately before the block
they belong to; they never take an id.
"""
import json
import pathlib
import re

import yaml


class _Dumper(yaml.SafeDumper):
    pass


def _str_presenter(dumper, data):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_Dumper.add_representer(str, _str_presenter)

REF_TAIL = re.compile(r"\^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\s*$")


def clean_lines(text):
    """Split block text into lines that cannot break the block grammar:
    no blank lines (they would end the block), outer whitespace trimmed."""
    out = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = line.strip()
        if line:
            out.append(line)
    return out


def heading_line(path, title):
    parts = [p for p in str(path).split(".") if p != ""]
    depth = len(parts) + 1                      # '##' is tree depth 1
    hashes = "#" * min(depth, 6)
    title = " ".join(clean_lines(title)) or "—"
    if depth > 6:
        title = f"**{title}**"
    return f"{hashes} {title} ^{'-'.join(parts)}-0"


def render(work, vault_root):
    vault_root = pathlib.Path(vault_root)
    lines = ["---", yaml.dump(work["frontmatter"], Dumper=_Dumper, allow_unicode=True,
                              sort_keys=False, width=10_000).rstrip(), "---", ""]
    title = " ".join(clean_lines(work["title"]))
    lines += [f"# {title} ^0", ""]
    target = work.get("target_file")
    scheme = work.get("id_scheme", "h2")
    sidecar_blocks = {}
    headings = []
    counters = {}
    h2 = "0"
    next_flat = 1
    used = set()
    for item in work["items"]:
        if item["kind"] == "heading":
            hl = heading_line(item["path"], item["title"])
            lines += [hl, ""]
            if len(str(item["path"]).split(".")) == 1:
                h2 = str(item["path"])
            headings.append({"line": hl, "path": item["path"], "title": item["title"],
                             "source": item.get("source")})
            continue
        text_lines = clean_lines(item["text"])
        if not text_lines:
            continue
        if scheme == "flat":
            bid = str(item.get("id") or next_flat)
            if bid.isdigit():
                next_flat = int(bid) + 1
        else:
            counters[h2] = counters.get(h2, 0) + 1
            bid = f"{h2}-{counters[h2]}"
        if bid in used:
            raise ValueError(f"{work['path']}: duplicate block id ^{bid}")
        used.add(bid)
        if REF_TAIL.search(text_lines[-1]):
            raise ValueError(f"{work['path']}: block text ends like a block id: {text_lines[-1][-30:]!r}")
        if text_lines[0].startswith("#") or text_lines[0].startswith("![["):
            # content would be parsed as a heading or a transclusion; never
            # alter the text to dodge it — stop and let a human decide
            raise ValueError(f"{work['path']}: block text starts with markup: {text_lines[0][:30]!r}")
        for t in item.get("targets") or []:
            lines.append(f"![[{target}#^{t}]]")
        if item.get("targets"):
            lines.append("")
        text_lines[-1] = f"{text_lines[-1]} ^{bid}"
        lines += text_lines
        lines.append("")
        for note in item.get("notes") or []:
            lines += [note, ""]
        sidecar_blocks[bid] = {k: v for k, v in item.items()
                               if k in ("source", "annotations", "targets", "alignment", "role", "comments", "overlays") and v}
        sidecar_blocks[bid]["text"] = "".join(text_lines[:-1] + [text_lines[-1][: -len(bid) - 2]])
    md = "\n".join(lines).rstrip() + "\n"
    out = vault_root / work["path"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    if work.get("sidecar"):
        sc = {"file": work["path"], "id_scheme": scheme, "target_file": target,
              "headings": headings, "blocks": sidecar_blocks, **(work.get("extra") or {})}
        sp = vault_root / work["sidecar"]
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(sc, ensure_ascii=False, indent=1), encoding="utf-8")
    return out, len(sidecar_blocks), len(headings)
