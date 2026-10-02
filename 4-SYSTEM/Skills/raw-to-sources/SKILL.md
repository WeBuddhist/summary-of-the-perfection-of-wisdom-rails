---
name: raw-to-sources
description: >
  Bring one raw, human-reviewed file from the inbox into `1-SOURCES/` as a
  cleaned, frontmattered root-text or commentary file — the first step of the
  ingest chain, before any segmentation, TOC, or block IDs. Any language.

  Trigger on "ingest this raw file", "bring this into sources", "promote this
  from the inbox", "this OCR export needs a home".
---

# raw-to-sources

**The promotion rule this skill exists to enforce.** `1-SOURCES/` is the citation
floor and is otherwise LLM-no-write. An intake skill is the one permitted
exception, and it stays inside that exception by **creating whole files** from
material a human has already reviewed in the inbox. It **never edits an existing
`1-SOURCES/` file in place**, and re-running it overwrites its own output rather
than merging into somebody else's. If the target already exists, that is a
collision to report, not a file to patch.

**Work type decides the folder.** A root text or a stand-alone treatise goes to
`1-SOURCES/Text/`; a commentary goes to `1-SOURCES/Commentaries/`; an existing human
translation goes to `1-SOURCES/Translations/`. The discriminator is authorship and title,
not a catalogue category: a single catalogue heading routinely holds both a root
treatise and a commentary on it. If the work type is not stated, ask — never
infer it from the folder the raw file happened to arrive in.

**A commentary is linked to its root only on exact title evidence.** Set
`root_text:` when the commentary's title is the root's title plus a commentary
suffix, or when the supplied catalogue metadata states the relation outright.
Looser matching — substring overlap, an English paraphrase, "these are obviously
about the same thing" — pairs texts that merely share vocabulary. Where no exact
match exists, leave the field blank, say why in `source_description`, and report
it for a human.

**Language-neutral.** The worked shape below happens to be Tibetan, but nothing
in the procedure is: substitute the target language's `language`, `script` and
`lang_tag` values, and use that language's own catalogue identifiers.

