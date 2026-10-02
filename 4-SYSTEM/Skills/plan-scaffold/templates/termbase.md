---
plan: <plan-name>
stream: <lang>
purpose: authoring
source_glossary: $GLOSSARIES/<src>-<tgt>.md
status: draft
---

# <Plan title> — `<lang>` termbase (authoring)

One chosen rendering per keyword that appears in this stream's day files. The
generator carries this table in full; it never picks a rendering mid-sentence.

Built by `glossary-select` from `$GLOSSARIES/<src>-<tgt>.md`, guided by
`requirements.md`. When no attested rendering is satisfactory, derive one from
the relevant `$LOCAL_WIKI` article and write the new rendering back to the
consolidated bilingual glossary as a new attestation row.

## Terms

| Source lemma | Rendering | Rationale | First used |
|---|---|---|---|
| `<lemma>` | <rendering> | <one line> | day <N> |

## Names and epithets

Proper names are kept; epithets and descriptive titles are rendered plainly.

| Source | Write | Not |
|---|---|---|
| `<epithet>` | <plain rendering> | <the jargon rendering to avoid> |

## Display names

<Only if the plan cites commentators, teachers or works by name. The machine id
is what the rails use; the display name is what the reader sees.>

| id | Display name | Order |
|---|---|---|
| `<machine-id>` | <Display Name (Work)> | 1 |

## Controlled vocabulary

<Category labels, section sub-labels, or any other fixed list the day files use.
Keep the list in one place — here — not duplicated in a skill.>

| Concept | Label in this stream |
|---|---|
| `<id>` | `<label>` |
