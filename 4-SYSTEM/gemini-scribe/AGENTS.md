# AGENTS.md — Gemini Scribe

This file provides context about the vault for AI agents invoked through the Gemini Scribe plugin. Full operational instructions live in [`../CLAUDE.md`](../CLAUDE.md) — read that first.

---

## What this vault is

This is a **Railroads vault** — a method for making AI-powered work on a classical text reliable, traceable, and consistent at scale. It serves **[name of text]**.

The vault uses a four-stage pipeline:

```
0-INBOX/          scratch / not authoritative
1-SOURCES/        human-produced ground truth (read-only)
2-RAILS/          original-language descriptive context (primary work area)
3-TRANSFORMATIONS/ AI-generated outputs (three categories)
4-SYSTEM/         guidelines, skills, templates (read-only)
```

---

## Key topics covered in this vault

[Fill in the key topics, traditions, and languages relevant to your text. Example:]

- [Source language] classical literature and commentary tradition
- Classical commentaries and sub-commentaries
- [Target language(s)] translation and adaptation
- Multilingual glossary work

---

## Working rules

- **Check the catalog first.** Read `4-SYSTEM/Skills/SKILLS-CATALOG.md` before starting any task and follow the matching `SKILL.md` exactly. A task done without its skill must be redone.
- **Prefer the vault's own terminology.** Take definitions and renderings from `2-RAILS/Local-Wiki/` and `2-RAILS/Bilingual-Glossaries/` before general knowledge or a web search. That is what those files are for.
- **Draft in `0-INBOX/`** when you are unsure where something belongs; move it out once it is formatted and verified.

## Do not do these things

- Do not write to `1-SOURCES/` (except adding block IDs and frontmatter via skills).
- Do not write to `4-SYSTEM/` — the one exception is skills and scripts, when explicitly asked to build tooling.
- Do not edit or regenerate a file marked `PROTECTED — SOURCE OF TRUTH` without explicit human confirmation.
- Do not introduce parametric knowledge — every claim must cite a `1-SOURCES/` file.
- Do not mark your own output `status: complete` — domain specialists do that.
- Preserve all diacritics and non-ASCII characters exactly as given.

---

## Reading paths

For a specific task, read:

1. [`../CLAUDE.md`](../CLAUDE.md) — operational instructions.
2. The `About <Folder>.md` in the folder you're working in.
3. [`../Guidelines/vault-annex.md`](../Guidelines/vault-annex.md) — vault-specific conventions.
4. `../Skills/<skill>/SKILL.md` — the skill for the specific workflow you're running.

---

## Example prompts

```json
[
  "Summarise the commentary's interpretation of verse [verse-id] for the verse-context package.",
  "Draft a translation of [verse-id] using the [track-name] termbase.",
  "Check the verse package at 2-RAILS/Verses/[verse-id].md against the citation-chain rules.",
  "List all terms in verse [verse-id] that need Local-Wiki articles."
]
```
