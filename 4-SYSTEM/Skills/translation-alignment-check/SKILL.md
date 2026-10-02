---
name: translation-alignment-check
description: >
  Report-only structural check that every translation of a text mirrors its root
  exactly — same segment references in the same order, same line count per segment,
  same segment types, same heading ids and levels, the same table-of-contents tree,
  a transclusion pointing at the same id above every block, and no numeral or
  heading text leaking into content. With --payloads it also checks that the
  parser's edition / toc / alignment JSON say the same thing; with --live, that the
  published root edition still matches the root file.

  Trigger this skill whenever the user wants to know whether a translation still
  lines up with its source: "check the alignment", "is the translation still in
  sync", "did the re-cut break anything", "verify before upload", "the block ids
  don't match", "why is the translation off by one". Run it before any upload and
  after any re-segmentation, re-translation or heading change.
---

# translation-alignment-check

One deterministic script, no model calls: `4-SYSTEM/Skills/translation-alignment-check/scripts/check_translation_alignment.py`. It reads the root file and every translation with the **same parser the uploader uses** (`4-SYSTEM/Skills/translation-alignment-check/scripts/parser-root-text/parser.py`), so what it compares is exactly what would be published, and prints one table plus every failed check with the offending ids. Exit status 0 means every translation mirrors the root.

The check exists because block-ID alignment is **identity, not similarity**: block `^7` of a translation renders block `^7` of the root, and nothing reconciles them if they drift. A single renamed or dropped id silently misaligns every pair after it, and the failure is invisible in both files read on their own — you only see it when the two are read side by side, which is what this script does.

## What it proves, per translation, against the root

| Check | Why it matters |
|---|---|
| Segment references identical, in order | The alignment is identity by block id; one missing or renamed id breaks every later pair |
| Line count per segment identical | The display is line-parallel; a 5-line stanza rendered in 4 lines misaligns the reader's eye |
| Segment types identical (front matter, verse, back matter) | The types are derived from the ids, so a mismatch means the id scheme has drifted |
| Headings identical in level and id, and the same TOC tree | The translation's table of contents must nest exactly like the root's, whatever the titles say |
| No heading title inside content, no `#` in content | Headings are structure, never text — a stray copy in the body would be published as content |
| No heading title starting with a numeral | An editorial `1.` in the root's heading is an artefact of the source; translations drop it |
| A transclusion above every block pointing at the same id | That is where the alignment is read from |
| No untranslated placeholder; `file_type: translation`; `root_text` names the root | Upload preconditions |

With `--payloads`, for each file's `<stem>.edition.json` / `.toc.json` / `.alignment.json` under the parser's output directory: references equal the file's own, content equals the file's parse and carries no `#` and no heading title, spans are contiguous and cover the whole content, the table of contents has one root section whose subsections are contiguous and carry the file's heading titles in the file's language, and the alignment is identity over every segment.

With `--live`, the root file is compared against what is already published (GET only): the live root edition's segment references and its TOC subsection count.

---

## Inputs

| Input | Description | Required |
|---|---|---|
| Root file | `--root <path>` — the root text every translation is checked against | yes |
| Translation files | Positional paths. Default: every block-aligned translation under `3-TRANSFORMATIONS/Translations/` whose stem derives from the root's | no |
| `--payloads` | Also check the parser outputs. Run the `translation-upload` dry run first so they exist | no |
| `--live` | Compare against the published edition. Needs the API credentials in the environment | no |

**Credentials.** The `--live` mode reads its key from the environment. Keep it in a git-ignored `4-SYSTEM/scripts/.env` and source that file before running; never pass a key on the command line, and never commit one.

## Output

A report on stdout only. **Nothing is written or modified** — not the files, not the payloads, not the ledger.

---

## Rules

1. **Report-only.** The script writes nothing. If it did, a failing check could hide itself.
2. **The root is the reference.** The published edition is checked against the root file, never the other way round.
3. **A translation that fails is not uploaded** until it passes.
4. **Fix a failure at its source** — re-render the translation, or correct the root — never by hand-editing a payload. A payload is generated; editing it fixes the symptom for exactly one run and leaves the cause in place.

---

## Procedure

```bash
# 1. Files only.
python3 4-SYSTEM/Skills/translation-alignment-check/scripts/check_translation_alignment.py --root <root file>

# 2. After the dry-run upload has written the payloads.
python3 4-SYSTEM/Skills/translation-alignment-check/scripts/check_translation_alignment.py --root <root file> --payloads

# 3. Before executing a real upload, with credentials loaded.
set -a; source 4-SYSTEM/scripts/.env; set +a
python3 4-SYSTEM/Skills/translation-alignment-check/scripts/check_translation_alignment.py --root <root file> --payloads --live
```

Read every failure line back to the user **with the ids it names** — the ids are the whole value of the report; a summary that says "3 failures" and drops them wastes the run.

---

## Completion check

- [ ] Ran on every translation that is about to be uploaded, with `--payloads`
- [ ] Either the run reported success, or every failure was reported with its ids and fixed at the source
- [ ] `--live` run once before any execute
- [ ] Nothing was written by this skill
