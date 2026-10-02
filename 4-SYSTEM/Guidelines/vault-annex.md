# Vault Annex — [text-slug] conventions

The methodology guidelines (`0-VAULT-Structure.md`, `../../1-SOURCES/About Sources.md`, `../../2-RAILS/About Rails.md`, `../../3-TRANSFORMATIONS/About Transformations.md`) are **text-agnostic** — they apply to any Railroads vault built on any classical text. This annex records the conventions that are specific to *this* vault: **[name of text]**.

When the Guidelines and this annex disagree on a vault-specific detail, this annex wins — **for the points it actually states**. Everything it does not state follows the defaults unchanged.

This file may be renamed for its text (`<text-slug>-annex.md`) as long as `README.md` and `4-SYSTEM/CLAUDE.md` link to it.

> **Template instructions:** Fill in each section below, replacing all `[placeholder]` text. Delete this instruction block when done.

---

## 1. The text

This vault serves **[name of text]** — [one-sentence description of the text and its tradition].

Source-text files in `1-SOURCES/Text/` correspond to the following books / volumes:

| Order | Book / Volume | Filename |
| ----- | ------------- | -------- |
| 1 | [Title] | `[lang]-[slug].md` |
| 2 | [Title] | `[lang]-[slug].md` |

Only books that have been ingested are present in the folder. The primary text currently being railed out is **[book / chapter]**.

---

## 2. Addressing scheme

