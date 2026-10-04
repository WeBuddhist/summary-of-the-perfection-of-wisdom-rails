---
name: root-text-upload
description: >
  Lint, parse and upload one root text to the library backend as a text, an
  edition whose segmentation references are its block IDs, and a table of
  contents. The root is published FIRST: its translations need its text_id and
  edition_id, so `translation-upload` cannot run until this has. Dry-run by
  default; reuses an existing text id rather than creating a duplicate; never
  executes without explicit human confirmation.

  Trigger this skill when the user wants a root text published: "upload the root
  text", "push the Tibetan to the library", "publish the source text", "upload
  this sadhana", "why did the root upload fail", "re-upload after the re-cut".
profile: vault-local
---

# root-text-upload

The root-text half of the chain whose translation half is [`translation-upload`](4-SYSTEM/Skills/translation-upload/SKILL.md). One script, `4-SYSTEM/Skills/root-text-upload/scripts/upload_root_text.py`, chains the linter and parser and then talks to the library API:

```
1. POST /v2/texts                                   <- <stem>.text.json     -> text_id
2. POST /v2/texts/{text_id}/editions                <- <stem>.edition.json  -> edition_id
3. POST /v2/editions/{edition_id}/table-of-contents  <- <stem>.toc.json      -> toc_id
```

**Three calls, not four.** There is no alignment step: a root text is the *target* of alignments, never a side of one. Its translations are attached afterwards, each by `translation-upload`, which reads this file's `text_id` and `edition_id`. That is why the root is always published first — a translation uploaded against a root that has no ids has nothing to align to.

**The linter and parser are not bundled here.** They live once in `translation-upload/scripts/` (`linter-root-text/`, `parser-root-text/`) and this script finds them. A second copy would drift from the first, and the two would start disagreeing about what a valid edition is.

**Why deletion is dangerous.** Deleting a segmentation on the backend deletes every alignment hanging off it — and a root text's segmentation is the one every translation aligns *to*, so deleting it takes out the whole language set at once. That is the reason for Rule 3 below: reuse, never re-create.

---

## Inputs

| Input | Description | Required |
|---|---|---|
| **Root-text file** | A `file_type: root-text` (or `edition`) file whose every content block and heading carries a block ID | yes |
| **Credentials** | The API key in the environment. Keep it in a git-ignored `4-SYSTEM/scripts/.env` and `set -a; source 4-SYSTEM/scripts/.env; set +a` before running. Never print, pass on the command line, or commit one | for `--execute` and the live checks |

## What the file must look like

- **`file_type: root-text`** — this matters more than it looks. The linter validates the body, the block IDs and the table of contents **only** for `root-text`, `edition` and `translation`. Any other value (`sadhana`, `prayer`, …) silently skips all of it and the file appears to pass. Put the genre in a separate `genre:` field.
- **Frontmatter**: `title`, `language`, `lang_tag`, `category_id`, `license` (one of the ten allowed values), `source` or `source_url` (an `http(s)://` URL), `edition_type` (`critical` unless there is a reason), and `author` when the contributors are to be recorded. `text_id` / `edition_id` / `toc_id` stay empty until this skill fills them.
- **Contributors**: `author:` is a `,`/`;`-separated string, and each name needs an id tag — `Name [bdrc:P1234]` or `Name [op:ID]` — or it is **dropped with a warning, not an error**. An `authors:` list of objects is not read at all. Check the warning block: a text can upload cleanly with every author silently missing.
- **Body**: one level-1 heading, then the structural headings, each ending in its `^<path>-0` id; every content block ends in its own id. Heading ids may have any number of parts; content ids at most three.

## Output

- The lint report and three parser payloads, under the shared tools' output directories.
- On `--execute`: `text_id`, `edition_id` and `toc_id` patched into the file's frontmatter after each successful call, plus a receipt appended to the ledger after every call — so an interrupted run resumes, and a step whose id is already recorded is skipped.

---

## Rules

