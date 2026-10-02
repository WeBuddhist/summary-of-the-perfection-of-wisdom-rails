---
name: term-localization
description: Translate a text's key terms in the term-localization table into the track's target languages, deriving each rendering from the commentary-based Meaning column rather than generic dictionary lookups.
---

# term-localization

This skill fills the translation columns of `2-RAILS/Termbases/term-localization.md`. For each term it reads the source-language term (the `<src-lang>` column) and the commentary-sourced definition (Meaning column) to determine the precise sense the term carries in this text, then produces a contextually accurate rendering in each target language. Renderings must be clear and accessible — natural in the target language, understandable to a non-specialist — while remaining fully faithful to the commentary's definition. When the Meaning cell contains multiple commentary quotations (two or more sources defining the term), the skill selects the rendering that best fits this text's context and register rather than averaging or listing all senses. The skill prevents mislocalization caused by using generic dictionary equivalents for polysemous source-language terms: the Meaning column is the authoritative disambiguator. When the Meaning cell is empty for a term, the skill flags the row and skips it rather than guessing from the source term alone.

The text's genre, audience and register — the criteria used to pick between competing senses — are **not** stated in this skill. They are declared once per vault in `4-SYSTEM/Guidelines/vault-annex.md`. Read that file before starting.

---

## Inputs

- **Term or term list** — one or more terms from the `<src-lang>` column of `2-RAILS/Termbases/term-localization.md`. If the user says "all" or supplies no restriction, process every row whose target language cell(s) are empty.
- **Source language** (`<src-lang>`) — the language of the term column, per `4-SYSTEM/Guidelines/vault-annex.md`. This is the column the Meaning definitions gloss.
- **Target languages** — the list of target-language columns to fill. This is an **input**, not a fixed set: it is whatever columns the table actually carries. When the user gives no list, fill every target column present in the table. The columns used in the worked example below — `En`, `Zh`, `Hin`, `Nep`, `Rus`, `Mon` — are a default example set, not a requirement.
- **The term table** — `2-RAILS/Termbases/term-localization.md` — the table to update.
- **`4-SYSTEM/Guidelines/vault-annex.md`** — for the text's genre, audience and register.

---

## Output

`2-RAILS/Termbases/term-localization.md` — modified in place. For each processed term, the relevant translation cells are filled with the rendered term in the target language.

---

## Output cell format

Each translation cell receives a **single rendered term or short phrase** — the localized equivalent of the source term as defined by the Meaning column. Do not include quotation marks, citations, or explanatory prose in translation cells. The cell must be suitable for use as a glossary entry. Prefer plain, natural phrasing over heavy technical jargon; a rendering that a thoughtful non-specialist can understand without a dictionary is preferred, provided it accurately reflects the commentary's definition.

The table's shape is: an index column, the source-language term column, the Meaning column, then one column per target language. Example with the default column set:

```
| S.No | <src-lang> | Meaning | En              | Zh      | Hin        | Nep        | Rus             | Mon            |
| ---- | ---------- | ------- | --------------- | ------- | ---------- | ---------- | --------------- | -------------- |
| N    | [term]     | [def]   | [English term]  | [汉字]  | [हिन्दी]   | [नेपाली]   | [Русский]       | [Монгол]       |
```

**Language-specific conventions.** The notes below are the defaults for the example column set. A vault that publishes into other languages adds its own row here and follows the same shape: name the attested translation tradition to prefer, name the script, and say what to do when no attested rendering exists.

- **En (English):** Use established English translation conventions for this text's tradition, preferring accessible modern renderings over archaic or heavily Sanskritised ones. Where no consensus exists, derive a rendering from the Meaning cell definition and mark it with `*`.
- **Zh (Chinese):** Use standard Chinese Buddhist canon equivalents where they exist. For terms without canon equivalents, use a descriptive Chinese phrase derived from the Meaning cell.
- **Hin (Hindi):** Use Sanskrit-origin Buddhist technical terms in Devanāgarī script where standard Sanskrit equivalents are established. Where no Sanskrit term applies, use a descriptive Hindi phrase.
- **Nep (Nepali):** Use Nepali Buddhist terminology in Devanāgarī script. Nepali terms often parallel Hindi/Sanskrit equivalents; distinguish where Nepali usage differs.
- **Rus (Russian):** Use established Russian Buddhist translation equivalents where attested. Transliterate Sanskrit loanwords in Cyrillic when no native Russian equivalent exists.
- **Mon (Mongolian):** Use classical Mongolian Buddhist terminology where attested in the Mongolian canon (Ganjur/Danjur). For terms without canonical Mongolian equivalents, derive a rendering from the Meaning cell. Write in traditional Mongolian Cyrillic script (Khalkha standard).

---

## Rules

