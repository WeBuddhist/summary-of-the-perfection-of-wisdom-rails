#!/usr/bin/env python3
r"""
apply.py — Obsidian-Block-ID-to-Commentary skill

Adds Obsidian-style block IDs to every ###/#### sub-heading and body-text
block in a Tibetan commentary file, keyed off a label the human contributor
has already written by hand on each enclosing ## heading.

Numbering scheme:
- The # title (at most one per file) is auto-generated: -> ^0
- Every ## heading MUST already end in a manually-added "^{label}-0" id
  before this script will tag anything in the file. {label} can be any
  short token the contributor is using for that section (a running number,
  a Roman numeral, a letter, ...) — this script never generates, edits, or
  guesses a ## heading's own id. If any ## heading is missing one, the
  script aborts and names every offending heading rather than tagging the
  rest of the file around it.
- ### Sub-section        -> ^{label}-{h3}-0          (h3 resets to 1 at each new ##)
- #### Sub-sub-section    -> ^{label}-{h3}-{h4}-0     (h4 resets to 1 at each new ###)
- Body-text blocks (a run of consecutive non-blank, non-heading,
  non-transclusion lines, terminated by a blank line or a heading) are
  numbered ^{label}-{n}, where {label} is the enclosing ##'s manual label
  and n is a running counter that starts at 1 under each ## and is NOT
  reset by ### or #### sub-headings within it.
- Root-text transclusion lines (![[...]]) are never modified and never
  receive an id, and they do not consume a body counter value — they are
  invisible to the numbering.
- The block id is appended to the END of the block's LAST line only
  (" ^id"), never inserted as a new line. ## heading lines are never
  appended to — their id is already there, written by hand.

Assumptions / limitations (see SKILL.md §Rules):
- No body content may appear between the `#` title and the first `##`
  heading. If any is found, the script aborts rather than guessing a
  numbering for it (front matter of that shape has never been validated).
- Only heading levels 1-4 (#, ##, ###, ####) are supported. A ##### or
  deeper heading aborts the script - flag it for human review instead of
  inventing a fifth numbering tier. A #### heading also requires an
  enclosing ### in the same ## section; one that doesn't have one aborts
  rather than guessing a numbering for it.
- A heading line always starts a new block, even if it directly abuts the
  previous line with no blank line between them (a known formatting
  inconsistency in some raw commentary files).
- YAML frontmatter (a file that opens with a `---` line) is passed through
  untouched, matching the sibling `commentary-verse-id` skill.

Usage:
    python apply.py audit <path-to-file.md>
    python apply.py apply <path-to-file.md> [output.md]

`audit` reports, per ## section (identified by its manual label), the
first id, last id, and block count that would be tagged - without writing
anything. It also runs the ## label pre-flight check, so a missing label
is caught here before any real run.
`apply` writes the tagged output. If output.md is omitted, the input file
is overwritten in place.
"""
import re
import sys

HEADING_RE = re.compile(r'^(#{1,6})\s+\S')
TRANSCLUSION_RE = re.compile(r'^!\[\[.*\]\]\s*$')
# Idempotency check for lines this script itself tags (#, ###, ####, body):
# a label (letters/digits) followed by zero to three purely-numeric segments.
EXISTING_ID_RE = re.compile(r'\s\^[0-9A-Za-z]+(?:-[0-9]+){0,3}\s*$')
# A ## heading's manually-added id: "^{label}-0" at end of line. {label}
# may contain letters and/or digits (Roman numerals, plain numbers, or
# single/double letters all fit this) but not a hyphen.
HEADING2_ID_RE = re.compile(r'\^([0-9A-Za-z]+)-0\s*$')


class AbortError(Exception):
    pass


def read_lines(path):
    data = open(path, encoding='utf-8', newline='').read()
    eol = '\r\n' if '\r\n' in data else '\n'
    return data.split(eol), eol


