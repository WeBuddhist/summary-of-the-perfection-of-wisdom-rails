---
name: plan-day-package
description: >
  Build the machine-anchored per-day dossier that an app or API consumes: a
  source-of-record package that copies the day's verse rails verbatim, plus its
  translation, each carrying the plan's challenge sections, the day's verses by
  block ID, and every rail layer under `<!-- … -->` anchors with display-only
  headings. Then enforce the locked format with the reorder / conform /
  validate / guard tool chain.

  Trigger on "build the day package", "day package for day 15", "make the
  dossier the app reads", "validate the day packages", "conform the package",
  "re-baseline the guard", "the package has the wrong commentator order".

  Optional: a plan only needs this when something outside Obsidian consumes the
  day's material.
---

# plan-day-package

Produces a complete, format-locked **day package** for a single day of a plan,
in one pass, across the parallel deliverables the vault keeps: the
**source-of-record** package (rails copied verbatim, in the rails' own language)
and its **translation** (termbase-consistent, in the reader's language).

Correct output is a matched set of files that (a) copy the verse-rail content
verbatim in the source-of-record and render it faithfully in the translation,
(b) carry the plan's challenge sections and the day's verses, (c) place the
plan's declared first commentator first, (d) use display-only commentator
headings with the machine id in the anchor, and (e) pass
`day_package_tools.py validate` with zero errors.

The skill exists so that new days are built identically to old ones rather than
drifting. It prevents the recurring failure of hand-built packages that reword
rails, lose citations, mis-order commentators, or leak machine ids into
reader-facing headings.

This is the end-to-end wrapper. The three phases can also be run alone; when
only translating an already-built source-of-record file, start at Phase B.

---

## Inputs

Gather all of the following before starting. If any is missing or ambiguous,
stop and ask the human contributor — never guess a verse range or invent rail
content.

| Input | What it is | Where it comes from |
|---|---|---|
| Day number + chapter | Which day to build | the request |
| Schedule | Maps each day to its verse range and date | `About <plan>.md` → **Naming**; the stream's `schedule.md` |
| Verse rails | Per-verse source content: root verse, interlinear gloss, per-commentator explanations, stories, metaphors, scriptural quotations, main teaching points, key terms, synthesis | `2-RAILS/Verses/<verse-id>.md` |
| Plan day file | The plan-track section of the package, per stream | the stream's `days/` folder, per the plan's naming pattern |
| Verse source per stream | Reader-facing verse text, addressed by block ID | `About <plan>.md` → **Streams** |
| Format contract | The locked template every output must match | the plan's `Day-Packages/<stream>/_TEMPLATE.md`, scaffolded from `4-SYSTEM/Skills/plan-day-package/templates/day-package.md` |
| Package spec | The machine-readable section vocabulary | `Day-Packages/_package-spec.json`, scaffolded from `4-SYSTEM/Skills/plan-day-package/templates/package-spec.json` |
| Termbase | Fixed term renderings, the commentator id → display-name table, and the commentator order | the plan's `Day-Packages/<stream>/_TERMBASE.md`, or the stream's `termbase.md` |
| Tooling | validate / conform / guard and the reorder script | `4-SYSTEM/Skills/plan-day-package/scripts/day_package_tools.py`, `4-SYSTEM/Skills/plan-day-package/scripts/reorder_commentators.py` |

**The plan-track section's source is the part that changes most between plans
and streams.** Take it from the plan day file for that stream — a top-level file
in the stream's `days/` folder, never from `Archive/` or a drafts folder. Map
the plan's declared section ids onto the package's challenge sub-blocks once, in
`About <plan>.md`, and follow that mapping. Sections the package does not carry
(liturgy, dedication) are not part of the package.

If no plan day file exists for that day, **stop and ask the human contributor**
whether to (a) leave the section as the declared empty placeholder or (b) source
it from somewhere else. Never silently fall back to another stream's block, an
archived draft, or invented content — a past run that did so had to be undone by
hand.

## Output

Two files, one per language, in the parallel package folders (create the day's
folder if it does not exist):

```
3-TRANSFORMATIONS/Day-Packages/<source-stream>/<folder>/<day>.md
3-TRANSFORMATIONS/Day-Packages/<target-stream>/<folder>/<day>-<lang>.md
```

The folder naming and the file naming come from `About <plan>.md`; **the day
number is the absolute session number across the whole plan**, never
chapter-relative, in the file name, the `day:` frontmatter and the folder range.

Both are **protected source-of-truth files**: they carry `protected: true`, the
`PROTECTED — SOURCE OF TRUTH` banner, and are tracked by the drift guard. After
writing, re-baseline the guard (Phase C).

---

## Output file format

The canonical shape is the plan's `_TEMPLATE.md`; read it in full before
writing. `4-SYSTEM/Skills/plan-day-package/templates/day-package.md` is the generic skeleton it is
scaffolded from, and it carries the full list of format invariants.

Key invariants:

- Every tracked heading is immediately preceded by its `<!-- … -->` anchor, with
  no blank line between.
- **Commentator and story H5 headings are display-only** — name + work, or story
  title. The machine id lives *only* in the `<!-- cm:<id> -->` /
  `<!-- story:<id> -->` anchor above it.
- **The plan's declared first commentator comes first** in every commentary
  section; the others follow in source order. Not every verse has a block for
  that commentator; the reorder tool leaves such a section as it is.
- The **commentator count varies per verse.** Include exactly the commentators
  the rail has — never invent a missing one.
- Optional sub-sections (stories, metaphors, quotations) appear only when the
  rail has them. Some verses have none; that is valid.
- A **Divergences** heading must **start with the word "Divergences"** (a leading
  `⚑` is allowed) and carry the `<!-- div:divergences -->` anchor. If it does
  not, the validator treats it as a commentator block and errors. Two
  Divergences blocks in one file (one per verse) is fine.
- **Story ids may be placeholders** and may repeat across two stories in the same
  verse; keep them as the rail has them — duplicate `story:` anchors pass
  validation.
- Provenance is **one `Sources: [[…]] [[…]]` line per leaf section**. No inline
  `([[…]])` in prose, no `![[…]]` transclusions — the consumer is a raw-fetch
  API, not Obsidian. A table keeps its own `Source` column.
- The synthesis has two labelled parts, worded exactly `**Brief introduction.**`
  then `**Key points.**`. Do not write "Overview" or "Main points", which collide
  with the separate teaching-points section and throw off the reader view. The
  bulleted recap belongs to the synthesis by design; it is not a duplication
  error.
- The verse blocks must exactly cover the `verses:` range in the frontmatter.
- **Verse text always comes from the stream's designated verse source**, both in
  the `verse_source:` frontmatter field and everywhere the verse is quoted.
- **Verse quotes preserve the source's line breaks** — each source line gets its
  own `> ` line. Never join a multi-line verse into one flowing paragraph.

---

## Rules

1. **Never reword the rails when building the source-of-record file.** Phase A
   copies rail content verbatim — structure, prose, citations. Interpretation or
   paraphrase in the source-of-record corrupts the ground truth.
2. **Translate faithfully in Phase B.** The five constraints are mandatory: (a)
   not a literal word-for-word rendering — keep the cultural context; (b)
   terminology consistent with the termbase throughout; (c) no needlessly hard
   words and no unnecessary idioms; (d) natural, non-awkward prose; (e)
   humanised, readable. Do not add doctrine that is not in the rail.
3. **Terminology comes from the termbase.** Use the listed renderings verbatim,
   including each commentator's display name. If a needed term is absent, stop
   and ask; do not coin a new rendering silently.
4. **The machine id never appears in a reader-facing heading or in prose.** Ids
   live in anchors only. If a raw id appears in a synthesis bullet, a key-terms
   cell or a story label, replace it with the display name.
5. **The declared first commentator comes first when present.** After writing,
   run `reorder_commentators.py --first <id>` to guarantee the order even if the
   draft placed the block elsewhere. Verses with no such block are left as they
   are.
6. **Do not edit `1-SOURCES/` or `2-RAILS/`.** Rails and plan files are
   read-only inputs. This skill writes only to the package folders (and
   re-baselines the guard).
7. **A day is not done until `validate` passes with zero errors** and the drift
   guard has been re-recorded.
8. **Both files are protected.** Preserve the `protected: true` /
   `edit_policy:` frontmatter and the banner on both.
9. **Take the plan-track section from the correct plan day file for that
   stream**, and end the section with a source line naming the file actually
   used.
10. **Use the absolute day number** for the file name, the `day:` frontmatter
    and the folder range — never a chapter-relative number.
11. **No chapter special-casing.** Everything that differs between chapters —
    which sections exist, which sub-blocks are carried, where the plan-track
    section comes from — is declared once in `About <plan>.md`. A rule that
    applies only to one chapter belongs in the plan's declaration, not in this
    skill.

### The protected-file convention

A file that downstream tooling reads directly is **protected**: it carries
`protected: true` and an `edit_policy:` in its frontmatter, and the
`PROTECTED — SOURCE OF TRUTH` banner immediately under the frontmatter.

- **Regenerating a protected file counts as editing it.** Ask first.
- The guard is **advisory drift-detection, not enforcement.** It cannot stop an
  edit; it can only make an unauthorised one loud.
- `guard.paths` lists the protected globs relative to the vault root; the lock
  file records a sha256 per file. Install both in the vault — the paths file is
  written once and ships; the lock file is generated and **never hand-edited**,
  never shared between vaults.
- After an **approved** change, re-run `guard record` so the baseline stays
  current. `guard check` after an unapproved change should fail; if it does not,
  the baseline was re-recorded when it should not have been.

---

## Procedure

### Phase A — Build the source-of-record package

1. In the stream's `schedule.md`, look up the day's **verse range** and **date**.
   Derive the chapter and the output folder name from the plan's naming pattern.
2. Create the output folders if absent under both package language folders.
3. Read each verse's rail at `2-RAILS/Verses/<verse-id>.md`. For each verse, **copy
   verbatim** into the rails section every layer the package declares: root
   verse, interlinear gloss, commentary explanations (one H5 per commentator),
   stories, metaphors, scriptural quotations, main teaching points, key terms,
   synthesis. Keep the rails' own prose and their citations.
4. Build the plan-track section from that stream's plan day file, mapping the
   plan's section ids onto the package's challenge sub-blocks per
   `About <plan>.md`. End the section with a `*(Source: <plan file>)*` line
   naming the file actually used.
5. Fill the verse section and each verse's root-verse block from the stream's
   designated verse source by block ID, preserving that file's line breaks
   within each verse.
6. Add the frontmatter, the protected banner (copied verbatim from the template)
   and the day header.
7. Insert `<!-- cm:<id> -->` anchors above each commentator H5 and rewrite each
   commentator H5 to display-only (`##### <Name> (<Work>)`); do the same for
   story H5s (`<!-- story:<id> -->` + title).

### Phase B — Translate into the target package

8. Copy the source-of-record file's structure to the target path. Set
   `document_type`, `translated_from:` and the translation note the template
   declares. Take the plan-track section from the **target stream's own** plan
   day file, mapped the same way, and set `sources.plan_day_file` and the
   `*(Source: …)*` line to that file.
9. Render every rail block under Rule 2 and the termbase (Rule 3). Where a
   term-to-term mapping matters (key-terms rows, metaphor labels), keep the
   original term in parentheses.
10. Pull the verse section and each root-verse block verbatim from the **target
    stream's** designated verse source by block ID; do not translate these —
    they are already in the target language. **Preserve the source's line
    breaks** in both places.
11. Keep commentator and story headings display-only; keep the anchors from
    Phase A. Make any Divergences heading start with the word "Divergences".

### Phase C — Enforce the format

12. Reorder commentators so the declared first one leads:
    ```bash
    python3 "4-SYSTEM/Skills/plan-day-package/scripts/reorder_commentators.py" --first "<machine-id>" \
      --section-heading "<commentary heading, source stream>" \
      --section-heading "<commentary heading, target stream>" \
      "<source-of-record.md>" "<translation.md>"
    ```
13. Conform (inserts and normalises anchors, consolidates citations into one
    `Sources:` line per section; idempotent):
    ```bash
    python3 "4-SYSTEM/Skills/plan-day-package/scripts/day_package_tools.py" conform \
      --spec "<package-spec.json>" "<translation.md>"
    ```
14. Validate — must print `[PASS]` with zero `ERROR:` lines:
    ```bash
    python3 "4-SYSTEM/Skills/plan-day-package/scripts/day_package_tools.py" validate \
      --spec "<package-spec.json>" "<translation.md>"
    ```
    Fix every reported error and re-run until it passes.
15. Re-baseline the drift guard (the new files are protected):
    ```bash
    python3 "4-SYSTEM/Skills/plan-day-package/scripts/day_package_tools.py" guard record --root "<vault root>"
    python3 "4-SYSTEM/Skills/plan-day-package/scripts/day_package_tools.py" guard check  --root "<vault root>"
    ```
    Use chapter-agnostic globs in `guard.paths` so a new chapter's files are
    picked up automatically and the paths file never needs editing.

---

## Completion check

- [ ] Both files exist at the two parallel paths, named with the **absolute day
      number**, in the declared folder.
- [ ] The plan-track section comes from the correct plan day file for each
      stream, in that stream's language, and the `*(Source: …)*` line names the
      file used.
- [ ] Verse coverage in each file exactly matches the schedule's range for that
      day — no missing or extra verse blocks; each verse includes exactly the
      commentators its rail has.
- [ ] The source-of-record file's rail content is a verbatim copy of the source
      rails, with no rewording; the translation honours the five constraints and
      the termbase.
- [ ] Every commentary section lists the plan's declared first commentator
      first, where a block for it exists.
- [ ] All commentator and story headings are display-only; no machine id appears
      in any heading or in prose.
- [ ] Provenance is one `Sources:` line per leaf section; no inline `([[…]])`,
      no `![[…]]`.
- [ ] Every verse quote comes from that stream's designated verse source — in
      both the `verse_source:` frontmatter and the quoted text — and preserves
      the source's internal line breaks.
- [ ] Both files carry the protected banner and `protected: true` /
      `edit_policy:` frontmatter.
- [ ] `day_package_tools.py validate` prints `[PASS]` with zero errors.
- [ ] `guard record` then `guard check` reports OK with the new files included,
      and the re-baseline followed an approved change rather than masking an
      unapproved one.
