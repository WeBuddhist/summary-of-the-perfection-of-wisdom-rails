# Vault maintenance — policy and practice

This document sets out how maintenance is handled in a collaborative vault: what is automated, what is not, why, and what each contributor is responsible for.

---

## Core principle: audit automatically, fix deliberately

A collaborative vault with a strict citation chain is not a codebase that can be auto-formatted. Moving or renaming files breaks Obsidian wiki links across dozens of files, corrupts block ID references, and produces Git diffs that are hard for collaborators to review. An automated "cleanup" skill that restructures files is more dangerous than no maintenance at all.

The right model is borrowed from software CI: **automated auditing, human-initiated remediation.**

- A scheduled `vault-audit` skill runs weekly. It is read-only. It produces a report.
- The report flags specific, actionable problems.
- Contributors read the report and fix issues using existing targeted skills or manually.
- No skill ever restructures the vault autonomously.

---

## The vault-audit skill

The `vault-audit` skill lives at `4-SYSTEM/Skills/vault-audit/SKILL.md`. It checks six categories and writes its findings to a dated report at `0-INBOX/vault-audit-<YYYY-MM-DD>.md`.

### What it checks

**1. Skills sync**
Every folder inside `4-SYSTEM/Skills/` that contains a `SKILL.md` must have:
- A matching entry in `4-SYSTEM/Skills/SKILLS-CATALOG.md`
- A matching file at `.claude/commands/<skill-name>.md`

This is the most common drift in a collaborative vault. When a contributor adds a skill folder but forgets to register it, agents can't discover it automatically. The audit catches the gap immediately.

**2. Frontmatter completeness**
Every file in `2-RAILS/` must have the minimum frontmatter fields required for its type (verse packages, section summaries, bilingual glossaries). Every file in `3-TRANSFORMATIONS/` must have a `context_packages:` field listing the rail files it was generated from. Missing fields are flagged by file path.

**3. Citation chain integrity**
No file in `3-TRANSFORMATIONS/` should reference `1-SOURCES/` directly (the one-way chain is `1-SOURCES/ → 2-RAILS/ → 3-TRANSFORMATIONS/`). The audit scans `3-TRANSFORMATIONS/` for any wiki links or transclusions that point into `1-SOURCES/` and flags them as chain violations.

**4. Status consistency**
A file with `status: complete` must not depend on any rail file with `status: draft`. The audit walks `context_packages:` frontmatter in `3-TRANSFORMATIONS/` files, looks up the status of each cited rail, and flags any complete output that rests on an incomplete rail.

**5. Stale inbox files**
Files in `0-INBOX/temp/` older than 7 days are listed for human review. They may be safe to delete or may need to be promoted to a permanent location. The audit never deletes them — it only surfaces them.

**6. Dead wiki links**
Internal `[[...]]` links in `2-RAILS/` and `3-TRANSFORMATIONS/` that point to files that do not exist are flagged. This catches links to files that were renamed or deleted without updating references.

### What the audit does not check

- Whether content is correct, accurate, or well-cited (that requires human domain expertise)
- Whether block IDs are semantically meaningful
- Whether translations follow `requirements.md` — that is the job of `translation-qa`
- Whether files in `1-SOURCES/` are well-formed — source files are received material and should not be audited by automation

### Report format

The report is a markdown file at `0-INBOX/vault-audit-<YYYY-MM-DD>.md`. Each category gets a section. Issues are listed as checkboxes so contributors can tick them off as they resolve them. A summary line at the top states the total issue count. A clean audit produces a report with all sections marked `✓ No issues found.`

---

## Scheduling

The `vault-audit` skill is run on a weekly schedule — typically Saturday morning before the week's work begins. It runs automatically via the Cowork scheduled-tasks system and requires no human initiation.

**The schedule is audit-only.** No other skill runs on a schedule. All write operations — fixing frontmatter, syncing skill entries, resolving citation violations — are human-initiated, using the appropriate targeted skill.

If the audit is producing too many false positives (e.g. flagging deliberate exceptions), the SKILL.md should be updated to exclude those cases rather than disabling the check entirely.

---

## What is never automated

**File restructuring.** Moving, renaming, or merging files is never done by a scheduled process. It requires human judgment about link impact and Git history.

**Deleting files.** Even stale temp files are only listed — never deleted. A contributor decides what to do with each one.

**Promoting draft status to complete.** `status: complete` is set only by a domain specialist who has reviewed the content. No script or skill sets this field.

**Fixing citation chain violations.** If a `3-TRANSFORMATIONS/` file references `1-SOURCES/` directly, fixing it means understanding what rail file should sit in between — that is not a mechanical substitution.

---

## Contributor responsibilities

Each contributor is responsible for:

**When adding a skill:**
Follow the four-step checklist in `4-SYSTEM/Guidelines/skills-system.md` — folder, catalog entry, command file, and CLAUDE.md §12 table update. Do not leave the audit to catch a missing entry; register the skill as part of the same commit.

**When renaming or moving a file:**
Search for all references to the old path before the rename (`grep -r "old-filename" .`), update every link, and verify with the audit on the next run.

**When reading the audit report:**
Triage within 48 hours of the report appearing in `0-INBOX/`. Skills-sync issues should be fixed immediately — they block agent skill discovery. Citation chain violations should be fixed before any new transformations are generated from the affected files. Stale inbox files can be handled at the contributor's discretion.

**When a check produces a false positive:**
Note it in the `0-INBOX/vault-audit-<date>.md` report with a comment explaining why it is expected. If the same false positive recurs in subsequent audits, update the `vault-audit` SKILL.md to exclude it explicitly.

---

## Why not a Git hook?

A pre-commit Git hook running the skills-sync check would be more immediate than a weekly audit. The tradeoff is setup burden: every contributor must install the hook on their local machine, and the hook must work across macOS, Windows, and WSL. Given the vault's mixed contributor setup, a scheduled in-vault audit is lower friction and more reliable in practice. If the team moves to a more uniform development environment, a pre-commit hook for the skills-sync check specifically is worth revisiting.
