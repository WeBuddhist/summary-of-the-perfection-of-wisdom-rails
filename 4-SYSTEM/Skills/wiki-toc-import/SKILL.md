---
name: wiki-toc-import
description: Take a text's table of contents from its proofread Wikisource Index page (or, failing that, its Wikipedia article) and apply it to the source files as headings with block IDs — the root text, its translations (headings in each file's own language) and any commentary that has its own Index page — replacing a TOC that is missing or too granular. Use when asked to "get the TOC from Wikisource", "use the Wikisource/Wikipedia table of contents", "fix the TOC with the wiki page", "the TOC is too granular, use the dkar chag on Wikisource", or given a sheet of Wikisource/Wikipedia links for a text and its commentaries.
profile: rails-vault
---

# wiki-toc-import

Builds an **outline file** from a published table of contents — preferably the one on a text's proofread **Wikisource Index page**, where every heading stands inline in the page text right before the passage it opens — pinned to revisions, each node placed at a row of the text, with a label per language. `aligned-corpus-intake` then applies it (`toc.kind: outline`), so headings, block IDs and every transclusion into the file are regenerated in one deterministic build. It exists because an outline generated from a commentary's own *sa bcad* is often far too granular for a root text, and because a heading copied across languages must be rendered in each file's own language. Correct output: the Index's headings, and no others, stand exactly where the Index puts them; ids follow them (`^<path>-0` headings, `^<top>-<n>` blocks); the verifier reports no lost letter and no dangling transclusion; and every transclusion that changed id resolves to the same text as before.

---

## Inputs

| Input | Where | Notes |
|---|---|---|
| The TOC source per text | a sheet row or the user | **Wikisource Index page** (`Index:<file>.pdf`, the sheet's "Wikisource Link") is the default. A Wikipedia article is a fallback only when the user asks for it — its outline is a summary written about the text, not the text's own TOC. A Wikisource *transclusion* page is not used: the Index carries the same TOC with the headings' exact positions. |
| Which works it applies to | the vault's intake manifest (`0-INBOX/raw-data/intake-manifest.yaml`) | Root Index → the root work and every work paired with it by rows. Commentary Index → that commentary only — and only if it is in the vault: match by title **and** author against `1-SOURCES/Commentaries/*.md`. Report the rest; never ingest a new text here. |
| Labels for other languages | the translations' own vocabulary | The Index gives one language; a translation's headings are editorial renderings, recorded as such. |

The skill needs a vault built by `aligned-corpus-intake` with the `md_rows` adapter (row-aligned texts + manifest). Without one it stops and says so.

## Output

- `2-RAILS/Sections/Raw/toc-wikisource/<outline-id>.md` (or `toc-wikipedia/` for the fallback) — one outline file per source TOC; `<outline-id>` = the commentary's `registered_id`, or the root's slug.
- In the manifest, on the works concerned: `toc: {kind: outline, file: …, note: …}`; `row_splits` where a heading falls inside a row (human-decided); `supplement_rows` where a TOC section's text is missing from the corpus (human-decided).
- Rebuilt `1-SOURCES/` files and sidecars (by `aligned-corpus-intake`, never by hand), with every transclusion into them regenerated.
- An ID-migration entry in the vault annex.

---

## Output file format

```markdown
---
outline_id: <id>
registered_id: <commentary id>          # commentaries only
source: wikisource.org
index_page: Index:<file>.pdf
index_url: <url>
index_revid: <n>                        # the Index revision the TOC was read from
edition: <edition the Index reproduces>
heading_pages:                          # the Page: pages carrying the headings, pinned
- {page: "Page:<file>.pdf/1", revid: <n>, headings: ["1", "2"]}
retrieved: '<yyyy-mm-dd>'
placed_on: <manifest work key whose rows start_row counts>
placed_on_text: <raw_root>/<that work's text file>
placed_on_sha1: <sha1 of that raw file>  # the build refuses a stale placement
applied_to: [<work keys>]
labels:
  bo: verbatim from the Index's table of contents (numbers dropped)
  sa: editorial translation …           # one line per language, saying where it came from
placement: <how: mechanical letter match / placement pass; who checked>
replaces: <previous TOC source, if any>
status: complete
---

# <title> — outline from the Wikisource Index

<What it is, which rows precede node 1, any split rows and added rows and why, a table node | labels | rows | text after the heading.>

```yaml
nodes:
- path: "1"
  start_row: "2"                         # a row, or "N.k" = part k of a split row
  labels: {bo: མདོའི་གླེང་གཞི།, sa: निदानम्, zh: 序分}
  clause: <first words after the heading, verbatim from the row>
```
```

The build reads only the frontmatter and the `yaml` block: `path` (decimal, nesting by dots), `start_row` (a lettered row of `placed_on_text`, a declared split part `N.k`, or a supplement row; in order), `labels` (one per `lang_tag` of every work in `applied_to`).

Manifest fields the outline may need (on the work it is placed on):

```yaml
row_splits:                       # a heading inside a row — the row is cut before each clause
- row: 10
  at: [<clause verbatim, found once in the row>, …]
  targets: [[0], [1], []]         # per part: indices into the row's own transclusion targets
  reason: …
  decided_by: <the human who decided>
  date: 'yyyy-mm-dd'
supplement_rows:                  # TOC section whose text the corpus lacks — added from the source
- row: 33                         # numbered after the last raw row
  text: <verbatim>
  source: <page, revision, edition>
  reason: …
  decided_by: <the human who decided>
  date: 'yyyy-mm-dd'
```

---

## Rules

1. **Labels are the source's, verbatim** in its language — markup and section numbers removed, nothing reworded, no node added or dropped.
2. **Every translation gets headings in its own language**, never the source language's. They are editorial: use the translation's own vocabulary where it has a fitting word, and say so in `labels:`.
3. **Pin revisions** — the Index page and every Page: page that carries a heading.
4. **Place where the source places.** On Wikisource the heading's position in the proofread page decides; it is found in our text by letters. Never move a heading to a "nicer" row.
5. **A heading inside a row needs a human decision.** Either split the row there (`row_splits`; each root segment the row transcludes is shown once, before the first part that comments on it) or keep the row whole — ask; never split on your own.
6. **Missing text needs a human decision.** If a TOC section's text is absent from the corpus (e.g. a translators' colophon), ask whether to add it from the source (`supplement_rows`, with provenance) or leave that section without a heading.
7. **Never edit `1-SOURCES/` by hand.** Change the manifest and rebuild; the build regenerates ids and every transclusion together.
8. **Apply only to works in the vault.** A page whose text is not in the vault is reported, not ingested.
9. **No interpretive claim** enters `1-SOURCES/`: the outline file in `2-RAILS/` carries provenance and reasoning.
10. **Regenerating a protected file** (`protected: true`) needs human confirmation first.

