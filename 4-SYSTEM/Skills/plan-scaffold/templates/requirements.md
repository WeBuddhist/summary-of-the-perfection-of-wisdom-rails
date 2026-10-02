---
plan: <plan-name>
stream: <lang>
role: authoring | translation
language: <language name>
status: draft
---

# <Plan title> — <language> stream: style contract

> **Write this file in `<language>`, not in English.** It is read by whoever
> writes and reviews this stream's day files, and its rules are binding.
> The section *list* is declared once in `About <plan-name>.md`; this file says
> how this language renders each section.

## 1. Audience and register

- **Reader:** <who they are in this language market; prior knowledge>
- **Reading level:** <e.g. CEFR A2–B1 / plain 8th-grade / scholarly>
- **Sentence length:** <e.g. one idea per sentence, under 20 words>
- **Voice:** <active / passive, address form, honorific policy>

State the reading level explicitly. A generated section drifts into the
register of whatever source material was fed to it unless the register rule is
restated for every section.

## 2. Per-section rendering conventions

One entry per section id from `About <plan-name>.md`.

### `<section id>` — `<heading in this language>`

- **Type:** Fixed | Extracted | Generated | Translated
- **Voice:** <neutral / first person / second person>
- **Ceiling:** <N words | N syllables> — a ceiling, never a target
- **Required formula:** `<verbatim opening or closing phrase>` | none
- **Grounding:** <which file, which layer>
- **Rules:** <what this section must do, and what belongs to a different
  section. Name the failure you are guarding against.>

## 3. Terms and names

- Genuine terms of art and proper names to keep as-is: <list, or "see termbase">
- Epithets and descriptive titles are rendered **plainly**, not as jargon. The
  scholarly alternative is not the right answer in this stream. Full tables in
  `termbase.md`.
- Glossing policy: <gloss once per file / never gloss / footnote>
- Diacritics: <policy, and the exemptions — e.g. verbatim verse quotations and
  italicised work titles keep whatever the source has>

## 4. Forbidden elements

Read by `plan-day-qa`. Each line is a checkable rule.

- <e.g. no em-dashes in body prose>
- <e.g. no emojis in body text>
- <e.g. no glossary block at the end of a day>
- <e.g. no sub-headings below `##`>
- <e.g. no horizontal rules between sections>
- <e.g. no rhetorical question-and-answer>
- <e.g. no consequence stated without naming who it falls on>
- <e.g. no importance asserted ("great", "profound") instead of shown>

## 5. Word-count bands (diagnostics, not targets)

| Section | Band |
|---|---|
| `<id>` | <low>–<high> <words/syllables> |

A section outside its band is **reported**, not padded or trimmed. For a
Translated section the length is set by the source; changing it means adding or
cutting content the source does not have.

## 6. Language-specific grammar rules

<Rules that only this language needs: ending particles, honorific forms,
numeral systems, clause-connection ladder, contamination patterns from a
neighbouring language, transliteration scheme. Give tables, with a right and a
wrong column, so the rule is mechanically checkable.>

## 7. Communications style

- Push notification: <max length, tone, what it may not be>
- Social copy: <max length, platform conventions>
- Email subject: <max length>
