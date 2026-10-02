---
name: vault-audit
description: Read-only weekly audit of vault integrity. Eight checks: skill registration and frontmatter, rail and output frontmatter completeness, citation-chain integrity, status consistency, stale inbox files, dead wiki links, file placement, and unfilled template placeholders. Writes a dated report to 0-INBOX/. Never modifies vault files.
---

# vault-audit

This skill audits the vault for mechanical integrity issues that accumulate in collaborative work. It is **read-only**: it produces a report and nothing else. All remediation is human-initiated using existing targeted skills.

Run this skill on a weekly schedule or any time after a batch of collaborative changes. Do not run it as part of a transformation workflow — it is a maintenance tool, not a pipeline step.

---

## Inputs

None. The skill operates on the vault as a whole.

## Output

One report file at:

```
0-INBOX/vault-audit-<YYYY-MM-DD>.md
```

Where `<YYYY-MM-DD>` is today's date. If a report already exists for today, append a `-2` suffix rather than overwriting.

---

## Output file format

```markdown
---
audit_date: <YYYY-MM-DD>
total_issues: <N>
---

# Vault audit — <YYYY-MM-DD>

**<N> issue(s) found.** / **No issues found.**

---

## 1. Skills sync

<✓ No issues found.>
<OR list of issues as checkboxes — see Check 1 below>

## 2. Frontmatter completeness

<✓ No issues found.>
<OR list of issues>

## 3. Citation chain integrity

<✓ No issues found.>
<OR list of issues>

## 4. Status consistency

<✓ No issues found.>
<OR list of issues>

## 5. Stale inbox files

<✓ No files older than 7 days in 0-INBOX/.>
<OR list of files with their modification dates>

## 6. Dead wiki links

<✓ No issues found.>
<OR list of issues>

## 7. File placement

<✓ No issues found.>
<OR list of issues>

## 8. Unfilled template placeholders

<✓ No issues found.>
<OR list of files still carrying [text-slug] / [name of text]>
```

---

## Rules

1. **Never write to any file other than the report.** This skill is read-only. Do not fix issues, do not update frontmatter, do not modify SKILLS-CATALOG.md or command files.
2. **Report every issue found, even if many.** Do not truncate or summarise away specific file paths — contributors need exact locations to act on.
3. **Use checkboxes for every issue** so contributors can tick items off as they resolve them.
4. **A clean audit is a valid output.** If no issues are found in a category, write `✓ No issues found.` in that section. Do not omit sections.
5. **Do not flag 4-SYSTEM/Skills/ subfolders that lack a SKILL.md** — those may be support-file-only folders (e.g. `converters/`). Only flag folders that contain a `SKILL.md` but are missing a catalog entry or command file.
6. **Do not flag 3-TRANSFORMATIONS/ About *.md files for missing context_packages:** — those are documentation files, not generated outputs.

---

## Procedure

### Check 1 — Skills sync

1. List every immediate subdirectory of `4-SYSTEM/Skills/` that contains a `SKILL.md`.
2. For each such directory `<skill-name>`:
   a. Check whether `4-SYSTEM/Skills/SKILLS-CATALOG.md` contains a section heading `### \`<skill-name>\``.
   b. Check whether the skill is registered for slash-command discovery by **either** mechanism: a stub at `.claude/commands/<skill-name>.md`, **or** a native skill at `.claude/skills/<skill-name>/SKILL.md`. Either satisfies this check; neither is a failure.
   c. Check whether `4-SYSTEM/Skills/<skill-name>/SKILL.md` opens with YAML frontmatter carrying at least `name:` and `description:`. Without it the skill cannot be discovered or triggered automatically, however good it is.
3. Flag each missing entry as a checkbox item:
   - `- [ ] \`<skill-name>\`: missing from SKILLS-CATALOG.md`
   - `- [ ] \`<skill-name>\`: not registered — add .claude/commands/<skill-name>.md or .claude/skills/<skill-name>/`
   - `- [ ] \`<skill-name>\`: SKILL.md has no \`name:\`/\`description:\` frontmatter — it cannot be discovered`
4. Also check the reverse: for every entry in SKILLS-CATALOG.md marked `[exists]`, verify a corresponding `4-SYSTEM/Skills/<skill-name>/SKILL.md` actually exists. Flag any catalog entry pointing to a nonexistent skill folder.

### Check 2 — Frontmatter completeness

Scan every `.md` file in `2-RAILS/` and `3-TRANSFORMATIONS/` (excluding `About *.md` files).

For files in `2-RAILS/Verses/`, the minimum required frontmatter fields are:
`verse_id`, `root_text`, `root_block`, `language`, `commentaries`, `status`

