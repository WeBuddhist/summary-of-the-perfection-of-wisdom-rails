# Linter — Root Text

Checks a vault source file (`.md`) against the API schemas and writes a JSON payload ready to submit to the API.

Use it for root texts, editions and translations. Commentaries have their own linter (`linter-commentary`).

## What it does

1. Reads the YAML frontmatter and body of the file
2. For `file_type: translation`, follows `root_text` to the file being translated and, in the output payload:
   - sets `translation_of` from that file's `text_id` (warning if it has none)
   - copies its `category_id` when the translation has none
3. Validates the text metadata (see [Rules](#rules))
4. For `file_type` `root-text`, `edition` or `translation`, also validates the edition body and the table of contents. Other file types get the metadata check only
5. Adds each author/translator that has a `[bdrc:ID]` or `[op:ID]` tag to `contributions`. Names are never looked up: anyone without an id is left out with a warning
6. Writes `output/<stem>.lint.json` on success, or `output/<stem>.lint.errors.json` on failure
7. Patches the source file's frontmatter in place: `language` (code → name) and `lang_tag` (set from `language`)

> The linter edits the source file (step 7). Run it on a copy, or commit first, if the file must not change.

## Rules

### Text metadata

| Field | Rule |
|-------|------|
| `title` | Required. A string, or an object of `{lang: title}` |
| `alt_titles` | Optional (warning if missing). A string or a list of strings, in the same language as the file |
| `language` | Required: a language code or name known to the API. If missing, it is inferred from a valid `lang_tag` |
| `lang_tag` | If set, must be a known language code |
| `category_id` | Required |
| `license` | Required. One of `cc0`, `public`, `cc-by`, `cc-by-sa`, `cc-by-nd`, `cc-by-nc`, `cc-by-nc-sa`, `cc-by-nc-nd`, `copyrighted`, `unknown` |
| `root_text` | Required when `file_type: translation` |
| `author` / `translator` | Optional (warning if both missing). See [Contributors](#contributors) |
| `bdrc_work_id` (or `bdrc`) | Optional. Passed through as `bdrc`; never looked up by title |
| `wiki`, `date`, `commentary_of`, `translation_of` | Optional strings |
| `tag_ids` | Optional list of strings |

Pali (`pi`) titles must be in Roman script; see [Titles](#titles).

### Edition

- `source` or `source_url` is required and must be an `http://` or `https://` URL
- `lang_tag` or `language` is required
- `edition_type`, if set, must be `diplomatic`, `critical` or `collated`; anything other than `critical` gives a warning
- The body must not be empty
- Blocks are separated by blank lines. Every block must end with a block ID (`^ref`), except blocks that contain only transclusions (`![[...#^ref]]`), which are skipped
- Heading IDs may have any number of parts (`^n-n-n-…`); content IDs may have at most 3 (`^n-n-n`)
- Block IDs must be unique (headings and content are checked separately)

### Table of contents

- The file must have at least one heading
- The first heading must be level 1 (`#`)
- Every heading must end with a block ID
- Heading levels must not skip (e.g. `###` directly after `#`)

### Contributors

`author` and `translator` may list several names separated by `,` or `;`. Each name needs an id tag to be included:

| Value | Result |
|-------|--------|
| `Name [bdrc:P1234]` | person with that BDRC id |
| `Name [op:ID]` | person with that API id |
| `[op:ID]` (no name) or `rails` | AI contributor |
| `[FILL ...]` | ignored |
| `Name` (no id) | skipped, with the warning `no BDRC or OP id provided` |

The `… in English` / `…_in_english` variants of these fields take priority when set.

### Titles

`title` and `alt_titles` are keyed by the text's own language code (`lang_tag`, or `language` if `lang_tag` is not set), with no script suffix, and kept in the script they are written in:

```yaml
lang_tag: sa
title: बोधिचर्यावतार
alt_titles:
  - bodhicaryāvatāra
```

→ `title: {"sa": "बोधिचर्यावतार"}`, `alt_titles: [{"sa": "bodhicaryāvatāra"}]`, `language: "sa"`

- **Exception — Pali:** titles are still keyed `pi`, but must be written in Roman script (e.g. IAST: `Dhammasaṅgaṇī`). Any non-Latin letter (Sinhala, Thai, Burmese, Devanagari, …) is an error
- `title_in_english` (or `title in English`) is added under `en`
- Titles given as a `{lang: title}` object are kept, but script-suffixed keys are reduced to the language code (`sa-x-iast` → `sa`, `pi-x-iast` → `pi`)
- Tibetan titles written in Wylie (e.g. `kun dpal spyod 'jug`) are converted to Unicode (needs `pyewts`)

## Output

```
output/
  <stem>.lint.json          # success: text_input payload, notes, warnings
  <stem>.lint.errors.json   # failure: errors, notes, warnings, resolved payload
```

The `text_input` block is what gets submitted to the API to create the text.

## Files

| File | Role |
|------|------|
| `lint_text_input.py` | Entry point — reads the file, runs validation, writes output, patches the source |
| `build.py` | Builds the `text_input` payload |
| `validate.py` | Validation rules |
| `lookup.py` | Person lookups via the persons API / BDRC — no longer used |
| `constants.py` | API endpoints, allowed values, field lists |
| `languages.py` | Language codes/names, refreshed from the API on each run |
| `requirements.txt` | Python dependencies |

## Requirements

```
pip install -r requirements.txt
```

Python 3.8+. Network access is only used to refresh the language list; without it the linter uses the saved `languages.py`.

## How to run

Run from the vault root (the folder that contains `1-SOURCES/` and `4-SYSTEM/`). Several files can be passed at once:

```bash
python3 4-SYSTEM\scripts\linter-root-text\lint_text_input.py "1-SOURCES\Text\<lang>-<title>.md"
```

Then run `parser-root-text` on the file and its `.lint.json`.

## Source file format

See `4-SYSTEM/Templates/FILE_YAML_PROPERTIES.md` for the YAML properties of each file type.

## Notes

- The source file's `title` is never overwritten
- Set `text_id` on the root text before linting its translations, otherwise `translation_of` stays empty
- After the text, edition and TOC are created in the API, save the returned ids back to the source file as `text_id`, `edition_id` and `toc_id`
