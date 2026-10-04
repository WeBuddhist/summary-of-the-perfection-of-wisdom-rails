#!/usr/bin/env python3
"""Deterministic steps of running toc-generate on a row-aligned commentary
(aligned-corpus-intake Route B). The LLM phases stay isolated subagents as
toc-generate prescribes; these are the mechanical steps between them.

    python3 toc_rows.py merge   <id>                 # after Phases A and B
    python3 toc_rows.py place   <id>                 # after the placement subagent
    python3 toc_rows.py promote <id> <work-key> [--accept]   # after both checkers

All paths follow toc-generate: 0-INBOX/temp/TOC-<id>/ (chunks, source.md,
source.json, placement.md/.tsv), 0-INBOX/temp/toc-*-<id>.md (merged files,
tree, QC reports), 2-RAILS/Sections/Raw/toc-*/ (promoted). Run from the vault
root.

merge    Concatenate the per-chunk candidate and enumeration files on disk
         (frontmatter as toc-generate specifies) — the text never passes
         through an orchestrator's context.
place    Take the placement subagent's output (tree with [[line]] pointers,
         '---', TSV), check that the tree is unchanged apart from the
         pointers, write the pointered tree over 0-INBOX/temp/toc-tree-<id>.md
         (the unplaced tree is kept as .unplaced.md) and the TSV beside the
         source. Run qc_check_tree.py on the .unplaced.md copy (it does not
         strip pointers) and qc_tree_vs_source.py on the pointered tree.
promote  Refuse unless both QC reports exist and report 0 issues — or
         --accept, when each remaining flag has been checked against the
         source and the QC report ends with that review and
         `issues_after_review: 0`. Write the tree to
         2-RAILS/Sections/Raw/toc-tree/<id>.md with pointer_source_sha1 (what
         the build checks) and the placement table under '## Placement', and
         move the evidence next to it.
"""
import datetime
import json
import pathlib
import re
import shutil
import sys

T = pathlib.Path("0-INBOX/temp")
R = pathlib.Path("2-RAILS/Sections/Raw")
NODE = re.compile(r"^\s*\*\s")
PTR = re.compile(r"\s*\[\[(\d+|\?)\]\]\s*$")


def merge(rid):
    d = T / f"TOC-{rid}"
    cand = sorted((d / "candidates").glob("chunk_*.md"))
    enum = sorted((d / "enumerations").glob("chunk_*.md"))
    body = "\n".join(p.read_text(encoding="utf-8").rstrip() + "\n" for p in cand)
    n = len(re.findall(r"^SECTION_TITLE:", body, re.M))
    today = datetime.date.today()
    (T / f"toc-candidates-{rid}.md").write_text(
        f"---\nsource: {rid}\nskill: toc-generate\nstage: candidates\ndate: {today}\ntotal_candidates: {n}\n---\n\n" + body,
        encoding="utf-8")
    parts = []
    for p in enum:
        t = p.read_text(encoding="utf-8").strip()
        if t and "NO ENUMERATIONS" not in t[:40]:
            parts.append(f"<!-- {p.name} -->\n{t}\n")
    (T / f"toc-enumerations-{rid}.md").write_text(
        f"---\nsource: {rid}\nskill: toc-generate\nstage: enumerations\ndate: {today}\n"
        f"chunks_with_enumerations: {len(parts)}\n---\n\n" + "\n".join(parts), encoding="utf-8")
    print(f"{rid}: {n} candidates, {len(parts)} chunk(s) with enumerations")


def place(rid):
    tree_p = T / f"toc-tree-{rid}.md"
    unplaced = T / f"toc-tree-{rid}.unplaced.md"
    if not unplaced.exists():
        unplaced.write_text(tree_p.read_text(encoding="utf-8"), encoding="utf-8")
    base = unplaced.read_text(encoding="utf-8")
    head, _, tsv = (T / f"TOC-{rid}" / "placement.md").read_text(encoding="utf-8").partition("\n---\n")
    want = [l.rstrip() for l in base.splitlines() if NODE.match(l)]
    got = [l.rstrip() for l in head.splitlines() if NODE.match(l)]
    if [PTR.sub("", l) for l in got] != want:
        sys.exit(f"{rid}: the placement changed the tree itself — re-run the placement pass")
    if any(not PTR.search(l) for l in got):
        sys.exit(f"{rid}: some nodes have no pointer")
    it = iter(got)
    tree_p.write_text("\n".join(next(it) if NODE.match(l) else l for l in base.splitlines()).rstrip() + "\n",
                      encoding="utf-8")
    (T / f"TOC-{rid}" / "placement.tsv").write_text(tsv.strip() + "\n", encoding="utf-8")
    q = sum(1 for l in got if "[[?]]" in l)
    print(f"{rid}: {len(got)} nodes placed, {q} unresolved ([[?]] — repair or re-place before promoting)")


