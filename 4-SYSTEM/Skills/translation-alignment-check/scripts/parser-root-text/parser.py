#!/usr/bin/env python3
"""Parse linter output files and produce clean API-ready payloads."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent / "output"

YAML_PROPS_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
# Headers: ^n, ^n-n, ^n-n-n, ^n-n-n-… (any depth). Content: max ^n-n-n (3 parts).
REF_RE = re.compile(r'(\^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\s*$')
VERSE_REF_MAX_PARTS = 3
ROMAN_RE = re.compile(r'^[IVXLCDM]+$')
VERSE_X_RE = re.compile(r'\d+[xX]\d+')
TRANSCLUSION_RE = re.compile(r'^\s*!\[\[.*?#\^.*?\]\]\s*$')
_TRANS_REF_RE = re.compile(r'!\[\[.*?#\^([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\]\]')
_WYLIE_RE = re.compile(r"'[a-zA-Z]")


def _ref_part_count(ref):
    """Count hyphen-separated parts in a ^ref (caret stripped)."""
    return len(ref.lstrip("^").split("-")) if ref else 0


def _wylie_to_unicode(text, lang_tag):
    if lang_tag != "bo":
        return text
    if not text or any("ༀ" <= c <= "࿿" for c in text):
        return text
    if not _WYLIE_RE.search(text):
        return text
    try:
        import pyewts as _pyewts
        converter = _pyewts.pyewts()
        converted = converter.toUnicode(text)
        if converted and converted.strip():
            return converted
    except ImportError:
        pass
    return text


def _is_empty(value):
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, dict)) and not value:
        return True
    return False


def _read_source(path):
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("PyYAML is required: pip install pyyaml") from exc
    text = path.read_bytes().replace(b'\x00', b'').decode("utf-8", errors="replace")
    m = YAML_PROPS_RE.match(text)
    if not m:
        raise ValueError("no YAML properties found")
    data = yaml.safe_load(m.group(1)) or {}
    body = text[m.end():]
    return data, body


def _resolve_root_text_path(val, source_path):
    val_path = Path(val)
    for base in [source_path.parent, *source_path.parents]:
        candidate = base / val_path
        if candidate.exists():
            return candidate
    name = val_path.name
    for base in source_path.parents:
        matches = list(base.rglob(name))
        if matches:
            return matches[0]
    return None


def _extract_blocks(body):
    blocks = []
    for raw in re.split(r'\r?\n[ \t]*\r?\n', body.strip()):
        block = raw.strip()
        if not block:
            continue
        lines = [l.rstrip('\r') for l in block.split('\n')]
        is_header = lines[0].lstrip().startswith('#')
        ref = None
        for line in reversed(lines):
            stripped = line.rstrip()
            if stripped:
                m = REF_RE.search(stripped)
                if m:
                    ref = m.group(1)
                break
        blocks.append({"ref": ref, "is_header": is_header, "lines": lines, "raw": block})
    return blocks


def _heading_level(line):
    stripped = line.strip()
    return len(stripped) - len(stripped.lstrip('#'))


def _root_heading_refs(fm, source_path):
    """Block IDs of the headings in the file linked by root_text.

    Headings are not edition segments, so a transclusion that points at one
    cannot be aligned.
    """
    root_text_val = fm.get("root_text")
    if not root_text_val:
        return set()
    resolved = _resolve_root_text_path(str(root_text_val), source_path)
    if not resolved:
        return set()
    try:
        _, root_body = _read_source(resolved)
    except (ValueError, OSError):
        return set()
    return {
        b["ref"].lstrip("^")
        for b in _extract_blocks(root_body)
        if b["is_header"] and b["ref"]
    }


def _infer_segment_type(ref_no_caret, doc_default):
    if not ref_no_caret:
        return doc_default
    if ref_no_caret[0].upper() == 'T':
        return "top_segment"
    parts = ref_no_caret.split('-')
    first = parts[0]
    if ROMAN_RE.match(first):
        return "front_matter"
    # A Roman part later in the ref marks front matter inside a book/volume
    # (e.g. ^2-I-3 in a book-chapter-verse file) → front_matter
    for part in parts:
        base = re.sub(r'[xX]\d+$', '', part)
        if ROMAN_RE.match(base):
            return "front_matter"
    if VERSE_X_RE.search(ref_no_caret):
        return "verse"
    last = parts[-1] if parts else ""
    if re.match(r'^U\d+$', re.sub(r'[xX]\d+$', '', last)):
        return "verse"  # U = unnumbered, not a type
    for part in parts:
        base = re.sub(r'[xX]\d+$', '', part)
        if part and not base.isdigit() and not ROMAN_RE.match(base):
            if re.match(r'^[a-z]+$', base):
                return "back_matter"
    return doc_default


# ---------------------------------------------------------------------------
# Function 1: extract text_input
# ---------------------------------------------------------------------------

def extract_text_input(lint_path):
    data = json.loads(
        lint_path.read_bytes().replace(b'\x00', b'').decode("utf-8", errors="replace")
    )
    text_input = data.get("text_input") or data.get("resolved")
    if text_input is None:
        raise ValueError(f"no text_input found in {lint_path.name}")
    clean = {k: v for k, v in text_input.items() if not _is_empty(v)}

    if "alt_titles" not in clean:
        print("  WARN alt_titles: missing — ignored", file=sys.stderr)

    contribs = clean.get("contributions")
    if contribs is None:
        print("  WARN contributions: author/translator missing — ignored", file=sys.stderr)
    elif isinstance(contribs, list):
        kept = []
        for i, entry in enumerate(contribs):
            if not isinstance(entry, dict):
                print(f"  WARN contributions[{i}]: invalid entry — skipped", file=sys.stderr)
                continue
            role = entry.get("role", "contributor")
            if entry.get("type") == "ai":
                if entry.get("id") or entry.get("ai_id"):
                    kept.append(entry)
                else:
                    print(
                        f"  WARN {role}: AI contributor missing id — skipped",
                        file=sys.stderr,
                    )
                continue
            if entry.get("id") or entry.get("bdrc_id"):
                kept.append(entry)
            else:
                print(
                    f"  WARN {role}: not found (no id) — skipped",
                    file=sys.stderr,
                )
        if kept:
            clean["contributions"] = kept
        else:
            clean.pop("contributions", None)
            if contribs:
                print(
                    "  WARN contributions: none had resolvable ids — omitted",
                    file=sys.stderr,
                )

    stem = lint_path.stem
    if stem.endswith(".lint"):
        stem = stem[:-len(".lint")]
    out_path = OUTPUT_DIR / f"{stem}.text.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Function 2: build edition
# ---------------------------------------------------------------------------

def _build_content_and_segmentation(blocks, doc_default):
    """Build the edition content and its segments.

    Headings are not part of the edition: they add no segment and no content.
    They are returned separately, with the content offset where they occur,
    for the table of contents.
    """
    parts = []
    seg_list = []
    headings = []
    pos = 0

    for block_num, block in enumerate(blocks, start=1):
        ref = block["ref"]
        raw_lines = block["lines"]
        is_header = block["is_header"]

        content_lines = [l for l in raw_lines if not TRANSCLUSION_RE.match(l)]
        # Pure transclusion block — silently skip, used for alignment only
        if not any(l.strip() for l in content_lines):
            continue

        if not ref:
            print(f"  WARN block {block_num}: no reference marker — skipped", file=sys.stderr)
            continue

        ref_no_caret = ref[1:] if ref.startswith("^") else ref

        if is_header:
            text = raw_lines[0].strip().lstrip('#').strip()
            ref_idx = text.rfind(ref)
            if ref_idx != -1:
                text = text[:ref_idx].rstrip()
            if text:
                headings.append({
                    "level": _heading_level(raw_lines[0]),
                    "title": text,
                    "reference": ref_no_caret,
                    "offset": pos,
                })
            continue

        if _ref_part_count(ref) > VERSE_REF_MAX_PARTS:
            print(
                f"  WARN block {block_num}: reference {ref!r} has {_ref_part_count(ref)} parts; "
                f"verses allow at most ^n-n-n ({VERSE_REF_MAX_PARTS} parts) — skipped",
                file=sys.stderr,
            )
            continue

        last_nonempty_idx = -1
        for i in range(len(content_lines) - 1, -1, -1):
            if content_lines[i].rstrip():
                last_nonempty_idx = i
                break
        line_spans = []
        for i, raw_line in enumerate(content_lines):
            text = raw_line.rstrip()
            if i == last_nonempty_idx:
                ref_idx = text.rfind(ref)
                if ref_idx != -1:
                    text = text[:ref_idx].rstrip()
            if not text:
                continue
            start = pos
            parts.append(text)
            pos += len(text)
            line_spans.append({"start": start, "end": start + len(text)})
        seg_type = _infer_segment_type(ref_no_caret, doc_default)
        seg_list.append({"lines": line_spans, "type": seg_type, "reference": ref_no_caret})

    return "".join(parts), seg_list, headings


def build_edition(source_path, lint_path):
    fm, body = _read_source(source_path)
    blocks = _extract_blocks(body)

    file_type = fm.get("file_type", "")
    if file_type == "translation":
        root_text_val = fm.get("root_text")
        root_file_type = None
        if root_text_val:
            resolved_root = _resolve_root_text_path(str(root_text_val), source_path)
            if resolved_root:
                try:
                    root_fm, _ = _read_source(resolved_root)
                    root_file_type = root_fm.get("file_type", "")
                except (ValueError, OSError):
                    pass
        doc_default = "paragraph" if root_file_type == "commentary" else "verse"
    else:
        doc_default = "paragraph" if fm.get("commentary_of") else "verse"

    content_str, seg_list, headings = _build_content_and_segmentation(blocks, doc_default)

    edition_type = fm.get("edition_type", "critical")
    source_url = (
        fm.get("source") or fm.get("source_url") or ""
    )
    metadata = {"type": edition_type, "source": source_url}

    out = {
        "metadata": metadata,
        "content": content_str,
        "segmentation": {"segments": seg_list},
    }

    stem = source_path.stem
    out_path = OUTPUT_DIR / f"{stem}.edition.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path, out, headings


# ---------------------------------------------------------------------------
# Function 3: build TOC
# ---------------------------------------------------------------------------

def build_toc(source_path, edition_result, headings):
    """Build the TOC from the headings (which are not in the edition content).

    A section starts at the content offset of its heading and ends where the
    next heading of the same or a higher level starts (or at the end).
    """
    fm, _ = _read_source(source_path)
    lang_tag = fm.get("lang_tag") or "en"
    content_len = len(edition_result["content"])

    title_nodes = []
    for i, heading in enumerate(headings):
        span_end = content_len
        for later in headings[i + 1:]:
            if later["level"] <= heading["level"]:
                span_end = later["offset"]
                break
        title_nodes.append({
            "level": heading["level"],
            "title": _wylie_to_unicode(heading["title"], lang_tag),
            "span_start": heading["offset"],
            "span_end": span_end,
        })

    def _nest(nodes, idx, parent_level):
        sections = []
        i = idx
        while i < len(nodes):
            node = nodes[i]
            if node["level"] <= parent_level:
                break
            if node["level"] == parent_level + 1:
                section = {
                    "title": {lang_tag: node["title"]},
                    "span": {"start": node["span_start"], "end": node["span_end"]},
                }
                subsections, i = _nest(nodes, i + 1, node["level"])
                if subsections:
                    section["subsections"] = subsections
                sections.append(section)
            else:
                i += 1
        return sections, i

    top_level = title_nodes[0]["level"] if title_nodes else 1
    sections, _ = _nest(title_nodes, 0, top_level - 1)

    out = {"sections": sections}

    stem = source_path.stem
    out_path = OUTPUT_DIR / f"{stem}.toc.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path, out


# ---------------------------------------------------------------------------
# Function 4: build alignment (translation/commentary only)
# ---------------------------------------------------------------------------

def build_alignment(source_path):
    fm, body = _read_source(source_path)
    file_type = fm.get("file_type", "")
    if file_type not in ("translation", "commentary"):
        raise ValueError(
            f"alignment only applies to translation/commentary files, got file_type={file_type!r}"
        )

    heading_refs = _root_heading_refs(fm, source_path)
    skipped_heading_targets = set()
    alignments = []
    seen_pairs = set()
    blocks = _extract_blocks(body)
    pending_targets = []

    for block in blocks:
        lines = block["lines"]
        trans_refs = [_TRANS_REF_RE.search(l).group(1)
                      for l in lines if _TRANS_REF_RE.search(l)]

        # Headings are not segments: never aligned, and transclusions
        # waiting for a content block do not carry past a heading.
        if block["is_header"]:
            pending_targets = []
            continue

        if trans_refs and not block["ref"]:
            pending_targets.extend(trans_refs)
        elif block["ref"]:
            source_ref = block["ref"].lstrip("^")
            pending_targets.extend(trans_refs)
            for target_ref in pending_targets:
                if target_ref in heading_refs:
                    skipped_heading_targets.add(target_ref)
                    continue
                pair = (source_ref, target_ref)
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    alignments.append({
                        "source_segment_reference": source_ref,
                        "target_segment_reference": target_ref,
                    })
            pending_targets = []

    if skipped_heading_targets:
        print(
            "  WARN alignment: transclusions of root-text headings skipped "
            f"(headings are not segments): {sorted(skipped_heading_targets)}",
            file=sys.stderr,
        )

    out = {"alignments": alignments}
    stem = source_path.stem
    out_path = OUTPUT_DIR / f"{stem}.alignment.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path, out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    args = (argv if argv is not None else sys.argv[1:])
    usage = (
        'Usage:\n'
        '  python3 4-SYSTEM\\scripts\\parser-root-text\\parser.py '
        '"<source.md>" "<file.lint.json>"'
    )

    if len(args) != 2:
        print(usage)
        sys.exit(0 if not args else 1)

    source_path, lint_path = Path(args[0]), Path(args[1])
    if source_path.suffix != ".md" or ".lint" not in lint_path.name:
        print(usage)
        sys.exit(1)

    had_error = False

    try:
        source_fm, _ = _read_source(source_path)
        source_file_type = source_fm.get("file_type", "")
    except Exception as exc:
        print(f"ERROR reading source: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        text_out = extract_text_input(lint_path)
        print(f"OK    {lint_path}  ->  {text_out}")
    except Exception as exc:
        print(f"ERROR text_input: {exc}", file=sys.stderr)
        had_error = True

    edition_result = None
    try:
        edition_out, edition_result, headings = build_edition(source_path, lint_path)
        segs = edition_result["segmentation"]["segments"]
        content_len = len(edition_result["content"])
        by_type = {}
        for s in segs:
            by_type[s["type"]] = by_type.get(s["type"], 0) + 1
        print(f"OK    {source_path}  ->  {edition_out}")
        print(f"  content length   : {content_len} chars")
        print(f"  segments         : {len(segs)}")
        print(f"  headings (toc)   : {len(headings)}")
        for t, n in sorted(by_type.items()):
            print(f"    {t}: {n}")
    except Exception as exc:
        print(f"ERROR edition: {exc}", file=sys.stderr)
        had_error = True

    if edition_result is not None:
        try:
            toc_out, toc_result = build_toc(source_path, edition_result, headings)
            sections = toc_result["sections"]

            def _toc_stats(nodes, depth=0):
                total = max_depth = 0
                for node in nodes:
                    total += 1
                    max_depth = max(max_depth, depth)
                    if node.get("subsections"):
                        n, d = _toc_stats(node["subsections"], depth + 1)
                        total += n
                        max_depth = max(max_depth, d)
                return total, max_depth

            toc_nodes, toc_depth = _toc_stats(sections)
            print(f"OK    {source_path}  ->  {toc_out}")
            print(f"  top sections     : {len(sections)}")
            print(f"  toc nodes        : {toc_nodes}")
            print(f"  max depth        : {toc_depth}")
        except Exception as exc:
            print(f"ERROR toc: {exc}", file=sys.stderr)
            had_error = True

    if source_file_type in ("translation", "commentary"):
        try:
            align_out, align_result = build_alignment(source_path)
            n = len(align_result["alignments"])
            print(f"OK    {source_path}  ->  {align_out}")
            print(f"  alignments       : {n}")
        except Exception as exc:
            print(f"ERROR alignment: {exc}", file=sys.stderr)
            had_error = True

    if had_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
