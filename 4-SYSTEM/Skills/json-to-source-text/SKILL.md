---
name: json-to-source-text
description: Convert JSON dumps of classical texts (tipitaka.org, SuttaCentral, GRETIL exports, BDRC, custom scraped JSON) into properly formatted Markdown source-text files for 1-SOURCES/Text/. Adaptive — inspects each JSON's schema, reuses an existing converter if the source shape is known, otherwise generates a new converter. The current converter (tipitaka_org_book.py) produces Pāli Tipiṭaka root texts in the Bible-style book-verse numbering scheme.
---

# json-to-source-text

> **OPTIONAL intake path.** Use this skill only when your text originates as
> a JSON export (tipitaka.org, SuttaCentral, GRETIL, BDRC, or a custom
> scrape). If you already have a plain-text or markdown source, skip this
> skill entirely and start from `clean-raw-text` with the file placed in
> `0-INBOX/raw-data/`.

Converts JSON-formatted classical text dumps into Markdown source-text files
that obey the vault's conventions — `4-SYSTEM/CLAUDE.md` §5–5b and
`1-SOURCES/About Sources.md` §5 for block IDs and headings, `About Sources.md`
§4 for frontmatter (and `4-SYSTEM/Guidelines/annotation-conventions.md`, which both implement).

The skill is **adaptive**: every JSON source uses its own schema (tipitaka.org
exports look very different from SuttaCentral exports, which look different
from BDRC dumps). For each new JSON shape the skill first profiles the
structure, then either reuses an existing source-specific converter or
generates a new one.

---

## Workflow Overview

```
JSON file
   │
   ▼
Step 1: Inspect ──► profile JSON (top-level keys, segment schema,
   │                              type/class distribution, samples)
   ▼
Step 2: Check converters/ for matching source slug
   │
   ├─ Found ──► Step 4: Run existing converter
   │
   └─ Not found ──► Step 3: Generate new converter ──► Step 4: Run it
                                                           │
                                                           ▼
                                                    Step 5: Review output
                                                    against CLAUDE.md §5–5b
```

---

## Step 1 — Inspect the JSON

Run the inspector to extract a structural profile:

```bash
python3 4-SYSTEM/Skills/json-to-source-text/json_inspector.py path/to/source.json
```

The inspector outputs JSON containing:

- `file` — path and size
- `top_level` — type and keys (or array length) of the root
- `metadata_candidates` — string/numeric top-level fields that look like metadata (`id`, `title`, `author`, `language`, `source`, etc.)
- `content_array` — if the root contains an array of segment-like objects, the inspector reports its name, length, and the union of keys
- `category_fields` — for any key whose values come from a small enumerated set (`type`, `class`, `css_class`, `level`, `role`), the distribution of values is reported with sample content for each
- `chapter_field` — best guess at which field carries chapter/section numbering, plus the distribution of values
- `samples` — first 3, middle 1, last 3 segments, fully expanded
- `source_slug` — suggested slug for naming the converter (derived from `id`, `source_filename`, `publisher`, or the filename)

Read the profile carefully. Pay particular attention to:

- **`category_fields`** — these are the "what kind of segment is this" signals. Each distinct value (e.g. `centered`, `chapter`, `subhead`, `bodytext`) needs a routing rule in the converter: does it become a heading? a body verse? a discardable element? Look at the sample content for each category to decide.
- **`chapter_field` distribution** — tells you how the source author divided the text. If chapter `0` contains homage/title material it maps to `## 0. Introduction`. If chapter `0` is already an authored chapter, you may need to shift everything: extract the prefatory segments and place them in a synthetic `## 0. Introduction`, then renumber.
- **`samples`** — confirm each category's role from real content. A `title` class with content `"2. Dukamātikā"` is a `###` subsection, not a chapter.

---

## Step 2 — Check for an Existing Converter

Look in `4-SYSTEM/Skills/json-to-source-text/converters/` for a file named
`<source_slug>.py`.

**If a matching converter exists:** skip to Step 4.

**If no converter exists:** proceed to Step 3.

Existing converters in this skill:

| Slug | Source convention | Output convention | Languages |
|---|---|---|---|
| `tipitaka_org_book.py` | tipitaka.org book exports (Mūla layer): top-level metadata + `segments[]` array with `chapter`, `paragraph`, `content`, `css_class` | **Pāli Tipiṭaka root text (Bible-style book-verse numbering).** One file per book. Main-book verse IDs come directly from the source's leading `N.` markers (e.g. `583. Katame dhammā…` → `^1-583`), so source-N and block-ID stay aligned even when h4/h5 sub-section headings appear between numbered verses — a verse can span multiple subsections without restarting the counter. The Mātikā TOC chapter uses letter-suffixed sub-namespaces (`^1-0a-V`, `^1-0b-V`) with an internal counter, because the source itself restarts numbering across its TOC sub-sections. Heading hierarchy goes `#` (pitaka) → `##` (book) → `###`/`####`/`#####`. |
| `english_paired_translation.py` | tipitaka.org-paired English translation exports: a flat array of `{text, original, rys_davids, ai}` objects with embedded `<h1>/<h2>/<h3>` structural tags | Companion translation file matching `tipitaka_org_book.py`'s book-verse IDs, so a root text and its paired translation stay verse-aligned. | Pāli → English |