[Describe how block IDs are structured for this text. Use one of the standard schemes from `1-SOURCES/About Sources.md` §5, or document a custom scheme here if the text's structure requires it.]

**`verse_id_format`:** `[chapter-verse | verse | book-chapter-verse | book-verse | custom]`

**Format example:** `^[example]`

### Heading hierarchy

| Markdown | Role | Anchor |
| -------- | ---- | ------ |
| `#` | [e.g. Piṭaka / collection] | `^[slug]-0` |
| `##` | [e.g. Book / volume] | `^[book]-0` |
| `###` | [e.g. Chapter / major section] | `^[book]-[ch]-0` |
| `####` | [Sub-section] | `^[book]-[ch]-[s]-0` |

### Verse numbering rule

[Describe whether verse numbers restart at each chapter boundary, or run continuously through a book, and any exceptions. State the rule even when it is the default — a reader should not have to infer it.]

### ⚑ Registered deviations — overrides of the default conventions

[List every point where this vault departs from [`annotation-conventions.md`](annotation-conventions.md), one subsection each, with a date. A deviation that is not recorded here is a defect, not a convention. Delete this section if there are none.

Format each one as: what the default says, what this vault does instead, and **why** — the reason is what stops a later contributor "fixing" it back. For example:

### ⚑ [Deviation name] — overrides `annotation-conventions.md` §[n] (registered [YYYY-MM-DD])

[What the default rule is. What this vault does instead. Which files it applies to. Why the text's own structure requires it.]

The recognised deviation types are listed in `annotation-conventions.md` §7: intro / back-matter zones, Bible-style `book-verse`, letter sub-namespaces, and flat `^N` for collections.]

### Re-segmentation and ID-migration log

[Every change to an addressing scheme after rails already cited it. One dated entry each: what changed, where the pre-change file is kept, and what has to be re-checked.

This section exists because a block ID is a citation. Re-segmenting a file silently invalidates every rail that cited it, and the only defence is a written record. Delete this section while the vault is new and nothing has been re-segmented.

**[YYYY-MM-DD] [What changed].** [Which files. Where the backup lives, e.g. `0-INBOX/migration-backups/<date>/`. The consequence: "any rail written before this date that cites a block ID in these files is citing the old scheme and must be re-checked."]]

---

## 2a. Canonical spine slots — *optional, only if this vault runs the claims pipeline*

[The **spine** is the root text's own structure expressed as a list of stable slot IDs. It is the shared coordinate system every commentary is mapped onto, and the unit that claims consolidation works in: one topic page per slot.

**This registry is the only source of slot IDs.** A skill may not coin a slot locally; if a commentary needs one that is not listed here, a human contributor registers it here first. Slot IDs are stable forever — a topic page's filename comes from its slot, so renaming one orphans its page.

### Spine-proper slots — derived from the root text's own structure

| Slot | Root anchor | Content |
| ---- | ----------- | ------- |
| `[slot-id]` | `^[block-id]` | [what this slot holds] |

### Global slots — recurring material outside the root's sequence

[Bodies of commentarial material that are not root-text blocks: a commentary's own account of the text's structure, an origin narrative given as its own section, and so on. Added as the corpus is mapped, never invented per commentary.]

| Slot | Content | First observed |
| ---- | ------- | -------------- |
| `[slot-id]` | [what it holds] | [where] |

**Not every body of material belongs to a slot.** A commentary's front matter, colophon, ritual appendices and story collections are dispositioned as *unmapped nodes*. That is a legitimate outcome: the claims are preserved, they simply feed no topic page.

**Granularity.** One slot per unit of the root's own structure, at whatever level keeps a topic page under roughly 40–50 claims. For a long treatise that is a chapter or a verse group; for a short praise it may be a single stanza.]

---

## 3. Registered commentary IDs

Every commentary file in `1-SOURCES/Commentaries/` declares a `registered_id` in its frontmatter. That short ID is the only string used to attribute claims to the commentary throughout `2-RAILS/`.

Once assigned, a `registered_id` never changes. New commentaries must be added to the roster below before their `registered_id` is used in any rail.

| `registered_id` | Author / Title | Tier | School or tradition | `book_id` | Language | File |
| --------------- | -------------- | ---- | ------------------- | --------- | -------- | ---- |
| `[short-id]` | [Author, or the commentary's title] | [commentary \| sub-commentary \| …] | [School, or "unaffiliated"] | `[CODE]` | [Language] | `1-SOURCES/Commentaries/[lang]-[slug].md` |

Add a `Role` column where the commentaries do different jobs — annotation, story, scholarly exposition, word-commentary — because the verse-package skills need to know which commentary supplies which layer.

**Tier ordering** within a verse package's Traditional Interpretation section: [describe the order commentaries are presented in].

Where the text has **no hierarchical commentary tradition** — a set of independent works from several schools, rather than one root commentary with sub-commentaries — say so and give a grouping rule instead (for example, by school in the order this roster lists them, and within a school by the roster's own order). Do not invent a "the real commentary is X" hierarchy that the tradition does not have.

**ID migrations.** A `registered_id` never changes. If a human contributor directs one to change anyway — an author is identified, a placeholder is retired — record the migration here with its date, the old and new IDs, and confirmation that every live file and filename was migrated in one pass. The never-changes rule otherwise stands.

---

## 4. Language tracks

| Tag | Language | Translation track | Plan stream |
| --- | -------- | ----------------- | ----------- |
| `[src-tag]` | [Source language] | — (source) | `days/[tag]/` (if applicable) |
| `[tgt-tag]` | [Target language 1] | `[lang]-[descriptor]/` | — |
| `[tgt-tag]` | [Target language 2] | `[lang]-[descriptor]/` | — |

### Analysis language per rail section

[State which language each part of `2-RAILS/` is written in. The default is: Traditional Interpretation paraphrases and Translation Notes in English, everything else — AI Overview, Disambiguated Restatement, Local-Wiki articles, Key Concepts — in the original language. Record here if this vault differs, and for which sections.]

Each translation track's `requirements.md` is written in its own target language. New tracks are added by creating `Translations/[lang]-[descriptor]/` and running the `glossary-select` skill from the consolidated `2-RAILS/Bilingual-Glossaries/[src]-[tgt].md`.

---

## 5. Bilingual glossary pairs

The consolidated bilingual glossaries in `2-RAILS/Bilingual-Glossaries/` cover the following source→target combinations:

| File | Source language | Target language | Status |
| ---- | --------------- | --------------- | ------ |
| `[src]-[tgt].md` | [Source] | [Target] | `draft` |

---

## 6. Active transformation tracks

| Track | Category | Status |
| ----- | -------- | ------ |
| `[lang]-[descriptor]` | Translation | `draft` |
| `[plan-id]` | Plan | `draft` |

---

## 6a. Sanctioned exceptions to the citation chain — *optional*

[The citation chain (`1-SOURCES/ → 2-RAILS/ → 3-TRANSFORMATIONS/`) has no general exceptions. A specific, bounded one may be granted to a pipeline that carries an equivalent guarantee of its own — for example, a generator that reaches directly into `1-SOURCES/` but verifies every quotation character-for-character against its cited source before its output can pass.

Record each one here: what reaches past the rails, what the substitute guarantee is, and which document governs that output instead of `About Transformations.md`. An exception that is not recorded here is a violation. Delete this section if there are none.]

---

## 7. Source-language tags used in this vault

| Tag | Script / System | Use in this vault |
| --- | --------------- | ----------------- |
| `-[tag]` | [Script] | [When used] |

The default for every [language] source is `-[default-tag]`.

---

## 8. Where to look next

- [`0-VAULT-Structure.md`](0-VAULT-Structure.md) — the architecture in full.
- [`../../1-SOURCES/About Sources.md`](../../1-SOURCES/About%20Sources.md) — source-file rules.
- [`../../2-RAILS/About Rails.md`](../../2-RAILS/About%20Rails.md) — rails schema.
- [`../../3-TRANSFORMATIONS/About Transformations.md`](../../3-TRANSFORMATIONS/About%20Transformations.md) — track and output rules.
- [`annotation-conventions.md`](annotation-conventions.md) — the default block-ID conventions this annex may register deviations from.
- [`vault-variants.md`](vault-variants.md) — the three documented vault shapes, if this vault is not the common case.
- [`../CLAUDE.md`](../CLAUDE.md) — the operational quick-reference. *This annex overrides it on the points recorded above.*
- [Top-level `README.md`](../../README.md) — pipeline overview and reading paths.