1. **The Meaning column is the primary source.** Derive the rendering from the commentary definition in the Meaning cell, not from a generic bilingual dictionary or parametric knowledge alone. The Meaning cell resolves polysemy.
2. **Prioritise clarity without sacrificing accuracy.** Each rendering must be easy to understand in the target language — natural phrasing, no unnecessary jargon — but must still faithfully represent the sense given in the Meaning cell. If a simpler word captures the definition as well as a technical one, prefer the simpler word.
3. **When the Meaning cell contains multiple definitions, choose the one most fitting for this text.** If the Meaning cell includes quotations from two or more commentaries that give different or complementary senses, do not blend them or list all options. Read the definitions together, judge which sense is most appropriate to this text's genre, audience and register **as stated in `4-SYSTEM/Guidelines/vault-annex.md`**, and base the rendering on that sense. Note the choice in the end report.
4. **Skip empty Meaning cells.** If the Meaning cell for a row is blank, do not fill any translation cell for that row. Add the term to the skip list in the end report.
5. **Do not overwrite non-empty cells without explicit instruction.** If a target language cell already contains text, skip it unless the user says to overwrite or append.
6. **Do not modify the source-term or Meaning columns.** Only the target language columns may be changed by this skill.
7. **One rendering per cell.** Each cell holds a single term or short phrase. No definitions, citations, or explanatory brackets in the cell itself. If a term genuinely requires a parenthetical disambiguation, place it in parentheses directly after the rendering: e.g., `mind (aspirational)`.
8. **Flag novel renderings.** When a rendering is derived from the Meaning cell definition rather than from an attested translation convention, append `*` to the cell value: e.g., `vast field*`. Record all flagged renderings in the end report.
9. **Script fidelity.** Write each target language in the script its convention row names. Where a language has more than one script in use (Simplified vs Traditional Han, Cyrillic vs traditional Mongolian), follow the table's existing rows; if the table is empty, ask the user once and record the answer in the vault annex.
10. **Do not modify `1-SOURCES/` files.** This skill reads the table only; it never writes to source files.
11. **Batch safely.** When processing "all" terms, work in sequential row order. Do not skip rows silently — every row is either filled, skipped (empty Meaning), or skipped (cell already populated). All three cases are reported.

---

## Procedure

### Step 1 — Identify terms and target languages

1. Open `2-RAILS/Termbases/term-localization.md` and read the full table.
2. Read `4-SYSTEM/Guidelines/vault-annex.md` for the text's genre, audience and register.
3. If the user named specific terms, collect only those rows. If the user said "all" or gave no restriction, collect all rows.
4. Determine which target language columns to fill. Default: every target column the table carries.
5. For each row, check:
   a. Is the Meaning cell empty? → Add to skip list (reason: no definition).
   b. Is the target language cell already populated? → Add to skip list (reason: already filled), unless the user authorised overwriting.
   c. Otherwise → Add to the work list.

### Step 2 — Translate each term

For each row in the work list, in sequential order:

1. Read the source-language term (`<src-lang>` cell).
2. Read the Meaning cell. Count how many commentary quotations it contains.
   a. **One quotation:** that definition is the meaning to translate.
   b. **Two or more quotations:** read all of them. Identify which sense best fits this text — its genre, its audience, and its register as the vault annex states them. Select that sense as the basis for translation. Record the chosen commentary and your reasoning briefly in the end report.
3. From the selected meaning, identify the single key sense to translate. Prefer the most direct, natural way to express that sense in each target language; avoid technical terms when a plain equivalent captures the meaning equally well.
4. For each target language column being filled:
   a. Check whether an established canonical or scholarly rendering exists for this source term carrying this specific meaning.
   b. If an established rendering exists and is clear in the target language: use it (no `*`).
   c. If an established rendering exists but is heavily technical or obscure to non-specialists: assess whether a plainer equivalent is equally faithful. If so, use the plainer form and flag with `*`.
   d. If no established rendering exists: derive one from the selected definition and append `*`.
   e. Apply language-specific script and convention rules (§ Output cell format).
5. Record the proposed rendering for each column.

### Step 3 — Write results to the term table

1. Open `2-RAILS/Termbases/term-localization.md`.
2. For each row in the work list:
   a. Locate the row by S.No and source-term cell value.
   b. Fill each target language cell with the rendering from Step 2.
3. Write the updated file back to disk.
4. Do not reformat, reorder, or change spacing in any other part of the table.

### Step 4 — Report

After processing, report:
- How many rows were processed (translations filled).
- How many rows were skipped due to empty Meaning cells (list the terms).
- How many rows were skipped because target cells were already populated (list the terms).
- How many cells received a flagged rendering (`*`) and in which languages.

---

## Completion check

- [ ] Only the target language columns were modified; the source-term and Meaning columns are unchanged
- [ ] No translation cell was filled for a row with an empty Meaning cell
- [ ] No non-empty cell was overwritten without explicit user authorisation
- [ ] All renderings reflect the sense given in the Meaning column, not generic dictionary defaults
- [ ] Renderings are clear and accessible in each target language, not unnecessarily technical or archaic
- [ ] For rows with multiple Meaning quotations, one sense was selected on the genre/audience/register stated in `4-SYSTEM/Guidelines/vault-annex.md`; the choice is noted in the end report
- [ ] Novel or simplified renderings are flagged with `*`
- [ ] Script conventions are correct for every target language filled
- [ ] `2-RAILS/Termbases/term-localization.md` was saved back to disk with all changes applied
- [ ] End report lists all processed, skipped, flagged, and multi-definition selection rows
