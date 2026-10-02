---
plan: <plan-name>
stream: <lang>
purpose: translation
forked_from: $TRANSFORMATIONS/Plans/<plan-name>/<lang>/termbase.md
status: draft
---

# <Plan title> — `<lang>` termbase (translation fork)

This is the table `plan-day-translate` obeys. `termbase.md` governs **authored**
day content and carries authoring-only rules; this fork governs **translated**
day content. Two unlinked termbases in one stream drift within a chapter — so
this file states only what differs, and `forked_from:` above says where the rest
comes from.

## Terms that differ from the authoring termbase

| Source lemma | Rendering here | Why it differs from `termbase.md` |
|---|---|---|
| `<lemma>` | <rendering> | <one line> |

## Names and epithets

Keep genuine terms of art and proper names. Render epithets and descriptive
titles plainly — translating these as jargon is what makes a day unreadable,
and it is usually done out of reverence rather than necessity.

| Source | Write | Not |
|---|---|---|
| `<epithet>` | <plain rendering> | <the jargon rendering> |

## Sub-block labels

The exact labels this stream writes for the authoring stream's labelled
sub-blocks. `plan-day-translate` matches these by text.

| Source label | Label in this stream |
|---|---|
| `<source label>` | `**<label>:**` |

## Practice-category labels

The controlled vocabulary lives here, not in any skill file — duplicating it
would create two places to edit and two places to drift. The category list
itself is declared in `About <plan-name>.md`; this table gives each category's
rendering in this language.

| Category (authoring language) | Label in this stream |
|---|---|
| `<category>` | `<label>` |

A category not in this table is a stop: propose a rendering, log it under
Pending terms, and ask before writing the day.

## Diacritics policy

<e.g. none in body prose. Exemptions: verse quotations reproduced verbatim keep
whatever the source has; the italicised title of a cited work keeps its
diacritics. The distinction is between a term used in prose and a title being
cited.>

## Pending terms

A pending term is not a permanent state. When a human approves one, it moves
into the table above, drops off this list, and is cleared from the
`pending_terms:` of any day file that carries it the next time that file is
touched. Before generating a new day, check whether a term it needs is already
pending from an earlier day and **reuse that rendering** rather than inventing a
second one. An entry older than one chapter of generation means the review step
is not happening — say so when reporting.

| Source term | Proposed rendering | First appeared | Status |
|---|---|---|---|
| `<term>` | <rendering> | day <N> | pending |
