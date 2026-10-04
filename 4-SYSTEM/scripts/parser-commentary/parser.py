#!/usr/bin/env python3
"""Parse linter output for commentary files and produce API-ready payloads.

Commentary content segments default to type ``paragraph`` (not verse).
Always builds alignment.json from Obsidian root-text transclusions.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent / "output"


def _out_dir(stem):
    """Each source file gets its own folder: output/<stem>/."""
    d = OUTPUT_DIR / stem
    d.mkdir(parents=True, exist_ok=True)
    return d

YAML_PROPS_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
# Headers: ^n, ^n-n, ^n-n-n, ^n-n-n-… (any depth). Content: max ^n-n-n (3 parts).
REF_RE = re.compile(r'(\^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\s*$')
VERSE_REF_MAX_PARTS = 3
ROMAN_RE = re.compile(r'^[IVXLCDM]+$')
VERSE_X_RE = re.compile(r'\d+[xX]\d+')
TRANSCLUSION_RE = re.compile(r'^\s*!\[\[.*?#\^.*?\]\]\s*$')
_TRANS_REF_RE = re.compile(r'!\[\[.*?#\^([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\]\]')
# Same, capturing the linked file as well: (file, ref)
_TRANS_FILE_REF_RE = re.compile(r'!\[\[([^\]#|]*)#\^([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\]\]')
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


# Footnotes (`[^n]` markers and `[^n]: …` definition lines) are not accepted by
# the library backend yet, so they are left out of the edition, segmentation,
# TOC and alignment — the same treatment as the <small> yigchung marks. The
# source file is never changed. When the backend takes footnote annotations, a
# separate parser will read them from the source.
FOOTNOTE_DEF_RE = re.compile(r"^[ \t]*\[\^[^\]\s]+\]:.*(?:\r?\n|$)", re.MULTILINE)
FOOTNOTE_REF_RE = re.compile(r"\[\^[^\]\s]+\](?!:)")


def strip_footnotes(body):
    """Drop footnote definition lines and inline footnote markers from a body."""
    return FOOTNOTE_REF_RE.sub("", FOOTNOTE_DEF_RE.sub("", body))


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
    body = strip_footnotes(text[m.end():])
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


# Characters that look blank but are not whitespace (zero-width space, BOM,
# non-breaking space). A line made only of these is an empty line.
BLANK_CHARS = "\u200b\u200c\u200d\ufeff\xa0"


def _is_blank_line(line):
    return not line.strip().strip(BLANK_CHARS).strip()


def _is_verse_shape(content_lines):
    """True for 2+ consecutive lines with no empty line between them.

    Verse is written one line per pāda, with no gap. An empty line inside a
    block (often an invisible zero-width space) means the block is really two
    paragraphs that were never given their own block IDs.
    """
    if any(_is_blank_line(l) for l in content_lines):
        return False
    return sum(1 for l in content_lines if l.strip()) > 1


# Inline formatting used for interlinear glosses in the sources. The gloss
# text stays in the edition; only the tags are dropped.
INLINE_TAG_RE = re.compile(r"</?small>", re.IGNORECASE)


def _strip_inline_tags(text):
    """Clean a line for the edition content: drop inline gloss tags, and turn
    non-breaking spaces (U+00A0) into ordinary spaces."""
    return INLINE_TAG_RE.sub("", text).replace("\u00a0", " ")


def _heading_level(line):
    stripped = line.strip()
    return len(stripped) - len(stripped.lstrip('#'))


BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _clean_heading_title(text, level):
    """Obsidian renders only six heading levels, so a deeper heading (7+ '#')
    is often written in bold to look like one. That bold is display-only:
    drop the ** markers from the TOC title."""
    if level > 6:
        text = BOLD_RE.sub(r"\1", text).strip()
    return text


def _note_name(link):
    """File name an Obsidian link resolves by: last path part, `.md` implied, NFC."""
    name = Path(link.strip()).name
    if name and not name.endswith(".md"):
        name += ".md"
    return unicodedata.normalize("NFC", name)


def _root_file_name(fm):
    root_text_val = fm.get("root_text")
    return _note_name(str(root_text_val)) if root_text_val else None


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
    # x-suffix / U-leaf stay content; commentaries use paragraph default
    if VERSE_X_RE.search(ref_no_caret):
        return doc_default
    last = parts[-1] if parts else ""
    if re.match(r'^U\d+$', re.sub(r'[xX]\d+$', '', last)):
        return doc_default
    for part in parts:
        base = re.sub(r'[xX]\d+$', '', part)
        if part and not base.isdigit() and not ROMAN_RE.match(base):
            if re.match(r'^[a-z]+$', base):
                return "back_matter"
    return doc_default


# ---------------------------------------------------------------------------
# Function 1: extract text_input
# ---------------------------------------------------------------------------

def extract_text_input(lint_path, source_stem=None):
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
    if stem.endswith(".lint.errors"):
        stem = stem[: -len(".lint.errors")]
    elif stem.endswith(".lint"):
        stem = stem[: -len(".lint")]
    if source_stem:
        stem = source_stem
    out_path = _out_dir(stem) / f"{stem}.text.json"
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
            text = _strip_inline_tags(raw_lines[0].strip().lstrip('#').strip())
            ref_idx = text.rfind(ref)
            if ref_idx != -1:
                text = text[:ref_idx].rstrip()
            level = _heading_level(raw_lines[0])
            text = _clean_heading_title(text, level)
            if text:
                headings.append({
                    "level": level,
                    "title": text,
                    "reference": ref_no_caret,
                    "offset": pos,
                })
            continue

        if _ref_part_count(ref) > VERSE_REF_MAX_PARTS:
            print(
                f"  WARN block {block_num}: reference {ref!r} has {_ref_part_count(ref)} parts; "
                f"content segments allow at most ^n-n-n ({VERSE_REF_MAX_PARTS} parts) — skipped",
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
            text = _strip_inline_tags(raw_line.rstrip())
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
        if any(_is_blank_line(l) for l in content_lines[1:-1]):
            print(
                f"  WARN block {block_num}: empty line inside the block — kept as one "
                f"segment; the parts may each need their own block ID",
                file=sys.stderr,
            )
        # Verse wins: several lines with no gap is a verse wherever it sits,
        # front matter or colophon included. Otherwise the ID decides.
        if _is_verse_shape(content_lines):
            seg_type = "verse"
        else:
            seg_type = _infer_segment_type(ref_no_caret, doc_default)
        seg_list.append({"lines": line_spans, "type": seg_type, "reference": ref_no_caret})

    return "".join(parts), seg_list, headings


def build_edition(source_path, lint_path):
    fm, body = _read_source(source_path)
    blocks = _extract_blocks(body)

    # Commentaries are paragraph-segmented (not verse)
    doc_default = "paragraph"

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
    out_path = _out_dir(stem) / f"{stem}.edition.json"
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
    out_path = _out_dir(stem) / f"{stem}.toc.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path, out


# ---------------------------------------------------------------------------
# Function 4: build alignment (commentary → root text via transclusions)
# ---------------------------------------------------------------------------

def build_alignment(source_path):
    fm, body = _read_source(source_path)
    file_type = fm.get("file_type", "")
    if file_type and file_type != "commentary":
        raise ValueError(
            f"parser-commentary expects file_type 'commentary', got {file_type!r}"
        )

    heading_refs = _root_heading_refs(fm, source_path)
    root_name = _root_file_name(fm)
    skipped_heading_targets = set()
    foreign_transclusions = {}
    alignments = []
    seen_pairs = set()
    blocks = _extract_blocks(body)
    active_targets = []
    prev_trans_only = False

    for block in blocks:
        lines = block["lines"]
        # Headings are invisible to alignment (FORK, Dzongsar-dolma-bumtsok-rails
        # 2026-09-26): they are never aligned and they neither close nor reset the
        # current scope — only the next transclusion group does. A heading line
        # glued to transclusion lines is dropped and the rest read as usual.
        if block["is_header"]:
            lines = [l for l in lines if not l.lstrip().startswith('#')]
            if not any(l.strip() for l in lines):
                continue
            block = {**block, "ref": None}
        # Only transclusions of the root_text file give alignment targets
        # (FORK, Dzongsar-dolma-bumtsok-rails 2026-09-26). A transclusion of any
        # other file still counts as a transclusion group — it closes the
        # current scope — but adds no target, so the commentary under it stays
        # unaligned instead of being paired with a same-numbered root block.
        trans_links = [(f, r) for l in lines for f, r in _TRANS_FILE_REF_RE.findall(l)]
        trans_refs = [r for f, r in trans_links
                      if root_name is None or _note_name(f) == root_name]
        for f, r in trans_links:
            if root_name is not None and _note_name(f) != root_name:
                foreign_transclusions.setdefault(f, set()).add(r)
        trans_only = bool(trans_links) and not block["ref"] and all(
            _TRANS_REF_RE.search(l) for l in lines if l.strip()
        )

        if trans_links:
            if trans_only and prev_trans_only:
                # Transclusions written one after another (even with blank
                # lines between them) form one group: add to it.
                active_targets = list(dict.fromkeys(active_targets + trans_refs))
            else:
                # A transclusion group opens a new scope, replacing any
                # previous one. It stays active for the commentary blocks
                # that follow.
                active_targets = list(dict.fromkeys(trans_refs))
        prev_trans_only = trans_only

        if block["ref"]:
            source_ref = block["ref"].lstrip("^")
            for target_ref in active_targets:
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

    if skipped_heading_targets:
        print(
            "  WARN alignment: transclusions of root-text headings skipped "
            f"(headings are not segments): {sorted(skipped_heading_targets)}",
            file=sys.stderr,
        )
    if foreign_transclusions:
        print(
            "  WARN alignment: transclusions of files other than root_text "
            "close the scope without a target: "
            + ", ".join(f"{f} ({len(r)})" for f, r in sorted(foreign_transclusions.items())),
            file=sys.stderr,
        )

    out = {"alignments": alignments}
    stem = source_path.stem
    out_path = _out_dir(stem) / f"{stem}.alignment.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path, out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    args = (argv if argv is not None else sys.argv[1:])
    usage = (
        'Usage:\n'
        '  python3 4-SYSTEM\\scripts\\parser-commentary\\parser.py '
        '"<commentary.md>" "<file.lint.json>"'
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
        if source_file_type and source_file_type != "commentary":
            print(
                f"ERROR {source_path}: expected file_type 'commentary', "
                f"got {source_file_type!r}",
                file=sys.stderr,
            )
            sys.exit(1)
    except Exception as exc:
        print(f"ERROR reading source: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        text_out = extract_text_input(lint_path, source_path.stem)
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
