---
name: plan-schedule
description: >
  Build, audit and edit a plan stream's day → verse distribution table. `build`
  generates the initial schedule from the root text's block IDs and a
  verses-per-day rule (with a start date and skipped dates); `audit` checks each
  chapter's ranges for contiguity, gaps, overlaps and a constant index offset;
  `plan` dry-runs a verse shift; `apply` rewrites the schedule and `git mv`s the
  affected day files to match.

  Trigger on "build the schedule", "generate the day-verse distribution", "how
  many verses per day", "move verse 3.22 to day 50", "shift 5.40 one day later",
  "put 8.100 on day 240 instead", "redistribute the verses", "check the
  schedule", "the day files don't match the schedule".

  The schedule path, the column names, the range separator and the day-file
  name pattern are all parameters — nothing about one text or one plan is baked
  into the script.
---

# plan-schedule

Owns the day ↔ verse calendar of a plan stream.

A schedule row's range cell (`3.20–3.22`) and index cell (`127–129`) describe a
contiguous, gap-free block of a chapter's verses. Moving one verse to a
different day means the boundary between two days shifts, and every day
strictly between the old and new position has to shift with it to stay
contiguous. Done by hand this is error-prone arithmetic across a long table
plus a matching set of file renames; this skill delegates the arithmetic to
`4-SYSTEM/Skills/plan-schedule/scripts/plan_schedule.py` so that the two source-of-truth artefacts —
the schedule table and the day-file names — never drift out of sync.

This skill changes **only** the range and index cells for the affected days,
and the day-file *names* for those same days. It does not touch the day-number,
group or date columns, and it does not touch the *content* inside any day file.

---

## Inputs

| Input | Description | Default |
|---|---|---|
| `schedule` | Path to the stream's schedule file. | `3-TRANSFORMATIONS/Plans/<plan>/<lang>/schedule.md` |
| `root` (build only) | The root text carrying `^C-V` block IDs. | per `vault-annex.md` |
| `verses-per-day` (build only) | How many verses each day covers. Days never cross a chapter boundary, so the last day of a chapter may be shorter. | — |
| `start-date` (build only) | ISO date of day 1. | — |
| `skip-weekday` / `skip-date` (build only) | Weekdays and individual dates the calendar skips. Repeatable. | none |
| `verse` / `to-day` (plan, apply) | The verse to move, as `C.V` or `C-V`, and the target day number. | — |
| `day-dir` | Folder holding the day files. May contain `{chapter}` and globs, e.g. `…/days` or `…/days/Chapter-{chapter} D*`. | — |
| `day-file-pattern` | Day-file name as a format string over `{day} {chapter} {start} {end}`. | — |
| `day-file-pattern-single` | Optional variant used when `start == end`. | same as `day-file-pattern` |
| Column names | `--day-col --group-col --range-col --index-col --date-col`. Pass `--index-col ""` when the schedule has no index column. | `Day`, `Ch.Day`, `Verses`, `Index`, `Date` |
| `range-dash` | Separator inside a range cell. | en dash `–` |

Read these off `About <plan-name>.md` (**Naming** part) rather than asking the
human for paths that the plan already declares. If the plan does not declare
them, that is a `plan-scaffold` gap — say so.

## Output

- The stream's `schedule.md`, created by `build` or modified in place by
  `apply`: range and index cells rewritten for every day between (and
  including) the verse's old day and its new day.
- The stream's day files, renamed in place (via `git mv` when the folder is
  inside a git repo, so history follows the file) for every day whose verse
  range changed. **File contents are untouched by this skill.**

---

## Output file format

The schedule is a markdown table under YAML frontmatter:

```markdown
| Day | Ch.Day | Verses  | Index | Date       |
|-----|--------|---------|-------|------------|
| 1   | 1      | 1.1–1.2 | 1–2   | 2026-07-06 |
| 2   | 2      | 1.3–1.4 | 3–4   | 2026-07-07 |
```

- **Day** — absolute session number across the whole plan, no zero-padding.
- **Ch.Day** — ordinal of the day within its chapter.
- **Verses** — contiguous `C.V–C.V` range, or a single `C.V`.
- **Index** — running verse index across the whole text for the downstream
  consumer; `Index − verse` is constant within a chapter.
- **Date** — delivery date.

Shifting `3.22` from day 49 to day 50 (unaffected columns identical):

```
| 49 | 9  | 3.20–3.22 | 127–129 | Aug 23 |
| 50 | 10 | 3.23–3.24 | 130–131 | Aug 24 |
```
becomes
```
| 49 | 9  | 3.20–3.21 | 127–128 | Aug 23 |
| 50 | 10 | 3.22–3.24 | 129–131 | Aug 24 |
```

with the matching renames:

```
day-49-ch3-v20-22.md  ->  day-49-ch3-v20-21.md
day-50-ch3-v23-24.md  ->  day-50-ch3-v22-24.md
```

---

## Rules

1. **A verse can only move if it sits at a boundary of its current day.** If it
   is the last verse of its day it may move forward to any later day in the same
   chapter; if it is the first verse it may move backward to any earlier day. A
   verse in the middle of a day cannot move without splitting that day's range —
   the script stops and reports this rather than guessing what the user meant.
2. **Cross-chapter moves are not supported.** A shift where the target day
   belongs to a different chapter than the source verse changes each chapter's
   total verse count, the chapter folder's own day range, and the index offset —
   that needs a human decision, not an automated ripple. The script stops and
   reports this.
3. **No day may be emptied.** If a shift would reduce some day's range to zero
   verses, the script stops before writing anything.