def segment_blocks(lines, frontmatter_end):
    """Return a list of (start, end, kind) over lines[frontmatter_end:],
    kind in {'heading', 'transclusion', 'body'}. A heading line always
    forces its own block boundary, even without a blank line around it.
    """
    blocks = []
    i = frontmatter_end
    n = len(lines)
    current_start = None
    while i < n:
        stripped = lines[i].strip()
        if stripped == '':
            if current_start is not None:
                blocks.append((current_start, i - 1, 'body'))
                current_start = None
            i += 1
            continue
        if HEADING_RE.match(stripped):
            if current_start is not None:
                blocks.append((current_start, i - 1, 'body'))
                current_start = None
            level = len(stripped) - len(stripped.lstrip('#'))
            if level >= 5:
                raise AbortError(
                    f"Line {i+1}: heading level {level} (#####+) is not "
                    f"supported by this skill — stop and flag for human "
                    f"review instead of guessing a fifth numbering tier.\n"
                    f"  {lines[i]!r}"
                )
            blocks.append((i, i, 'heading'))
            i += 1
            continue
        if TRANSCLUSION_RE.match(stripped) and current_start is None:
            blocks.append((i, i, 'transclusion'))
            i += 1
            continue
        if current_start is None:
            current_start = i
        i += 1
    if current_start is not None:
        blocks.append((current_start, n - 1, 'body'))
    return blocks


def check_all_h2_labeled(lines, blocks):
    """Pre-flight check (SKILL.md Rule 1): every ## heading must already
    carry a manual ^{label}-0 id. Collects ALL offenders before aborting,
    so the contributor gets one complete list rather than discovering them
    one re-run at a time.
    """
    missing = []
    for (s, e, kind) in blocks:
        if kind != 'heading':
            continue
        stripped = lines[s].strip()
        level = len(stripped) - len(stripped.lstrip('#'))
        if level != 2:
            continue
        if not HEADING2_ID_RE.search(lines[e]):
            missing.append((s + 1, lines[s]))
    if missing:
        lines_desc = "\n".join(f"  Line {ln}: {txt!r}" for ln, txt in missing)
        raise AbortError(
            "ABORTED — nothing written. The following ## heading(s) are "
            "missing a manually-added block id (must end in \"^{label}-0\", "
            "e.g. \"^I-0\", \"^1-0\", \"^a-0\") and this skill will never "
            "generate one on its own:\n"
            f"{lines_desc}\n"
            "Add an id to each of these by hand, then re-run."
        )


