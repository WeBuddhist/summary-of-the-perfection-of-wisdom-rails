---
name: term-definition
description: Extract verbatim definitions of key terms from the commentaries and fill them into the Meaning column of the term-localization table, formatted in the source tradition's quotation style.
---

# term-definition

This skill populates the **Meaning** column of `2-RAILS/Termbases/term-localization.md` by locating definitional passages in `1-SOURCES/Commentaries/` and extracting them verbatim. A definitional passage is one where a commentary explains a term using a formulaic definitional marker of the source language (§ Definitional marker patterns). Extracted text is formatted in the source tradition's quotation style. The skill never paraphrases, summarises, or writes any explanatory text of its own — all content comes word-for-word from the cited commentary.

---

## Inputs

- **Term or term list** — one or more terms from the `<src-lang>` column of `2-RAILS/Termbases/term-localization.md`. If the user says "all terms" or supplies no specific term, process every row whose Meaning cell is currently empty.
- **Source language** (`<src-lang>`) — per `4-SYSTEM/Guidelines/vault-annex.md`. It selects the definitional-marker row to use below.
- **Commentary files** — all files under `1-SOURCES/Commentaries/` are eligible sources. The skill searches them all unless the user restricts to a named commentary.
- **The term table** — `2-RAILS/Termbases/term-localization.md` — the table to update.

---

## Output

`2-RAILS/Termbases/term-localization.md` — modified in place. For each processed term, the Meaning cell is filled with one or more quotation entries, one per commentary passage found.

---

## Output cell format

Every definitional hit — whether from one commentary or many — is written into the same Meaning cell using this format:

```
[short-name] "[verbatim explanation text]" [closing frame] ([1-SOURCES/Commentaries/<filename> > ^<block-id>](1-SOURCES/Commentaries/<filename>#^<block-id>))
```

When multiple hits exist (from the same or different commentaries), list each one on its own line inside the cell, one after the other:

```
[commentary-A-short-name] "[verbatim explanation text A]" [closing frame] ([1-SOURCES/Commentaries/<filename-A> > ^<block-id-A>](1-SOURCES/Commentaries/<filename-A>#^<block-id-A>))
[commentary-B-short-name] "[verbatim explanation text B]" [closing frame] ([1-SOURCES/Commentaries/<filename-B> > ^<block-id-B>](1-SOURCES/Commentaries/<filename-B>#^<block-id-B>))
```

There is no special treatment for single vs. multiple hits — the format is identical; additional entries are simply appended as additional lines.

> **Write the citation path out in full.** A citation's markdown link must carry the real, literal path — the one that resolves when a reader clicks it. Obsidian expands nothing at read time, so a placeholder left inside an href renders as dead text and the citation chain silently breaks. Prose in this skill may name a location however it likes; a link template may not.

**`[short-name]`** is the registered short ID for the commentary as declared in the file's frontmatter (`id:` or `short_id:` field). If no short ID is declared, use the filename stem without the language tag.

**`"[verbatim explanation text]"`** is enclosed in standard double quotation marks `"..."`. The text is the exact content extracted from the commentary, beginning immediately after the definitional marker and ending at the first sentence-final punctuation of the source language (or the next structural boundary). Do not include the marker itself in the quotation.

**`[closing frame]`** is the source tradition's fixed "thus it is said" formula — for Tibetan, `ཞེས་གསུངས་སོ།།`. It is a fixed frame, not original writing. A vault working in another source language declares its own closing frame in `4-SYSTEM/Guidelines/vault-annex.md`; if none is declared, omit the frame rather than inventing one.

**The citation** is a markdown hyperlink: display text is `1-SOURCES/Commentaries/<filename> > ^<block-id>` and the href is `1-SOURCES/Commentaries/<filename>#^<block-id>`, wrapped in parentheses after the closing frame.

---

## Definitional marker patterns

The marker set is **declared per source language**. Search for these patterns in commentary files, where `{TERM}` is the exact source-language string of the target term.

**Tibetan (`-bo`) — the default set:**

| Pattern         | Example                 |
| --------------- | ----------------------- |
| `{TERM}་ནི་`    | (with tsheg before ནི་) |
| `{TERM}ཞེས་པ་`  | `སེམས་བསྐྱེད་པ་ཞེས་པ་`  |
| `{TERM}ཅེས་པ་`  | `སེམས་བསྐྱེད་པ་ཅེས་པ་`  |

**Other source languages — fill in before first use:**

| Source language | Pattern | Example |
| --- | --- | --- |
| Sanskrit (`-sk`) | *(declare in `4-SYSTEM/Guidelines/vault-annex.md`; the quotative particle `iti` and the gloss verbs are the usual starting point)* | |
| Pāli (`-pi`) | *(declare in the annex; the quotative `…ti` and the commentarial gloss formulae are the usual starting point)* | |
| Chinese (`-zh`) | *(declare in the annex)* | |
| *(other)* | *(declare in the annex)* | |