4. **Only the range and index cells change.** The day number, the group column
   and the date are never modified — the calendar and the day-count structure
   stay fixed; only which verses fall on which day changes.
5. **Day-file content is never touched by this skill.** Only the file *name*
   changes to match the new verse range. If the verse text or headings inside a
   renamed day file need to follow the verse to its new day, that is a separate,
   explicit follow-up — tell the human it is outstanding after the rename.
6. **All-or-nothing.** If any row in the affected range would become invalid
   (empty, cross-chapter, non-boundary verse, inconsistent index offset), no
   file is written and no rename happens — never leave the schedule and the
   filenames partially updated relative to each other.
7. **Never hand-edit the schedule table or day-file names for this task.**
   Always go through the script so the ripple arithmetic and the renames stay
   derived from the same computation. Manual edits are only for fixing an
   unrelated, already-flagged anomaly after review.
8. **Renames use `git mv` when the day folder is inside a git repo**, so file
   history follows the move; they fall back to a plain rename otherwise.
9. **`build` never overwrites an existing schedule.** A rebuild discards every
   manual correction and every shift ever applied. It requires `--force` and an
   explicit human instruction.
10. **Days never cross a chapter boundary.** `build` starts a fresh bucket at
    every chapter, so the last day of a chapter may hold fewer verses than the
    rule asks for. That is correct, not an error.
11. **A pre-existing anomaly is reported, not silently fixed.** If `audit`
    flags a non-canonical cell or a gap that predates the requested change,
    record it in the schedule's "Known anomalies" section and leave it alone
    unless the human asks for it.

---

## Procedure

The helper script lives at `4-SYSTEM/Skills/plan-schedule/scripts/plan_schedule.py`. Construct its path
at runtime from this skill's own location.

### `build` — create the initial calendar

```bash
python3 "4-SYSTEM/Skills/plan-schedule/scripts/plan_schedule.py" build \
  --root "<root text path>" \
  --verses-per-day <N> --start-date <YYYY-MM-DD> \
  [--skip-weekday Sun] [--skip-date <YYYY-MM-DD>] [--chapters 1-10] \
  [--date-format "%Y-%m-%d"] \
  --plan <plan-name> --stream <lang> --title "<Plan title> — <lang> schedule" \
  --out "3-TRANSFORMATIONS/Plans/<plan>/<lang>/schedule.md"
```

The script reads every two-segment content block ID (`^C-V`) in document order,
skipping heading anchors (the `-0` slot), buckets them per chapter into runs of
`--verses-per-day`, assigns the running index, and walks the calendar forward
skipping the excluded dates. Then run `audit` on the result and read it.

If the root text has no block IDs, stop — run `add-block-ids` / the vault's
formatting skill first. Do not invent a verse count.

### `audit` — check the table

```bash
python3 "4-SYSTEM/Skills/plan-schedule/scripts/plan_schedule.py" audit --schedule "<schedule.md>"
```

Run this **once per session before relying on the schedule**; it is cheap and
catches pre-existing data issues. It confirms, per chapter, that the ranges are
contiguous and gap-free, that the index offset is constant, that no day number
repeats, and that no range cell needed the tolerant fallback parser. A cell that
parsed only via the fallback is flagged, not corrected.

### `plan` — dry run a shift

```bash
python3 "4-SYSTEM/Skills/plan-schedule/scripts/plan_schedule.py" plan \
  --schedule "<schedule.md>" --verse "<C.V>" --to-day <N> \
  --day-dir "<day folder>" --day-file-pattern "<pattern>"
```

Read the printed table of old → new cells per affected day and the list of file
renames. If the script exits with an error (non-boundary verse, cross-chapter,
would-empty day, inconsistent offset), relay that message to the human plainly —
do not try to route around it by hand.

**Confirm scope with the human if the ripple is large.** A one-day-adjacent move
touches two rows; a move across many days touches every day in between. If the
plan shows more than a handful of affected days, say so and let the human
confirm before applying — it is easy to typo a target day far from the intended
one.

### `apply` — perform the shift

```bash
python3 "4-SYSTEM/Skills/plan-schedule/scripts/plan_schedule.py" apply \
  --schedule "<schedule.md>" --verse "<C.V>" --to-day <N> \
  --day-dir "<day folder>" --day-file-pattern "<pattern>" \
  [--day-file-pattern-single "<pattern>"]
```

This rewrites the schedule and renames the day files in one pass, using the
exact same computation already reviewed by `plan`.

### Verify and report

Re-run `audit` to confirm no new contiguity or offset problems were introduced,
and spot-check that the renamed files exist with their new names. Then tell the
human what was and was not done — **state explicitly that day-file content was
not modified**, in case the verse text inside those files needs manual follow-up
to match its new day.

---

## Completion check

- [ ] `audit` was run and any pre-existing issues were noted, not silently fixed.
- [ ] For `build`: the output covers every verse of the requested range with no
      gap, no day crosses a chapter, and `audit` reports no issues.
- [ ] For a shift: `plan` was run and its output reviewed before `apply`.
- [ ] Large ripples (more than a couple of days) were confirmed with the human
      before applying.
- [ ] `apply` completed with the schedule file and every affected day-file
      rename done together (all-or-nothing).
- [ ] Post-apply `audit` shows no new contiguity or offset issues.
- [ ] The human was told that day-file content (verse text, headings) was not
      changed — only the schedule table and the file names.
- [ ] Column names, day-file pattern and day folder were taken from
      `About <plan-name>.md`, not guessed.