def promote(rid, key, accept=False):
    qc1, qc2 = T / f"toc-tree-qc-{rid}.md", T / f"toc-tree-qc-source-{rid}.md"
    for q in (qc1, qc2):
        if not q.exists():
            sys.exit(f"missing {q}")
        text = q.read_text(encoding="utf-8")
        n = int(re.search(r"issues(?:_after)?:\s*(\d+)", text).group(1))
        if n and not (accept and "issues_after_review: 0" in text):
            sys.exit(f"{q}: {n} issue(s) — repair, or review each against the source and record it before --accept")
    src = json.loads((T / f"TOC-{rid}" / "source.json").read_text(encoding="utf-8"))
    tree = re.sub(r"\A---\n.*?\n---\n\n?", "", (T / f"toc-tree-{rid}.md").read_text(encoding="utf-8"), flags=re.S).strip()
    if "[[?]]" in tree:
        sys.exit(f"{rid}: the tree still has an unresolved [[?]] pointer")
    nodes = {PTR.sub("", l).split()[1].rstrip(".") for l in tree.splitlines() if NODE.match(l)}
    tsv = "\n".join(l for l in (T / f"TOC-{rid}" / "placement.tsv").read_text(encoding="utf-8").splitlines()
                    if l.split("\t")[0].strip() in nodes)
    for sub in ("toc-tree", "toc-candidates", "toc-enumerations", "toc-qc"):
        (R / sub).mkdir(parents=True, exist_ok=True)
    fm = (f"---\nregistered_id: {rid}\nsource_file: 1-SOURCES/Commentaries/{key}.md\n"
          f"pointer_source: 0-INBOX/temp/TOC-{rid}/source.md\npointer_source_sha1: {src['sha1']}\n"
          f"pointer_source_rebuild: python3 4-SYSTEM/Skills/aligned-corpus-intake/scripts/build_sources.py "
          f"0-INBOX/raw-data/intake-manifest.yaml --stage pre-toc --only {key}\n"
          f"qc_reports: [2-RAILS/Sections/Raw/toc-qc/{qc1.name}, 2-RAILS/Sections/Raw/toc-qc/{qc2.name}]\n"
          f"status: complete\n" + ("qc_accepted: \"flags reviewed against the source — see the source QC report\"\n" if accept else "")
          + "---\n\n")
    body = (f"{tree}\n\n## Placement\n\nEach node's `[[N]]` is the line, in `pointer_source`, of the row its heading "
            f"stands before (rows are indivisible alignment units). Columns: decimal, line, where the opening clause "
            f"sits in its row (START, END->NEXT, MID), the clause verbatim. Written by the placement pass "
            f"(`4-SYSTEM/Skills/aligned-corpus-intake/prompts/place-toc-at-rows.md`).\n\n```tsv\n{tsv}\n```\n")
    (R / "toc-tree" / f"{rid}.md").write_text(fm + body, encoding="utf-8")
    shutil.move(str(T / f"toc-candidates-{rid}.md"), R / "toc-candidates" / f"{rid}.md")
    shutil.move(str(T / f"toc-enumerations-{rid}.md"), R / "toc-enumerations" / f"{rid}.md")
    shutil.move(str(qc1), R / "toc-qc" / qc1.name)
    shutil.move(str(qc2), R / "toc-qc" / qc2.name)
    print(f"promoted {rid} -> {R / 'toc-tree' / (rid + '.md')}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("merge", "place", "promote"):
        sys.exit(__doc__)
    if a[0] == "merge":
        merge(a[1])
    elif a[0] == "place":
        place(a[1])
    else:
        promote(a[1], a[2], accept="--accept" in a)
