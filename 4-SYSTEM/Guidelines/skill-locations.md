# Skill locations — what `$NAME` means in this vault

The skills in `4-SYSTEM/Skills/` come from a shared library used by several
vaults and by the library-ingest pipeline. They refer to their inputs and
outputs by **logical location** — `$COMMENTARIES/<id>.md`, `$WORK/`,
`$SECTIONS` — rather than by hard-coded path. That indirection is what lets one
copy of a skill serve every vault instead of one fork per vault.

This file resolves those names for **this** vault.

## How a skill uses this

A skill says:

> Read `$COMMENTARIES/<commentary-id>.md`, write to `$WORK/`.

You resolve each `$NAME` from the table below.

## The `rails-vault` profile — this vault

Material flows strictly left to right through the five stages; a later stage
never writes back into an earlier one.

| Logical name | Path | Holds |
|---|---|---|
| `$INBOX` | `0-INBOX/` | Unprocessed arrivals; scratch |
| `$WORK` | `0-INBOX/temp/` | Intermediate drafts |
| `$SOURCES` | `1-SOURCES/` | All human-produced source material (the folder that contains the rows below) |
| `$SOURCE_TEXTS` | `1-SOURCES/Text/` | Root texts (canonical, citable) |
| `$COMMENTARIES` | `1-SOURCES/Commentaries/` | Commentaries |
| `$TRANSLATIONS` | `1-SOURCES/Translations/` | Existing human translations |
| `$REFERENCES` | `1-SOURCES/References/` | Secondary literature |
| `$RAILS` | `2-RAILS/` | Derived, reusable structure |
| `$SECTIONS` | `2-RAILS/Sections/` | Per-TOC-node summaries |
| `$SECTIONS_RAW` | `2-RAILS/Sections/Raw/<commentary>/` | Per-commentary raw summaries |
| `$VERSES` | `2-RAILS/Verses/` | Per-verse context packages |
| `$GLOSSARIES` | `2-RAILS/Bilingual-Glossaries/` | Consolidated glossaries |
| `$GLOSSARIES_RAW` | `2-RAILS/Bilingual-Glossaries/Raw/` | Per-source raw glossaries |
| `$LOCAL_WIKI` | `2-RAILS/Local-Wiki/` | Per-term wiki articles |
| `$KEYWORDS` | `2-RAILS/Keywords/` | Descriptive graded keyword inventories (source-term registry, frequency matrix, ranked article queue) |
| `$CLAIMS` | `2-RAILS/Claims/` | Extracted + consolidated claims |
| `$TERMBASES` | `2-RAILS/termbases/` | Locked terminology |
| `$TRANSFORMATIONS` | `3-TRANSFORMATIONS/` | Audience-facing outputs |
| `$SYSTEM` | `4-SYSTEM/` | Skills, scripts, docs |
| `$SKILLS` | `4-SYSTEM/Skills/` | The installed skill folders (`$SKILLS/<skill-name>/`) |
| `$SKILL` | `4-SYSTEM/Skills/<this-skill>/` | The folder of the skill currently being executed — its own `scripts/`, `prompts/`, `templates/`, `references/` |

**Not every vault has every folder.** Liturgy-rails has no `Commentaries/`,
`Claims/` and `Keywords/` exist only in vaults that run the claims / keyword
pipelines, `termbases/` is BCA-only. A skill whose input
folder does not exist in the current vault should say so and stop, not invent
a location.

**Permission rule.** `1-SOURCES/` is the citation floor. The only edits
permitted to a source file are structural: block boundaries, block IDs,
navigation links, and factual `[Ed: …]` notes. Rewording, glossing or "fixing"
the text is interpretation and is forbidden — that belongs downstream in
`2-RAILS/` or `3-TRANSFORMATIONS/`.

---


## Two notes on using these names

- **`$NAME` tokens are for a skill's prose, never for a link inside a vault file.** A wiki link or transclusion must carry the resolved literal path (`![[1-SOURCES/Text/...#^1-1]]`), because Obsidian does not expand these tokens. Resolve the name before you write the link.
- **A skill whose input folder does not exist here should say so and stop**, not invent a location. The optional folders (`Claims/`, `Keywords/`, `Termbases/`) exist only in vaults running those pipelines.

## Where to look next

- [`annotation-conventions.md`](annotation-conventions.md) — the block-ID and tag conventions every skill implements.
- [`skills-system.md`](skills-system.md) — how skills are discovered, run, created and registered.
- [`0-VAULT-Structure.md`](0-VAULT-Structure.md) — what each folder is for.
