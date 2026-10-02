#!/usr/bin/env python3
"""Reorder commentator blocks inside every commentary section so that a named
commentator's block comes FIRST.

Which id goes first, and how the commentary section's heading is recognised,
are parameters — the plan declares them, not this script.

  python3 reorder_commentators.py --first <machine-id> \\
      [--section-heading "Commentary Explanations"] \\
      [--section-heading "<the same heading in another language>"] \\
      <file.md> [...]

Works on both a conformed package (with `<!-- cm:* -->` anchors and
consolidated `Sources:` lines) and an unconformed source package (plain
heading, inline `([[...]])` citations). Idempotent: if the named id is already
first, the file is left unchanged. A section with no block for that id is left
exactly as it is.

Stdlib only.
"""
import argparse
import re
import sys

H5 = re.compile(r'^#####\s+(\S+)')
ANCHOR_BLOCK = re.compile(r'^<!--\s*(?:cm|story|div):')       # travels WITH its block
ANCHOR_ID = re.compile(r'^<!--\s*(?:cm|story|div):([A-Za-z0-9._:-]+)\s*-->')
ANCHOR_SECT = re.compile(r'^<!--\s*(?:sub|verse|sec):')       # marks the NEXT section
HEAD_LE4 = re.compile(r'^#{2,4}\s')


def is_commentary_heading(line, headings):
    if not line.startswith("#### "):
        return False
    return any(h in line for h in headings)


def reorder_content(content, first_id):
    c = content[:]
    # peel trailing tail (blank lines / '---' / the next section's anchor)
    tail = []
    while c:
        s = c[-1].strip()
        if s == "" or s == "---" or ANCHOR_SECT.match(s):
            tail.insert(0, c.pop())
        else:
            break
    # locate H5 block starts (carry a preceding cm/story/div anchor into the block)
    starts = []
    for k, l in enumerate(c):
        if H5.match(l):
            start = k - 1 if (k > 0 and ANCHOR_BLOCK.match(c[k - 1].strip())) else k
            starts.append((start, k))
    if not starts:
        return content
    head = c[:starts[0][0]]
    blocks = []
    for bi, (start, h5) in enumerate(starts):
        end = starts[bi + 1][0] if bi + 1 < len(starts) else len(c)
        # the machine id lives in the cm/story/div anchor (headings are display-only);
        # fall back to the heading's first token for un-anchored legacy blocks.
        am = ANCHOR_ID.match(c[start].strip())
        bid = am.group(1) if am else H5.match(c[h5]).group(1)
        blocks.append((bid, c[start:end]))
    if blocks[0][0] == first_id:
        return content                       # already first
    wanted = [b for b in blocks if b[0] == first_id]
    if not wanted:
        return content                       # no block for that id here
    rest = [b for b in blocks if b[0] != first_id]
    new = list(head)
    for _bid, blk in wanted + rest:
        new += blk
    new += tail
    return new


def reorder(path, first_id, headings):
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    idx = 0
    while idx < len(lines):
        if is_commentary_heading(lines[idx], headings):
            j = idx + 1
            while j < len(lines) and not HEAD_LE4.match(lines[j]):
                j += 1
            lines[idx + 1:j] = reorder_content(lines[idx + 1:j], first_id)
            idx += 1
        else:
            idx += 1
    new = "\n".join(lines)
    if new != text:
        open(path, "w", encoding="utf-8").write(new)
        print("reordered: %s" % path)
        return True
    print("unchanged: %s" % path)
    return False


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--first", required=True,
                   help="the commentator machine id that must come first")
    p.add_argument("--section-heading", action="append", default=None,
                   help="text identifying the commentary H4 heading; repeatable "
                        "(once per language in use). Default: 'Commentary Explanations'")
    p.add_argument("files", nargs="+")
    args = p.parse_args()
    headings = args.section_heading or ["Commentary Explanations"]
    for f in args.files:
        reorder(f, args.first, headings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
