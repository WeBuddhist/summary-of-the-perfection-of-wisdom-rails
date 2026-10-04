---
name: translation-upload
description: >
  Lint, parse and upload one finished translation to the library backend as an
  edition of its own text — aligned segment-for-segment to the published root
  edition and carrying its own table of contents. Dry-run by default; reuses an
  existing text id rather than creating a duplicate; never executes without
  explicit human confirmation.

  Trigger this skill when the user wants a translation published: "upload the
  translation", "push this to the library", "publish the English", "send it to the
  backend", "why did the upload fail", "re-upload after the re-cut".
---

# translation-upload

The translation-side counterpart of the root-text upload chain. One script, `4-SYSTEM/Skills/translation-upload/scripts/upload_translation.py`, chains the bundled linter and parser and then talks to the library API:

```
1. POST   texts                                   <- <stem>.text.json       only when the file has no text_id
2. POST   texts/{text_id}/editions                <- <stem>.edition.json    -> edition_id
3. PUT    editions/{root_edition}/alignments/{edition_id}
                                                  <- <stem>.alignment.json  (the root is the SOURCE side)
4. POST   editions/{edition_id}/table-of-contents <- <stem>.toc.json        -> toc_id
```

**Why the shape matters.** A translation is its own *text* on the backend, marked as a translation of the root's text id — a link that can only be set when the text is created, never patched afterwards. It has its own *edition* (the content, plus a segmentation whose references are the block IDs), an *alignment* from the root edition's segments to its own (identity pairs, because block `^N` here renders block `^N` of the root), and a *table of contents* whose spans mirror the root's, since headings are annotation over the translated blocks rather than content of their own.

**Why deletion is dangerous.** Deleting a segmentation on the backend deletes every alignment hanging off it. A corpus has been lost this way and had to be re-cut and re-uploaded under its surviving text ids. That is the reason for Rule 3 below: reuse, never re-create.

---

## Inputs

| Input | Description | Required |
|---|---|---|
| **Translation file** | A `file_type: translation` file whose body is block-ID aligned to the root and whose `root_text:` resolves to it | yes |
| **Root ids** | The root file's frontmatter must already carry `text_id` and `edition_id` — the root is published first | yes |
| **Credentials** | The API key in the environment. Keep it in a git-ignored `4-SYSTEM/scripts/.env` and `set -a; source 4-SYSTEM/scripts/.env; set +a` before running. Never print, pass on the command line, or commit one | for `--execute` and the live checks |

## What the file must look like

- **Frontmatter**: `title` in the target language, `language`, `lang_tag`, `file_type: translation`, `root_text`, `category_id`, `license`, `source`, `edition_type`. Optionally `translator`, `alt_titles`, an authority id. Do **not** set the translation-of link by hand — the linter resolves it from the root's `text_id`.
- `text_id` present when the translation text already exists on the backend, so it is reused; `edition_id` and `toc_id` stay empty until this skill fills them.
- **Body**: the title line with its ID, then the root's headings with their `^<path>-0` IDs, then for each block a transclusion of the root block, a blank line, and the translation ending in its own matching ` ^<id>`. Every block carries an ID — the linter rejects a block without one.

The machine-baseline translation skills render exactly this shape, so their output is uploadable without reshaping.

## Output

- The lint report and the four parser payloads, under the bundled tools' output directories.
- On `--execute`: `edition_id`, the aligned-to edition id, and `toc_id` patched into the file's frontmatter after each successful call, plus a receipt appended to the upload ledger after every call — so an interrupted run resumes, and a step whose id is already recorded is skipped.

---

## Rules

1. **Dry run is the default, and is always run first.** It lints, parses, and checks — read-only — that the edition's references equal the live root's segment references one for one, that the live translation text points at the root and has no edition yet, and that the alignment is identity. Any problem aborts before a plan is printed.
2. **Never pass `--execute` without explicit human confirmation in the conversation.** A dry-run summary is not consent. State what will be sent — host, text id, segment count, pair count, TOC sections — and wait for a clear yes.
3. **Never re-create a text that exists.** A file carrying `text_id` reuses it. If the live text already has an edition, stop and report: the human decides whether to point the file at it or remove the stale one. Re-creating loses every alignment that referenced the old segmentation.
4. **The root's live segmentation is the truth.** If the file's block IDs differ from the live root's references, fix the file or re-upload the root — never the payload.
5. **Ids go back into the file.** After `--execute` the file carries its edition and TOC ids and the ledger holds the receipts. Report both.
6. **One translation per invocation**, and verify each one afterwards.

---

## Procedure

### Step 0 — Structural check

Run `translation-alignment-check` first. It must pass before anything below runs; after Step 1 run it again with `--payloads --live`.

### Step 1 — Dry run

```bash
set -a; source 4-SYSTEM/scripts/.env; set +a
python3 4-SYSTEM/Skills/translation-upload/scripts/upload_translation.py "<translation file>"
```

Read the linter warnings (an unresolved translator with no authority id is expected for machine output and is skipped, not an error), the parser's counts, the live-check block, and the plan. The linter normalises `language` / `lang_tag` in the file against the API's own names; that is expected.

### Step 2 — Confirm with the human

State: the host, whether the text id is reused or created, the edition size, the pair count, the TOC subsection count, and that the file's frontmatter will be patched. Wait for a clear yes.

### Step 3 — Execute

```bash
python3 4-SYSTEM/Skills/translation-upload/scripts/upload_translation.py "<translation file>" --execute --skip-lint
```

It stops on the first error. The ids assigned so far are already in the file and the ledger, so re-running the same command resumes rather than duplicating.

### Step 4 — Verify

```bash
python3 4-SYSTEM/Skills/translation-upload/scripts/upload_translation.py "<translation file>" --verify
```

Fetches the text, the edition's segments, the alignment and the table of contents, and prints them. Compare against the file: same segment count, same reference order, one root TOC section whose subsections are in the target language.

### Step 5 — Report and record

Report per translation: text id, edition id, TOC id, segments, pairs, TOC subsections. Commit the patched files and the ledger.

---

## Completion check

- [ ] Dry run read back: lint clean, parse counts right, live checks passed, plan as expected
- [ ] `translation-alignment-check` passed, including `--payloads --live`
- [ ] Human confirmed `--execute` in this conversation, with the host named
- [ ] `--execute` ran to completion; ids patched into the file; receipts in the ledger
- [ ] `--verify` read back and matches the file
- [ ] Nothing under `1-SOURCES/` changed