A placeholder row is not a licence to guess. If the row for this vault's source language is still empty, stop and ask the contributor to declare the marker set in the vault annex before running the skill.

Accept the pattern anywhere in a paragraph — not only at the start of a sentence. A hit is valid only when the term is followed immediately (without intervening words) by one of these markers.

---

## Rules

1. **No original writing.** The Meaning cell contains only verbatim text from the source commentary plus the fixed frame words. If a term has no definitional hit in any commentary, leave the Meaning cell empty and move to the next term. Do not write a placeholder, a note, or a summary.
2. **Verbatim extraction only.** Copy the explanation exactly as it appears in the commentary. Do not correct spelling, normalise orthography, or truncate for length unless a passage runs more than three sentences — in that case, take only the first complete sentence after the marker.
3. **No interpretation.** Do not choose between two passages on the basis of which is "better" or "clearer". Include all valid hits, each as its own quotation line.
4. **Do not touch any column other than Meaning.** No other column — the source-term column or any target-language column — is modified by this skill.
5. **Do not overwrite non-empty Meaning cells without explicit instruction.** If a Meaning cell already contains text, skip that row unless the user explicitly asks to overwrite or append.
6. **Cite every quotation to its block ID.** After the closing frame append a markdown hyperlink in parentheses, with the path written out in full: `([1-SOURCES/Commentaries/<filename> > ^<block-id>](1-SOURCES/Commentaries/<filename>#^<block-id>))`. Use the inline citation form — no footnotes.
7. **Use the commentary short ID, not the full filename.** Check the frontmatter of each commentary file for a registered `id:` or `short_id:` before constructing the quotation frame.
8. **Do not modify `1-SOURCES/` files.** This skill reads commentaries but never writes to them.

---

## Procedure

### Step 1 — Identify terms to process

1. Open `2-RAILS/Termbases/term-localization.md` and read the full table.
2. If the user named specific terms, collect only those rows. If the user said "all" or gave no restriction, collect all rows where the Meaning cell is empty (contains only whitespace).
3. Record each term as a source-language string for the search step.

### Step 2 — Load commentary short IDs

1. List all files under `1-SOURCES/Commentaries/`.
2. For each file, read its YAML frontmatter and record the `id:` or `short_id:` field. If neither is present, derive the short name from the filename stem by dropping the language tag suffix.
3. Build a lookup table: `{filename → short-name}`.

### Step 3 — Search for definitions

For each term in the work list:

1. Search every commentary file for the definitional marker patterns declared for this vault's source language (§ Definitional marker patterns above). Use literal string search — the term must appear verbatim.
2. For each hit, record:
   - The commentary filename
   - The block ID of the containing paragraph (`^block-id` suffix on that paragraph)
   - The verbatim text starting immediately after the marker and ending at the first sentence-final punctuation that closes the definitional clause
3. If a commentary file has multiple definitional passages for the same term, record each separately.

### Step 4 — Format quotation entries

For each hit recorded in Step 3:

1. Look up the commentary short name from the table built in Step 2.
2. Construct the quotation entry, with the citation path written out in full:
   ```
   [short-name] "[verbatim text]" [closing frame] ([1-SOURCES/Commentaries/<filename> > ^<block-id>](1-SOURCES/Commentaries/<filename>#^<block-id>))
   ```
3. If multiple hits exist for the same term, order them by commentary (alphabetical by short name) unless the user specifies an order.

### Step 5 — Write results to the term table

1. Open `2-RAILS/Termbases/term-localization.md`.
2. For each processed term:
   a. Locate the row matching the source-term cell.
   b. Replace the empty Meaning cell content with all formatted quotation entries for that term, each on its own line, in the order found (alphabetical by commentary short name unless the user specifies otherwise).
3. Write the updated file back to disk.
4. Do not reformat, reorder, or change spacing in any other part of the table.

### Step 6 — Report

After processing, report:
- How many terms were processed.
- How many terms received at least one definition.
- How many terms had no definitional hit in any commentary (list the terms).

---

## Completion check

- [ ] Only the Meaning column was modified; all other columns are unchanged
- [ ] Every filled Meaning cell contains only verbatim text from a commentary, framed with `[short-name] "…" [closing frame]`
- [ ] Every quotation entry includes the block-ID as a markdown hyperlink in parentheses, with the path written out in full: `([1-SOURCES/Commentaries/<file>.md > ^<id>](1-SOURCES/Commentaries/<file>.md#^<id>))` — a real, literal path inside the href, never a placeholder
- [ ] No Meaning cell was overwritten unless the user explicitly authorised it
- [ ] Terms with no definitional hit are left blank (not filled with a note or placeholder)
- [ ] No file in `1-SOURCES/` was modified
- [ ] `2-RAILS/Termbases/term-localization.md` was saved back to disk with all changes applied
