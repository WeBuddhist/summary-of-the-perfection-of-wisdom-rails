#!/usr/bin/env python3
"""Generate a read-only Obsidian reading preview from a fenced-wikitext article.md.

Converts the ```wikitext fence body of an article file (the wiki-article-from-claims
output convention) into plain Obsidian markdown in which
every <ref> becomes an Obsidian footnote, so a human reviewer can read the article in
Obsidian's reading view with citations collapsed to clickable superscript numbers —
the same reading experience the published bo.wikipedia page will give.

The output (article-preview.md, written beside the input) is derived, disposable, and
read-only by convention: corrections belong in article.md, then this script is re-run.
Works on output from every version of the skill (the retired v1 batch included).

Usage:
    python3 make_preview.py <path-to-article.md> [more article.md paths ...]

Conversions applied to the fence body:
    <ref name="x">content</ref>  ->  [^label]  (definition collected for the footer;
                                     label = slug of that commentary's author_in_english,
                                     read live from 1-SOURCES/Commentaries/ frontmatter,
                                     so reviewers see the author's name, not the internal
                                     ref key; falls back to the raw ref name if unmapped)
    <ref name="x" />             ->  [^label]
    <ref>content</ref>           ->  [^rN]  (auto-numbered, definition collected)
    == Heading ==                ->  ## Heading   (=== -> ###, etc.)
    '''bold'''                   ->  **bold**
    ''italic''                   ->  *italic*
    [[རིགས་དབྱེ།:...]]              ->  (dropped — category link, meaningless in preview)
    [[target|display]]           ->  display      (plain text: no fake vault links)
    [[target]]                   ->  target       (plain text)
    <references />               ->  (dropped — footnote definitions render instead)

No content inside quotations or Tibetan prose is altered beyond these markers.
"""

import re
import sys
import unicodedata
from pathlib import Path

FENCE_RE = re.compile(r"^```wikitext\s*$(.*?)^```\s*$", re.M | re.S)
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)

# Vault root, resolved relative to this script (scripts/ -> skill -> Skills -> 4-SYSTEM -> root)
VAULT_ROOT = Path(__file__).resolve().parents[4]


def _slugify(name: str) -> str:
    """'Jetsün Yama Sonam' -> 'jetsun-yama-sonam'. Parentheticals dropped, diacritics folded."""
    name = re.sub(r"\([^)]*\)", "", name)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return name


def load_author_labels() -> dict[str, str]:
    """registered_id -> footnote label slug, from each commentary's author_in_english.

    Read live from 1-SOURCES/Commentaries/ frontmatter so the preview always shows the
    current human-reviewed name; the wikitext ref name (the frozen registered_id) is
    untouched. Falls back silently to {} if the folder is unavailable.
    """
    labels: dict[str, str] = {}
    used: dict[str, str] = {}
    try:
        for f in sorted((VAULT_ROOT / "1-SOURCES" / "Commentaries").glob("*.md")):
            head = f.read_text(encoding="utf-8").split("\n---\n", 1)[0]
            rid = re.search(r'^registered_id:\s*"?([\w\-]+)"?\s*$', head, re.M)
            eng = re.search(r'^author_in_english:\s*"?(.+?)"?\s*$', head, re.M)
            if not (rid and eng):
                continue
            slug = _slugify(eng.group(1))
            if not slug:
                continue
            if slug in used and used[slug] != rid.group(1):
                slug = f"{slug}-{rid.group(1)}"
            used[slug] = rid.group(1)
            labels[rid.group(1)] = slug
    except OSError:
        pass
    return labels

WARNING_CALLOUT = (
    "> [!warning] Generated preview — do not edit\n"
    "> This file is rendered from `article.md` for review reading only. Citations appear\n"
    "> as footnotes. Any correction belongs in `article.md` (inside the wikitext fence);\n"
    "> then regenerate this preview with\n"
    "> `<skills>/wiki-article-from-claims/scripts/make_preview.py`.\n"
    "> This file is never published.\n"
)


def extract_fence(text: str) -> str:
    m = FENCE_RE.search(text)
    if not m:
        raise ValueError("no ```wikitext fence found")
    return m.group(1)


def extract_topic(text: str) -> str:
    m = FRONTMATTER_RE.match(text)
    if m:
        tm = re.search(r"^topic:\s*(.+)$", m.group(1), re.M)
        if tm:
            return tm.group(1).strip()
    return ""


def sanitize_footnote_id(name: str) -> str:
    """Obsidian footnote ids: keep it to word chars and dashes."""
    name = name.strip().strip('"').strip("'")
    name = re.sub(r"[^\w\-]", "-", name)
    return name or "ref"


