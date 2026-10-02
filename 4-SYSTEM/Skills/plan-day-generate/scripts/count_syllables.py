#!/usr/bin/env python3
"""Count Tibetan syllables in a text — used to enforce the syllable ceilings
declared in a plan's section-type table.

Method: Tibetan syllables are tsheg-delimited units. This module strips
markdown scaffolding (headings, bold/italic markers, wikilinks, block-id
anchors) and Tibetan punctuation (tsheg, the various shad forms), then counts
the remaining whitespace/tsheg/shad-delimited chunks. This is an
approximation — good enough for a hard-ceiling check, but treat counts within
a syllable or two of the limit as "verify by eye", not gospel.

Also usable as a module: `from count_syllables import count_syllables,
count_words`.

Usage:
    python3 count_syllables.py path/to/file.md
    python3 count_syllables.py -            # read from stdin
    echo "..." | python3 count_syllables.py -
"""
import re
import sys

# Block IDs are `^C-V`, `^V`, `^C-V-N` … — any run of alphanumeric segments.
BLOCK_ID = re.compile(r"\^[0-9A-Za-z]+(?:-[0-9A-Za-z]+)*")


def clean(text):
    text = re.sub(r"!?\[\[.*?\]\]", " ", text)   # wikilinks and transclusions
    text = BLOCK_ID.sub(" ", text)               # block-id anchors
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)  # html comments
    text = re.sub(r"[#>*_`]", " ", text)         # markdown scaffolding
    text = re.sub(r"^\s*-{3,}\s*$", " ", text, flags=re.MULTILINE)  # hr rules
    return text


def count_syllables(text):
    text = clean(text)
    # Tibetan tsheg U+0F0B, shad variants U+0F0D-U+0F0E, plus whitespace
    boundary = re.compile(r"[་།༎༌\s]+")
    parts = [p for p in boundary.split(text) if p.strip()]
    return len(parts)


def count_words(text):
    """Whitespace-delimited word count for alphabetic and abugida scripts."""
    text = clean(text)
    text = re.sub(r"[|]", " ", text)
    parts = [p for p in re.split(r"\s+", text) if p.strip(" .,;:!?()[]{}।॥")]
    return len(parts)


def count(text, unit):
    if unit == "syllables":
        return count_syllables(text)
    if unit == "words":
        return count_words(text)
    raise ValueError("unknown unit %r (use 'words' or 'syllables')" % unit)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    data = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    print(count_syllables(data))


if __name__ == "__main__":
    main()
