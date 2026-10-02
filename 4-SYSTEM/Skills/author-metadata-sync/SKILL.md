---
name: author-metadata-sync
description: Propagate human-curated author metadata (author, author_in_use, author_in_english) from the 16 commentary frontmatters in 1-SOURCES/ into the raw tree-guided claims files, and report every registry surface (vault annex, sources.yaml, drafted articles) that still disagrees — so a name review by a human contributor reaches the whole vault in one deterministic pass.
---

# author-metadata-sync

Whenever a human contributor reviews or changes an author's name in a commentary's frontmatter — the Tibetan `author`, the in-article address form `author_in_use` (added 2026-08-18), or the English phonetic `author_in_english` — that change must reach every place the vault repeats the name. Before this skill existed, the 2026-08-19 name review left the claims files, the vault-annex registry, `sources.yaml`, and 69 drafted articles carrying three different generations of author names, including 44 published-draft refs that still read "(མཛད་པ་པོ་མ་གསལ།)" after the author had been identified. Correct output is: claims-file frontmatter byte-identical to the source frontmatter for the three author fields, and an explicit report of every remaining mismatch elsewhere — nothing silently divergent, nothing silently overwritten.

This is a **metadata sync, never a re-extraction**: it touches only frontmatter fields and the one human-readable header line, never claim content, never `1-SOURCES/` (except that a human, not this skill, edits the source values it reads).

---

## Inputs

1. **The commentary files** — every `1-SOURCES/Commentaries/*.md` carrying a `registered_id`. Their frontmatter is the single point of truth for `author`, `author_in_use`, `author_in_english`. If a file lacks `registered_id`, stop and run `frontmatter` (Variant 2) first.
2. **The raw claims files** — `2-RAILS/Claims/raw/tree-guided/<registered-id>.md`, one per commentary (produced by `commentary-claims` (Strategy 1)).
3. **The bundled script** — `4-SYSTEM/Skills/author-metadata-sync/scripts/sync_author_metadata.py`. All frontmatter writes go through it; do not hand-edit claims frontmatter for this purpose.

## Output

- Updated frontmatter (`author`, `author_in_use`, `author_in_english`) and the `**Commentary:** \`<id>\` · <english>` header line in each `2-RAILS/Claims/raw/tree-guided/<registered-id>.md` that was out of sync.
- A console report of mismatches the script does **not** fix: the `4-SYSTEM/Guidelines/vault-annex.md` registry table, every `sources.yaml` under `4-SYSTEM/Pipelines/*/corpora/*/`, and placeholder author strings still sitting in drafted articles under `3-TRANSFORMATIONS/Wikipedia/`.

---

## Output file format

Only three frontmatter fields and one header line change in each claims file; everything else is byte-identical:

```markdown
---
registered_id: <registered-id>
title: "…"                                  (untouched)
author: "<verbatim from the source commentary frontmatter>"
author_in_use: "<verbatim from source; if source value is blank, the author value>"
author_in_english: "<verbatim from source>"
…                                            (all other fields untouched)
---

# Tree-guided claims — …                     (untouched)

**Commentary:** `<registered-id>` · <author_in_english>
…                                            (all claim content untouched)
```

---

## Rules

1. **Source frontmatter is the single point of truth.** Values are copied verbatim — never composed, never honorific-upgraded, never "improved" in passing. If a source value looks wrong, report it to the human contributor; do not fix it in `1-SOURCES/`.
2. **Blank `author_in_use` falls back to `author`.** A human contributor leaving `author_in_use` empty means "address this author by the `author` value" — the sync writes the `author` value into the claims file's `author_in_use` so downstream skills never see a blank.
3. **`author_in_english` phonetics may be authored only on explicit human instruction** (as on 2026-08-19), and are anchored to the vault-annex registry's existing English names where those exist. Once written into the source frontmatter they are human-owned like every other source field.
4. **Metadata only, never content.** The script must not alter any claim heading, བོད་ཡིག quotation, citation, Grounding-index row, or count. If a diff shows anything beyond the three fields and the header line, revert and report.
5. **Registry surfaces are reported, never auto-edited.** The vault-annex table and `sources.yaml` carry human judgment (school attributions, resolved ⚑ flags); the script only lists mismatches. Fixing them is a deliberate step in the Procedure, done with the human-readable context in view.
6. **Drafted articles are never patched by this skill**, with one exception: a *placeholder* author string (e.g. `(མཛད་པ་པོ་མ་གསལ།)`) may be replaced with the now-known author on explicit instruction, because that is a factual correction with no grammatical risk. Old-but-real name forms inside sentences are left for the article redraft (wiki-article-from-claims Rule 17) — a blind replacement breaks ergative particles.
7. **Check mode before write mode, every time.** Run the script without `--write` first and read the plan; only then run `--write`.

---

## Procedure

1. **Check mode.** Run:
   ```
   python3 4-SYSTEM/Skills/author-metadata-sync/scripts/sync_author_metadata.py
   ```
   Read the three report sections: planned claims-file edits, registry mismatches, article placeholders. If a source file is reported as missing `author` or `registered_id`, stop and fix that first (via `frontmatter` (Variant 2) / the human contributor).
2. **Write mode.** Re-run with `--write`. Confirm the console lists only `author` / `author_in_use` / `author_in_english` / header-line edits.
3. **Verify.** Re-run check mode: the claims-sync section must report "all claims files already in sync".
4. **Registry pass (manual, per Rule 5).** For each reported mismatch: update the author column of the `4-SYSTEM/Guidelines/vault-annex.md` §Commentaries table and the `author:` values in the affected `sources.yaml`, keeping any ⚑ flags accurate (resolve or annotate them; never delete an open flag silently).
5. **Placeholder pass (only if instructed, per Rule 6).** Replace placeholder author strings in drafted articles with the source `author` value, formatted per the wikitext spec's ref form (`<AUTHOR>། <TITLE>།`). Log which files were touched.
6. **Report.** Summarise: files synced, registry rows fixed, placeholders replaced, and anything still open for the human contributor.

---

## Completion check

- [ ] Script run in check mode, then `--write`, then check mode again reporting a clean sync
- [ ] Every claims-file diff limited to the three author fields + the header line — no claim content touched
- [ ] Blank source `author_in_use` values propagated as the `author` value, not as blanks
- [ ] Registry mismatches either fixed (annex table, sources.yaml) or explicitly listed as open in the report
- [ ] No edit to `1-SOURCES/` by this skill; source values reported, never changed
- [ ] Article sentences with old-but-real names left untouched (redraft's job); only instructed placeholder replacements made, and logged
