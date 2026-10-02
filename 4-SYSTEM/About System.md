# 4-SYSTEM — Methodology and tooling

This folder holds everything the vault needs to *operate*: the guidelines that define the methodology, the skills that automate every workflow step, the how-to guides for contributors, the templates for new files, and the LLM-facing operational instructions.

Nothing here is project content. Project content lives in `1-SOURCES/`, `2-RAILS/`, and `3-TRANSFORMATIONS/`. This folder is the *operating system* of the vault: read the guidelines to understand the rules, invoke the skills to do the work, follow the how-to guides for hand operations.

---

## What's here

- **[`CLAUDE.md`](CLAUDE.md)** — operational instructions for an AI agent: the skills-first gate, the protected-file policy, the citation chain, write permissions, block-ID rules, and the standard operations. The first thing any agent reads when it picks up work in this vault.
- **[`Guidelines/`](Guidelines/)** — the rules. Text-agnostic except for the annex.
  - [`why-rails.md`](Guidelines/why-rails.md) — why the methodology works: the specialist-pair and Wikipedia analogies.
  - [`0-VAULT-Structure.md`](Guidelines/0-VAULT-Structure.md) — top-level architecture, the citation chain, the status lifecycle, and the new-vault setup checklist.
  - [`annotation-conventions.md`](Guidelines/annotation-conventions.md) — **the canonical block-ID and tag specification.** When any other document disagrees with it, it wins.
  - [`skill-locations.md`](Guidelines/skill-locations.md) — what `$COMMENTARIES`, `$WORK`, `$SECTIONS` and the other logical names in a shared skill resolve to here.
  - [`skills-system.md`](Guidelines/skills-system.md) — how skills are discovered, executed, created and registered.
  - [`vault-maintenance.md`](Guidelines/vault-maintenance.md) — the policy behind the weekly `vault-audit`: audit automatically, fix deliberately.
  - [`vault-variants.md`](Guidelines/vault-variants.md) — how the methodology adapts to a collection of short texts, a multi-book canon, or a parallel-witness corpus.
  - [`vault-annex.md`](Guidelines/vault-annex.md) — the conventions specific to *this* vault: addressing scheme, commentary roster, language tracks, registered deviations. **This is the only file in `Guidelines/` that is text-specific.**
- **[`Skills/`](Skills/)** — the operators. One folder per skill, each with a `SKILL.md` and optional bundled scripts, prompts, templates and references. See [`SKILLS-CATALOG.md`](Skills/SKILLS-CATALOG.md) for the full list grouped by pipeline phase.
- **[`Templates/`](Templates/)** — blank templates for new files: the audience profile, the upload-facing frontmatter schema, and the rails templates.
- **[`How-to guides/`](How-to%20guides/)** — human-facing instructions for tasks that are not skills: vault setup, sync and troubleshooting, syncing with the template, the GitHub project board.
- **`scripts/`** — standalone scripts that are not bundled inside a single skill. Vendored third-party code records its upstream in an `UPSTREAM.md` beside it.
- **`Pipelines/`** *(optional)* — multi-stage programs with their own code, gates and CLI. Installed and run, not invoked as skills; each carries its own `CLAUDE.md` and `STATE.md`.
- **`gemini-scribe/`** — configuration for the Gemini Scribe plugin (`AGENTS.md`, `Prompts/`, `Scheduled-Tasks/`, `Background-Tasks/`, `Agent-Sessions/`, `Skills/`).

---

## Write permissions inside this folder

`4-SYSTEM/` is **mostly read-only for the LLM**. The exception is tooling: an agent may create and edit skills (`Skills/<skill>/`) and standalone scripts (`scripts/`) when asked to build or improve tooling, and must update `Skills/SKILLS-CATALOG.md` and `.claude/commands/` to match. The rules themselves — `CLAUDE.md`, the `Guidelines/`, the folder `About` files, the templates — change only by human contributor action.

See [`CLAUDE.md`](CLAUDE.md) §2 for the full permission table.

---

## Generated reports do not live here

Audit reports, diff reports and run summaries go to `0-INBOX/` (for example `0-INBOX/vault-audit-<YYYY-MM-DD>.md`), never into `4-SYSTEM/`. This folder holds rules and tools, not output.

---

## Reading order

The canonical reading orders live in the top-level [`README.md`](../README.md) — one path for human contributors, one for AI agents. This folder slots into both. Don't read it in isolation; start at the README.
