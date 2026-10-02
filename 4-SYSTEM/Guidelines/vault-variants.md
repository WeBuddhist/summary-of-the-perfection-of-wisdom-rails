# Vault variants — when the default shape does not fit

The methodology assumes the common case: **one classical text, in one source language, with a commentary tradition, addressed by chapter and verse.** Most vaults are that.

Some are not. Three variants have been built and are documented here so that a new vault of the same kind starts from what was learned rather than rediscovering it. A variant is not a licence to improvise: whatever a vault does differently is **declared in its annex** ([`vault-annex.md`](vault-annex.md)) and everything not declared follows the defaults.

The block-ID deviations named below are the registered ones listed in [`annotation-conventions.md`](annotation-conventions.md) §7.

---

## 1. Collection vault — many short texts

*A liturgy corpus, a sādhana collection, a story anthology: dozens or hundreds of short, independent, often performed texts rather than one long treatise.*

**The unit of work is the text, not the verse.**

| Default | Collection variant |
|---|---|
| `2-RAILS/Verses/<verse-id>.md` is the primary rail | `2-RAILS/Texts/<text-id>.md` is the primary rail — one package per text: what it is, which tradition and lineage use it, its function, when it is used, what it accompanies |
| `2-RAILS/Sections/` per TOC node | `Sections/` only for the longer multi-part texts |
| `Local-Wiki/` per key term of one text | `Local-Wiki/` centred on **recurring formulae** — a term article is amortised across many texts, which makes it far more valuable here |
| `1-SOURCES/Commentaries/` is central | There may be **no commentaries at all**. A skill whose input folder is missing says so and stops |
| `^chapter-verse` | **Flat `^N`** per text (`verse_id_format: verse`), or hierarchical `^k-j-n` with `^k-0` / `^k-j-0` heading slots where a text has internal sections |

**A machine-readable catalog beside the texts.** A collection needs a registry the notes themselves do not carry: `1-SOURCES/<corpus>-catalog.json`, mapping rank ↔ filename ↔ title ↔ any external or backend IDs ↔ per-text metadata (including a `layout: verse | prose` field, which drives formatting and review). Keeping IDs in the catalog rather than in each note means a text can be re-generated without losing its identity.

**Empty metadata values are deliberate.** A key with no value means the upstream source records none. Never fill it with a guess — an empty key is a truthful "not recorded", and a guess is a fabrication that survives into the catalog.

**The inbox may be the master copy.** In a collection built by script, `0-INBOX/` can hold the expert-segmented source of truth and `1-SOURCES/` can be *generated* from it. That inverts the default (inbox = scratch) and must be stated in the annex, because it changes one rule: hand-edits to a generated file are not preserved across a regeneration, so **fix the formatter, not the output**. Nothing downstream ever cites `0-INBOX/` either way.

**Never delete and re-create a text.** Its ID is referenced everywhere. Update in place.

---

## 2. Multi-book canon — Bible-style addressing

*A canonical collection addressed by book and verse, with a continuous verse counter per book: Pāli nikāyas, Abhidhamma books, and similar.*

Declared as `verse_id_format: book-verse`. The registered deviations this needs:

- **`^<book>-<verse>` with a single continuous counter per book.** The counter does **not** restart at any heading boundary. The counter value is the source's own verse number, not a running tally the formatter invents.
- **More than four heading levels.** `#` piṭaka / collection, `##` book, `###`–`#####` the book's own divisions, each heading taking the full path plus `-0`.
- **Letter-suffixed sub-namespaces** where a section's children are lettered in the tradition rather than numbered: `^1-0a-1`, `^1-0b-7`.
- **Verse grouping.** A body line that opens with a source verse number starts a new verse; unnumbered continuation lines merge into the current verse, and the block ID goes on the verse's **final** line.
- **Verses spanning headings.** A single source verse may run across several sub-headings. The headings are emitted at their structural position but do not restart or advance the verse counter.
- **Unlabelled sections** are emitted as one block with no verse-level ID — only the heading is addressable. This preserves the invariant that every `^<book>-<verse>` corresponds to a real verse in the source.
- **Sub-verse citations** (`^1-1a`, `^1-1b`) are never generated in `1-SOURCES/`. Sub-verse addressing is added at citation time in `2-RAILS/`.

Tier vocabulary for the commentary roster is the tradition's own (commentary / sub-commentary / sub-sub-commentary), and the annex's tier order drives the order of the Traditional Interpretation sections in a verse package.

---

## 3. Parallel-witness corpus — the same work in two languages

*A work surviving in two canonical languages — for example a Tibetan and a Chinese witness of the same treatise — where the alignment between them is itself part of the material.*

- **Both witnesses live in the same folder as the work they belong to.** A commentary in two languages is two files in `1-SOURCES/Commentaries/`, named by language tag, not split across folders. The frontmatter field `aligned_with:` records the counterpart.
- **Alignment is by ID, never by position.** Segments are joined on their identifier; a pair that does not join is reported, not guessed into place. Where the intake carries alignment information (numbering, footnote anchors, highlighting), preserve it through the conversion rather than re-deriving it later.
- **The parallel is expressed by transclusion**: each segment of the second witness is preceded by a transclusion of its counterpart in the first.
- **Script variants need their own tags** beyond the defaults — traditional, simplified and modern renderings of the same language are different files with different tags, and an `edition_variant:` frontmatter field records which.
- **Catalog identifiers matter more than usual.** A work known in several canons carries each canon's identifier in frontmatter, plus a vault-internal `work_id` that joins them.

**Sheet-driven intake.** A corpus assembled from a shared spreadsheet gets a two-step intake: a skill writes one inbox file per row (with a manifest and a pending list), a human reviews, and a second skill promotes the reviewed files into `1-SOURCES/` — creating whole files, never editing existing ones in place. The tally of what has been promoted lives in a generated inventory file that is regenerated rather than hand-edited.

---

## What every variant still owes

Whatever a vault changes, these do not move:

- The one-way citation chain, `1-SOURCES/ → 2-RAILS/ → 3-TRANSFORMATIONS/`.
- `1-SOURCES/` as the citation floor: structural additions only, no interpretation.
- Block IDs as the sole verse-level linking mechanism, with `verse_id_format` declared per file so a parser never has to guess.
- The `status` lifecycle, and a domain specialist — never the LLM — setting `complete`.
- Divergences recorded, never flattened.

---

## Where to look next

- [`vault-annex.md`](vault-annex.md) — where this vault declares its own variant and deviations.
- [`annotation-conventions.md`](annotation-conventions.md) §7 — the registered block-ID deviations in full.
- [`0-VAULT-Structure.md`](0-VAULT-Structure.md) — the default architecture these vary from.