def tag_blocks(lines, blocks):
    check_all_h2_labeled(lines, blocks)

    label = None        # current ##'s manual label, e.g. "I", "1", "a"
    h3 = 0
    h4 = 0
    body_counter = 1
    seen_h2 = False
    stats = []  # (label, first_n, last_n, count)
    current_section = None  # [label, first, last]
    heading_count = 0

    for (s, e, kind) in blocks:
        if kind == 'heading':
            stripped = lines[s].strip()
            level = len(stripped) - len(stripped.lstrip('#'))
            heading_count += 1

            if level == 1:
                bid = "^0"
                if EXISTING_ID_RE.search(lines[e]):
                    continue
                lines[e] = lines[e] + " " + bid
                continue

            if level == 2:
                if not seen_h2 and body_counter > 1:
                    raise AbortError(
                        "Body content was found between the # title and "
                        "the first ## heading — this skill does not have "
                        "a validated numbering for that case. Stop and "
                        "ask the human contributor how to number it."
                    )
                m = HEADING2_ID_RE.search(lines[e])
                if not m:
                    # Guaranteed present by check_all_h2_labeled; guard anyway.
                    raise AbortError(
                        f"Line {s+1}: expected a manual ^{{label}}-0 id on "
                        f"this ## heading."
                    )
                seen_h2 = True
                label = m.group(1)
                h3 = 0
                h4 = 0
                if current_section is not None:
                    stats.append(tuple(current_section))
                current_section = [label, None, None]
                body_counter = 1
                # Never modify a ## heading line — its id is manual (Rule 1).
                continue

            if level == 3:
                if not seen_h2:
                    raise AbortError(
                        f"Line {s+1}: a ### heading appeared before any "
                        f"## heading — cannot assign ^{{label}}-{{h3}}-0."
                    )
                h3 += 1
                h4 = 0
                bid = f"^{label}-{h3}-0"
                if EXISTING_ID_RE.search(lines[e]):
                    continue
                lines[e] = lines[e] + " " + bid
                continue

            if level == 4:
                if not seen_h2:
                    raise AbortError(
                        f"Line {s+1}: a #### heading appeared before any "
                        f"## heading — cannot assign ^{{label}}-{{h3}}-{{h4}}-0."
                    )
                if h3 == 0:
                    raise AbortError(
                        f"Line {s+1}: a #### heading appeared before any "
                        f"### heading in this ## section — cannot assign "
                        f"^{{label}}-{{h3}}-{{h4}}-0 without an enclosing ###."
                    )
                h4 += 1
                bid = f"^{label}-{h3}-{h4}-0"
                if EXISTING_ID_RE.search(lines[e]):
                    continue
                lines[e] = lines[e] + " " + bid
                continue

            raise AbortError(f"Unreachable heading level {level} at line {s+1}")

        if kind == 'transclusion':
            continue  # never tagged, never consumes a counter

        # body block
        if not seen_h2:
            raise AbortError(
                f"Line {s+1}: body content appears before the first ## "
                f"heading — this skill does not have a validated "
                f"numbering for that case. Stop and ask the human "
                f"contributor how to number it."
            )
        bid = f"^{label}-{body_counter}"
        if EXISTING_ID_RE.search(lines[e]):
            continue  # idempotent: already tagged, leave untouched, no counter bump
        if current_section[1] is None:
            current_section[1] = body_counter
        current_section[2] = body_counter
        lines[e] = lines[e] + " " + bid
        body_counter += 1

    if current_section is not None:
        stats.append(tuple(current_section))
    return lines, heading_count, stats


def process(lines):
    frontmatter_end = 0
    if lines and lines[0].strip() == '---':
        for j in range(1, len(lines)):
            if lines[j].strip() == '---':
                frontmatter_end = j + 1
                break
    blocks = segment_blocks(lines, frontmatter_end)
    return tag_blocks(lines, blocks)


def print_stats(heading_count, stats):
    print(f"Headings seen: {heading_count}")
    if not stats:
        print("No body blocks found — nothing to tag.")
        return
    print(f"{'section':<10}{'first_id':<16}{'last_id':<16}{'count'}")
    for label, first, last in stats:
        header = f"^{label}"
        if first is None:
            print(f"{header:<10}{'(none)':<16}{'(none)':<16}0")
            continue
        count = last - first + 1
        first_id = f"^{label}-{first}"
        last_id = f"^{label}-{last}"
        print(f"{header:<10}{first_id:<16}{last_id:<16}{count}")


def cmd_audit(path):
    lines, eol = read_lines(path)
    _, heading_count, stats = process(lines)
    print_stats(heading_count, stats)


def cmd_apply(infile, outfile):
    lines, eol = read_lines(infile)
    new_lines, heading_count, stats = process(lines)
    new_data = eol.join(new_lines)
    open(outfile, 'w', encoding='utf-8', newline='').write(new_data)
    print(f"Wrote {outfile}")
    print_stats(heading_count, stats)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    infile = sys.argv[2]
    try:
        if mode == 'audit':
            cmd_audit(infile)
        elif mode == 'apply':
            outfile = sys.argv[3] if len(sys.argv) > 3 else infile
            cmd_apply(infile, outfile)
        else:
            print(__doc__)
            sys.exit(1)
    except AbortError as exc:
        print(f"{exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
