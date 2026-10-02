---
name: extract-source-metadata
description: >
  Pull a source text's own metadata — title, author or composer, translator,
  publication details, scribe, patron, place and date — out of its first and last
  pages, and write it into the file's frontmatter properties.

  Trigger on "extract the source properties", "pull the title from this file", "read
  the colophon", "what does the colophon say", "get the metadata out of this text", or
  as the metadata step of an ingest run.

  Traditional Tibetan, Sanskrit, Pāli and Chinese texts put the title at the very
  beginning and the publication data in the colophon at the very end. Never analyse
  the middle of the text — it costs context and adds nothing.
---

# Extract title and colophon metadata from a source text

Two modes, and they are a sequence rather than a choice:

| Mode | Use | Depth |
|---|---|---|
| 1 — Colophon extraction | The text has a real colophon | Deep: parses the colophon's own formulae for scribe, patron, place, date, lineage |
| 2 — First/last page pass | No colophon, or the colophon yielded little | Quick: title from the top, whatever metadata sits at the bottom |

**Run mode 1 first, then mode 2 as the fallback for whatever is still empty.** Mode 2
alone will miss most of what a colophon actually encodes; mode 1 alone returns
nothing on a text that has no colophon.

Whatever either mode finds goes into the frontmatter through `frontmatter`'s schema
for that `file_type` — this skill extracts, it does not decide the schema.

---

## Mode 1 — Colophon extraction

The deep pass. Traditional colophons follow recognisable formulae; this mode reads them rather than pattern-matching for names.

This mode extracts structured metadata from a source file by analysing the
first and last 200 syllables of the text. It uses the LLM to identify the
author, title, language, and other colophon information, then writes the
extracted metadata into the YAML frontmatter (Properties) of the **same file**,
leaving the filename and body content unchanged.

**Catalogue IDs are optional.** Where the filename itself encodes a catalogue
number — a Derge `D####`, a Taishō number, a Tōhoku number — record it in the
matching frontmatter field. Where it does not, omit that field and carry on;
nothing about this mode depends on a catalogue-style filename.

This skill prevents the common failure mode of manually guessing metadata or
reading entire large files when the relevant information is concentrated in
the title block and colophon.

---

### Inputs

| Input | Description | Required |
|---|---|---|
| `file_path` | Path to the source file | yes |
| `file_type` | `root-text`, `commentary`, `translation` or `reference` — **taken from context**: the folder the file sits in, the caller's instruction, or the file's existing frontmatter. Never assumed. If it cannot be determined, ask. | yes |
| `batch` | If `true`, process a caller-supplied set of files sequentially. Overrides `file_path`. | no (default: `false`) |

If neither `file_path` nor `batch: true` is provided, ask the user which
file(s) to process.

### Output

The input file is updated in place: its YAML frontmatter (Properties) is
populated with the extracted metadata. The filename and body content are
**not changed**.

---

### Frontmatter schema

The following fields are written into the file's YAML frontmatter block. If
a frontmatter block already exists, update only these fields; leave any
other existing fields untouched. If no frontmatter block exists, prepend
one. The `frontmatter` skill owns the full schema for each `file_type`; this
mode only fills in what the text's own head and tail state.

```yaml
---
title:                        # exact title of the work in original script
title_in_english:             # English translation of the title
author:                       # author name in original script
author_in_english:            # romanized/English author name
file_type:                    # from context — root-text | commentary | translation | reference
language:                     # e.g. Tibetan, Sanskrit, Chinese
lang_tag:                     # tag from About Sources §12 — bo, sk, zh, pi, en …
source_description: ""        # to be filled by a human later
colophon:                     # the colophon transcribed, or a short summary of what it states
derge_catalog_id:             # only when the filename carries one — omit otherwise
---
```

The body content of the file is **not modified**.

---

### Rules

1. **Syllable extraction uses tseg and shad as delimiters.** Split the text using the regex pattern `[་།]` (Tibetan tseg `་` U+0F0D and shad `།` U+0F0B). Each non-empty segment after splitting counts as one syllable.
2. **Extract exactly 200 syllables from the end** (the colophon region) and **200 syllables from the beginning** (the title region). If the file has fewer than 400 syllables total, use the entire text.
3. **Do not read the middle of the text.** The skill must work without loading the full file body into the LLM context. Read only the head and tail regions.
4. **The LLM analyses only the extracted syllable regions.** From the colophon region, extract: author name, translator name (if present), place of composition (if present), and any closing dedication or attribution. From the title region, extract: formal title and Sanskrit/alternate title (if present).
5. **The `lang_tag` is determined from the text content**, not assumed. Verify from the opening lines (look for language-declaration markers, e.g. Tibetan `རྒྱ་གར་སྐད་དུ།` / `བོད་སྐད་དུ།`).
6. **A catalogue ID is extracted from the original filename only when it carries one** (e.g. `D3872` from `D3872.txt` → `derge_catalog_id`). It is an optional field, not a precondition: a file with an ordinary filename is processed exactly the same way, with the field omitted.
7. **Do not rename or move the file.** Only the frontmatter of the existing file is updated.
8. **Do not modify the body content of the file.** Only the YAML frontmatter block is written or updated.
9. **If the LLM cannot confidently identify the author**, set `author: unknown` in frontmatter and report this to the user.
10. **`file_type` comes from context, never from a default.** The folder the file sits in, the caller's instruction, or the file's existing frontmatter decide it. Writing `root-text` onto a commentary sends every downstream schema check the wrong way.

