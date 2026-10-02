---
name: toc-generate
description: >
  Build a Tibetan Buddhist text's ས་བཅད (sa bcad) table of contents end to end —
  scan the text for structural-outline candidates, copy the division-announcement
  passages verbatim, reconcile them into one nested decimal tree, verify that tree
  against the source with two deterministic checkers, and ingest it back into the
  text as markdown headings with block IDs.

  This is the **Tibetan *sa bcad* pipeline**. It works because Tibetan commentarial
  prose announces its own divisions inline. A text that does not do that — most
  Pāli, Sanskrit, Chinese and modern prose — gets its structure through
  `structural-outline-ingest` (an outline stated separately from the prose) or
  `add-toc` (a navigational TOC block over existing headings) instead.

  Trigger this skill whenever the user wants any part of a text's structural outline:
  "extract the sa bcad", "build the TOC tree", "make the dkar chag / dkar-chag",
  "find the divisions", "reconstruct the outline hierarchy", "add section headings
  to the commentary", "ingest the toc tree", "add a clickable TOC", "make this text
  navigable", or "insert headings at the structural markers". Also triggers on
  ས་བཅད, sa bcad, dkar chag, Type A announcements, Type B node headers, and Type C
  closing counts.

  Runs the whole pipeline by default; individual phases are separately addressable
  (see Entry points) when a tree already exists or only candidates are wanted.
---

