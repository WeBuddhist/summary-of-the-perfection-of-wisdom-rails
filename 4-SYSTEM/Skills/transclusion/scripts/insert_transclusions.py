"""
insert_transclusions.py
Type 1 version-to-version transclusion insertion.

Inserts ![[source#^N-V]] transclusion links into target file immediately
before each verse line, following the vault transclusion skill format:

  [blank line]
  ![[1-SOURCES/Text/<root-text>.md#^N-V]]
  [blank line]
  verse text ^N-V

Skips any ID whose transclusion already appears immediately before it
(safe to re-run on a partially-transcluded file).

Usage:
  python3 insert_transclusions.py --source <full vault-relative source path> \
      <target-file.md> [--dry-run]

--source is the full vault-relative path (with .md) written inside the
transclusion link; it is required. Without --dry-run the target is rewritten
in place.
"""

import re
import sys

# The full vault-relative path written inside every ![[...]] link, and the
# file that receives them. Both are required — nothing is hard-coded.
_flags = [a for a in sys.argv[1:] if a.startswith("--")]
_args = [a for a in sys.argv[1:] if not a.startswith("--")]

if "--source" in sys.argv:
    _i = sys.argv.index("--source")
    try:
        TRANSCLUSION_BASE = sys.argv[_i + 1]
    except IndexError:
        sys.exit("--source needs a value")
    _args = [a for a in _args if a != TRANSCLUSION_BASE]
else:
    sys.exit(__doc__)

if not _args:
    sys.exit("give the target file to receive the transclusions")
TARGET_PATH = _args[0]

# Matches verse/colophon block IDs:
#   ^I-1, ^1-1, ^10-58, ^10-a, ^a-1, ^b-3, etc.
# Does NOT match heading IDs ending in -0: ^I-0, ^1-0, ^a-0, ^b-0
# Does NOT match bare title ID: ^0
VERSE_ID_RE = re.compile(r" \^(I|\d+|[a-z])-(?!0$)([a-zA-Z0-9]+)$")

dry_run = "--dry-run" in sys.argv


def process(path: str) -> tuple[list[str], list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    output: list[str] = []
    inserted: list[str] = []

    for line in lines:
        stripped = line.rstrip("\n")
        m = VERSE_ID_RE.search(stripped)
        if m:
            block_id = f"^{m.group(1)}-{m.group(2)}"
            transclusion = f"![[{TRANSCLUSION_BASE}#{block_id}]]\n"
            # Skip if this transclusion already exists immediately before this
            # verse (walk back past any trailing blank lines to find the last
            # non-blank line).
            already_there = False
            for prev in reversed(output):
                if prev.strip() == "":
                    continue
                if prev.rstrip("\n") == transclusion.rstrip("\n"):
                    already_there = True
                break
            if not already_there:
                # Insert transclusion + blank line before the verse line.
                # The blank line already present in output before this verse
                # becomes the blank line before the transclusion block.
                output.append(transclusion)
                output.append("\n")
                inserted.append(block_id)
        output.append(line)

    return output, inserted


output_lines, inserted = process(TARGET_PATH)

print(f"Transclusions to insert: {len(inserted)}")
if inserted:
    print(f"  First: {inserted[0]}")
    print(f"  Last:  {inserted[-1]}")
    if len(inserted) <= 20:
        for bid in inserted:
            print(f"    {bid}")

if dry_run:
    print("\n[dry-run] No file written.")
else:
    with open(TARGET_PATH, "w", encoding="utf-8") as f:
        f.writelines(output_lines)
    print("\nFile written successfully.")
