---
day: <N>
chapter: <C>
verses: "<C>-<start> to <C>-<end>"
date: <YYYY-MM-DD>
transformation_type: plan-session
stream: <lang>
translated_from: <authoring-stream day file path — translation streams only; omit in the authoring stream>
verse_source: <the file the verse text was inlined from, by block ID>
context_packages:
  - $VERSES/<C>-<start>.md
pending_terms: []
generation_date: <YYYY-MM-DD>
generated_by: <plan-day-generate | plan-day-translate>
status: draft
---

<!--
  One block per section id declared in `About <plan-name>.md`, in the declared
  order, each under the heading declared for this stream. Delete this comment
  and every guidance line before saving.

  Fixed      → copied character-for-character from `<lang>/assets/liturgy.md`
  Extracted  → copied verbatim from `verse_source` by block ID, line breaks kept
  Generated  → composed for this day inside its ceiling, voice and formula
  Translated → rendered from the matching section of `translated_from`

  Verse text is INLINED verbatim, with its block ID, and never retyped from
  memory. Use `![[…]]` transclusion only when the plan declares
  `consumer: obsidian`.

  A section that may legitimately be absent is dropped heading and all — and the
  absence is stated in the reply, never silently.

  No translation note, no generation note, no QA commentary goes in this file.
  The day file is a reader-facing document. Everything a reviewer needs is
  reported in the reply.

  `status:` is always `draft`. Only a domain specialist sets `complete`.
-->

# <Day title — optional, per the plan's naming convention>

## <heading for section id `<id>`>

<content>

## <heading for section id `<id>`>

<verse text, verbatim, line breaks preserved> ^<C>-<V>