This is the missing first rung of the ingest chain: a raw `.txt`/`.docx.txt` export (OCR output, or a human transcriber's rough line-numbered segmentation) has no home in `1-SOURCES/` until it is cleaned and frontmattered. This skill is a thin orchestrator — it does not reimplement cleaning or frontmatter extraction, both of which already exist as skills; it sequences them and places the result. What "correct output" looks like: a file at `1-SOURCES/Text/<title>.md` or `1-SOURCES/Commentaries/<title>.md`, OCR debris stripped, frontmatter complete for every field that is mechanically derivable or already known — but **still unsegmented and un-block-ID'd**. Segmentation, TOC extraction, transclusion, and block IDs are later, separate skills; conflating them here would make failures in this skill hard to isolate from failures in those.

---

## Inputs

| Input | Description | Format |
|---|---|---|
| **Raw file** | One raw text export, already reviewed by a human. | Path under `0-INBOX/raw-data/…` — a `.txt`, `.docx.txt` or `.md` file. |
| **`--type`** | `root`, `commentary` or `translation`. Required — never inferred from content or from where the file sits. If omitted, stop and ask. | `root` \| `commentary` \| `translation` |
| **Known metadata** *(optional)* | Title, author, tradition/school already resolved from a curated catalogue shipped alongside the raw files (a spreadsheet, a དཀར་ཆག, a catalogue export). When present, this is authoritative — prefer it over a colophon guess. | title / author / tradition strings |
| **Root text path** *(commentary only, optional)* | The vault-relative path to the already-ingested root text, for the `root_text:` frontmatter field. If the root has not been ingested yet, leave blank — do not block on it. | `1-SOURCES/Text/<file>.md` |

## Output

One file:

```
1-SOURCES/Text/<title>.md     if --type root
1-SOURCES/Commentaries/<title>.md     if --type commentary
1-SOURCES/Translations/<title>.md     if --type translation
```

`<title>` is the raw file's own title in its own script, with any catalogue ID prefix and transcription-process suffix (`Segmentation`, `- corrected`, `.docx`) stripped — those belong in frontmatter (`book_id`), not the filename.

---

## Output file format

```yaml
---
title: "<title in the text's own script, verbatim>"
title_in_english: "<English gloss, if confidently known — else omit the field rather than guess>"
author: "<author name in the text's own script, verbatim — from known metadata if supplied, else from the colophon>"
file_type: root-text | commentary | translation
language: <the text's language>
script: <the script it is written in>
lang_tag: <the tag for that language — see the vault's About Sources §12>
source_description: "Raw OCR/segmentation export received into <raw file's 0-INBOX path>; <catalogue reference if one exists>."
book_id: "<the raw filename's own catalogue ID prefix — omit the field if it has none>"
status: 0-raw
# commentary only, from commentary-frontmatter:
registered_id: <short id, assigned by commentary-frontmatter>
root_text: <path, only on exact title evidence — else omit>
covers_verses:        # left blank — manual review
# left blank on every file — manual review, not guessed here:
bdrc_work_id:
school:
copyright:
---

<cleaned body — OCR debris stripped, original line/verse numbering preserved as-is,
NOT yet resegmented into sense units, NOT yet block-ID'd>
```

---

## Rules

1. **Never overwrite an existing target file, and never edit one in place.** This skill creates whole files. If the target path already exists, stop and report the collision — do not silently pick a different filename, do not merge, and do not patch the existing file.
2. **Cleaning only, never interpretation.** The same no-loss invariant as `clean-raw-text`: strip page markers, running headers/footers, mid-word spaces, and the script's own stray artifacts (for Tibetan, non-breaking tshegs) — never reorder, reword, gloss, or "fix" the text.
3. **Frontmatter fields are either mechanically derivable or supplied — never guessed from parametric knowledge.** `book_id` comes from the raw filename's own catalogue prefix, when it has one. `title`/`author`/tradition come from supplied catalogue metadata when given, otherwise from the `frontmatter` skill's own colophon-reading procedure — never from what the model "knows" about the text.
4. **`covers_verses`, `bdrc_work_id`, `school`, `copyright` stay blank.** These need judgment or an external lookup (`bdrc_fetch.py`) this skill does not perform. Leaving them blank is correct output, not incomplete output.
5. **`registered_id` is assigned by `frontmatter` (Variant 2), never invented here.** That skill already owns the uniqueness check against the vault annex.
5a. **Work type decides the folder, and `root_text:` is set only on exact title evidence** (see the two rules at the top).
6. **The body stays unsegmented and un-block-ID'd.** Do not run `segment-commentary` (Phase 2), `format-tibetan-root-text`, or any block-ID skill as part of this one — those are separate steps with their own verification.
7. **The raw source file is read-only.** Never edit or move anything under `0-INBOX/raw-data/`.
8. **`status: 0-raw` is this skill's exit marker.** Later steps update it; this skill only ever sets that one initial value. Promotion beyond it is a human decision.

---

## Procedure

1. **Resolve inputs.** Confirm the raw file path exists and `--type` is given. Stop and ask if either is missing.
2. **Clean.** Run `clean-raw-text` on the raw file. Its output lands at `0-INBOX/temp/<text-id>/cleaned.md`.
3. **Derive the target filename.** Strip the raw filename's catalogue ID prefix and process-suffix (`Segmentation`, `- corrected`, `.docx`), keep the title verbatim in its own script, append `.md`.
4. **Check for a collision** at the target path implied by `--type`. Stop and report if the file already exists — do not edit it.
5. **Write the cleaned body** to that path — no frontmatter yet, just the cleaned text.
6. **Run `frontmatter`** on the newly placed file — Variant 1 for `--type root`, Variant 2 for `--type commentary`, Variant 3 for `--type translation`.
7. **Add the two fields those skills don't cover:** `book_id`/`openpecha_id` (raw filename's hex prefix, if present) and `status: 0-raw`.
8. **Reconcile with supplied catalogue metadata, if any.** Where known-good title/author/tradition was given as an input, prefer it over what the frontmatter skill derived from the colophon, and name the catalogue as the source in `source_description`.
9. **Report** the finished file's path and full frontmatter back to the human.

---

## Completion check

- [ ] Target file **created whole** at the path its work type dictates, with no pre-existing collision and no in-place edit of any existing `1-SOURCES/` file
- [ ] Body is cleaned (OCR debris stripped) but **not** segmented and **not** block-ID'd
- [ ] Frontmatter populated via `frontmatter` (Variant 1)/`frontmatter` (Variant 2) (title, author, `file_type`, `language`, `lang_tag`, `source_description`, and `registered_id` for commentaries)
- [ ] `book_id`/`openpecha_id` (when derivable) and `status: 0-raw` added
- [ ] `covers_verses`, `bdrc_work_id`, `school`, `copyright` left blank, not fabricated
- [ ] `root_text:` set only on exact title evidence, or left blank with a note
- [ ] Raw source file under `0-INBOX/raw-data/` unmodified