---

### Procedure

#### Step 1 — Validate the input file

1. Confirm the file exists at the given path.
2. Establish its `file_type` from context (folder, caller, existing frontmatter). If it is genuinely unclear, ask rather than defaulting.
3. If the filename carries a catalogue ID (e.g. `D3872`), extract it; otherwise skip this step.

#### Step 2 — Extract syllable regions

1. Read the **first 3,000 characters** of the file (this generously covers 200+ syllables for the title region).
2. Read the **last 3,000 characters** of the file (this generously covers 200+ syllables for the colophon region).
3. For each region, split the text by the regex pattern `[་།]` and filter out empty strings.
4. From the beginning region, take the **first 200 syllable tokens** and rejoin them with their original delimiters (preserve the original text).
5. From the ending region, take the **last 200 syllable tokens** and rejoin them with their original delimiters (preserve the original text).

#### Step 3 — LLM metadata extraction

Present the two extracted regions to the LLM with the following prompt
structure:

```
You are analysing a classical text. Below are the TITLE REGION (first 200 syllables) and COLOPHON REGION (last 200 syllables) of the text.

TITLE REGION:
{title_region_text}

COLOPHON REGION:
{colophon_region_text}

Extract the following metadata. Return ONLY the metadata in this exact format, with no additional commentary:

title: [exact title in original script]
title_in_english: [English translation of the title]
author: [author name in original script]
author_in_english: [romanized/English author name]
translator: [translator name if mentioned, otherwise "none"]
language: [primary language of the text]
lang_tag: [tag: bo, sa, zh, en]

If you cannot determine a field with confidence, write "unknown".
```

#### Step 4 — Build the frontmatter block

Build the YAML frontmatter using the extracted metadata and the Derge
catalog ID.

#### Step 5 — Write the frontmatter into the existing file

1. Read the current content of the input file.
2. If the file already begins with a `---` frontmatter block, replace it with the new frontmatter. Preserve all body content exactly.
3. If no frontmatter block exists, prepend the new frontmatter block (followed by a blank line) before the existing content.
4. Write the updated content back to the **same file** at the same path. Do not change the filename or move the file.
5. Report to the user: the filename, and the extracted metadata fields.

#### Step 6 — Batch mode (if applicable)

If `batch: true`:
1. Take the caller-supplied file list (or glob), which must name a real folder in this repo — a catalogue-style filename pattern is one possible glob, not a requirement.
2. For each file, execute Steps 1–5.
3. At the end, report a summary table: filename → author → title.

---

### Completion check

- [ ] Syllable extraction used `[་།]` regex, not word-level or line-level splitting
- [ ] Exactly 200 syllables extracted from each end (or full text if shorter)
- [ ] Middle of the text was not read into LLM context
- [ ] Frontmatter has all fields populated (or marked `unknown`)
- [ ] `file_type` taken from context, not defaulted
- [ ] A catalogue ID field is present only where the filename actually carries one, and matches it
- [ ] Filename is unchanged
- [ ] Body content of the file is unmodified

---

---

## Mode 2 — First/last page property pass

The general fallback. Run after mode 1, for fields still empty.

This mode defines the standard procedure for extracting metadata from a source
text under `1-SOURCES/` and adding it as frontmatter properties.

### Context
Source texts (especially traditional Tibetan and Chinese texts, like
commentaries and root texts) contain their title at the very beginning
(first page) and their publication, author, or translator metadata in the
colophon at the very end (last page).

### Directives
To save processing time, preserve context, and ensure accuracy, **do not
analyze the middle of the text**.

1. **First Page (Title):** Examine only the beginning of the text to extract the main title. Look for traditional title markers (e.g., in Tibetan: `༄༅། །... ཞེས་བྱ་བ་བཞུགས་སོ། །`).
2. **Last Page (Colophon):** Examine only the final paragraphs/lines of the text to extract colophon information, which typically includes the author, translator, scribe, location, and date.
3. **Apply Properties:** Edit only the YAML frontmatter block at the top of the file — never rewrite the whole document — to add the extracted metadata.

### Recommended Properties
When extracting, aim to populate the following properties (the `frontmatter`
skill owns the full schema for each `file_type`):
- `title`: The formal title of the work.
- `author`: The author or composer.
- `translator`: The translator, if applicable.
- `colophon`: The colophon transcribed, or a short factual summary of what it states. This is the one field that preserves the evidence the other fields were read from, so a later reader can check them without reopening the source.
- `source_description`: A brief description of the source material derived from the colophon.

### Example: extracting from a Tibetan file's title and colophon
If a user asks you to add properties to a Tibetan-language source file:
1. Read the file content.
2. Look at the top-most lines to identify the title.
3. Look at the bottom-most lines to identify the colophon.
4. Ignore the rest of the text body.
5. Edit the YAML frontmatter block to add `title`, `author`, `colophon` and
   `source_description` based on what you found.

### Important Note
Edit only the frontmatter block (the `---`-delimited YAML at the top of the
file) rather than rewriting the entire document. This ensures that the
extensive root text or commentary in the middle remains completely untouched
and safe.

### Rules & Edge Cases
- **Do not hallucinate:** If a specific piece of information (like an English translation) is not available in the title or colophon, do not invent it. Either skip that property or leave it empty.
- **Efficiency:** Stick strictly to the title and colophon to keep processing fast and focused.

