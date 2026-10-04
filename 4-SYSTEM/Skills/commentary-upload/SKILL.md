---
name: commentary-upload
description: >
  Lint, parse and upload one commentary to the library backend as its own text
  (commentary_of the root), an edition whose segmentation references are its
  block IDs, a table of contents, and an alignment from its segments to the
  root edition's segments built from its root-text transclusions. Footnotes are
  kept out of every payload. Dry-run by default; never executes without
  explicit human confirmation.

  Trigger this skill when the user wants a commentary published: "upload the
  commentary", "push the commentary to the library", "prepare the commentary
  payload", "why did the commentary upload fail".
profile: vault-local
---

# commentary-upload

The commentary counterpart of [`root-text-upload`](4-SYSTEM/Skills/root-text-upload/SKILL.md) and [`translation-upload`](4-SYSTEM/Skills/translation-upload/SKILL.md). One script, `4-SYSTEM/Skills/commentary-upload/scripts/upload_commentary.py`, chains the vault's `linter-commentary` and `parser-commentary` (in `4-SYSTEM/scripts/`, forked from 21-taras-rails) and then talks to the library API:

```
1. POST /v2/texts                                     <- <stem>.text.json       -> text_id   (commentary_of = root text_id)
2. POST /v2/texts/{text_id}/editions                  <- <stem>.edition.json    -> edition_id
3. POST /v2/editions/{edition_id}/table-of-contents   <- <stem>.toc.json        -> toc_id
4. PUT  /v2/editions/{edition_id}/alignments/{root_edition_id}
                                                      <- <stem>.alignment.json  (commentary = source, root = target)
```

**Every commentary is a commentary of the root.** A commentary in another language — even a translation of another commentary — is uploaded as its own commentary of the root text and aligned to the root only. Its segment count need not match any other commentary's. The script refuses a file that carries `translation_of`.

**Alignment direction.** The commentary edition is the *source*, the root edition the *target*, and the parser's pairs are sent unchanged. This matches the commentaries already live on the library (the 21-taras commentaries answer on `GET editions/<commentary>/alignments/<root>` and not the reverse). It is the opposite of `translation-upload`.

**How the alignment is derived** (parser-commentary, `build_alignment`): a transclusion `![[<root>#^ref]]`, or a run of consecutive transclusions, opens a scope; every commentary block after it is aligned to all of those root segments until the next transclusion group, which replaces the scope. Headings are ignored entirely: never aligned, and they neither close nor reset the scope. Only commentary before the first transclusion in the file is left unaligned. Transclusions of root headings are skipped (headings are not segments). Transclusions of any file other than `root_text` give no target and close the scope. The result may be many-to-one or many-to-many.

**No cross-language `alt_titles`.** The library merges `alt_titles` into the text's title map, and titles are unique per language. An English alt title on a Tibetan commentary therefore claims that English title and blocks the English commentary (HTTP 422 "title … already exists"), and it cannot be removed afterwards (`PATCH` ignores `[]` and rejects `null`). The dry run refuses them.

**Footnotes.** The backend has no footnote annotations yet. The linter and parser drop `[^n]` markers and `[^n]: …` note lines before building anything, as they drop `<small>` tags; the source keeps them for a future footnote parser. The script checks that no marker and no note text reached the content or the TOC.

---

## Inputs

| Input | Description | Required |
|---|---|---|
| **Commentary file** | `file_type: commentary`, every content block and heading carrying a block ID (`add-block-ids` Mode 1), root-text transclusions where it discusses the root | yes |
| **Root ids** | The `root_text:` file must carry `text_id` and `edition_id` — the root is published first | yes |
| **Frontmatter** | `title`, `language`, `root_text`, `category_id`, `license`, `source` (http/https), `edition_type`, `date` as a string; `commentary_of` is filled by the linter from the root | yes |
| **Credentials** | `WEBUDDHIST_API_KEY` in a git-ignored `4-SYSTEM/scripts/.env`; `set -a; source 4-SYSTEM/scripts/.env; set +a`. Never print, pass on the command line, or commit it | for `--execute` |

## Rules

1. **Dry run is the default, and is always run first.** It lints, parses, checks and prints the plan; nothing is sent.
2. **Never pass `--execute` without explicit human confirmation in the conversation**, naming the host, the files, segment and pair counts. A dry-run summary is not consent.
3. **Never re-create a text that exists.** A file carrying `text_id` reuses it; the dry run also stops if the root already lists a commentary with the same language and title.
4. **Ids go back into the file.** After `--execute` the note carries `text_id`, `edition_id`, `toc_id`, `aligned_to_edition_id`, and `scripts/upload_ledger.json` holds a receipt per call. Re-running resumes.
5. **One commentary per invocation**, verified afterwards with `--verify`.

## Procedure

```bash
set -a; source 4-SYSTEM/scripts/.env; set +a
python3 4-SYSTEM/Skills/commentary-upload/scripts/upload_commentary.py "<commentary.md>"                       # 1. dry run
python3 4-SYSTEM/Skills/commentary-upload/scripts/upload_commentary.py "<commentary.md>" --execute --skip-lint  # 2. after a clear yes
python3 4-SYSTEM/Skills/commentary-upload/scripts/upload_commentary.py "<commentary.md>" --verify               # 3. read back
```

The checks the dry run performs: `commentary_of` equals the root's `text_id` and there is no `translation_of`; content non-empty; segment references unique; spans cover the content contiguously; no footnote marker or note text and no `![[`, `<small>`, `**` in the content or TOC; one TOC root section; every alignment source is a segment of this edition and every target a block of the root file; live: the root text lists its edition, every target is in the live root segmentation, no duplicate commentary on the root.

## Completion check

- [ ] Dry run read back: lint clean, parse counts right, all checks passed, plan as expected
- [ ] Human confirmed `--execute` in this conversation, with the host named
- [ ] `--execute` ran to completion; ids patched into the file; receipts in the ledger
- [ ] `--verify` matches the file: segment count, alignment pairs, TOC nodes
