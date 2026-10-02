#!/usr/bin/env python3
"""
plan_schedule.py — build, audit and edit a plan stream's day -> verse schedule.

Subcommands:
  build   — generate the initial schedule table from a root text's block IDs
            and a verses-per-day rule (no existing schedule needed)
  audit   — structural health check of a schedule file (no changes)
  plan    — dry run: show exactly what a verse shift would change (no changes)
  apply   — perform the shift: rewrite the schedule file and rename day files

Usage:
  python plan_schedule.py build --root <root-text.md> --verses-per-day 2 \\
      --start-date 2026-07-06 [--skip-weekday Sun] [--skip-date 2026-08-01] \\
      --out <schedule.md>
  python plan_schedule.py audit --schedule <schedule.md>
  python plan_schedule.py plan  --schedule <schedule.md> --verse 3.22 --to-day 50
  python plan_schedule.py apply --schedule <schedule.md> --verse 3.22 --to-day 50 \\
      --day-dir "<plan>/<lang>/days" \\
      --day-file-pattern "day-{day}-ch{chapter}-v{start}-{end}.md"

Model
-----
Each chapter's verses are partitioned into contiguous, non-overlapping,
gap-free day-buckets (rows sharing the same chapter). A verse can only move to
a *different* day by pushing it across the boundary it currently sits on:

  - If the verse is the LAST verse of its day, it may move FORWARD to any
    later day in the same chapter. Every day strictly between the source and
    target loses one verse from its front and gains one at its back (net size
    unchanged, whole range shifts down by one); the source day shrinks by one
    verse at its end; the target day grows by one verse at its front.

  - If the verse is the FIRST verse of its day, it may move BACKWARD to any
    earlier day in the same chapter, by the mirror-image rule.

  - A single-verse day's verse is both first and last, so it may move either
    direction.

A verse in the *middle* of a day cannot be moved this way without splitting
that day's range in two, which this script does not support — it stops and
reports the problem instead of guessing.

The index column tracks the text's global verse numbering. Within one chapter,
index - chapter_verse is a constant offset (verified by `audit`), so once the
range column is recomputed the index column follows by re-adding that offset.
This script never touches the day-number, group or date columns — only the
range and index cells for the rows between (and including) the source and
target day, plus the day-file names for those same rows.

Every column name, the range separator, the day-file name pattern and the
day-file folder are parameters; nothing about one particular text or plan is
baked in. Stdlib only.
"""

import argparse
import datetime
import glob
import os
import re
import subprocess
import sys

SENTINEL = "\x00"

WEEKDAYS = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
}


# --------------------------------------------------------------- table I/O --

