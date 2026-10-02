# How to sync with rails-template

This guide covers two operations:
- **Pulling updates from the template into a vault** (e.g. a new skill or CLAUDE.md improvement)
- **Backporting improvements from a vault into the template** (e.g. a generic skill that other vaults should have)

---

## What to always exclude

The following folders are vault-specific and must **never** be touched when syncing in either direction:

| Path | Reason |
|------|--------|
| `gemini-scribe/` | Vault-specific plugin state (prompts, scheduled-tasks JSON, agent sessions) |
| `4-SYSTEM/gemini-scribe/` | Vault-specific AGENTS.md and plugin sessions |
| `4-SYSTEM/Guidelines/vault-annex.md` | Vault-specific addressing scheme, commentary IDs, language tracks |
| `4-SYSTEM/Skills/<vault-specific-skills>/` | Skills that only make sense for this text (e.g. `atthakatha-summaries`, `daily-tipitaka-day`, `practice-summaries`) |
| `.claude/commands/<vault-specific-commands>.md` | Command files for vault-specific skills |
| `1-SOURCES/` | All source material is vault-specific |
| `2-RAILS/` | All rails are vault-specific |
| `3-TRANSFORMATIONS/` | All outputs are vault-specific |
| `0-INBOX/` | All inbox content is vault-specific |
| `4-SYSTEM/Pipelines/` | Pipelines belong to the vault that runs them |
| `4-SYSTEM/scripts/` | Except where a script is explicitly shared — most are vault-specific |
| `5-*/` and any numbered folder ≥ 5 | Delivery tooling and generated review bundles, outside the citation chain |
| `.claude/settings.json` | Permissions are per-contributor and per-vault |
| Any skill marked `profile: vault-local` | Specific to this text by declaration |

---

## What is safe to sync

Files that carry generic methodology and should stay in sync across all vaults:

| Path | Notes |
|------|-------|
| `4-SYSTEM/CLAUDE.md` | Apply additions; preserve vault-specific §12 table rows and annex link |
| `4-SYSTEM/Skills/SKILLS-CATALOG.md` | Apply generic sections; preserve vault-specific skill entries |
| `4-SYSTEM/Guidelines/0-VAULT-Structure.md` | Generic architecture doc |
| `4-SYSTEM/Guidelines/why-rails.md` | Generic methodology doc |
| `4-SYSTEM/Guidelines/skills-system.md` | Generic skills discovery doc |
| `4-SYSTEM/Skills/<generic-skill>/` | Any skill that works in any vault (add-toc, epub-to-markdown, verse-context, create-skill, vault-audit, etc.) |
| `.claude/commands/<generic-command>.md` | Command files for generic skills |
| `.obsidian/plugins/` | Plugin updates (main.js, manifest.json, styles.css) — not data.json |
| `4-SYSTEM/How-to guides/` | Generic how-to docs |
| `README.md` | Apply structural improvements; preserve vault-specific text |
| `4-SYSTEM/Guidelines/annotation-conventions.md` | The canonical block-ID spec — sync as a whole; record deviations in the annex instead of editing it |
| `4-SYSTEM/Guidelines/skill-locations.md` | Logical path names used by the shared skills |
| `4-SYSTEM/Guidelines/vault-variants.md` | The documented vault shapes |
| `4-SYSTEM/Guidelines/vault-maintenance.md` | The audit policy |
| `4-SYSTEM/About System.md` | Generic folder README |
| `4-SYSTEM/Templates/` | Generic file templates, including the frontmatter schema |
| `2-RAILS/Verses/_TEMPLATE.md` | The verse-package skeleton |
| `AGENTS.md` | Thin pointer to `CLAUDE.md` |

---

## When pulling from rails-template into a vault

1. Open both repos side by side.
2. For each file in the "safe to sync" list above, diff template vs vault.
3. Apply additions and structural improvements to the vault copy.
4. When updating `CLAUDE.md` or `SKILLS-CATALOG.md`: merge carefully — the vault version has vault-specific content (annex links, skill rows) that must be preserved.
5. After adding any new generic skill from the template, check that its `.claude/commands/` file is also present in the vault.
6. **Do not touch anything in the "always exclude" list.**

## When backporting from a vault into rails-template

1. Identify the change to backport: a new generic skill, a CLAUDE.md improvement, a new script, etc.
2. Check whether the change is truly generic (works in any vault) or vault-specific. If vault-specific, do not backport.
3. For generic skills: copy the skill folder, update SKILLS-CATALOG.md (generic sections only), add the `.claude/commands/` file.
4. For CLAUDE.md improvements: apply them in template-neutral language (remove vault-specific text like commentary IDs, specific skill names that only exist in the source vault).
5. **Do not touch anything in the "always exclude" list.**

---

## Syncing skills from the shared library

Most skills are not written in the template either — they come from the shared skill library, and the template carries an installed copy. That means there are two sync directions to keep straight:

```
shared skill library  →  rails-template  →  each vault
```

A fix belongs in the library. The template picks it up, and vaults pick it up from the template. Patching a vault copy directly puts the fix somewhere neither of the other two will ever see it.

When installing a skill from the library into the template or a vault:

1. Copy the whole skill folder, including its `scripts/`, `prompts/`, `templates/` and `references/`. A skill that arrives without its bundled files is broken.
2. Resolve the logical location names (`$COMMENTARIES`, `$WORK`, …) to this vault's real paths, per [`../Guidelines/skill-locations.md`](../Guidelines/skill-locations.md). Keep literal paths in anything that becomes a link or a transclusion — Obsidian does not expand the tokens.
3. Drop the library-only frontmatter keys (`supersedes:`, and `profile:` if the vault does not use profiles); keep `name:` and `description:`.
4. Register it: add the `SKILLS-CATALOG.md` entry and the `.claude/commands/<skill>.md` stub, and add a row to `CLAUDE.md` §12 if it will be used often.
5. Run `vault-audit` — its first check is exactly this registration triple.

Do not copy `__pycache__/`, `.venv/`, or any `.env` file.
