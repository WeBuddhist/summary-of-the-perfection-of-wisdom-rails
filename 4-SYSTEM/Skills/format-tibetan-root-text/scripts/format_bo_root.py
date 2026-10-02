#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
format_bo_root.py — table-driven Tibetan root-text formatter.

Unlike format_bca.py (which detects chapter boundaries from a colophon
formula), this script applies an explicit CHAPTER_STARTS / COLOPHONS /
CHAPTER_HEADINGS table. Edit the constants below for a new text — best used
when the source has plain sequential verse numbers with no colophon marker
reliable enough to auto-detect.

Writes `^N-0` chapter-heading anchors (the repo's canonical convention —
see 4-SYSTEM/CLAUDE.md §5a). Does NOT write the deprecated `^TOC-N`
style.

Usage:
    python3 format_bo_root.py --input 0-INBOX/temp/<text-id>/cleaned.md \
                               --output 0-INBOX/temp/<text-id>/segmented.md

The constants below (CHAPTER_STARTS, COLOPHONS, CHAPTER_HEADINGS) are the
Bodhicaryāvatāra (BCA) example this script was built against — replace them
with the equivalent table for a new text before running.
"""

import os
import sys
import re
import argparse

# Example (from the Bodhicaryāvatāra) — chapter starts (list item numbers in
# the input file). Replace for a new text.
CHAPTER_STARTS = {
    1: 5,
    2: 42,
    3: 108,
    4: 142,
    5: 191,
    6: 301,
    7: 436,
    8: 513,
    9: 701,
    10: 869
}

# Example (from the Bodhicaryāvatāra) — colophon list item numbers.
COLOPHONS = {
    1: 41,
    2: 107,
    3: 141,
    4: 190,
    5: 300,
    6: 435,
    7: 512,
    8: 700,
    9: 868,
    10: 927
}

# Example (from the Bodhicaryāvatāra) — chapter headings with ^N-0 anchors
# (NOT the deprecated ^TOC-N style).
CHAPTER_HEADINGS = {
    1: "## 1. ལེའུ་དང་པོ། བྱང་ཆུབ་སེམས་ཀྱི་ཕན་ཡོན་བཤད་པ། ^1-0",
    2: "## 2. ལེའུ་གཉིས་པ། སྡིག་པ་བཤགས་པ། ^2-0",
    3: "## 3. ལེའུ་གསུམ་པ། བྱང་ཆུབ་ཀྱི་སེམས་ཡོངས་སུ་བཟུང་བ། ^3-0",
    4: "## 4. ལེའུ་བཞི་པ། བག་ཡོད་བསྟན་པ། ^4-0",
    5: "## 5. ལེའུ་ལྔ་པ། ཤེས་བཞིན་བསྲུང་བར་བྱ་བ། ^5-0",
    6: "## 6. ལེའུ་དྲུག་པ། བཟོད་པ་བསྟན་པ། ^6-0",
    7: "## 7. ལེའུ་བདུན་པ། བརྩོན་འགྲུས་བསྟན་པ། ^7-0",
    8: "## 8. ལེའུ་བརྒྱད་པ། བསམ་གཏན་བསྟན་པ། ^8-0",
    9: "## 9. ལེའུ་དགུ་པ། ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ། ^9-0",
    10: "## 10. ལེའུ་བཅུ་པ། བསྔོ་བ། ^10-0"
}

def get_chapter_for_num(num):
    current_ch = 0
    for ch, start in sorted(CHAPTER_STARTS.items()):
        if num >= start:
            current_ch = ch
        else:
            break
    return current_ch

def split_stanza(text):
    text = text.strip()
    parts = text.split(' །')
    lines = []
    for part in parts:
        part = part.strip()
        if part:
            lines.append(part + ' །')
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--input', required=True, help='Path to 0-INBOX/temp/<text-id>/cleaned.md (or similar)')
    ap.add_argument('--output', required=True, help='Path to write 0-INBOX/temp/<text-id>/segmented.md')
    args = ap.parse_args()

    INPUT_PATH = args.input
    OUTPUT_PATH = args.output

    print(f"Input path: {INPUT_PATH}")
    print(f"Output path: {OUTPUT_PATH}")

    if not os.path.exists(INPUT_PATH):
        sys.exit(f"Error: Input file not found at {INPUT_PATH}")

    # Read input file
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()

    print(f"Read {len(raw_lines)} lines from input.")

    LINE_PAT = re.compile(r'^(\d+)\.\s+(.*)$')

    formatted_lines = []

    # Write Frontmatter
    formatted_lines.append("---")
    formatted_lines.append("title: <fill in — Tibetan Root Text>")
    formatted_lines.append("author: <fill in>")
    formatted_lines.append("language: Tibetan")
    formatted_lines.append("file_type: root-text")
    formatted_lines.append("lang_tag: bo")
    formatted_lines.append("source_description: \"<fill in — see 1-SOURCES/About Sources.md §4>\"")
    formatted_lines.append("verse_id_format: chapter-verse")
    formatted_lines.append("---")
    formatted_lines.append("")

    current_chapter = 0

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue

        m = LINE_PAT.match(line)
        if not m:
            continue

        num = int(m.group(1))
        text = m.group(2).strip()

        # Chapter 0 (Introduction)
        if 1 <= num <= 4:
            if num == 1:
                formatted_lines.append("## 0. Introduction ^0-0")
                formatted_lines.append("")
            # Clean ch-1 prefix
            text = re.sub(r'^ch-\d+\s+', '', text)
            formatted_lines.append(f"{text} ^0-{num}")
            formatted_lines.append("")
            continue

        # Check for chapter start
        ch = get_chapter_for_num(num)
        if ch != current_chapter and ch > 0:
            current_chapter = ch
            formatted_lines.append(CHAPTER_HEADINGS[ch])
            formatted_lines.append("")

        # Check if colophon line
        if num in COLOPHONS.values():
            formatted_lines.append(text)
            formatted_lines.append("")
            continue

        # Check if trailing translator colophon (line number one past the last chapter's colophon)
        if num == max(COLOPHONS.values()) + 1:
            formatted_lines.append("## Translator Colophon")
            formatted_lines.append("")
            formatted_lines.append(text)
            formatted_lines.append("")
            continue

        # Otherwise, it's a standard verse in chapter `ch`
        if ch > 0:
            rel_v = num - CHAPTER_STARTS[ch] + 1
            # Clean ch-N prefix if present
            text = re.sub(r'^ch-\d+\s+', '', text)

            vlines = split_stanza(text)
            for i, vl in enumerate(vlines):
                if i == len(vlines) - 1:
                    formatted_lines.append(f"{vl} ^{ch}-{rel_v}")
                else:
                    formatted_lines.append(vl)
            formatted_lines.append("")

    # Ensure output directory exists
    out_dir = os.path.dirname(OUTPUT_PATH)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Write output file
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(formatted_lines))

    print(f"Successfully formatted Tibetan root text and saved to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
