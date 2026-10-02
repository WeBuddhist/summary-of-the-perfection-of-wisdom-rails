# Worked example — a six-section Tibetan day (illustrative only)

**This file is an example, not a contract.** Everything below is specific to one
plan in one vault (a 365-day Tibetan practice arc over the
*Bodhisattvacaryāvatāra*). It is reproduced here so a new plan's author can see
what a filled-in section declaration looks like end to end. **Do not copy any
heading, liturgy text, category or ceiling from this file into another plan** —
they belong to that plan's `About <plan-name>.md` and `assets/liturgy.md`, and
another text's plan will declare different ones.

---

## 1. The declaration, filled in

| id | type | voice | ceiling | formula | absent | grounding |
|---|---|---|---|---|---|---|
| `refuge` | Fixed | none | — | — | required | `assets/liturgy.md` |
| `opening` | Generated | neutral | — (1–2 sentences) | a hand-built citation phrase naming chapter and verse ordinals | required | the day's verses + synthesis layer |
| `verses` | Extracted | none | — | — | required | the root text, by block ID |
| `commentary` | Generated | neutral | 300 syllables | a fixed opening phrase with a slot for story / point / simile / citation | may be absent | the rails' commentary, quotation and teaching-point layers |
| `dedication` | Fixed | none | — | — | required | `assets/liturgy.md` |
| `practice` | Generated | first person | 30 syllables (commitment sub-block only) | category tag `_(…)_` opening the explanation | required | the rails' teaching-point and practical-application layers |

Headings by stream (one column per language) and the heading-alias table live
beside this in `About <plan-name>.md`.

The practice section has three sub-blocks: the commitment (≤ 30 syllables, first
person, "today I will …"), the explanation (opens with the category tag), and
the verse the practice was built on — inserted from the already-verified
extracted text, never retyped.

## 2. Why each column earns its place

- **Fixed** sections drift the moment they are retyped. Keeping them in one file
  and copying character-for-character is the whole mechanism.
- The **citation phrase** in the opening section is hand-built from an ordinal
  table before generation, because number words in this language are irregular:
  the forms for 35th and 45th look similar but take different decade prefixes.
  Guessing one is the single most frequent error in this plan's history.
- The **commentary** section's "may be absent" is real. When the commentaries
  offer nothing beyond ordinary verse explanation, the section is correctly left
  out. Filling it with plausible general knowledge is the failure this column
  exists to prevent.
- The **syllable** unit is used because the stream's script is tsheg-delimited;
  an alphabetic stream would declare a word ceiling instead. The unit lives in
  the declaration precisely so the checker does not have to guess.
- The **practice** ceiling applies only to the commitment sub-block, which is
  why the spec scopes the count with `count_from_label`.

## 3. A language-specific grammar rule (belongs in `requirements.md`, not here)

This plan's stream has an ending-particle rule: when a sentence-final verb closes
with one of ten suffix letters, the matching particle must be used, and the
sentence must close with a double shad rather than a single one. Models get this
wrong reliably, and correcting it is mechanical cleanup rather than authorship.

The rule is written as a **table with a right and a wrong column** in
`<lang>/requirements.md` §6, so it can be checked item by item — not narrated in
prose, and not carried inside a skill. A different language's stream will have a
different §6 (honorific register, numeral system, clause-connection ladder, or
nothing at all).

## 4. The nine practice categories of that plan

Listed here only to show the *shape* of a category list: a small closed set, in
the authoring language, each mapping to a recognisable kind of action —
avoiding harm, doing good, taming the mind, and one per perfection (generosity,
ethics, patience, diligence, meditation, wisdom).

Another plan's list will be different, and lives in its own
`About <plan-name>.md`. A category that is not on the plan's list is a stop:
propose it, log it, and ask.

## 5. Pre-assigned teaching mode

A sibling plan in the same vault runs `commentary-mode: teaching-file`: a single
teacher's own commentary is pre-assigned to days in a
`teaching-assignment.md`, and each day's blocks are copied **verbatim** into the
commentary section under the teaching title from that file, closed with a
citation line naming the blocks used. Nothing is paraphrased, summarised, or
supplemented — the value of that mode is that the teaching reaches the reader in
the teacher's own words.