> **Scope — which texts this is for.** This is the Tibetan *sa bcad* pipeline. Every
> phase below assumes the text states its own divisions inline: "this has two parts,
> X and Y", "as for the second, Y …", "those are the three". Phases 0–D recover that
> announced structure; Phase E writes it back into the text as headings.
>
> For a text with **no inline structural announcements**, do not run this skill:
> - The structure is stated **separately** from the prose (a standalone outline, an
>   editor's synopsis, a commentary that lists the sections up front) →
>   `structural-outline-ingest`.
> - The file **already has headings** and just needs a navigable index block →
>   `add-toc`.
> - The announcements exist and are already headings, and you want the announcing
>   phrases wikilinked to them → `tag-inline-toc` (run after Phase E).

## Entry points

The full run is Phase 0 → A → B → C → D → E. Four shorter entries are supported,
because these used to be separate skills and are still individually useful:

| The user wants | Run | Was |
|---|---|---|
| The whole TOC, from raw text to headings in the file | Phase 0 → E | `toc-tree-extraction` + `toc-tree-ingest` |
| Just the candidate scan — "find the divisions", no tree | Phase 0 → A, then stop and report | `toc-candidate-extraction` |
| An exhaustive, miss-nothing candidate sweep | Phase 0 → A with `--recall`, then stop and report | `toc-candidate-extraction` (original recall-first prompt) |
| A tree already exists; put it into the text | Phase E only | `toc-tree-ingest` / `TOC-to-HEADING` |
| A quick two-level clickable TOC, no tree file, no vault | Simple mode (end of this file) | `TOC-GENERATOR` |

Phase A in its **default** form is balanced — it weighs recall against precision and
omits doubtful candidates (see `prompts/pass1-candidates.md`). Only the `--recall`
variant (`prompts/pass1-candidates-recall.md`) is deliberately recall-over-precision;
its output contains false positives by design. Neither output is citable as attested
structure — the tree that survives Phase D is. Say which variant you ran when
reporting.

# ས་བཅད Table of Contents — extract, verify, ingest

## Why this is an orchestrator, not one big prompt — READ THIS FIRST

The pipeline's precision comes from **task isolation**: each phase runs as a *separate
call* with only that one task's system prompt and only the relevant input. The
candidate-extraction call never sees the tree-building instructions, so it cannot drift into
tree-building; the verbatim-copy call never sees the "interpret and reconcile" instructions,
so it stays literal. Merging the four jobs into one prompt/one context collapses that
isolation and precision drops.

**Therefore you (the orchestrating agent) must NOT perform the four extraction phases
yourself in this context.** Each phase runs as its own **isolated subagent** (via the `Task`
tool) whose entire instruction set is one prompt file under `prompts/` plus its specific
input.

**Each subagent reads its input by path and writes its own output file.** Do not paste chunk
text into the subagent prompt and do not funnel results back through your context to write
them yourself — that serialises the writes and bloats your context with every chunk's Tibetan.
Instead, hand each subagent the *paths* of its prompt file and its input, and the *path* it
must write. Distinct output filenames mean parallel subagents never collide. You only: chunk,
dispatch subagents, do the deterministic merge, run the checkers, and dispatch the repair
subagent. Do not read the phase prompt files into your own context and do the work inline —
that re-merges what this design deliberately separates.

The isolated prompts live in:

| File | Phase |
|---|---|
| `prompts/pass1-candidates.md` | Phase A — section candidates, balanced (default; one subagent per chunk) |
| `prompts/pass1-candidates-recall.md` | Phase A — section candidates, recall-first (`--recall`; one subagent per chunk) |
| `prompts/pass2-enumerations.md` | Phase B — verbatim enumeration blocks (one subagent per chunk) |
| `prompts/pass3-tree.md` | Phase C — build nested decimal tree (one subagent) |
| `prompts/pass4-qc-repair.md` | Phase D — repair flagged issues (one subagent per repair round) |

---

## Inputs

| Input | Description |
|---|---|
| `input-file` | Path to the commentary/root-text `.md`, normally under `1-SOURCES/Commentaries/` |
| `commentary-id` | Short id for output filenames (inferred from the filename if obvious) |

If the file path is missing, or the `commentary-id` is not obvious from the filename, **stop
and ask** before doing anything else.

**Precondition for Phase E.** The file the headings go into must already be the
canonical file under `1-SOURCES/` — for a commentary, `1-SOURCES/Commentaries/<id>.md`, already
brought in by the vault's intake skill (`raw-to-sources` or equivalent) and already
segmented into blocks (`segment-commentary` / `commentary-resegment`). Phase E edits
that file **in place**; it does not create a side-copy and it is not a way to import a
new text. If the file is not yet in `1-SOURCES/`, stop and run intake first.

## Outputs

Working intermediates, all scratch, never cited from `2-RAILS/`:

| File | Stage |
|---|---|
| `0-INBOX/temp/TOC-<id>/chunk-index.tsv` | chunk line-range index (no text duplicated) |
| `0-INBOX/temp/TOC-<id>/candidates/chunk_NNN.md` | per-chunk section candidates (resumable) |
| `0-INBOX/temp/TOC-<id>/enumerations/chunk_NNN.md` | per-chunk verbatim enumeration blocks |
| `0-INBOX/temp/toc-candidates-<id>.md` | merged candidates |
| `0-INBOX/temp/toc-enumerations-<id>.md` | merged verbatim enumerations |
| `0-INBOX/temp/toc-tree-<id>.md` | the tree, in progress through QC/repair rounds |
| `0-INBOX/temp/toc-tree-qc-<id>.md` | QC report vs. the candidates+enumerations corpus (issues before / after repair) |
| `0-INBOX/temp/toc-tree-qc-source-<id>.md` | QC report vs. the source commentary itself — pointer validity, near-pointer attestation, monotonicity/collisions, sibling-count congruence |

The rail and its evidence trail — written only once both checkers are clean (the
Promotion step after Phase D):

| File | Content |
|---|---|
| `2-RAILS/Sections/Raw/toc-tree/<id>.md` | the finished tree, frontmatter naming both QC reports |
| `2-RAILS/Sections/Raw/toc-candidates/<id>.md` | the merged candidate scan (evidence only, never citable) |
| `2-RAILS/Sections/Raw/toc-enumerations/<id>.md` | the merged verbatim enumerations (evidence only, never citable) |
| `2-RAILS/Sections/Raw/toc-qc/toc-tree-qc-<id>.md`, `…/toc-tree-qc-source-<id>.md` | both QC reports |

The tree file itself has **no `^toc` block IDs** — the decimal numbering alone
identifies each entry. The block IDs appear only on the headings Phase E writes into
the text.

---

## Phase 0 — Plan the chunks (deterministic helper, index-only)

Do NOT copy the text into per-chunk files. Just plan the line windows — subagents read their
range straight from the source:

```bash
python 4-SYSTEM/Skills/toc-generate/scripts/chunk_file.py \
  "<input-file>" --chunk-size 150 --overlap 25 --index-only \
  --output-dir 0-INBOX/temp/TOC-<id>
```

This writes one tiny file, `0-INBOX/temp/TOC-<id>/chunk-index.tsv`, with a row per chunk:
`chunk_id <TAB> start_line <TAB> end_line` (1-based, inclusive). The 25-line overlap
guarantees every candidate appears in full in at least one window; no source text is
duplicated on disk. Read this small index into your context — it's just numbers — and drive
the phases from it.

**Resumability:** before dispatching a Phase A / Phase B subagent for a chunk, check whether
its output file already exists and skip if so, so an interrupted run resumes from the first
missing chunk.

---

## Phase A — Section candidates · ISOLATED subagent per chunk

**Which prompt.** Default is `prompts/pass1-candidates.md` — balanced recall and
precision, omits doubtful candidates, emits `CONTEXT: / SECTION_TITLE: / ITEMS:`
blocks with the title already normalised (division clause stripped). This is what
Phase C's tree builder is tuned for; use it unless the user asks otherwise.

Run `prompts/pass1-candidates-recall.md` instead when the user invokes `--recall`, or
asks for an exhaustive sweep ("don't miss anything", "every possible division", a
first pass over an unfamiliar or badly OCR'd text). That prompt prioritises recall
over precision, never omits a doubtful candidate, and emits type-tagged
`[TYPE: A/B/C] / CANDIDATE: / CONTEXT: / ITEMS:` blocks. Its output has false
positives by design; it is a scan to be reviewed, never attested structure. If you
feed a `--recall` run into Phase C, say so in the report — the tree builder will have
to discard more.

For each chunk row whose result file does not already exist, dispatch a **separate `Task`
subagent**. Pass it the prompt path, the source path, and that chunk's line range from the
index — never chunk text:

> Read `4-SYSTEM/Skills/toc-generate/prompts/pass1-candidates.md` and follow it
> exactly. Read ONLY lines START–END of the source file `<input-file>` (use
> `sed -n 'START,ENDp' "<input-file>"`, or the Read tool with offset=START / limit=END−START+1).
> Write your output to `0-INBOX/temp/TOC-<id>/candidates/chunk_NNN.md`, starting with the
> line `<!-- chunk NNN | lines START–END | source: <id> -->`, a blank line, then the
> candidate blocks — or `<!-- no candidates -->` if the prompt yields `NO CANDIDATES`. Do no
> other task; reply only with the path you wrote.

(Substitute the actual `START`, `END`, `NNN`, and `<input-file>` from the index row. For a
`--recall` run, substitute `prompts/pass1-candidates-recall.md` for the prompt path.)

Independent chunks have no dependencies, so dispatch several Phase A subagents **in parallel**
— multiple `Task` calls in one message. (The harness runs a bounded number at once and queues
the rest.) Because each writes a distinct `chunk_NNN.md`, parallel writes never collide.

---

## Phase B — Verbatim enumerations · ISOLATED subagent per chunk

Run **separately** over the same chunks — a different isolated subagent, because verbatim
copying must not be contaminated by the interpretive instructions of the other phases. Same
read-by-path / write-own-file pattern:

> Read `4-SYSTEM/Skills/toc-generate/prompts/pass2-enumerations.md` and follow it
> exactly. Read ONLY lines START–END of the source file `<input-file>` (use
> `sed -n 'START,ENDp' "<input-file>"`). Write your output to
> `0-INBOX/temp/TOC-<id>/enumerations/chunk_NNN.md` — the enumeration blocks, or
> `NO ENUMERATIONS`. Isolate ONLY the division-announcement clauses (start at the topic being
> divided, stop at the closing count/list marker); do NOT copy the commentary body that
> explains each part. Copy verbatim; add no interpretation. Reply only with the path you wrote.

These run in parallel too (one message, multiple `Task` calls), each writing a distinct file.

---

## Merge (deterministic — concatenate on disk, don't read into context)

Merging is mechanical text assembly, not inference. Do it with the shell so the chunk text
never enters your context. Concatenate the per-chunk candidate files (keeping their
`<!-- chunk NNN -->` headers) into `0-INBOX/temp/toc-candidates-<id>.md`, e.g.:

```bash
cd 0-INBOX/temp/TOC-<id>/candidates && cat chunk_*.md > /tmp/cand-body.md
# then prepend frontmatter and move into place
```

Frontmatter:

```yaml
---
source: <id>
skill: toc-generate
stage: candidates
date: <YYYY-MM-DD>
total_candidates: <N>
---
```

Likewise concatenate the enumeration files (skipping `NO ENUMERATIONS` ones, in document
order) into `0-INBOX/temp/toc-enumerations-<id>.md`. Phase C reads both merged files by path.

---

## Phase C — Build the nested decimal tree · ISOLATED subagent

Dispatch ONE subagent with only the Phase C prompt and the paths of the two merged inputs:

> Read `4-SYSTEM/Skills/toc-generate/prompts/pass3-tree.md` and follow it exactly.
> Build the full nested decimal TOC for commentary "<id>" from the candidates in
> `0-INBOX/temp/toc-candidates-<id>.md`, reconciled against the enumerations in
> `0-INBOX/temp/toc-enumerations-<id>.md`. Write only the tree block (starting with
> `## དཀར་ཆག / Table of Contents`) to `0-INBOX/temp/toc-tree-<id>.md`. Reply only with the path
> you wrote.

After it returns, prepend `stage: toc-tree` frontmatter to `0-INBOX/temp/toc-tree-<id>.md` if the
subagent did not.

---

## Phase D — Deterministic QC, then ISOLATED repair subagent

Run **both** bundled checkers yourself (NOT by hand — each encodes exact
numbering/attestation logic and must be identical every run). They check different things
and neither substitutes for the other:

```bash
python 4-SYSTEM/Skills/toc-generate/scripts/qc_check_tree.py \
  0-INBOX/temp/toc-tree-<id>.md \
  --corpus 0-INBOX/temp/toc-candidates-<id>.md 0-INBOX/temp/toc-enumerations-<id>.md \
  --out 0-INBOX/temp/toc-tree-qc-<id>.md

python 4-SYSTEM/Skills/toc-generate/scripts/qc_tree_vs_source.py \
  0-INBOX/temp/toc-tree-<id>.md --source <input-file> \
  --out 0-INBOX/temp/toc-tree-qc-source-<id>.md
```

`qc_check_tree.py` flags indentation errors, Tibetan-ordinal vs decimal mismatch, duplicate
decimals, sibling gaps/dups, titles not attested *in the candidates+enumerations the model
itself extracted* (possible hallucination), and ordinals not attested for a title. That
corpus is LLM output too, so **a tree can pass this check cleanly while still being
inconsistent with the actual commentary** — reporting `issues_before: 0, issues_after: 0`
while carrying real defects. That is precisely why the second checker exists; see
`qc_tree_vs_source.py`'s module docstring for the failure signatures it was written
against. Never treat a clean `qc_check_tree.py` run as proof the tree is right.

`qc_tree_vs_source.py` is the check against the commentary itself: pointer bounds, title
attestation *near* each node's own `[[N]]`/`[[?]]` pointer (not just somewhere in the
file), document-order monotonicity, repeated-pointer collisions (the "extractor lost its
cursor" signature — a value repeating three or more times across different titled
subsections), and a heuristic sibling-count check (does a node's own announcing text name
a division count that matches how many children the tree actually gives it). **Pass the
exact file version the tree's line numbers were computed against** — `--source` must be
the same bytes `chunk_file.py` chunked, not a later resegmentation of the same
commentary, or every pointer will look wrong for a reason that has nothing to do with the
tree.

Both exit codes = issue count. If either reports issues, dispatch ONE **isolated repair
subagent** with only the Phase D repair prompt and the paths of both issue reports, tree, and
both sources:

> Read `4-SYSTEM/Skills/toc-generate/prompts/pass4-qc-repair.md` and follow it exactly.
> Correct the tree for commentary "<id>", fixing every issue in `0-INBOX/temp/toc-tree-qc-<id>.md`
> AND `0-INBOX/temp/toc-tree-qc-source-<id>.md` against the enumerations
> (`0-INBOX/temp/toc-enumerations-<id>.md`), the candidates (`0-INBOX/temp/toc-candidates-<id>.md`),
> and the source commentary itself (`<input-file>`) — the source is the final authority
> when it and the candidates disagree. The tree to fix is `0-INBOX/temp/toc-tree-<id>.md`.
> Overwrite that same file with the corrected tree block and reply only with its path.

After it returns, **re-run both checkers** and record issues-before / issues-after in both
QC report files. Iterate (a fresh isolated repair subagent per round) until both counts are
0 or only genuinely-ambiguous issues remain (note those for the human — a sibling-count
mismatch or a same-line collision across nested levels is often legitimate, not wrong;
`qc_tree_vs_source.py` says so explicitly rather than treating every flag as proven error).
Keep both deterministic checkers as the gate — never declare the tree clean on a
subagent's say-so, and never report zero issues when a checker was not actually run.

---

## Promotion — write the rail and its evidence, once clean

Once both checkers report 0 issues (or only human-reviewed-and-accepted ones):

1. Copy the tree from `0-INBOX/temp/toc-tree-<id>.md` to `2-RAILS/Sections/Raw/toc-tree/<id>.md`,
   normalizing its frontmatter to:

```yaml
---
registered_id: <id>
source_file: 1-SOURCES/Commentaries/<filename>.md
qc_reports: [2-RAILS/Sections/Raw/toc-qc/toc-tree-qc-<id>.md, 2-RAILS/Sections/Raw/toc-qc/toc-tree-qc-source-<id>.md]
status: complete
---
```

2. Move the evidence trail out of scratch, next to the tree — a `status: complete` rail
   must not depend on files in `0-INBOX/temp/`:
   - `0-INBOX/temp/toc-candidates-<id>.md` → `2-RAILS/Sections/Raw/toc-candidates/<id>.md`
   - `0-INBOX/temp/toc-enumerations-<id>.md` → `2-RAILS/Sections/Raw/toc-enumerations/<id>.md`
   - `0-INBOX/temp/toc-tree-qc-<id>.md`, `0-INBOX/temp/toc-tree-qc-source-<id>.md` → `2-RAILS/Sections/Raw/toc-qc/` (filenames unchanged)

The per-chunk staging under `0-INBOX/temp/TOC-<id>/` stays in scratch. The promoted
candidate/enumeration files are extraction evidence, not attested structure — the candidate
scan trades precision for coverage, so it contains false positives by design; never cite
them from any rail or transformation. If a later resegmentation invalidates this tree,
rebuilding it overwrites `0-INBOX/temp/toc-tree-<id>.md` and re-promotes over all four promoted
files; do not leave a stale rail file next to a fresh one.

---

## Phase E — Ingest the tree into the text as headings

The tree is only useful once its nodes are headings in the text itself. This phase
inserts one markdown heading line per node, **in place**, into the canonical file.
Prose is never deleted, reordered, or retyped.

Which anchor the ingest uses depends on what the tree's `[[N]]` pointers mean —
this is the one decision to get right:

| Pointer meaning | Use | Why |
|---|---|---|
| Source **line numbers**, validated by `qc_tree_vs_source.py` (trees this skill built) | **E1 — scripted ingest** | The pointer already is the resolved position; no searching needed |
| Source **PDF page numbers**, or unvalidated (hand-made trees, external trees) | **E2 — read-and-place ingest** | A page pointer used as a line number silently puts headings in the wrong place |

If you are unsure which you have, run `qc_tree_vs_source.py` (Phase D) first. A
tree whose pointers are page numbers will fail its bounds check immediately.

### Heading level and block ID — both paths

Heading level follows **tree depth**, and depth is the count of dot-separated
segments in the entry's decimal number (`4-SYSTEM/Guidelines/annotation-conventions.md` §2):

| Decimal ID | Segments | Heading | Block ID |
|---|---|---|---|
| `1` | 1 | `##` | `^1-0` |
| `1.3` | 2 | `###` | `^1-3-0` |
| `1.3.2` | 3 | `####` | `^1-3-2-0` |
| `1.3.2.2` | 4 | `#####` | `^1-3-2-2-0` |
| `1.3.2.2.2` | 5 | `######` | `^1-3-2-2-2-0` |
| `1.3.2.2.2.2` | 6 | `######` + `**bold**` title | `^1-3-2-2-2-2-0` |
| `1.3.2.2.2.2.1.1.1` | 9 | `######` + `**bold**` title | `^1-3-2-2-2-2-1-1-1-0` |

**The block ID is the full decimal path, segments joined with `-`, then `-0`
appended. No zero-padding and no segment cap** — depth follows the tree exactly.
Never flatten, merge or truncate a deep tree to fit a shorter ID; the previous four
phases exist to recover that depth.

**One offset rule to watch.** The table above assumes the tree's depth-1 nodes are
the text's own top-level divisions. When a tree's single depth-1 entry is instead the
*work's own title* — which is already the file's `#` line — that entry is **excluded**
from insertion and its children (2 segments: `1.1`, `1.2`, …) are the `##` headings.
This is the normal shape of a hand-made or page-pointer tree, so it is the rule E2
states explicitly below. Decide which shape you have by comparing the depth-1 entry
against the file's `#` title line, and say which in the report.

Markdown renders only `#` through `######`. Nodes deeper than six keep `######`,
wrap the heading title in `**bold**` so the extra depth stays visible, and rely on
the full-path block ID as the authoritative record of position. Apply this
mechanically, however deep the tree goes — no need to check with the human
contributor.

> **Script deviation to fix by hand.** `toc_tree_ingest.py` caps the `#` run at six
> (correct) but does **not** bold titles deeper than six. After an E1 run on a tree
> deeper than six levels, bold those titles yourself and say so in the report.

### Step 0 — Back up (both paths)

This phase edits the canonical source file directly. Take an undo copy first. It is
a safety net, never a second source of truth:

```bash
mkdir -p "0-INBOX/temp/TOC-<id>"
cp "1-SOURCES/Commentaries/<id>.md" "0-INBOX/temp/TOC-<id>/pre-toc-ingest-backup.md"
```

---

### E1 — Scripted ingest (line-number pointers)

Parse once, then ingest in a single pass:

```bash
python3 4-SYSTEM/Skills/toc-generate/scripts/toc_tree_ingest.py parse \
  --input "2-RAILS/Sections/Raw/toc-tree/<id>.md" \
  --out "/tmp/toc-tree-<id>.json"

python3 4-SYSTEM/Skills/toc-generate/scripts/toc_tree_ingest.py ingest \
  --tree "/tmp/toc-tree-<id>.json" \
  --commentary "1-SOURCES/Commentaries/<id>.md"
```

Write the JSON to `/tmp/` to avoid NTFS ghost-file issues. Skip `parse` if the JSON
exists and the tree has not changed; it reports how many nodes carry no pointer
(`[[?]]`) — those will come back not-found.

**Nodes are inserted in reverse document order** (highest line number first), so
each insertion never shifts the line numbers of nodes not yet processed. The script
prints inserted / already-present / not-found counts and exits non-zero if anything
is not-found.

> **Retired anchor scheme — do not reintroduce.** An earlier version searched for a
> `[[context text]]` snippet with document-order cursor disambiguation. That never
> matched what `qc_tree_vs_source.py` validates (a `\d+|\?`-only pointer), so a tree
> could QC clean and still be ingested wrongly. Line-number pointers are the one
> format both tools agree on.

#### E1 Step 3 — Resolve not-found nodes

Not-found nodes fall into two categories:

**`[[?]]` pointer** — the tree could not resolve this node to a line. Read the
surrounding prose, locate the section by understanding the structure, and insert the
heading manually:

```
###### Label text ^block-id

```
(blank line after; immediately before the section's opening prose)

**Out-of-range `[[N]]`** — N exceeds the file's line count. The tree was built
against a *different version* of this file, almost certainly a resegmentation since.
Do not patch the pointer by hand: rebuild the tree (Phase 0–D) against the current
file.

After manual insertions, re-run the `ingest` command — the already-present check
skips them and should confirm zero not-found.

#### E1 Rules

1. **No pointer content in the output.** Only the label and block ID are written
   to the file.
2. **No prose is altered.** Existing lines are never deleted, reordered, or retyped.
3. **Block IDs follow the tree.** No segment cap. Use the full decimal path.
4. **Transclusion lines are structural** — they never take a block ID and never
   advance a body counter (`4-SYSTEM/Guidelines/annotation-conventions.md` §3).
5. **Single pass, reverse document order.** All depths are ingested in one run;
   processing highest-line-number-first means an earlier insertion never
   invalidates a later (smaller-line-number) node's pointer.
6. **Idempotent.** The already-present check (it looks for the block ID in the 1–3
   lines before the target line) makes re-runs safe.
7. **Write the JSON cache to `/tmp/`** (avoids NTFS ghost-file issues).
8. **Trust the tree's pointers, don't re-derive them here.** If a pointer looks
   wrong, that is an extraction QC problem — fix it upstream in Phases C–D (rebuild
   the tree or re-run the checkers), **never** by hand-editing the JSON cache.

#### E1 completion checklist

- [ ] Backup of the canonical file taken to `0-INBOX/temp/TOC-<id>/pre-toc-ingest-backup.md`
- [ ] JSON cache produced at `/tmp/toc-tree-<id>.json`
- [ ] `ingest` run: summary shows 0 not-found (or all not-found resolved manually)
- [ ] `1-SOURCES/Commentaries/<id>.md` updated in place — no `.toc.md` side-copy left behind as a second canonical file
- [ ] Final file line count = source line count + (2 × headings inserted)
- [ ] Any node deeper than six levels has its title bolded (see script deviation above)

---

### E2 — Read-and-place ingest (page pointers or unvalidated trees)

Do not trust the pointer as a position. For each TOC entry, read the prose and find
the sentence or clause that actually **announces** that section — the *sa bcad* — and
insert the heading immediately before it. Use the pointer only as a hint about
roughly where to look. The matching is done by reading and understanding the prose,
not by arithmetic.

The failure this prevents: mis-numbered or missing headings from blindly trusting a
`[[N]]` page pointer as a line number, or from inserting a heading at a
plausible-looking but wrong spot in the prose (splitting a sentence badly, or
stacking headings in the wrong order).

`4-SYSTEM/Skills/toc-generate/references/sachad-recognition.md` describes what a *sa bcad* announcement
looks like.

#### E2 Inputs

| Field | Description |
|---|---|
| `toc_file` | The finished TOC tree — `2-RAILS/Sections/Raw/toc-tree/<id>.md`, or a hand-made / externally supplied tree. A nested bullet list, each line `N.N.N … [[page]]`, indentation encoding depth. |
| `commentary_file` | The matching canonical file under `1-SOURCES/` (for a commentary, `1-SOURCES/Commentaries/<id>.md`). This file is edited **in place**. |

Confirm both files exist and that the TOC tree's top-level (depth-1) entry matches the
file's existing `# ` title line — that entry is **excluded** from ingestion (it is
already the document's H1). If the human contributor has already hand-ingested the
first several TOC entries as a worked example (as often happens — see Procedure Step
2), read that portion of the file first to confirm the exact formatting conventions in
use before touching the rest.

#### E2 Output

The same `commentary_file`, updated in place: one Markdown heading line inserted for
every TOC entry except the excluded top-level one. No existing prose is deleted,
reordered, or retyped — only split at a clause boundary where a heading must be
inserted mid-paragraph (see Rule 5).

#### E2 Output file format

**Heading level = TOC depth**, where depth is the count of dot-separated segments in
the entry's number, with the depth-1 entry excluded because it is the file's `#` line:

| TOC number | Segments | Heading | Block ID |
|---|---|---|---|
| `1.1` | 2 | `##` | `^1-1-0` |
| `1.2.1` | 3 | `###` | `^1-2-1-0` |
| `1.2.2.1` | 4 | `####` | `^1-2-2-1-0` |
| `1.2.2.1.1` | 5 | `#####` | `^1-2-2-1-1-0` |
| `1.2.2.1.1.1` | 6 | `######` | `^1-2-2-1-1-1-0` |
| `1.2.2.1.1.3.1` | 7 | `######` + **bold** (see below) | `^1-2-2-1-1-3-1-0` |
| `1.2.2.1.1.3.1.1` | 8 | `######` + **bold** (see below) | `^1-2-2-1-1-3-1-1-0` |

> **Block IDs — the one deliberate change from the original `TOC-to-HEADING` skill.**
> That skill wrote bare headings (`## དང་པོ་མདོར་བསྟན་པ།`) with no block ID.
> **E2 headings DO carry a block ID**: `^<full-decimal-path>-0`, exactly as E1 writes
> them, per `4-SYSTEM/Guidelines/annotation-conventions.md` §2. Every other rule below is that skill's,
> verbatim. Without the ID the heading cannot be cited or linked from a rail, and a
> parser expecting `^N-0` silently finds no table of contents.

**Depth beyond Markdown's maximum heading level (6):** Markdown renders only `#`
through `######` (level 6) as an actual heading; a longer run of hashes is just
literal hash characters on the page. Per `4-SYSTEM/Guidelines/annotation-conventions.md` §2, **cap the `#` run
at six** and additionally wrap the heading text itself in `**bold**` markers so it
still reads visually as a heading, with the full-path block ID carrying the real
depth. This is applied mechanically — no need to check with the human contributor
before proceeding, however deep a TOC entry goes.

**Heading text = TOC label, cleaned**: take the entry's text before the trailing
`[[page]]` reference, strip a trailing tsheg (`་`) if present, then end the heading
with a shad (`།`). At depth ≥ 7, also wrap that cleaned text in `**...**`.

```
དང་པོ་མདོར་བསྟན་པ་ [[24]]   →   ## དང་པོ་མདོར་བསྟན་པ། ^1-1-0
ཁྲོ་མོའི་ཚུལ་ལ་ཕྱག་འཚལ་བ་ [[126]]   →   ##### ཁྲོ་མོའི་ཚུལ་ལ་ཕྱག་འཚལ་བ། ^1-2-2-1-1-0
དང་པོ་ཁྲོས་པའི་ཞལ་གྱིས་བསྟོད་པ་ [[130]]   →   ###### **དང་པོ་ཁྲོས་པའི་ཞལ་གྱིས་བསྟོད་པ།** ^1-2-2-1-1-3-1-0
```

**Spacing**: every heading is followed by a blank line before whatever comes next —
content or another heading. When headings are stacked (see Rule 4), each one is
separated from the next by a blank line too:

```
##### ཁྲོ་མོའི་ཚུལ་ལ་ཕྱག་འཚལ་བ། ^1-2-2-1-1-0

###### དང་པོ་ཁྲོས་པའི་ཞལ་གྱིས་...བསྟོད་པ། ^1-2-2-1-1-1-0

དེའི་རྗེས་སུ་ཁྲོ་མོའི་ཚུལ་ལ་ཕྱག་འཚལ་བ་...
```

#### E2 Rules

1. **Exclude the top-level (depth-1) TOC entry.** It already exists as the file's
   `# ` document title — never duplicate it as a heading.
2. **Never guess a location.** Every heading must sit directly before the specific
   sentence or clause in the text that actually announces that section (usually ending
   in `ནི།`, `ལས།`, `དང་།`/`དང༌།`, or restating the TOC label near-verbatim). If no
   matching announcement can be found, stop and ask the human contributor rather than
   placing the heading at an approximate spot.
3. **One heading per standalone paragraph is the simple case.** When a TOC entry's
   announcement is already its own paragraph (blank line before and after), just insert
   `heading` + blank line directly before it.
4. **Stack headings when one paragraph announces several nested levels at once.**
   Tibetan outline prose often states a whole chain of divisions in one sentence (e.g.
   "…this section has two parts: body and mind; the first, body, has…"; culminating in
   "…the first is:"). When that happens, insert **all** the applicable headings
   together, each followed by a blank line, directly before that one paragraph — do not
   split the paragraph itself.
5. **Split the paragraph when an announcement is buried mid-sentence.** Sometimes a
   paragraph both closes out the previous section's content *and* opens the next one in
   a single run-on sentence, with no natural paragraph break. Split it at the clause
   boundary — commonly right after a `དང་།`/`དང༌།` connector, which this kind of text
   uses routinely as a paragraph-final "and, continued below" — and insert
   `blank / heading / blank` between the two resulting paragraph fragments. Never insert
   a heading in the middle of an unbroken clause.
6. **Preserve exact whitespace when matching.** Raw OCR/segmentation text frequently
   mixes regular spaces (U+0020) and non-breaking spaces (U+00A0, `\xa0`) within the
   same line. Normalize this difference for *matching* purposes only — never let it
   cause a false "not found." When splitting a paragraph (Rule 5), slice the *original*
   line text at the matched position, not a re-typed/hardcoded copy, so the exact source
   bytes are preserved on both sides of the split.
7. **Do not touch anything outside the TOC's scope.** Recap paragraphs, summary
   verses, or transitional content that has no corresponding TOC entry are left exactly
   as-is — do not invent a heading for them.
8. **Verify before finishing.** Count headings inserted; it must equal the number of
   TOC entries minus the excluded top-level one. Read back every insertion point to
   confirm correct nesting order and blank-line spacing.

#### E2 Procedure

1. **Read both files in full.** Read `toc_file` to get the complete nested list with
   depths and page numbers. Read `commentary_file` in full (it will usually exceed one
   page — read it in successive chunks rather than stopping partway).
2. **Check for a worked example.** If part of the TOC has already been hand-ingested
   into the file (a common way the human contributor demonstrates the exact conventions
   they want), compare those existing headings against their TOC entries to confirm: the
   heading-level-by-depth mapping, the label-cleanup rule, and the blank-line
   convention. Use that as ground truth over this document's general guidance if the two
   ever disagree.
3. **For each remaining TOC entry, in document order:** search the prose for the clause
   that announces it (per Rule 2). Common signals: the clause restates the TOC label's
   wording near-verbatim; it ends in `ནི།` (topic-introducing "as for…"); ordinal markers
   (`དང་པོ་`, `གཉིས་པ་`, `གསུམ་པ་`…) matching the entry's position among its siblings.
4. **Classify the match** as one of the three cases in Rules 3–5 (standalone paragraph /
   stacked multi-level paragraph / mid-paragraph split) and record the exact insertion
   point.
5. **Apply all insertions in one pass**, working from the bottom of the file upward (or
   by unique-text anchor rather than line number) so that earlier insertions never
   invalidate the position of insertions still to be made.
6. **Re-read the modified file** and confirm: heading count matches TOC entry count
   (minus the excluded top-level entry); hash counts match each entry's depth (capped at
   six, with bold beyond); every heading has a blank line above and below it; no prose
   was lost (a line-count check — new line count should equal old line count plus twice
   the number of `before`-style insertions, plus a smaller fixed amount per split
   insertion — is a good sanity check, not a substitute for reading the diff).
7. **Report back** which TOC entries required a paragraph split (Rule 5) or a stacked
   multi-level insertion (Rule 4), since those are the judgment calls most worth a second
   look by the human contributor.

#### E2 completion check

- [ ] Top-level TOC entry excluded (not duplicated as a heading)
- [ ] Every remaining TOC entry has exactly one corresponding heading in the file
- [ ] Heading hash-count matches each entry's TOC depth (segments separated by `.`), capped at six
- [ ] Heading text = TOC label with the `[[page]]` reference stripped and the trailing tsheg replaced by a shad
- [ ] Every heading carries its full-decimal-path block ID with the `-0` slot (`4-SYSTEM/Guidelines/annotation-conventions.md` §2)
- [ ] Blank line present above and below every heading, including between stacked headings
- [ ] No existing prose deleted, reordered, or retyped — paragraph splits (Rule 5) preserve both resulting fragments verbatim
- [ ] Any TOC depth beyond 6 used `######` with the heading text wrapped in `**bold**`
- [ ] File re-read after edits to confirm correct order and spacing

---

## Simple mode — two-level TOC, no tree file

When the user just wants a text made navigable and does not need a citable
tree rail, skip Phases 0–D entirely: detect the sa bcad directly and insert a
two-level set of headings (main topic / sub-topic) with block IDs at the point where
each topic's text begins, writing the result to a **new file**. The original prose is
never altered.

Use `4-SYSTEM/Skills/toc-generate/references/sachad-recognition.md` for detection and
`4-SYSTEM/Skills/toc-generate/scripts/insert_toc_headings.py` to apply the positions deterministically:
you produce an annotation JSON (`4-SYSTEM/Skills/toc-generate/references/example-annotation.json` shows the
shape) naming each section's depth, title and a verbatim line-unique
`body_start_context`, and the script assigns the block IDs, inserts the headings, and
proves no existing prose changed before writing.

```bash
python3 4-SYSTEM/Skills/toc-generate/scripts/insert_toc_headings.py render \
  --input  "<input-file>" \
  --annot  "0-INBOX/temp/<id>.annotation.json" \
  --output "0-INBOX/temp/<id>.toc.md"
```

**`insert_toc_headings.py` supports depth 1 and depth 2 only.** It raises on any
deeper node — collapse deeper nesting into its nearest depth-2 ancestor, or use the
full pipeline (Phases 0–E) instead, which has no depth limit. It emits conventional
heading anchors: `## <title> ^N-0` for a main topic and `### <title> ^N-M-0` for a
sub-topic (`4-SYSTEM/Guidelines/annotation-conventions.md` §2) — **not** `^toc-N`, which is the separate
namespace of the standalone outline block `add-toc` writes (§4).

Once headings are in, Obsidian's Outline panel, `[[file#Heading]]` links, and any
static-site TOC generator render a clickable TOC for free.

This mode is vault-independent — it needs no `2-RAILS/`, no promotion step, and no QC
corpus. It writes a new file rather than editing in place, so it is the right choice
for a one-off or an unfamiliar text, and the wrong choice when the tree itself has to
be cited, compared across commentaries, or fed to `section-summary` /
`commentary-claims`.

---

## After this skill

- `tag-inline-toc` — wikilink each announcing phrase in the prose to the heading it
  announces (`4-SYSTEM/Guidelines/annotation-conventions.md` §5).
- `add-toc` — write the standalone navigable outline block at the top of the file.
- `section-summary` / `commentary-claims` — both read the promoted tree.

---

## Execution summary

1. Confirm `input-file` and `commentary-id` (ask if not obvious); confirm the file is already the canonical one under `1-SOURCES/`.
2. Phase 0: `chunk_file.py --index-only` → `chunk-index.tsv` (line ranges only, no text copied).
3. Phase A: isolated subagent per chunk, reads its line range from the source + writes its own `candidates/chunk_NNN.md` (resumable, parallel). Default prompt `pass1-candidates.md`; `pass1-candidates-recall.md` on `--recall`.
4. Phase B: isolated subagent per chunk, writes its own `enumerations/chunk_NNN.md` (parallel).
5. Merge on disk (shell `cat`) → `0-INBOX/temp/toc-candidates-<id>.md` and `0-INBOX/temp/toc-enumerations-<id>.md`.
6. Phase C: one isolated subagent reads both merged files → writes `0-INBOX/temp/toc-tree-<id>.md`.
7. Phase D: run **both** checkers — `qc_check_tree.py` AND `qc_tree_vs_source.py` — then an isolated repair subagent (reads/overwrites by path) → re-run **both** checkers → `0-INBOX/temp/toc-tree-qc-<id>.md` and `0-INBOX/temp/toc-tree-qc-source-<id>.md`.
8. Promote: once both are clean, copy to `2-RAILS/Sections/Raw/toc-tree/<id>.md` with normalized frontmatter (above) and move the evidence trail alongside it.
9. Phase E: back up the file, then ingest the tree as headings — E1 (`toc_tree_ingest.py parse` + `ingest`) for line-number pointers, E2 (read-and-place) for page pointers or unvalidated trees. Resolve any not-found nodes and re-run until zero.
10. Report totals (candidates, enumeration blocks, issues before/after, headings inserted, which entries needed a split or a stack) and the output paths — both the `0-INBOX/temp/` working files and the promoted `2-RAILS/Sections/Raw/toc-tree/<id>.md`.

**Isolation is the whole point.** If you ever find yourself doing a phase's reasoning in this
orchestrating context instead of in its own subagent, stop and dispatch the subagent — that is
what preserves the per-task precision this pipeline was built around.