def convert(body: str) -> str:
    footnotes: dict[str, str] = {}   # id -> definition text (insertion-ordered)
    auto_n = 0
    author_labels = load_author_labels()

    def register(name: str, content: str | None) -> str:
        fid = sanitize_footnote_id(name)
        # show the reviewer the author's name, not the internal ref key;
        # unknown keys additionally try the frozen id's historical 'anon-' form
        fid = author_labels.get(fid) or author_labels.get(f"anon-{fid}") or fid
        if content is not None:
            content = content.strip()
            if fid in footnotes and footnotes[fid] and footnotes[fid] != content:
                # same name, different content: keep first, note nothing (spec forbids this anyway)
                pass
            elif content:
                footnotes[fid] = content
        else:
            footnotes.setdefault(fid, "")
        return f"[^{fid}]"

    def ref_full(m: re.Match) -> str:
        return register(m.group("name"), m.group("content"))

    def ref_self(m: re.Match) -> str:
        return register(m.group("name"), None)

    def ref_anon(m: re.Match) -> str:
        nonlocal auto_n
        auto_n += 1
        return register(f"r{auto_n}", m.group("content"))

    out = body
    # refs (named-full first, then self-closing, then anonymous)
    out = re.sub(
        r"<ref\s+name\s*=\s*(?P<name>\"[^\"]*\"|'[^']*'|[^\s/>]+)\s*>(?P<content>.*?)</ref>",
        ref_full, out, flags=re.S)
    out = re.sub(
        r"<ref\s+name\s*=\s*(?P<name>\"[^\"]*\"|'[^']*'|[^\s/>]+)\s*/\s*>",
        ref_self, out)
    out = re.sub(r"<ref\s*>(?P<content>.*?)</ref>", ref_anon, out, flags=re.S)

    # unresolved self-closing refs (name seen only as self-closing; definition unknown)
    # -> leave the marker; flag in footer below.

    # headings: == X == (2..6 '=') -> markdown ## X
    def heading(m: re.Match) -> str:
        level = len(m.group(1))
        return "#" * level + " " + m.group(2).strip()
    out = re.sub(r"^[ \t]*(={2,6})[ \t]*(.*?)[ \t]*\1[ \t]*$", heading, out, flags=re.M)

    # bold / italic
    out = re.sub(r"'''(.*?)'''", r"**\1**", out, flags=re.S)
    out = re.sub(r"''(.*?)''", r"*\1*", out, flags=re.S)

    # category links dropped entirely (line if alone, else inline)
    out = re.sub(r"^\[\[\s*རིགས་དབྱེ།\s*[:：][^\]]*\]\]\s*$", "", out, flags=re.M)
    out = re.sub(r"\[\[\s*རིགས་དབྱེ།\s*[:：][^\]]*\]\]", "", out)

    # wikilinks -> plain display text (never leak vault links into the preview)
    out = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", out)
    out = re.sub(r"\[\[([^\]]*)\]\]", r"\1", out)

    # <references /> dropped — Obsidian renders footnote definitions instead
    out = re.sub(r"^\s*<references\s*/>\s*$", "", out, flags=re.M)

    # tidy: collapse 3+ blank lines
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"

    # footnote definitions, in order of first appearance
    defs, missing = [], []
    for fid, content in footnotes.items():
        if content:
            defs.append(f"[^{fid}]: {content}")
        else:
            missing.append(fid)
            defs.append(f"[^{fid}]: (ref definition not found in article — check article.md)")
    if defs:
        out += "\n" + "\n".join(defs) + "\n"
    if missing:
        print(f"  WARNING: self-closing ref(s) with no full definition: {', '.join(missing)}",
              file=sys.stderr)
    return out


def make_preview(article_path: Path) -> Path:
    text = article_path.read_text(encoding="utf-8")
    body = extract_fence(text)
    topic = extract_topic(text) or article_path.parent.name
    converted = convert(body)

    frontmatter = (
        "---\n"
        f"topic: {topic}\n"
        "article_kind: article-preview\n"
        "generated: true\n"
        "generated_from: article.md\n"
        "generated_by: wiki-article-from-claims/scripts/make_preview.py\n"
        "---\n"
    )
    out_path = article_path.parent / "article-preview.md"
    out_path.write_text(frontmatter + "\n" + WARNING_CALLOUT + "\n" + converted,
                        encoding="utf-8")
    return out_path


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    status = 0
    for arg in argv:
        p = Path(arg)
        try:
            out = make_preview(p)
            print(f"OK  {p}  ->  {out}")
        except Exception as e:
            print(f"FAIL  {p}: {e}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