def parse_row(line, ncols):
    """Split a markdown table row into cells, stripping ==highlight== markers
    and recording which cells were highlighted."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    inner = stripped.strip("|")
    cells = [c.strip() for c in inner.split("|")]
    if ncols is not None and len(cells) != ncols:
        return None
    values, highlighted = [], []
    for c in cells:
        h = False
        if c.startswith("==") and c.endswith("==") and len(c) >= 4:
            h = True
            c = c[2:-2]
        values.append(c)
        highlighted.append(h)
    return values, highlighted


def parse_range_cell(cell):
    """Return (prefix, chapter, start, end, well_formed) from a range cell.

    Handles "3.20-3.22"-style ranges, "10.58"-style single verses,
    "Prologue, 1.1-1.3"-style prefixed rows, and tolerates a malformed end
    token (e.g. "3.32-3-33" where a dot was typed as a hyphen) by recovering
    it and flagging the row as not well-formed.
    """
    tokens = list(re.finditer(r"(\d+)\.(\d+)", cell))
    if not tokens:
        raise ValueError("cannot find a chapter.verse token in %r" % cell)
    first = tokens[0]
    chapter = int(first.group(1))
    start = int(first.group(2))
    prefix = cell[: first.start()]

    if len(tokens) >= 2:
        second = tokens[1]
        if int(second.group(1)) != chapter:
            raise ValueError("range spans two chapters in %r" % cell)
        return prefix, chapter, start, int(second.group(2)), True

    rest = cell[first.end():].strip()
    if not rest:
        return prefix, chapter, start, start, True  # genuine single verse

    rest = rest.lstrip("-–—").strip()
    m = re.match(r"(\d+)-(\d+)", rest)  # e.g. "3-33" meant as "3.33"
    if m and int(m.group(1)) == chapter:
        return prefix, chapter, start, int(m.group(2)), False
    m = re.match(r"(\d+)", rest)
    if m:
        return prefix, chapter, start, int(m.group(1)), False

    raise ValueError("cannot parse end of range in %r" % cell)


def parse_index_cell(cell):
    nums = re.findall(r"\d+", cell)
    if not nums:
        raise ValueError("cannot find a number in index cell %r" % cell)
    start = int(nums[0])
    end = int(nums[1]) if len(nums) > 1 else start
    return start, end


def format_range_cell(prefix, chapter, start, end, dash):
    body = ("%d.%d" % (chapter, start) if start == end
            else "%d.%d%s%d.%d" % (chapter, start, dash, chapter, end))
    return prefix + body


def format_index_cell(start, end, dash):
    return str(start) if start == end else "%d%s%d" % (start, dash, end)


def load_schedule(path, cols):
    """cols is a dict with keys day, group, range, index (index may be None)."""
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    header_idx = None
    header_cells = None
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cols["day"] in cells:
            header_idx, header_cells = i, cells
            break
    if header_idx is None:
        raise SystemExit(
            "Could not find a header row containing the column %r in %s. "
            "Pass --day-col/--range-col/--index-col to match this schedule's "
            "own column names." % (cols["day"], path))

    ncols = len(header_cells)
    idx_of = {}
    for key, name in cols.items():
        if name is None:
            idx_of[key] = None
            continue
        if name not in header_cells:
            if key in ("group", "index"):
                idx_of[key] = None
                continue
            raise SystemExit("Column %r not found in the header row of %s "
                             "(found: %s)" % (name, path, header_cells))
        idx_of[key] = header_cells.index(name)

    sep_idx = header_idx + 1
    sep_cells = [c.strip() for c in lines[sep_idx].strip().strip("|").split("|")]
    if len(sep_cells) != ncols:
        raise SystemExit("Header separator row does not have %d columns" % ncols)
    # keep the table's own column widths: the header line's cells, minus the
    # single space of padding on each side that render_row puts back.
    raw_parts = lines[header_idx].rstrip("\n").strip().strip("|").split("|")
    col_widths = [max(len(p) - 2, len(header_cells[k])) for k, p in enumerate(raw_parts)]

    rows = []
    for i in range(sep_idx + 1, len(lines)):
        line = lines[i]
        if not line.strip().startswith("|"):
            continue
        parsed = parse_row(line, ncols)
        if parsed is None:
            continue
        values, hl = parsed
        try:
            day = int(re.sub(r"[^\d]", "", values[idx_of["day"]]))
            rprefix, chapter, rstart, rend, ok = parse_range_cell(values[idx_of["range"]])
            if idx_of["index"] is not None:
                istart, iend = parse_index_cell(values[idx_of["index"]])
            else:
                istart = iend = None
        except (ValueError, IndexError) as e:
            print("WARNING: skipping unparseable row at line %d: %s" % (i + 1, e),
                  file=sys.stderr)
            continue
        rows.append({
            "line_idx": i,
            "cells": values,
            "highlighted": hl,
            "day": day,
            "chapter": chapter,
            "rprefix": rprefix,
            "rstart": rstart,
            "rend": rend,
            "range_well_formed": ok,
            "istart": istart,
            "iend": iend,
        })
    return lines, rows, col_widths, idx_of


def render_row(row, col_widths, idx_of, dash):
    cells = list(row["cells"])
    cells[idx_of["range"]] = format_range_cell(
        row["rprefix"], row["chapter"], row["rstart"], row["rend"], dash)
    if idx_of["index"] is not None:
        cells[idx_of["index"]] = format_index_cell(row["istart"], row["iend"], dash)
    out = []
    for c, w, h in zip(cells, col_widths, row["highlighted"]):
        content = "==%s==" % c if h else c
        out.append(" " + content.ljust(w) + " ")
    return "|" + "|".join(out) + "|\n"


# ------------------------------------------------------------------ build --

VERSE_ID_RE = re.compile(r"\^(\d+)-(\d+)\s*$")


def collect_verse_ids(root_path, chapters=None):
    """Read the root text and return [(chapter, verse)] in document order.

    Only two-segment content block IDs at end of line count. Heading anchors
    (`^N-0`, `^N-N-0`) and deeper paths are skipped: the `-0` slot is reserved
    for headings and original content always starts at 1.
    """
    ids = []
    seen = set()
    with open(root_path, encoding="utf-8") as f:
        for line in f:
            m = VERSE_ID_RE.search(line.rstrip())
            if not m:
                continue
            c, v = int(m.group(1)), int(m.group(2))
            if v == 0:
                continue                      # heading anchor
            if chapters and c not in chapters:
                continue
            if (c, v) in seen:
                continue
            seen.add((c, v))
            ids.append((c, v))
    return ids


def build_dates(start_date, count, skip_weekdays, skip_dates, fmt):
    out = []
    d = start_date
    while len(out) < count:
        if d.weekday() in skip_weekdays or d in skip_dates:
            d += datetime.timedelta(days=1)
            continue
        out.append(d.strftime(fmt))
        d += datetime.timedelta(days=1)
    return out


def cmd_build(args):
    if os.path.exists(args.out) and not args.force:
        raise SystemExit("%s already exists. Refusing to overwrite a schedule; "
                         "pass --force only if the human asked for a rebuild."
                         % args.out)
    chapters = None
    if args.chapters:
        chapters = set()
        for part in args.chapters.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                chapters.update(range(int(a), int(b) + 1))
            elif part:
                chapters.add(int(part))

    ids = collect_verse_ids(args.root, chapters)
    if not ids:
        raise SystemExit("No content block IDs of the form `^C-V` were found in %s. "
                         "Check that the root text carries block IDs." % args.root)

    # group into per-chapter buckets of --verses-per-day, never crossing a chapter
    buckets = []          # (chapter, start, end, ch_day)
    i = 0
    ch_day = {}
    while i < len(ids):
        c, v = ids[i]
        chunk = [ids[i]]
        j = i + 1
        while j < len(ids) and len(chunk) < args.verses_per_day and ids[j][0] == c:
            chunk.append(ids[j])
            j += 1
        ch_day[c] = ch_day.get(c, 0) + 1
        buckets.append((c, chunk[0][1], chunk[-1][1], ch_day[c]))
        i = j

    start = datetime.datetime.strptime(args.start_date, "%Y-%m-%d").date()
    skip_weekdays = set()
    for w in args.skip_weekday or []:
        key = w.strip().lower()[:3]
        if key not in WEEKDAYS:
            raise SystemExit("Unknown weekday %r (use Mon..Sun)" % w)
        skip_weekdays.add(WEEKDAYS[key])
    skip_dates = set(datetime.datetime.strptime(d, "%Y-%m-%d").date()
                     for d in (args.skip_date or []))
    dates = build_dates(start, len(buckets), skip_weekdays, skip_dates, args.date_format)

    headers = [args.day_col]
    if args.group_col:
        headers.append(args.group_col)
    headers.append(args.range_col)
    if args.index_col:
        headers.append(args.index_col)
    headers.append(args.date_col)

    index_of = {}
    for n, (c, v) in enumerate(ids, 1):
        index_of[(c, v)] = n

    body = []
    for n, (c, vs, ve, cd) in enumerate(buckets, 1):
        row = [str(n)]
        if args.group_col:
            row.append(str(cd))
        row.append(format_range_cell("", c, vs, ve, args.range_dash))
        if args.index_col:
            row.append(format_index_cell(index_of[(c, vs)], index_of[(c, ve)],
                                         args.range_dash))
        row.append(dates[n - 1])
        body.append(row)

    widths = [max([len(h)] + [len(r[k]) for r in body])
              for k, h in enumerate(headers)]

    def line(cells):
        return "|" + "|".join(" " + c.ljust(widths[k]) + " "
                              for k, c in enumerate(cells)) + "|"

    skipped = []
    if skip_weekdays:
        inv = {v: k for k, v in WEEKDAYS.items()}
        skipped += [inv[w].capitalize() for w in sorted(skip_weekdays)]
    skipped += [d.isoformat() for d in sorted(skip_dates)]

    out = []
    out.append("---")
    if args.plan:
        out.append("plan: %s" % args.plan)
    if args.stream:
        out.append("stream: %s" % args.stream)
    out.append("verses_per_day: %d" % args.verses_per_day)
    out.append("start_date: %s" % args.start_date)
    out.append("skipped: %s" % (", ".join(skipped) if skipped else "none"))
    out.append("generated_by: plan-schedule build")
    out.append("status: draft")
    out.append("---")
    out.append("")
    out.append("# %s" % (args.title or "Schedule"))
    out.append("")
    out.append("Generated by `plan-schedule build`. Never edit this table by hand —")
    out.append("use `plan-schedule plan` then `plan-schedule apply` to move a verse.")
    out.append("")
    out.append(line(headers))
    out.append("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    for row in body:
        out.append(line(row))
    out.append("")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(out))
    print("Wrote %d day rows covering %d verses -> %s"
          % (len(buckets), len(ids), args.out))
    return 0


# ------------------------------------------------------------------ audit --

def cmd_audit(args):
    cols = col_spec(args)
    _, rows, _, idx_of = load_schedule(args.schedule, cols)
    if not rows:
        raise SystemExit("No parseable rows found in %s" % args.schedule)
    chapters = sorted(set(r["chapter"] for r in rows))
    problems = 0
    for ch in chapters:
        crows = sorted([r for r in rows if r["chapter"] == ch], key=lambda r: r["day"])
        offsets = set()
        if idx_of["index"] is not None:
            offsets = set(r["istart"] - r["rstart"] for r in crows)
        expected_next = crows[0]["rstart"]
        gap_or_overlap = []
        for r in crows:
            if r["rstart"] != expected_next:
                gap_or_overlap.append(r["day"])
            expected_next = r["rend"] + 1
        malformed = [r["day"] for r in crows if not r["range_well_formed"]]
        status = "OK"
        if (idx_of["index"] is not None and len(offsets) != 1) or gap_or_overlap or malformed:
            status = "ISSUES"
            problems += 1
        print("Chapter %2d: days %d-%d, verses %d-%d, index-offset=%s, status=%s"
              % (ch, crows[0]["day"], crows[-1]["day"], crows[0]["rstart"],
                 crows[-1]["rend"], sorted(offsets) if offsets else "n/a", status))
        if gap_or_overlap:
            print("    gap/overlap at day(s): %s" % gap_or_overlap)
        if malformed:
            print("    non-canonical range cell formatting at day(s): %s "
                  "(parsed via a tolerant fallback — verify by hand)" % malformed)
    days = [r["day"] for r in rows]
    dupes = sorted(set(d for d in days if days.count(d) > 1))
    if dupes:
        print("    duplicate day numbers: %s" % dupes)
        problems += 1
    print("\n%d chapters checked, %d with issues." % (len(chapters), problems))
    return 1 if problems else 0


# ------------------------------------------------------------ plan / apply --

def find_source_row(rows, chapter, verse):
    for r in rows:
        if r["chapter"] == chapter and r["rstart"] <= verse <= r["rend"]:
            return r
    return None


def find_row_by_day(rows, day):
    for r in rows:
        if r["day"] == day:
            return r
    return None


def compute_shift(rows, chapter, verse, to_day, has_index):
    src = find_source_row(rows, chapter, verse)
    if src is None:
        raise SystemExit("Verse %d.%d was not found in any day of the schedule."
                         % (chapter, verse))
    dst = find_row_by_day(rows, to_day)
    if dst is None:
        raise SystemExit("Day %d was not found in the schedule." % to_day)
    if dst["day"] == src["day"]:
        print("Verse %d.%d is already on day %d. Nothing to do."
              % (chapter, verse, to_day))
        return None
    if dst["chapter"] != src["chapter"]:
        raise SystemExit(
            "Verse %d.%d is in chapter %d (day %d), but day %d is in chapter %d. "
            "This script only supports shifts within a single chapter — a "
            "cross-chapter move also changes each chapter's total verse count, "
            "the chapter folder's day range, and the index offset, and needs a "
            "human to adjudicate. Stopping without making any changes."
            % (chapter, verse, src["chapter"], src["day"], to_day, dst["chapter"]))

    is_last = verse == src["rend"]
    is_first = verse == src["rstart"]

    if to_day > src["day"]:
        if not is_last:
            raise SystemExit(
                "Verse %d.%d is not the LAST verse of day %d (that day covers "
                "%d.%d-%d.%d). Only the first or last verse of a day can move to "
                "another day without splitting that day's range. Stopping without "
                "making any changes."
                % (chapter, verse, src["day"], chapter, src["rstart"], chapter,
                   src["rend"]))
        direction = "forward"
    else:
        if not is_first:
            raise SystemExit(
                "Verse %d.%d is not the FIRST verse of day %d (that day covers "
                "%d.%d-%d.%d). Only the first or last verse of a day can move to "
                "another day without splitting that day's range. Stopping without "
                "making any changes."
                % (chapter, verse, src["day"], chapter, src["rstart"], chapter,
                   src["rend"]))
        direction = "backward"

    offset = None
    if has_index:
        offsets = set(r["istart"] - r["rstart"] for r in rows if r["chapter"] == chapter)
        if len(offsets) != 1:
            raise SystemExit(
                "Chapter %d's index offset is not constant across its rows (%s). "
                "Refusing to guess the new index numbers — fix the index column "
                "for chapter %d first, or compute the shift by hand."
                % (chapter, sorted(offsets), chapter))
        offset = next(iter(offsets))

    lo, hi = ((src["day"], dst["day"]) if direction == "forward"
              else (dst["day"], src["day"]))
    day_list = sorted([r for r in rows if lo <= r["day"] <= hi], key=lambda r: r["day"])

    changes = []
    n = len(day_list)
    for i, r in enumerate(day_list):
        new_start, new_end = r["rstart"], r["rend"]
        if direction == "forward":
            if i == 0:
                new_end -= 1
            elif i == n - 1:
                new_start -= 1
            else:
                new_start -= 1
                new_end -= 1
        else:
            if i == 0:
                new_end += 1
            elif i == n - 1:
                new_start += 1
            else:
                new_start += 1
                new_end += 1
        changes.append((r, new_start, new_end))

    for r, new_start, new_end in changes:
        if new_end < new_start:
            raise SystemExit(
                "Day %d (currently %d.%d-%d.%d) would become empty under this "
                "shift. This script does not support collapsing a day to zero "
                "verses. Stopping without making any changes."
                % (r["day"], chapter, r["rstart"], chapter, r["rend"]))

    result = []
    for r, new_start, new_end in changes:
        result.append({
            "row": r,
            "old_start": r["rstart"], "old_end": r["rend"],
            "new_start": new_start, "new_end": new_end,
            "new_istart": None if offset is None else new_start + offset,
            "new_iend": None if offset is None else new_end + offset,
        })
    return {"chapter": chapter, "verse": verse, "direction": direction,
            "source_day": src["day"], "target_day": dst["day"], "changes": result}


def day_filename(pattern, single_pattern, day, chapter, start, end):
    pat = single_pattern if (single_pattern and start == end) else pattern
    return pat.format(day=day, chapter=chapter, start=start, end=end)


def day_glob(pattern, day, chapter):
    p = pattern.format(day=day, chapter=chapter, start=SENTINEL, end=SENTINEL)
    i = p.find(SENTINEL)
    return (p[:i] + "*") if i >= 0 else p


def resolve_day_dir(day_dir_template, chapter):
    pat = day_dir_template.format(chapter=chapter)
    if any(ch in pat for ch in "*?["):
        matches = [m for m in sorted(glob.glob(pat)) if os.path.isdir(m)]
        if len(matches) != 1:
            raise SystemExit("Expected exactly one directory matching %r, found %d: %s"
                             % (pat, len(matches), matches))
        return matches[0]
    return pat


def print_plan(plan, args):
    print("Move verse %d.%d from day %d to day %d (%s shift, %d day(s) affected):\n"
          % (plan["chapter"], plan["verse"], plan["source_day"], plan["target_day"],
             plan["direction"], len(plan["changes"])))
    for c in plan["changes"]:
        r = c["row"]
        old_v = format_range_cell(r["rprefix"], plan["chapter"], c["old_start"],
                                  c["old_end"], args.range_dash)
        new_v = format_range_cell(r["rprefix"], plan["chapter"], c["new_start"],
                                  c["new_end"], args.range_dash)
        line = "  Day %3d  %s: %-22r -> %-22r" % (r["day"], args.range_col, old_v, new_v)
        if c["new_istart"] is not None:
            line += "  %s: %r -> %r" % (
                args.index_col,
                format_index_cell(r["istart"], r["iend"], args.range_dash),
                format_index_cell(c["new_istart"], c["new_iend"], args.range_dash))
        print(line)

    if args.day_file_pattern:
        print("\nDay files to rename:")
        for c in plan["changes"]:
            r = c["row"]
            old_name = day_filename(args.day_file_pattern, args.day_file_pattern_single,
                                    r["day"], plan["chapter"], c["old_start"], c["old_end"])
            new_name = day_filename(args.day_file_pattern, args.day_file_pattern_single,
                                    r["day"], plan["chapter"], c["new_start"], c["new_end"])
            print("  %s  ->  %s" % (old_name, new_name))


def apply_schedule(schedule_path, lines, col_widths, idx_of, plan, dash):
    for c in plan["changes"]:
        r = c["row"]
        r["rstart"], r["rend"] = c["new_start"], c["new_end"]
        if c["new_istart"] is not None:
            r["istart"], r["iend"] = c["new_istart"], c["new_iend"]
        lines[r["line_idx"]] = render_row(r, col_widths, idx_of, dash)
    with open(schedule_path, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    print("\nSchedule file updated: %s" % schedule_path)


def git_root_for(path):
    try:
        out = subprocess.run(
            ["git", "-C", os.path.dirname(os.path.abspath(path)),
             "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return None


def rename_day_files(args, plan):
    folder = resolve_day_dir(args.day_dir, plan["chapter"])
    repo_root = git_root_for(folder)
    for c in plan["changes"]:
        r = c["row"]
        pattern = day_glob(args.day_file_pattern, r["day"], plan["chapter"])
        candidates = sorted(glob.glob(os.path.join(folder, pattern)))
        if len(candidates) != 1:
            print("  WARNING: expected exactly one existing file matching %r in %s, "
                  "found %d: %s. Skipping rename for this day — rename it by hand."
                  % (pattern, folder, len(candidates), candidates), file=sys.stderr)
            continue
        old_path = candidates[0]
        new_path = os.path.join(folder, day_filename(
            args.day_file_pattern, args.day_file_pattern_single,
            r["day"], plan["chapter"], c["new_start"], c["new_end"]))
        if os.path.abspath(old_path) == os.path.abspath(new_path):
            continue
        moved = False
        if repo_root:
            rel_old = os.path.relpath(old_path, repo_root)
            rel_new = os.path.relpath(new_path, repo_root)
            res = subprocess.run(["git", "-C", repo_root, "mv", rel_old, rel_new],
                                 capture_output=True, text=True)
            if res.returncode == 0:
                moved = True
            else:
                print("  git mv failed for %s -> %s: %s"
                      % (rel_old, rel_new, res.stderr.strip()), file=sys.stderr)
        if not moved:
            os.rename(old_path, new_path)
        print("  Renamed: %s -> %s"
              % (os.path.basename(old_path), os.path.basename(new_path)))


def cmd_plan_or_apply(args, do_apply):
    m = re.match(r"^\s*(\d+)[.\-](\d+)\s*$", args.verse)
    if not m:
        raise SystemExit("--verse must look like '3.22' or '3-22', got %r" % args.verse)
    chapter, verse = int(m.group(1)), int(m.group(2))

    cols = col_spec(args)
    lines, rows, col_widths, idx_of = load_schedule(args.schedule, cols)
    plan = compute_shift(rows, chapter, verse, args.to_day, idx_of["index"] is not None)
    if plan is None:
        return 0
    print_plan(plan, args)

    if do_apply:
        print()
        apply_schedule(args.schedule, lines, col_widths, idx_of, plan, args.range_dash)
        if args.day_file_pattern and args.day_dir:
            print("Renaming day files:")
            rename_day_files(args, plan)
        else:
            print("No --day-dir/--day-file-pattern given: day files were NOT renamed.")
        print("\nDone. Day file *content* (verse text, headings) was NOT touched — "
              "only the schedule table and the file names. Review the renamed files "
              "if their content needs to follow the verses to their new day.")
    return 0


# ------------------------------------------------------------------- main --

def col_spec(args):
    return {"day": args.day_col, "group": args.group_col,
            "range": args.range_col, "index": args.index_col}


def add_col_args(p):
    p.add_argument("--day-col", default="Day")
    p.add_argument("--group-col", default="Ch.Day")
    p.add_argument("--range-col", default="Verses")
    p.add_argument("--index-col", default="Index",
                   help="pass an empty string if the schedule has no index column")
    p.add_argument("--date-col", default="Date")
    p.add_argument("--range-dash", default="–", help="separator inside a range cell")


def add_file_args(p):
    p.add_argument("--day-dir", default=None,
                   help="folder holding the day files; may contain {chapter} and globs")
    p.add_argument("--day-file-pattern", default=None,
                   help="e.g. 'day-{day}-ch{chapter}-v{start}-{end}.md'")
    p.add_argument("--day-file-pattern-single", default=None,
                   help="optional pattern used when start == end")


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("build", help="generate the initial schedule table")
    pb.add_argument("--root", required=True, help="root text carrying ^C-V block IDs")
    pb.add_argument("--verses-per-day", type=int, required=True)
    pb.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    pb.add_argument("--skip-weekday", action="append", help="Mon..Sun, repeatable")
    pb.add_argument("--skip-date", action="append", help="YYYY-MM-DD, repeatable")
    pb.add_argument("--chapters", help="e.g. '1-10' or '1,2,5'")
    pb.add_argument("--date-format", default="%Y-%m-%d")
    pb.add_argument("--out", required=True)
    pb.add_argument("--plan"), pb.add_argument("--stream"), pb.add_argument("--title")
    pb.add_argument("--force", action="store_true")
    add_col_args(pb)

    pa = sub.add_parser("audit", help="structural health check of the schedule")
    pa.add_argument("--schedule", required=True)
    add_col_args(pa)

    pp = sub.add_parser("plan", help="dry run: show what would change")
    pp.add_argument("--schedule", required=True)
    pp.add_argument("--verse", required=True, help="e.g. 3.22 or 3-22")
    pp.add_argument("--to-day", required=True, type=int)
    add_col_args(pp), add_file_args(pp)

    pap = sub.add_parser("apply", help="perform the edit")
    pap.add_argument("--schedule", required=True)
    pap.add_argument("--verse", required=True, help="e.g. 3.22 or 3-22")
    pap.add_argument("--to-day", required=True, type=int)
    add_col_args(pap), add_file_args(pap)

    args = p.parse_args()
    if getattr(args, "index_col", None) == "":
        args.index_col = None
    if args.cmd == "build":
        return cmd_build(args)
    if args.cmd == "audit":
        return cmd_audit(args)
    if args.cmd == "plan":
        return cmd_plan_or_apply(args, do_apply=False)
    if args.cmd == "apply":
        return cmd_plan_or_apply(args, do_apply=True)
    return 2


if __name__ == "__main__":
    sys.exit(main())
