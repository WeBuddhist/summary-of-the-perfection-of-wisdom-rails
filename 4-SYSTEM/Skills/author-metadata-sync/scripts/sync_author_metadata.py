#!/usr/bin/env python3
"""Propagate author metadata from 1-SOURCES/Commentaries/ frontmatter into the
per-commentary raw claims files, and report (never silently fix) every other
place in the vault that still disagrees.

The source commentary frontmatter is the single point of truth for:
    author            (Tibetan, human-curated)
    author_in_use     (Tibetan in-article address form; blank => falls back to author)
    author_in_english (English phonetic form)

Writes (only with --write):
    2-RAILS/Claims/raw/tree-guided/<id>.md   frontmatter: author, author_in_use,
                                             author_in_english; plus the
                                             "**Commentary:** `<id>` · <english>" header line.

Reports (never writes):
    4-SYSTEM/Guidelines/vault-annex.md       registry-table author column mismatches
    4-SYSTEM/Pipelines/wikipedia/corpora/*/sources.yaml   author mismatches
    3-TRANSFORMATIONS/Wikipedia/*/(term|slot)-articles + work/pilot-v2 articles:
        placeholder strings and old-name usage (informational; articles are
        fixed by redrafting, not by this script)

Usage:
    python3 sync_author_metadata.py            # check mode: report only
    python3 sync_author_metadata.py --write    # apply the claims-file sync
"""
import glob
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SOURCES = os.path.join(ROOT, "1-SOURCES", "Commentaries")
CLAIMS = os.path.join(ROOT, "2-RAILS", "Claims", "raw", "tree-guided")
ANNEX = os.path.join(ROOT, "4-SYSTEM", "Guidelines", "vault-annex.md")
PLACEHOLDERS = ["མཛད་པ་པོ་མ་གསལ", "མཇུག་བྱང་མི་གསལ", "author unknown", "unknown"]


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    d = {}
    if m:
        for line in m.group(1).split("\n"):
            mm = re.match(r'^([a-z_]+):\s*"?(.*?)"?\s*$', line)
            if mm:
                d[mm.group(1)] = mm.group(2).strip()
    return d


def load_sources():
    src = {}
    for f in glob.glob(os.path.join(SOURCES, "*.md")):
        d = frontmatter(f)
        rid = d.get("registered_id")
        if not rid:
            continue
        author = d.get("author", "")
        src[rid] = {
            "author": author,
            # blank author_in_use falls back to author by design (skill Rule 2)
            "author_in_use": d.get("author_in_use") or author,
            "author_in_english": d.get("author_in_english", ""),
            "file": os.path.relpath(f, ROOT),
        }
    return src


def set_field(head, field, value):
    """Replace field's value, or insert the field after author:, in a frontmatter block."""
    if re.search(rf"^{field}:", head, re.M):
        return re.sub(rf"^{field}:.*$", f'{field}: "{value}"', head, count=1, flags=re.M)
    return re.sub(r"^(author:.*)$", lambda m: m.group(1) + f'\n{field}: "{value}"', head, count=1, flags=re.M)


def sync_claims(src, write):
    changed = []
    for f in sorted(glob.glob(os.path.join(CLAIMS, "*.md"))):
        rid = os.path.basename(f)[:-3]
        if rid not in src:
            print(f"  !! {rid}: no source commentary with this registered_id — skipped")
            continue
        s = src[rid]
        text = open(f, encoding="utf-8").read()
        head, sep, rest = text.partition("\n---\n")
        d = frontmatter(f)
        edits = []
        for field in ("author", "author_in_use", "author_in_english"):
            if not s[field]:
                continue
            if d.get(field, "") != s[field]:
                edits.append(f"{field}: {d.get(field, '<absent>')!r} -> {s[field]!r}")
                head = set_field(head, field, s[field])
        # the human-readable header line under the H1 carries author_in_english
        if s["author_in_english"]:
            pat = rf"^(\*\*Commentary:\*\* `{re.escape(rid)}` · ).*$"
            new_rest, n = re.subn(pat, lambda m: m.group(1) + s["author_in_english"], rest, count=1, flags=re.M)
            if n and new_rest != rest:
                edits.append("header line updated")
                rest = new_rest
        if edits:
            changed.append((rid, edits))
            if write:
                open(f, "w", encoding="utf-8").write(head + sep + rest)
    return changed


def report_registry(src):
    """Annex table + sources.yaml rows whose author disagrees with the sources."""
    issues = []
    annex = open(ANNEX, encoding="utf-8").read() if os.path.exists(ANNEX) else ""
    for rid, s in sorted(src.items()):
        row = re.search(rf"^\| `{re.escape(rid)}` \| ([^|]+) \|", annex, re.M)
        if row and s["author_in_english"] and s["author_in_english"] not in row.group(1):
            issues.append(f"vault-annex row `{rid}`: {row.group(1).strip()!r} vs source {s['author_in_english']!r}")
    for y in glob.glob(os.path.join(ROOT, "4-SYSTEM", "Pipelines", "*", "corpora", "*", "sources.yaml")):
        text = open(y, encoding="utf-8").read()
        # sources.yaml rows are keyed by siglum, not registered_id — compare by value
        for rid, s in sorted(src.items()):
            if s["author"] and s["author"].rstrip("་།") not in text:
                issues.append(f"{os.path.relpath(y, ROOT)}: no row carries author {s['author']!r} ({rid})")
    return issues


def report_articles(src):
    """Placeholder strings still present in drafted articles (informational)."""
    hits = []
    pats = [p for p in PLACEHOLDERS if p not in ("unknown",)]
    for f in glob.glob(os.path.join(ROOT, "3-TRANSFORMATIONS", "Wikipedia", "*", "*-articles", "*", "*.md")) + \
             glob.glob(os.path.join(ROOT, "3-TRANSFORMATIONS", "Wikipedia", "*", "work", "pilot-v2", "*", "*.md")):
        text = open(f, encoding="utf-8").read()
        for p in pats:
            c = text.count(p)
            if c:
                hits.append(f"{os.path.relpath(f, ROOT)}: {c}x {p!r}")
    return hits


def main():
    write = "--write" in sys.argv
    src = load_sources()
    print(f"sources loaded: {len(src)} commentaries")
    for rid, s in sorted(src.items()):
        missing = [k for k in ("author", "author_in_use", "author_in_english") if not s[k]]
        if missing:
            print(f"  !! {rid}: missing {missing} in source frontmatter")

    print(f"\n== claims-file sync ({'WRITE' if write else 'check only'}) ==")
    changed = sync_claims(src, write)
    if not changed:
        print("  all claims files already in sync")
    for rid, edits in changed:
        print(f"  {rid}:")
        for e in edits:
            print(f"    - {e}")

    print("\n== registry mismatches (report-only; fix by hand or per skill Procedure) ==")
    issues = report_registry(src)
    print("  none" if not issues else "\n".join("  - " + i for i in issues))

    print("\n== article placeholders (report-only; fixed by redraft or targeted patch) ==")
    hits = report_articles(src)
    print("  none" if not hits else "\n".join("  - " + h for h in hits))


if __name__ == "__main__":
    main()