---

## Step 3 — Generate a Custom Converter

**First, pick the output convention** appropriate to the source's text type:

- **Pāli Tipiṭaka root texts** (Vinaya, Sutta, Abhidhamma books): use the Bible-style `book-verse` scheme. Model the new converter on `tipitaka_org_book.py`.
- **Sanskrit / Tibetan root texts**: use the generic `^chapter-verse` (or `^book-chapter-verse`) scheme in `4-SYSTEM/CLAUDE.md` §5.
- **Translations and commentaries**: follow the same block-ID system as the root text they accompany. (Out of scope for this repo's current root-text-only pipeline — see the repo README — but the converter pattern still applies if you're preparing material ahead of that support landing.)

If the source's text type doesn't fit any existing convention, note the new
convention you're introducing in the converter's docstring, then build the
converter.

Write the new Python script at:

```
4-SYSTEM/Skills/json-to-source-text/converters/<source_slug>.py
```

The script must expose a single function:

```python
def convert_json_to_source_text(json_path: str, output_path: str) -> None
```

and a CLI entry point so it can be run directly:

```bash
python converters/<source_slug>.py path/to/source.json path/to/output.md
```

Base the new converter on `json_to_source_text.py` (the generic template) —
copy and extend it rather than starting from scratch.

### What to customise

**3.1 Frontmatter mapping.** Map the JSON's top-level metadata fields to the
frontmatter required by `1-SOURCES/About Sources.md` §4. Required
minimum:

- `title` — `title` or `title_pali` or `title_sanskrit` etc.
- `language` — derived from the script/encoding of `content` (Pāli, Sanskrit, Tibetan, Chinese, English…)
- `script` — Devanāgarī, Roman-PTS, Unicode Tibetan, etc.
- `file_type` — `root-text` (this repo's current scope; `translation`/`commentary` for future use)
- `lang_tag` — see `1-SOURCES/About Sources.md` §12 (Sanskrit is `sk`, not `sa`)
- `verse_id_format` — usually `chapter-verse`; pick `verse` if there are no chapter divisions
- `source_description` — short prose describing where this came from (`"Tipitaka.org Mūla edition, exported {date}"`)
- `source_url` — original URL if recoverable from the JSON
- `source_filename` — keep the original filename for traceability

Any extra IDs the JSON carries (`source_id`, BDRC IDs, CBETA IDs, etc.)
should also be preserved as `other_ids` entries.

**3.2 Category routing.** For each distinct value of the category field
(`type`, `class`, `css_class`, etc.), assign a target role:

| Category role | Output |
|---|---|
| Chapter heading | `## N. {title} ^N-0` |
| Sub-section heading | `### N.M {title} ^N-M-0` |
| Body verse | `{content} ^N-V` where V increments per chapter |
| Pre-chapter material (homage, book title, scribal intro) | Place in `## 0. Introduction`, number `^0-1`, `^0-2`, … |
| Decorative / skip | omit |

Implement the routing as a dispatch table (`CATEGORY_TO_ROLE = {...}`) at the
top of the converter so it's easy to see and tweak.

**3.3 Heading IDs.** Per `4-SYSTEM/CLAUDE.md` §5a:

- `##` headings get `^chapter-0`
- `###` headings get `^chapter-section-0`
- Headings use `0` in the verse slot so they don't collide with verse IDs (verses never start at 0)
- Never emit the deprecated `^TOC-N` style.

**3.4 Verse numbering.** Restart verse counter at 1 for each chapter.
Sub-sections do **not** affect verse IDs — verses beneath a `###` still get
`^chapter-verse`, not `^chapter-section-verse`. A single verse can span
multiple subsections and headings — when a `####`/`#####` heading appears in
the middle of what the source treats as one numbered verse, emit the heading
at its structural position but do NOT restart, advance, or otherwise change
the verse counter; the verse's block ID lands on the last continuation line
after the heading.

For sources that carry an explicit per-verse number (e.g. tipitaka.org's
`583. …` prefixes), use that number directly as the verse part of the block
ID rather than an internal counter — this keeps source-N and block-ID
aligned and makes the "verses span subsections" case trivial. Unnumbered
prose between a heading and the next numbered verse is prepended to that
verse; unnumbered prose in a section the source itself left unlabelled is
emitted as a single block with no block ID (the structural heading is the
only anchor).

**3.5 Chapter 0 / pre-chapter handling.** If the JSON's first chapter
contains both prefatory material (homage, title lines, dedicatory verses)
and substantive authored content, split them: emit the prefatory material
under `## 0. Introduction ^0-0` and treat the authored chapter as Chapter 1
(renumbering all subsequent chapters). If the JSON's chapter 0 is *all*
prefatory, keep its numbering and just rename it `Introduction`.

**3.6 Output filename.** This repo's per-text contract expects the converted
file under `1-SOURCES/Text/`. If a converter needs to name an
intermediate file before the text ID is settled, use `[lang]-[text-slug].md`,
e.g. `pi-dhammasangani.md`, `sk-bodhicaryavatara.md` — no diacritics,
lowercase, hyphenated.

### Script template

The generic `json_to_source_text.py` provides:

- `load_metadata(data)` — extracts a minimum frontmatter dict from common top-level keys
- `format_frontmatter(meta)` — writes YAML
- `format_heading(level, num, title, section=None)` — emits a `## N. title ^N-0` or `### N.M title ^N-M-0` line
- `format_verse(text, chapter, verse)` — emits `text ^chapter-verse`
- `clean_text(s)` — strips whitespace and editorial brackets if needed
- `convert_json_to_source_text(json_path, output_path)` — orchestrates; override or extend

A new converter typically:
1. Imports `format_heading`, `format_verse`, `format_frontmatter` from the template
2. Defines `CATEGORY_TO_ROLE` mapping the source's category field to roles
3. Defines `extract_metadata(data) -> dict`
4. Defines `iter_blocks(data)` that yields `(role, content, chapter, [section_title])` tuples
5. Writes a thin `convert_json_to_source_text()` that walks `iter_blocks` and emits the markdown

---

## Step 4 — Run the Converter

Output goes to `0-INBOX/temp/` for review first:

```bash
python3 4-SYSTEM/Skills/json-to-source-text/converters/<source_slug>.py \
  <path-to-source>.json \
  0-INBOX/temp/<lang>-<text-slug>.md
```

Or, to avoid `.pyc` staleness on mounted filesystems:

```bash
python3 - << 'EOF'
import importlib.util
spec = importlib.util.spec_from_file_location("conv",
    "4-SYSTEM/Skills/json-to-source-text/converters/<source_slug>.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.convert_json_to_source_text(
    "<path-to-source>.json",
    "0-INBOX/temp/<lang>-<text-slug>.md")
EOF
```

Once reviewed and confirmed, copy or rename the file to
`1-SOURCES/Text/<file>.md`.

---

## Step 5 — Post-Conversion Review

### 5.1 Frontmatter

Verify the YAML block against `1-SOURCES/About Sources.md` §4:
- `source_description` is set
- `lang_tag`, `language`, `script` match the content
- `verse_id_format` is correct
- `source_url` and any external IDs are present if known

### 5.2 Block IDs

- Every chapter heading carries `^chapter-0`
- Every sub-section heading carries `^chapter-section-0`
- Every verse on its own line ends in `^chapter-verse`
- No zero-padding
- Verse numbers restart per chapter
- No `^TOC-N` anywhere (deprecated — `4-SYSTEM/Guidelines/annotation-conventions.md` §6)

Run a quick check:

```bash
grep -E "^\^|\^[0-9]+-[0-9]+( |$)" 0-INBOX/temp/<file>.md | head -20
```

### 5.3 Structure

- `## 0. Introduction` exists if there is any pre-chapter material
- Chapter headings are `##` and sub-sections are `###` (never `####`)
- The first chapter's first verse is `^1-1`, not `^1-0` or `^0-1`

### 5.4 Content fidelity

- Spot-check that `total_segments` in the JSON ≈ the number of lines with block IDs in the output (allowing for headings and any merged segments)
- Sample 3–5 segments from the inspector profile and confirm they appear at the expected location with the expected formatting in the output

---

## Reference Files

| File | Purpose |
|---|---|
| `json_inspector.py` | Profiles any JSON file; outputs schema, category fields, samples, suggested source slug |
| `json_to_source_text.py` | Generic template with shared formatting helpers; serves as the base for new converters |
| `converters/<source_slug>.py` | Source-specific converters (one per JSON schema convention) |

---

## Related References

- `4-SYSTEM/CLAUDE.md` §5–5b and `1-SOURCES/About Sources.md` §5 — the authoritative block-ID and heading rules. The converter output must conform to these.
- `1-SOURCES/About Sources.md` §4 — the authoritative frontmatter schema.
- `skills/format-root-text/SKILL.md` — for post-hoc cleanup of source files (this skill's output may benefit from a pass through that one, or through `format-tibetan-root-text` / `format-sanskrit-root-text` for those languages).

---

## Limitations

- **Footnotes and editorial brackets.** The JSON often carries text-critical apparatus inline (e.g. `[upādinnupādāniyā (syā.)]`). The generic template leaves these in place. Source-specific converters can normalise them (move to `[Ed: ...]` notes, drop, or keep inline) — decide per source.
- **Mixed-language content.** A single segment may contain both Pāli and Sanskrit, or Tibetan and Wylie. The converter emits the content verbatim; manual editing may be needed.
- **Verse vs. prose detection.** The JSON's category field rarely distinguishes verse from prose. The output treats every body segment as a "verse" for block-ID purposes — this is fine for the block-ID system but doesn't preserve metrical structure.
- **Unicode normalisation.** No NFC/NFD normalisation is applied. If downstream tools require a specific form, run a separate pass.

---