For files in `2-RAILS/Bilingual-Glossaries/` (non-Raw), required fields are:
`language_pair`, `source_language`, `target_language`, `raw_sources`, `status`

For files in `3-TRANSFORMATIONS/` that are not `About`, `requirements`, `termbase`, `audience`, `schedule`, or `qa-report` files, the required field is:
`context_packages`

Flag each file with a missing required field:
- `- [ ] \`<path>\`: missing frontmatter field(s): <field1>, <field2>`

### Check 3 — Citation chain integrity

Scan all `.md` files in `3-TRANSFORMATIONS/` for any occurrence of:
- `[[1-SOURCES/` (wiki link into 1-SOURCES)
- `![[1-SOURCES/` (transclusion into 1-SOURCES)

Exclude `About *.md` documentation files. Flag each violation:
- `- [ ] \`<path>\`: direct reference to 1-SOURCES/ bypasses 2-RAILS/ — line <N>: \`<offending link>\``

### Check 4 — Status consistency

For every file in `3-TRANSFORMATIONS/` (excluding About, requirements, termbase, audience, schedule, qa-report) that has `status: complete` in its frontmatter:
1. Read its `context_packages:` list.
2. For each listed rail file, read its frontmatter `status` field.
3. If any rail has `status: draft`, flag the transformation:
   - `- [ ] \`<transformation-path>\`: status: complete but depends on draft rail \`<rail-path>\``

### Check 5 — Stale inbox files

List every file in `0-INBOX/` (including `0-INBOX/temp/`) with a modification date older than 7 days. For each:
- `- [ ] \`0-INBOX/<filename>\` — last modified <date>. Review: promote to permanent location or delete.`

Do not flag files in `0-INBOX/raw-data/` — those are intentionally long-lived staging inputs.

### Check 6 — Dead wiki links

Scan all `.md` files in `2-RAILS/` and `3-TRANSFORMATIONS/` for internal wiki links matching `[[...]]` and `![[...]]`. For each link:
1. Extract the target file path (strip any `#^block-id` anchor).
2. Resolve the path relative to the vault root.
3. Check whether the target file exists.
4. Flag missing targets:
   - `- [ ] \`<source-path>\`: dead link → \`<target-path>\` (line <N>)`

Skip links to external URLs (`http://`, `https://`). Skip links into `4-SYSTEM/` — documentation cross-links are not production dependencies.

### Check 7 — File placement

This check catches two classes of structural error: files placed in the wrong rail folder, and transformation verse files whose corresponding rail does not yet exist.

**7a — Misplaced files in `2-RAILS/Verses/`**

Per CLAUDE.md §4, every file in `2-RAILS/Verses/` must be named with the verse-ID pattern: `<chapter>-<verse>.md` (e.g. `1-1.md`, `6-33.md`). Ignore `.gitkeep`.

For every file in `2-RAILS/Verses/` whose name does not match `^\d+-\d+\.md`:
- `- [ ] \`2-RAILS/Verses/<filename>\`: misplaced file — does not follow verse-ID naming convention (\`<chapter>-<verse>.md\`). Review: move to \`2-RAILS/Sections/\` or correct the filename.`

**7b — Missing verse rails for existing transformations**

Collect the set of unique filenames under any `3-TRANSFORMATIONS/*/Verses/` directory (e.g. `1-1.md`, `6-33.md`). For each filename that does not have a corresponding file at `2-RAILS/Verses/<filename>`:
- `- [ ] \`2-RAILS/Verses/<filename>\`: verse rail missing — transformation(s) exist but no rail has been authored. Do not generate further transformations from this verse until the rail is complete.`

### Check 8 — Unfilled template placeholders

A vault created from the template carries placeholders that must be replaced before the vault means anything. They are easy to leave behind, because nothing breaks when they stay.

Search the vault README, `4-SYSTEM/CLAUDE.md`, the vault annex (whatever it is named) and any agent-instruction file for the literal strings `[text-slug]`, `[name of text]`, and `> **Using this template:**`.

For each file that still contains one:
- `- [ ] \`<path>\`: still contains template placeholder \`<placeholder>\` — fill in or delete before the vault is used.`

Report `✓ No issues found.` once every placeholder is gone.

### Write the report

1. Collect all flagged issues across all eight checks.
2. Set `total_issues:` in the frontmatter to the total count of checkbox items.
3. Write the report to `0-INBOX/vault-audit-<YYYY-MM-DD>.md`.
4. Do not write or modify any other file.

---

## Completion check

- [ ] All eight checks have been executed
- [ ] Every flagged issue includes the exact file path and line number where applicable
- [ ] Every section has either a list of checkbox items or `✓ No issues found.`
- [ ] `total_issues:` frontmatter field reflects the correct count
- [ ] No file other than the report was written or modified