1. **Dry run is the default, and is always run first.** It lints, parses and checks — read-only — that the content is non-empty, that segment references are unique, that every span falls inside the content, that the TOC has exactly one root section, and (when the file already carries `text_id`) that the live text has no edition yet. Any problem aborts before a plan is printed.
2. **Never pass `--execute` without explicit human confirmation in the conversation.** A dry-run summary is not consent. State what will be sent — host, whether the text is created or reused, segment count, TOC section count — and wait for a clear yes.
3. **Never re-create a text that exists.** A file carrying `text_id` reuses it. If the live text already has an edition, stop and report: the human decides whether to point the file at it or remove the stale one.
4. **One root text per invocation**, and verify each one afterwards.
5. **Ids go back into the file.** After `--execute` the file carries all three ids and the ledger holds the receipts. Report both.
6. **Publish the root before its translations.** Then run `translation-upload` once per translation.
7. **If two files hold the same text, settle which one is the root before uploading.** Uploading both creates two texts in the library, and every translation can align to only one of them. Reconcile the copies first.

---

## Procedure

### Step 0 — Structural check

Confirm the file's block IDs match the translations that will align to it: every translation's ids must be the same set, in the same order. `translation-alignment-check` does this. A root uploaded with the wrong segmentation has to be re-cut and re-uploaded, and every translation re-aligned.

### Step 1 — Dry run

```bash
set -a; source 4-SYSTEM/scripts/.env; set +a
python3 4-SYSTEM/Skills/root-text-upload/scripts/upload_root_text.py "<root text file>"
```

Read the linter warnings (an author with no id is **skipped**, not an error — see above), the parser's counts, the checks block, and the plan. The linter normalises `language` / `lang_tag` in the file against the API's own names and refreshes its cached language list; both are expected.

### Step 2 — Confirm with the human

State: the host, whether the text id is reused or created, the edition size in chars and segments, the TOC subsection count, and that the file's frontmatter will be patched. Wait for a clear yes.

### Step 3 — Execute

```bash
python3 4-SYSTEM/Skills/root-text-upload/scripts/upload_root_text.py "<root text file>" --execute --skip-lint
```

It stops on the first error. The ids assigned so far are already in the file and the ledger, so re-running the same command resumes rather than duplicating.

### Step 4 — Verify

```bash
python3 4-SYSTEM/Skills/root-text-upload/scripts/upload_root_text.py "<root text file>" --verify
```

Fetches the text, the edition's segments and the table of contents, and prints them. Compare against the file: same segment count, same reference order, one root TOC section whose subsections are in the text's own language.

### Step 5 — Report and record

Report: text id, edition id, TOC id, segments, TOC subsections. Commit the patched file and the ledger. Then upload the translations with `translation-upload`.

---

## Flags

| Flag | Effect |
|---|---|
| *(none)* | dry run — lint, parse, check, print the plan, send nothing |
| `--execute` | send the three calls; needs human confirmation and `WEBUDDHIST_API_KEY` |
| `--skip-lint` | reuse the existing lint output (only when the file has not changed since) |
| `--no-live` | skip the read-only live checks (use when offline; you lose the stale-edition guard) |
| `--verify` | GET the live state of this text and exit |

Environment: `WEBUDDHIST_API_KEY` (`X-API-Key`), `WEBUDDHIST_APP` (optional `X-Application`), `WEBUDDHIST_API_BASE` (default `https://library.webuddhist.com`), `LEDGER_PATH`, `VAULT_ROOT`.

---

## Completion check

- [ ] Dry run read back: lint clean, parse counts right, checks passed, plan as expected
- [ ] Contributor warnings read — no author silently dropped that should have been recorded
- [ ] Only one file is being published as this text
- [ ] Human confirmed `--execute` in this conversation, with the host named
- [ ] `--execute` ran to completion; three ids patched into the file; receipts in the ledger
- [ ] `--verify` read back and matches the file
- [ ] Translations uploaded afterwards with `translation-upload`
- [ ] Nothing under `1-SOURCES/` changed except the permitted frontmatter additions
