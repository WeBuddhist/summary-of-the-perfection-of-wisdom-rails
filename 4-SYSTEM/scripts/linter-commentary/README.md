# Linter — Commentary

Checks a vault commentary file (`.md`) against the API schemas and writes a JSON payload ready to submit to the API.

Forked from `linter-root-text`. The differences: the file must be `file_type: commentary`, it must link to the text it comments on through `root_text`, and **`commentary_of`** is filled in from that text.

## What it does

1. Reads the YAML frontmatter and body of the file; stops if `file_type` is set to anything other than `commentary`
2. Follows `root_text` to the text being commented on (a root text or a translation) and:
   - sets `commentary_of` from that file's `text_id`, if not already set (warning if it has none)
   - copies its `category_id` when the commentary has none
3. Validates the text metadata, the edition body and the table of contents (see [Rules](#rules))
4. Adds each author that has a `[bdrc:ID]` or `[op:ID]` tag to `contributions`. Names are never looked up: anyone without an id is left out with a warning
5. Writes `output/<stem>.lint.json` on success, or `output/<stem>.lint.errors.json` on failure
6. Patches the source file's frontmatter in place: `language` (code → name), `lang_tag` (set from `language`), and `commentary_of` / `category_id` when they were filled in and are missing from the file

> The linter edits the source file (step 6). Run it on a copy, or commit first, if the file must not change.

## Rules

Same as `linter-root-text` (see its README), with these changes. That includes the title rules: titles are keyed by the text's language code and kept in their own script, except Pali, which must be in Roman script (still keyed `pi`), and every language key in `title` / `alt_titles` must be a code from the language API (`bod`, `english` and the like are errors).

| Field | Rule |
|-------|------|
| `file_type` | Required; must be `commentary` |
| `root_text` | Required |
| `commentary_of` | Warning if it can't be set (the linked text has no `text_id`) |

Footnote markers (`[^n]`) and definition lines (`[^n]: …`) are removed before validation, so a footnote definition needs no block ID (see the parser README).

Edition and TOC rules are the same: `source` or `source_url` (an http/https URL) is required, every block needs a block ID, content IDs have at most 3 parts, IDs are unique, the first heading is `#`, and heading levels don't skip.

## Output

```
output/
  <stem>.lint.json          # success: text_input payload (with commentary_of)
  <stem>.lint.errors.json   # failure: errors, notes, warnings, resolved payload
```

## Files

| File | Role |
|------|------|
| `lint_text_input.py` | Entry point — resolves `root_text`, runs validation, writes output, patches the source |
| `build.py` | Builds the `text_input` payload |
| `validate.py` | Validation rules (commentary-specific) |
| `lookup.py` | Person lookups via the persons API / BDRC — no longer used |
| `constants.py` | API endpoints, allowed values, field lists |
| `languages.py` | Language codes/names, refreshed from the API on each run |
| `requirements.txt` | Python dependencies |

## Requirements

```
pip install -r requirements.txt
```

Python 3.8+. Network access is only used to refresh the language list.

## How to run

Run from the vault root (the folder that contains `1-SOURCES/` and `4-SYSTEM/`):

```bash
python3 4-SYSTEM\scripts\linter-commentary\lint_text_input.py "1-SOURCES\Commentaries\<lang>-<title>.md"
```

Then parse:

```bash
python3 4-SYSTEM\scripts\parser-commentary\parser.py "1-SOURCES\Commentaries\<lang>-<title>.md" "4-SYSTEM\scripts\linter-commentary\output\<lang>-<title>.lint.json"
```

## Source file format

See `4-SYSTEM/Templates/FILE_YAML_PROPERTIES.md` §3 (Commentary).

Minimum linkage:

```yaml
file_type: commentary
root_text: 1-SOURCES/Text/<lang>-<title>.md
# commentary_of: <filled in from the root text's text_id>
# category_id: <copied from the root text if missing>
```

## Notes

- Set `text_id` on the root text first, otherwise `commentary_of` can't be filled in
- Blocks that contain only transclusions (`![[...]]`) are skipped by the edition checks; they are used for alignment
- After the text, edition and TOC are created in the API, save the returned ids back as `text_id`, `edition_id` and `toc_id`