---

## Procedure

1. **Match pages to works.** For each link, compare title and author with the manifest works and `1-SOURCES/` frontmatter. List: matched (work key), not in vault (skip and report).
2. **Fetch and place (Wikisource).**
   `python3 4-SYSTEM/Skills/wiki-toc-import/scripts/fetch_wiki_outline.py wikisource "<Index:… .pdf or URL>" --id <outline-id> --placed-on <work key>`
   writes `0-INBOX/temp/wiki-toc-<id>/outline.draft.md` (revisions pinned, nodes with `start_row`, suggested `row_splits`) and `pages.json`. Place a root outline on the stored root (the work the commentaries point at); a commentary outline on the commentary's own rows.
   - Check every node against the Index's TOC (`toc_entries`, `toc_entries_without_inline_heading`).
   - Spot-check each boundary (`grep -m1 "^N\. "` in the raw text).
   - `MID` nodes → ask the human (Rule 5). If they split: copy the suggested `row_splits`, decide `targets` per part from the row's transclusions (sidecar `blocks.<id>.targets`), record who decided.
   - `UNMATCHED` nodes → find out why (edition difference, or text missing — Rule 6).
   Fallback (Wikipedia, only on request): `sections`, then `draft --section N`, then one isolated placement subagent per outline with `prompts/place-outline-at-rows.md`; spot-check every boundary.
3. **Labels for translations.** One subagent per language or one for all: render each label, preferring words the translation itself uses (cite rows), short, nothing invented. Review and choose.
4. **Write the outline file** to `2-RAILS/Sections/Raw/toc-wikisource/<id>.md` in the format above, `status: complete`.
5. **Point the manifest** at it on every work in `applied_to` (`toc: {kind: outline, file: …, note: <source, revision, what it replaces, on whose instruction>}`), and add any decided `row_splits` / `supplement_rows`.
6. **Test build** to a scratch root and verify:
   `python3 4-SYSTEM/Skills/aligned-corpus-intake/scripts/build_sources.py <manifest> --out <scratch>`
   `python3 4-SYSTEM/Skills/aligned-corpus-intake/scripts/verify.py <manifest> --root <scratch>`
   Read the headings of every affected file in the scratch copy; check that each translation's sections start at the same passage as the root's.
7. **Check nothing outside `1-SOURCES/` cites the old ids** (`grep -rln "<file>.md#" 2-RAILS 3-TRANSFORMATIONS`). If something does, list it and ask before rebuilding.
8. **Build into the vault and verify** (same commands without `--out` / `--root`). Then prove every changed transclusion still points at the same text: map old id → text (`git show HEAD:<file>`) and new id → text per transcluding file, and compare the sequences.
9. **Independent review** by a fresh subagent: section starts across languages, id sequence, commentary headings against their transclusions.
10. **Record** in the vault annex: an ID-migration log entry (what changed, which files' ids, splits and added rows, that all transclusions were regenerated) and update any TOC-source table or registered deviation the change makes false.

---

## Completion check

- [ ] Every link is either matched to a vault work or reported as not in the vault
- [ ] Each outline file pins the Index revision and every heading page's revision, and has `placed_on_sha1`
- [ ] Labels match the source TOC verbatim; every work in `applied_to` has a label per node in its own language
- [ ] Every heading stands where the source puts it; every `MID` or missing-text case was decided by a human and recorded with `decided_by`
- [ ] `verify.py` passes for every work: no missing or extra letters, no dangling transclusion
- [ ] Old-to-new id mapping proved: every changed transclusion resolves to the same text as before
- [ ] Nothing in `2-RAILS/` or `3-TRANSFORMATIONS/` cites a changed id, or the citations were migrated with approval
- [ ] Vault annex updated (ID-migration log, TOC source)
