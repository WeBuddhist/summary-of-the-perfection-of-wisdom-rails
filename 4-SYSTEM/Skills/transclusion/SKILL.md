---
name: transclusion
description: >
  Insert Obsidian block-transclusion links (`![[root#^N-V]]`) for root-text
  verses into a commentary or a second version of the root text, placing each
  transclusion at the structurally correct position and formatting the spacing around
  it.

  Trigger on "add the transclusions", "transclude the root verses", "pull the root text
  into this commentary", "link the verses into the commentary", "insert the verse
  transclusions".

  Placement is the whole problem: a transclusion in the wrong place reads as though the
  commentary is discussing a verse it is not.
---

# Transclude root-text verses into another file

| Mode | Target | Placement rule | Scripted? |
|---|---|---|---|
| 1 — Commentary, quoted verses | Commentary that quotes each verse verbatim before commenting | Insert before the verse's first full inline quotation, then move up to the verse's own sa-bcad block where it has one | yes — 3 scripts |
| 2 — Commentary, sa-bcad introduced | Commentary that announces each verse with a sa-bcad statement | Before the sa-bcad statement that introduces the verse | no — by hand |
| 3 — Commentary, by section category | Commentary whose sections fall into overview / verse-by-verse / other | Classify each section first, then place by category | no — by hand |
| 4 — Second root-text version | Another version or edition of the root text | Structurally matching position | Type 1 yes — 3 scripts |

**Modes 1 and 2 reach the same place by different means.** Mode 2 is the manual
statement of the rule (the transclusion belongs before the sa-bcad that announces
the verse, not before the quotation); Mode 1 is the scripted implementation of it,
which gets there in two passes because the script must first find the quotation
before it can walk up to the sa-bcad. Prefer Mode 1 when the commentary is
Tibetan and regular enough for the matcher; fall back to Mode 2 by hand when it
is not.

**Decide the mode by reading the target's own habit, not by preference.** Look at
how the commentary actually introduces verses — does it quote them verbatim, announce
them with a sa-bcad statement, or neither? Getting this wrong puts every transclusion
in the same wrong place, consistently enough to look deliberate.

**A transclusion line is structural.** It never takes a block ID and never advances a
body counter (`4-SYSTEM/Guidelines/annotation-conventions.md` §3). If you are stamping IDs in the same pass,
this is the rule that goes wrong most often.

Transclusion requires the root text to already carry the block IDs being referenced —
run `add-block-ids` on the root text first, or every link resolves to nothing.

---

## House conventions — one link form, one spacing rule

All four modes write the same thing; only the *placement decision* differs.

**Link form — full vault-relative path, always.**

```
![[1-SOURCES/Text/<root-text>.md#^1-1]]
```

The full path from the vault root, including the `.md` extension. Never a bare
note name, never a short wiki-link. A short link resolves only while the note
name stays unique and stays put; the full path survives a rename of neither, but
it fails loudly instead of silently pointing at the wrong file.

**Spacing — one blank line on each side.**

```
<preceding line>

![[1-SOURCES/Text/<root-text>.md#^1-1]]

<the commentary text this introduces>
```

Exactly one blank line immediately before and immediately after the
transclusion, so it reads as its own Markdown block. A transclusion at the very
start or end of a file takes no leading/trailing blank. Consecutive verses
transcluded as a group sit on consecutive lines with **no** blank between them,
and the group as a whole is wrapped by one blank line on each side.

### The two registered variants

These are the only permitted deviations, and each is a property of the *target
file*, not a preference:

1. **Short link form via `--link-base` (Mode 1).** Mode 1's scripts take the
   link text as a `--link-base` argument and will emit whatever you give them.
   Pass the **full vault-relative path** as `--link-base` to get the house form.
   The short form is only correct when the file being edited already uses it
   throughout and you are matching its existing precedent — say so in the run
   report when you do.
2. **No blank line before a sa-bcad (Mode 4, Type 2, `tibetan-master`).** When
   the transclusion is placed immediately before an *inline sa-bcad phrase* (not
   a heading), it binds to that phrase: blank line before the transclusion, none
   between the transclusion and the sa-bcad line. This is deliberate — the
   transclusion and its announcement are one unit. Everywhere else in that same
   file, the house rule applies.

Mode 2's Rule 5 ("preceded by whatever spacing already separated the prior
content") is the house rule stated conservatively: it inserts the blank line
*after* the transclusion and leaves an already-correct blank line before it
alone. If there is no blank line before it, add one.

---

## Mode 1 — Commentary that quotes each verse verbatim

Three-stage pipeline: insert before each verse's first full inline quotation, then format placement and spacing.

This skill places root-text verse transclusions inside a Tibetan master's commentary, positions each transclusion correctly relative to the sa-bcad (ས་བཅད) structure that introduces its verse, and normalizes the blank-line spacing around it so the outline reads correctly in Obsidian.

It bundles three deterministic Python scripts that run as an ordered pipeline. Each stage has a dry-run mode (default) and an `--apply` mode. Always dry-run, review the report, then apply.

Transclusions are navigation aids added to `1-SOURCES/` files — never interpretive content. Beyond inserting `![[...]]` lines, moving them, and managing the blank lines immediately around them, **no commentary text is ever added, removed, reordered, or rephrased.**

> **Filename note.** Stage 2's script is still called `02_remove_blank_before_transclusions.py` and Stage 3's is still called `03_blank_before_sachad.py`, but their behavior has changed (see below) — the names are legacy and kept only so existing notes/commands referencing them still work. Rename them (`02_reposition_before_sachad.py`, `03_blank_around_transclusions.py`) next time you have shell access to the vault, if you want the filenames to match what they do now.

---

### When to use

- "Transclude the root verses into commentary X" → run Stage 1.
- "Put the transclusion before the verse's sa-bcad, not after it" / "reposition the transclusions relative to sa-bcad" → run Stage 2.
- "Add blank lines around the transclusions" / "space out the transclusions" → run Stage 3.
- "Do the whole transclusion pass on commentary X" → run Stages 1 → 2 → 3 in order.

Stages 2 and 3 assume the transclusions already exist (Stage 1 has run, or they were added previously).

---

### Inputs

| Field | Description | Example |
|---|---|---|
| `root` | Full vault-relative path to the root text / translation to transclude from. Must use `verse_id_format: chapter-verse` block IDs (`^N-V`). | `1-SOURCES/Text/<root-text>.md` |
| `commentary` | Full vault-relative path to the Tibetan commentary to modify in place. | `1-SOURCES/Commentaries/<commentary-id>_segmented.md` |
| `link-base` | The base of the transclusion link, exactly as it should appear inside `![[ … #^N-V]]`. The skill uses the short Obsidian link form. | `1-SOURCES/Text/<root-text>.md` |
| `chapter` | Optional. A single chapter label to scope the run, or `all` (default). Accepts a plain chapter number or a Roman-numeral front-matter label (see below). | `1`, `I`, `all` |

**Chapter labels aren't always numeric.** Some root files in this vault give the pre-chapter-1 front matter (Sanskrit title line, Tibetan title line, opening homage) Roman-numeral block IDs — `^I-1`, `^I-2`, `^I-3` — instead of the generic `^0-N` convention. All three scripts recognize `^[IVXLCDM]+-N` alongside `^N-V`, and `--chapter` accepts either form (`--chapter I` scopes to the Roman-numeral front matter). Roman-numeral chapters sort before chapter 1 in reports.

---

### Output

The commentary file is modified in place. The only changes are:

1. inserted `![[link-base#^N-V]]` transclusion lines (Stage 1),
2. the transclusion line moved up to sit right before the verse's own sa-bcad block, when it has one (Stage 2),
3. exactly one blank line inserted/normalized immediately before and immediately after each transclusion, wherever it now sits (Stage 3).

No new files are created. No existing commentary text is changed.

---

### The three stages

#### Stage 1 — Transclude verses (`4-SYSTEM/Skills/transclusion/scripts/01_transclude_verses.py`)

For each root verse stanza, the script finds the **first full inline quotation** of that stanza in the commentary and inserts `![[link-base#^N-V]]` on the line immediately before the stanza's first line. This stage always places the transclusion right before the verse text itself — Stage 2 decides whether it should move.

- **Full quotation preferred.** When a verse is quoted in more than one place, the occurrence where the most stanza lines match wins (ties → earliest). A 2-line illustrative citation inside an earlier verse's commentary loses to the full 4-line stanza in the verse's own section.
- **Variant-tolerant.** Lines are matched with a character-overlap ratio (≥ 0.80) plus containment, so minor orthographic variants are absorbed (e.g. `བསྒོམ`/`སྒོམ`, `དེང`/`དེ`, `ཟློག`/`བཟློག`). Matching anchors on *any* stanza line, so a variant first line does not block the match.
- **Passing single lines are not enough.** A one-line match is accepted only when followed by a citation closer (`ཞེས་པ་ནི།`, `ཅེས་པ་ནི།`, …) — i.e. a genuine short citation, never a line echoed mid-prose.
- **Single-line root segments (titles, the opening homage, colophon lines) get a second look.** The main matcher only searches for a match starting at the beginning of a commentary line, which is right for a block-quoted verse stanza but misses a short root line that a commentary paraphrases mid-sentence. For any root segment that is only one line long, a fallback pass additionally scans every commentary line for that text appearing *anywhere* inside it (exact equality or full containment). This is what lets a segment like the Sanskrit/Tibetan title lines or the opening homage (`^I-1`–`^I-3` where a vault registers the Roman-numeral front-matter zone — `4-SYSTEM/Guidelines/annotation-conventions.md` §7) get placed even though no commentary quotes them on their own dedicated line. It still won't force a match where the commentary only paraphrases the idea without the actual words — that stays `UNPLACED` for a human to place, same as always.
- **Idempotent.** Verses already transcluded are skipped.
- **No blank-line management.** Stage 1 no longer touches blank lines at all — that is entirely Stage 3's job now.

Verses the script cannot place are listed under `UNPLACED`. These are usually **split quotations** (the commentator breaks the stanza across prose explanation) or large variants. Resolve each by hand: locate the first line of the verse's quotation and insert `![[link-base#^N-V]]` on the line immediately before it.

```
python3 4-SYSTEM/Skills/transclusion/scripts/01_transclude_verses.py \
  --root "1-SOURCES/Text/<root-text>.md" \
  --commentary "1-SOURCES/Commentaries/<comm>.md" \
  --link-base "1-SOURCES/Text/<root-text>.md" \
  --chapter 1            # dry run
# review, then:
python3 4-SYSTEM/Skills/transclusion/scripts/01_transclude_verses.py ... --chapter 1 --apply
```

#### Stage 2 — Reposition before the verse's own sa-bcad (`4-SYSTEM/Skills/transclusion/scripts/02_remove_blank_before_transclusions.py`)

Decides, per verse, whether the transclusion belongs right before that verse's own **sa-bcad (ས་བཅད) block** or right before the **verse** itself, and moves it there:

- **If the verse has its own sa-bcad** — the line immediately above the transclusion is structural (an ordinal, a heading, an enumeration opener/member — see classification below) — the transclusion is moved up to sit immediately before the **first line of that sa-bcad block** (walking up through any enumeration so the block starts at a genuine opener/heading/ordinal, exactly as it used to only for blank-line placement).
- **If the verse has no sa-bcad** — the line above is ordinary prose, a connector, a commentary conclusion, or a root-verse fragment — the transclusion is **left exactly where Stage 1 put it**, right before the verse.

Only the `![[...]]` line itself moves. No blank lines are touched here (that's Stage 3), and no commentary text is added, removed, reordered, or rephrased.

```
python3 4-SYSTEM/Skills/transclusion/scripts/02_remove_blank_before_transclusions.py --commentary "<comm>.md" --report   # dry run, shows every decision
python3 4-SYSTEM/Skills/transclusion/scripts/02_remove_blank_before_transclusions.py --commentary "<comm>.md" --apply
```

#### Stage 3 — Blank line before and after every transclusion (`4-SYSTEM/Skills/transclusion/scripts/03_blank_before_sachad.py`)

Normalizes spacing to the house rule — exactly **one blank line** immediately before and immediately after every transclusion, wherever Stage 2 left it:

```
<preceding line>

![[link-base#^N-V]]

<following line>
```

Multiple existing blank lines touching a transclusion are collapsed to one; a missing blank is inserted. A transclusion at the very start or end of the file gets no leading/trailing blank (nothing to separate it from). Nothing else in the file is touched.

```
python3 4-SYSTEM/Skills/transclusion/scripts/03_blank_before_sachad.py --commentary "<comm>.md"          # dry run
python3 4-SYSTEM/Skills/transclusion/scripts/03_blank_before_sachad.py --commentary "<comm>.md" --apply
```

---

### Sa-bcad classification (used by Stage 2 to decide placement)

A line counts as **structural** (part of a sa-bcad block) when it is one of:

- an **ordinal-led** line: starts with `དང་པོ`, `གཉིས་པ`, `གསུམ་པ`, … `བཅུ་པ` — checked first, and normally enough regardless of what else the same block contains, **but only when heading-anchored if it also contains a ཞེས/ཅེས conclusion** (see the false-positive note below — this gate did not exist in earlier runs of this skill and its absence caused real misplacements);
- a **heading**: ends in `ནི།` / `ནི། །` (a "this is X" announcement), short (≤ 60 collapsed syllables);
- an **enumeration opener**: ends in `ལ།`, `ལ་ཡང་།`, `ལས།`, `ཏེ།`, `སྟེ།`, short;
- an **enumeration member / closer**: ends in `དང་།` / `དང༌།`, or a closing member `…པའོ། །` / `…བའོ། །` / `…ནོ། །` / `…ལོ། །`, or a count word (`…གསུམ།`, `…གཉིས།`, …), short.

A line is **not** structural (and stops the upward walk) when it is:

- ordinary commentary prose (long sentences);
- a connector: `དེའི་རྗེས་སུ།`, `དེའི་འཐད་པར།`, `དེའི་འཐད་པ་ནི།`;
- a quotation or commentary conclusion (contains `ཞེས` / `ཅེས`, e.g. `…ཞེས་པའོ། །`, `…ཞེས་གསུངས།`) — **unless the line is ordinal-led AND heading-anchored (see above and the false-positive note below)**;
- a **root-verse fragment** (ends in `དང་། །` / `དང་ནི། །`) — these are verse lines, not sa-bcad.

**Why the ordinal check runs first.** Some commentaries fold a sa-bcad announcement and its own extended explanation into a single block instead of keeping them as separate lines — e.g. `བཞི་པ་སྤྲོ་བ་བསྐྱེད་པ་ནི། <several sentences unpacking the point> ཞེས་པའི་དོན་ནོ། །` all as one paragraph. Classifying by the line's *ending* alone would see the trailing `ཞེས་པའི་དོན་ནོ` and call the whole block a prose conclusion, missing the `བཞི་པ་...ནི།` sa-bcad announcement sitting at its front. Checking `starts_ord` before the quotation/conclusion test means an ordinal-led block is normally recognized as its verse's own sa-bcad, no matter how much explanation follows in the same paragraph.

**Why unconditional ordinal-priority is wrong, and the heading-anchor fix.** An ordinal word at the front of a paragraph is not always a fresh sa-bcad for the verse that follows — a real placement bug was found (and fixed) after a human reviewer caught it in the actual commentary. Two recurring false-positive shapes, both confirmed in the segmented Tibetan commentary this heuristic was diagnosed on:

  1. *A pre-announced flat list, walked item by item.* A commentary announces a numbered list once in ordinary prose ("there are 27 gateways for faults… first: X, second: Y…") and then works through the items across several verses, sometimes packing more than one item into a single verse's own gloss. Every item still opens a fresh paragraph with its ordinal word, but most of them explain a WORD OR CLAUSE of the verse just quoted, not the verse that comes next. Confirmed example (verse IDs are from the commentary it was diagnosed on): verse ^5-49's own quoted line lists five distraction-terms in one stanza; the gloss then walks through them as list items "third" through "sixth" (`གསུམ་པ`…`དྲུག་པ`), all still explaining ^5-49. The ordinal-priority bug moved ^5-49's OWN transclusion to sit before item "second" (`གཉིས་པ`, itself closing out the *previous* verse, ^5-48) and moved ^5-50's transclusion to sit before item "fifth" (`ལྔ་པ`, still glossing a word — `ང་རྒྱལ` — inside ^5-49's already-quoted stanza). Both are wrong: neither `གཉིས་པ` nor `ལྔ་པ` introduces the verse that was moved to sit before it.
  2. *An opponent's objection, elaborated with its own step numbering.* A Madhyamaka-style rebuttal sets up an opponent's claim ("kho na re…" / "so they say…") and elaborates it with internal ordinals ("…second, applying analysis to the analysis itself, third, and so on, it would never end…"). Confirmed example: ^9-110's transclusion was moved to sit before such a `གཉིས་པ…གསུམ་པ…` sentence that is purely restating the objector's chain of reasoning, not introducing ^9-110's own verse.

The one structural signal that reliably tells a genuine sa-bcad resumption apart from these false positives is a **true markdown heading** (`##`–`############`, ending in a block ID like `^1-2-3-…-0`) sitting within the last couple of structural blocks above the ordinal line, restating the same topic. Confirmed genuine examples: ^1-3, ^8-120, ^9-118 — each sits directly under (or one transclusion-length below) a heading whose wording the ordinal-led prose repeats almost verbatim. So: **an ordinal-led block is trusted unconditionally only when such a heading anchor is found nearby; without one, an ordinal-led block that itself contains a ཞེས/ཅེས conclusion falls back to the plain conclusion test and is treated as `none`** — the transclusion then stays right before the verse, which is always the safe default when a sa-bcad can't be confidently identified.

This is a heuristic, not certainty, and it is deliberately conservative: a handful of genuinely fresh transitional arguments (an ordinal opening a new causal point, with no repeated heading text, that happens to also contain ཞེས/ཅེས somewhere in its own explanation) will now also fall back to "stays before verse" — confirmed example: ^6-25 in this same file, judged correct by manual reading but with no heading anchor for the automation to key off. **A missed sa-bcad placement (verse quoted a few lines later than ideal) is a much smaller error than a wrong one (root verse displaced across a neighboring verse's own commentary material)**, so this trade-off is intentional. This is exactly what the Stage 2 `--report` step is for — see the checklist below: skim the "stays before verse" list for chapters with heavy enumeration or debate prose (lists of faults/virtues, opponent-refutation dialogues) and hand-place any genuine sa-bcad the heuristic was too conservative about.

**Block start.** Walk up the contiguous run of structural lines above the transclusion; trim any leading member-only lines so the block begins at a genuine opener/heading/ordinal. The transclusion moves to right before that first line. If the run contains no opener/heading/ordinal (e.g. a lone `…པའོ། །` prose conclusion), it is not a real sa-bcad block → the transclusion is not moved.

**"Immediately above" skips blank lines, not just literal adjacency.** Segmented commentaries typically put every clause on its own paragraph, separated by a blank line - so the walk looks at the nearest *non-blank* line above the transclusion (and the nearest non-blank line above that, and so on), not literally `line[i-1]`. Reading it as strict line-adjacency would see a blank line everywhere and never find a sa-bcad at all. A markdown heading line (`##`–`########`, ending in its own block ID like `^1-2-1-0`) is never itself treated as structural — it always reads as `none` and stops the walk - only a plain-prose sa-bcad *announcement* sentence counts, even when it sits right below a heading that restates the same point.

---

### Worked example (verse ^1-4)

After Stage 1 (transclusion right before the verse, blank lines not yet normalized):

```
… ཡོད་པར་འགྱུར་རོ་ཞེས་པའོ། །              ← prose conclusion (stops the walk)
གཉིས་པ་བརྩམ་བྱ་…དངོས་བཤད་པ་ལ།            ← block FIRST line (ordinal + ལ། opener)
…ལེའུ་གསུམ།  /  …ལ་ཡང་།  /  …དང༌།          ← enumeration members
…
ལུས་རྟེན་…ཚུལ་དང་།
སེམས་རྟེན་…ཚུལ་ལོ། །
དང་པོ་ནི།                                  ← the immediate sa-bcad
![[1-SOURCES/Text/<root-text>.md#^1-4]]
```

After Stage 2 — the transclusion **moves up** to right before the **first line of the sa-bcad block** (not just before the immediate `དང་པོ་ནི།`):

```
… ཡོད་པར་འགྱུར་རོ་ཞེས་པའོ། །
![[1-SOURCES/Text/<root-text>.md#^1-4]]
གཉིས་པ་བརྩམ་བྱ་…དངོས་བཤད་པ་ལ།
… (enumeration unchanged) …
དང་པོ་ནི།
<verse text follows>
```

After Stage 3 — one blank line is added on each side of the transclusion:

```
… ཡོད་པར་འགྱུར་རོ་ཞེས་པའོ། །

![[1-SOURCES/Text/<root-text>.md#^1-4]]

གཉིས་པ་བརྩམ་བྱ་…དངོས་བཤད་པ་ལ།
… (enumeration unchanged) …
དང་པོ་ནི།
<verse text follows>
```

Contrast: where the line above the transclusion is a connector (`དེའི་འཐད་པར།`) or commentary prose (`…ཞེས་གསུངས།`), Stage 2 leaves the transclusion right before the verse, and Stage 3 still wraps it with one blank line on each side.

---

### Rules

1. **Read-only except for navigation links, their position, and their spacing.** `1-SOURCES/` files may receive block IDs, frontmatter, internal navigation links (transclusions qualify), and `[Ed:…]` notes only. This skill inserts `![[…]]` lines, moves them relative to sa-bcad structure, and manages the blank lines immediately around them — nothing else.
2. **Link form comes from `--link-base`.** The scripts emit `![[<link-base>#^N-V]]` verbatim. Pass the **full vault-relative path** (with `.md`) as `--link-base` — that is the house form (see **House conventions** above). Pass a short note name only when the target commentary already uses short links throughout, and say so in the run report.
3. **Never duplicate a transclusion.** Stage 1 skips any verse whose `^N-V` is already transcluded.
4. **Never modify existing commentary text.** Every stage only inserts, moves, or removes `![[…]]` lines and the blank lines immediately around them.
5. **Always dry-run first.** Run each stage without `--apply` (`--report` for Stage 2, plain dry-run for Stages 1 and 3), read the report, then apply. For Stage 1, hand-resolve every `UNPLACED` verse before moving on. A single-line root segment (title lines, the opening homage, a colophon line) that stays `UNPLACED` after the fallback pass usually means the commentary only paraphrases it rather than using its actual wording - place it by hand right before the passage that discusses it (prefer the line that most directly restates or quotes it; if that passage opens with its own heading, placing the transclusion right before the heading is also reasonable for a front-matter segment with no verse-style prose exposition of its own).
6. **Run the stages in order** (1 → 2 → 3) for a fresh commentary. Stages 2 and 3 may be run independently on a commentary that already has transclusions.
7. **Lenient read, clean write.** The scripts read the commentary leniently (so a stray truncated final byte does not abort a run) and re-validate the UTF-8 decode after writing. If a prior tool clipped the final colophon byte, repair the last line from a known-good backup before applying.
8. **Idempotent end-to-end.** Running Stages 2 and 3 again on an already-processed commentary makes no further changes.

---

### Procedure

1. Confirm `root` is a `1-SOURCES/` root/translation file with `^chapter-verse` block IDs, and `commentary` is a `1-SOURCES/` Tibetan commentary.
2. **Stage 1** — dry-run per chapter; review placements and `UNPLACED`; apply; hand-place any split/variant verses. After all chapters, confirm: transclusion count = unique verse-id count = root verse count.
3. **Stage 2** — `--report`; spot-check the sa-bcad decisions (especially multi-line enumeration blocks) — confirm each "moves before sa-bcad" verse genuinely has its own sa-bcad, and each "stays before verse" verse genuinely doesn't. Pay particular attention to chapters built around a pre-announced numbered list of faults/virtues or an opponent-refutation dialogue — read a few "moves before sa-bcad" entries there in full context to make sure the ordinal-led block being moved to actually introduces the verse now sitting after it, and not a word or sub-point of the verse just quoted above it (see the false-positive note above); apply.
4. **Stage 3** — dry-run; apply. Confirm every transclusion now has exactly one blank line immediately before and after it, and nothing else changed.
5. **Verify integrity** — compare non-blank lines before/after each apply; they must be byte-identical except for the transclusion lines themselves (present, possibly moved) and the blank lines directly touching them. Confirm the file still decodes as UTF-8 and ends correctly.

---

### Completion check

- [ ] Root confirmed to have `^N-V` (or `^[Roman numeral]-V` front-matter) block IDs; commentary confirmed in `1-SOURCES/`
- [ ] Stage 1: every verse placed (by the matcher or, for a single-line title/homage/colophon segment, by hand) or explicitly left `UNPLACED` with a reason; transclusions = unique ids = root verse count; no duplicates
- [ ] Stage 2: every transclusion sits right before its verse's own sa-bcad block when one exists, and right before the verse otherwise; no sa-bcad block wrongly identified or missed
- [ ] Stage 3: exactly one blank line immediately before and after every transclusion; no blank lines added or removed anywhere else
- [ ] Every inserted transclusion uses the agreed link form
- [ ] No commentary text deleted, reordered, or rephrased (non-blank, non-transclusion lines byte-identical)
- [ ] File decodes as UTF-8 and ends with the intact colophon

---

## Mode 2 — Commentary that introduces verses with a sa-bcad statement

For a commentary that both announces and reproduces the verse: the transclusion goes before the sa-bcad statement, not before the quotation.

This skill embeds `![[root-text#^id]]` transclusion links directly above the sa-bcad — the prose line that announces an outline point (e.g. "དང་པོ་ནི།", "...བསྟོད་པར་མཛད་པ་ནི།", always ending in ནི།) — that precedes each point in a commentary where a root-text verse is quoted verbatim (or near-verbatim) before being explained. It exists because many commentaries in this vault reproduce each verse's own wording inline — often with minor orthographic variants from the root's critical edition — rather than only naming the verse via a sa-bcad heading; readers should see the canonical root text pulled in before the commentary starts announcing and discussing it, not several lines down at the point where the commentary's own quotation happens to repeat the wording. The failure modes this skill prevents: transcluding at the wrong position (immediately above the quotation itself, after the sa-bcad, rather than before the sa-bcad that introduces it), re-embedding the same verse repeatedly when a commentary discusses it line-by-line in several separate places, and missing a match because the commentary's wording differs slightly from the root's.

---

### Inputs

- `root-text-file` — full vault-relative path to a root text or translation under `1-SOURCES/Text/` or `1-SOURCES/Translations/`, with `verse_id_format: chapter-verse` in its frontmatter and every verse already carrying a `^chapter-verse` (or `^letter-verse`, for appendix-style sections such as a benefits/phan-yon block) Obsidian block ID.
- `commentary-file` — one commentary file, typically under `1-SOURCES/Commentaries/`, that quotes root verses inline as part of its own text (in whole stanzas, or split line-by-line across several points). If the commentary only references verses through sa-bcad headings and never quotes their wording, this mode does not apply — use Mode 4 Type 2 instead.

If either file is missing required block IDs, stop and report which IDs are missing rather than guessing a position.

### Output

The same `commentary-file`, modified in place: a transclusion line plus one blank line inserted directly above the sa-bcad paragraph (or paragraphs) leading into every matched verse-quotation block, or directly above the quotation itself when no sa-bcad paragraph precedes it. No existing line is deleted, reordered, or reworded. Total line count increases by exactly two for each verse transcluded.

---

### Output file format

Given a root text with:

```
ཕྱག་འཚལ་སྒྲོལ་མ་མྱུར་མ་དཔའ་མོ། །
སྤྱན་ནི་སྐད་ཅིག་གློག་དང་འདྲ་མ། །
འཇིག་རྟེན་གསུམ་མགོན་ཆུ་སྐྱེས་ཞལ་གྱི། །
གེ་སར་ཕྱེ་བ་ལས་ནི་བྱུང་མ། ། ^1-1
```

and a commentary passage that quotes it (note the orthographic variant, བྱེ་བ vs ཕྱེ་བ, which is tolerated):

```
དང་པོ་ནི།

ཕྱག་འཚལ་སྒྲོལ་མ་མྱུར་མ་དཔའ་མོ། །
སྤྱན་ནི་སྐད་ཅིག་གློག་དང་འདྲ་མ། །
འཇིག་རྟེན་གསུམ་མགོན་ཆུ་སྐྱེས་ཞལ་གྱི། །
གེ་སར་བྱེ་བ་ལས་ནི་བྱུང་མ། ། ^2-2

ཞེས་པ་སྟེ། ...
```

the output is:

```
![[1-SOURCES/Text/<root-text-file>.md#^1-1]]

དང་པོ་ནི།

ཕྱག་འཚལ་སྒྲོལ་མ་མྱུར་མ་དཔའ་མོ། །
སྤྱན་ནི་སྐད་ཅིག་གློག་དང་འདྲ་མ། །
འཇིག་རྟེན་གསུམ་མགོན་ཆུ་སྐྱེས་ཞལ་གྱི། །
གེ་སར་བྱེ་བ་ལས་ནི་བྱུང་མ། ། ^2-2

ཞེས་པ་སྟེ། ...
```

The transclusion moved ahead of the sa-bcad line ("དང་པོ་ནི།"), which stays exactly as worded, right where it was, just now below the embed instead of above it. The commentary's own quotation and block ID are untouched, and nothing after the quotation is touched.

#### When the sa-bcad is more than one paragraph deep

Some outline points accumulate more than one ནི।-ending sentence before the quotation — e.g. a heading-level remark plus its own sub-point's announcement. Only the paragraphs that themselves end in ནི། (immediately before their block ID) count as "the sa-bcad" to jump; an ordinary explanatory paragraph that happens to sit between the heading and the sa-bcad, but ends some other way (དང་།, ཅིང་།, ལའོ།, etc.), is left exactly where it is:

```
##### གསུམ་པ་... ^0-2-2-1-1-3-0
###### དང་པོ་... ^0-2-2-1-1-3-1-0

[general remark, ends ...ལའོ། ། — does NOT end in ནི།, stays in place]

![[root-text.md#^1-4]]

[the actual sa-bcad, ends ...ཚུལ་ནི། — this is what the transclusion jumped]

ཕྱག་འཚལ་དེ་བཞིན་གཤེགས་པའི་གཙུག་ཏོར། །  ^2-16
```

The transclusion also always lands after any markdown heading(s) (##, ###, …) — those are structural navigation, not part of the sa-bcad, and are never displaced.

---

### Rules

1. **Full vault-relative paths only.** Every transclusion link uses the full path from the vault root with the `.md` extension, e.g. `![[1-SOURCES/Text/bo-སྒྲོལ་མ་ཉེར་གཅིག་ལ་བསྟོད་པ།.md#^1-1]]` — never a bare note name or short wiki-link, per **House conventions** above.
2. **Match by content, tolerant of orthographic variants.** A commentary's quotation rarely matches the root byte-for-byte (tsheg/vowel-length spelling, an alternate reading in the commentary's source witness). Match on substantive overlap — the same padas in the same order, allowing for known variant classes (e.g. ཏུཏྟཱ་ར/ཏུ་ཏྟྭ་ར, ཧཱུཾ/ཧཱུྃ, a synonym substitution) — not exact string equality. If a passage cannot be confidently matched to one specific verse (a paraphrase, or overlap ambiguous between two adjacent verses), stop and report it rather than guessing.
3. **One embed per verse, at its first occurrence.** When a commentary explains a verse line-by-line and quotes it in several separate, non-adjacent places (a pada at a time), insert the transclusion of the *complete* verse only above the sa-bcad leading into the *first* of those quotation points. Do not re-embed the same full verse at each subsequent partial quotation — that clutters the file with repeated, partially-spoiling embeds.
4. **Placement is immediately above the sa-bcad, not immediately above the quotation.** Starting from the quotation paragraph, walk backward through any immediately preceding paragraph(s) that are themselves sa-bcad / outline-announcement prose — recognizable because the paragraph, stripped of its trailing block-ID, ends in ནི། (e.g. "དང་པོ་ནི།", "...བསྟོད་པར་མཛད་པ་ནི།"). Keep walking back through a run of consecutive ནི།-ending paragraphs, but stop as soon as you hit a paragraph that does not end in ནི། (ordinary continuing commentary, e.g. ending in དང་།, ཅིང་།, ལའོ། ), a markdown heading, or another transclusion. Insert directly before the topmost paragraph in that ནི།-ending run. If no ནི།-ending paragraph precedes the quotation at all, insert directly above the quotation itself, exactly as before.
5. **Exactly one blank line between the transclusion and the paragraph now immediately following it** (the topmost sa-bcad paragraph, if the verse has one; otherwise the quotation itself), and the transclusion is preceded by whatever spacing already separated the prior content from that paragraph (do not add a second blank line if one already exists there).
6. **Never duplicate an existing transclusion.** Before inserting, check whether a transclusion of that same root block ID already sits at the correct insertion point identified by Rule 4. If so, skip it and note the skip in the report.
7. **Never modify existing content.** No line of the commentary's own quotation, its sa-bcad wording, its block ID, its explanatory prose, or any heading is deleted, reordered, or reworded. Insertions only — the sa-bcad and quotation keep their exact wording and relative order to each other, they just both move below the newly inserted embed.
8. **Preserve existing block IDs as-is.** Do not renumber, move, or re-anchor any `^...` id already present in the commentary.
9. **Report after writing.** For every insertion: the commentary file, the root block ID transcluded, and the first few words of the sa-bcad (or, if none, the quotation) it was placed above. For every skip (rule 3 split-verse continuations, or rule 6 duplicates): note it and why.

---

### Procedure

1. Read `root-text-file`'s frontmatter. Confirm `verse_id_format: chapter-verse` (or equivalent) is present. Extract every block ID and its verse text into a map `{block_id → verse_text}`, including any appendix-style section (e.g. `^a-1`...`^a-N` for a benefits/phan-yon block, `^I-1`...`^I-N` for a front-matter homage) in addition to the main `^chapter-verse` sequence.
2. Read `commentary-file` in full, and split it into paragraphs (blocks of lines set off by blank lines), keeping track of each paragraph's line range and whether it is a markdown heading (starts with `#`), a transclusion (starts with `![[`), or plain prose/verse text.
3. Scan the paragraphs for every one that quotes root-verse wording: it opens with a verse's characteristic opening words and consists of one to four pada lines ending in `།` / `། །` punctuation. For each such paragraph, match it against the map from step 1 using Rule 2 (content match, variant-tolerant). Record the paragraph's index and the matched `block_id`.
4. Group matches by `block_id`. Where a `block_id` has more than one matched paragraph (a split, line-by-line quotation), keep only the earliest (first in document order) as the insertion anchor for that verse; discard the rest per Rule 3.
5. For each insertion anchor, apply Rule 4: walk backward from the quotation paragraph through consecutive non-heading, non-transclusion paragraphs whose text (stripped of its trailing block-ID) ends in ནི།. The insertion point is immediately before the topmost paragraph reached this way, or immediately above the quotation itself if the paragraph directly before it does not end in ནི། (or is a heading, or is the start of the file).
6. At each insertion point, check Rule 6: does a transclusion of that exact `block_id` already sit there? If yes, drop it from the insertion list and record the skip.
7. Sort the remaining insertion points in descending order of line position (bottom of file first) so earlier insertions do not shift the line numbers of later ones.
8. For each insertion point, in that order, insert two lines: `![[<root-text-file, full vault-relative path>#^<block_id>]]`, then a blank line. Everything that was already at and after the insertion point (the sa-bcad run, then the quotation, then the rest of the file) shifts down unchanged.
9. Write the modified `commentary-file`.
10. Report every insertion made (per Rule 9) and every skip (split-continuation or duplicate).

---

### Completion check

- [ ] Both files confirmed to carry the required block IDs before any write; missing IDs reported and execution stopped rather than guessed
- [ ] Every inserted transclusion link uses the full vault-relative path with `.md` extension
- [ ] Every matched quotation verified against the root by content, not exact string equality, with variant spellings tolerated
- [ ] Every transclusion lands before the full run of ནི།-ending sa-bcad paragraphs leading into its quotation (or immediately above the quotation when no sa-bcad precedes it) — never merely above the quotation itself when a sa-bcad exists
- [ ] Markdown headings and any non-ནི།-ending explanatory paragraph between a heading and its sa-bcad were left in place, not displaced by the transclusion
- [ ] No verse re-embedded more than once when its quotation is split across multiple points in the commentary — only the first occurrence carries the transclusion
- [ ] No existing transclusion duplicated at any insertion point
- [ ] No existing line deleted, reordered, or reworded; only insertions made
- [ ] Exactly one blank line separates each transclusion from the paragraph beneath it
- [ ] Any passage that could not be confidently matched to a single verse was reported to the human rather than guessed
- [ ] Post-write report produced listing every verse inserted and every skip, with reasons

---

## Mode 3 — Commentary classified by section category

Classify every section as verse-group overview, verse-by-verse exposition, or neither, then place accordingly.

This is the canonical, general-purpose implementation of the "Format — with transclusions" layout described in the vault's own sources guideline (`1-SOURCES/About Sources.md`). It anchors a commentary to its root text by inserting `![[...]]` transclusion links, but only after classifying *why* the transclusion belongs where it belongs — the three-way distinction that guideline draws between a section that introduces a group of verses, a section that comments verse by verse, and an introductory section with no verse reference at all. Getting this classification wrong is the main failure mode this skill exists to prevent: transcluding all verses at the top of a verse-by-verse section (over-transclusion) or omitting the group transclusion at the opening of an overview section (under-transclusion) both misrepresent the commentary's own structure.

This skill is deliberately structure-first and script-agnostic — it does not assume Tibetan sa-bcad (ས་བཅད) phrasing or any other language's structural idiom. For Tibetan master's commentaries where transclusions must land on the exact line before a sa-bcad phrase (with its own blank-line conventions), use Mode 4 Type 2 (`commentary-type: tibetan-master`) or the scripted pipeline in Mode 1 instead — both give finer control over sa-bcad-level placement than this skill's section-level classification. Use this skill when the classification itself, not the fine placement within a Tibetan structural block, is the open question — including for non-Tibetan commentaries where no equivalent skill exists.

---

### Inputs

| Field | Description | Example |
|---|---|---|
| `root-text-file` | Full vault-relative path to the root text or translation to transclude from. Must declare `verse_id_format: chapter-verse` in frontmatter. | `1-SOURCES/Text/bo-root-text.md` |
| `commentary-file` | Full vault-relative path to the commentary to modify in place. Must be in `1-SOURCES/Commentaries/` with `file_type: commentary`. | `1-SOURCES/Commentaries/<commentary-id>.md` |
| `section-scope` | Optional. A chapter number, a `###` section heading, or `all` (default). Limits which sections are classified and modified in this run. | `1`, `1.2`, `all` |

If any input is missing or the named file does not exist, stop and ask the human contributor before proceeding — do not guess a path.

---

### Output

`commentary-file` is modified in place. The only changes are inserted `![[root-text-file#^N-V]]` transclusion lines, one per verse, each on its own line. No new files are created. No existing commentary text is added, removed, reordered, or rephrased — per the source-permission rule in `4-SYSTEM/Guidelines/skill-locations.md`, which admits internal navigation links such as transclusions.

Alongside the edit, produce a run report (in the response, not written to the vault) listing, for every section in scope: the section heading, its classification (group / verse-by-verse / introductory), and the verse IDs transcluded or skipped-as-duplicate.

---

### Output file format

#### Category A — section introducing a group of verses

All verses in the group are transcluded in sequence at the section's opening, before any commentary text:

```markdown
### 1.2 Verses 1–3 — Overview ^1-2-0

![[1-SOURCES/Text/[lang]-root-text.md#^1-1]]
![[1-SOURCES/Text/[lang]-root-text.md#^1-2]]
![[1-SOURCES/Text/[lang]-root-text.md#^1-3]]

[Introductory overview commentary addressing verses 1–3 together.] ^1-2-1
```

#### Category B — verse-by-verse section

Exactly one transclusion immediately before the commentary on each individual verse:

```markdown
### 1.3 Verse-by-verse commentary ^1-3-0

![[1-SOURCES/Text/[lang]-root-text.md#^1-1]]

[Commentary on verse 1 only.] ^1-3-1

![[1-SOURCES/Text/[lang]-root-text.md#^1-2]]

[Commentary on verse 2 only.] ^1-3-2
```

#### Category C — introductory section, no specific verse reference

No transclusion is inserted:

```markdown
### 1.1 Author's opening remarks ^1-1-0

[General remarks on the chapter's purpose, with no reference to a specific root verse.] ^1-1-1
```

#### Range syntax is never used

Obsidian does not support block-ID range transclusion (`#^1-1:#^1-3`). Category A always expands to sequential individual transclusion lines, one per verse, even for long groups.

---

### Rules

1. **Classify before writing.** Every `###`/`####` section in `section-scope` is assigned exactly one of three categories (A: group, B: verse-by-verse, C: introductory/no-verse) before any transclusion is inserted for that section. A section is never partially classified.
2. **Category A — all-at-once, at the opening.** If a section introduces a defined group of verses, every verse in that group is transcluded in sequence, immediately after the heading and before any commentary prose — never interleaved with the group's commentary.
3. **Category B — one-per-verse, immediately before its own commentary.** If a section addresses verses one at a time, each verse gets exactly one transclusion, placed on the line immediately before the first line of commentary that concerns it — not at the top of the section.
4. **Category C — nothing.** If a section makes no identifiable reference to a specific root verse or verse group (pure introduction, colophon remarks, historical background), no transclusion is inserted, even if the section falls within `section-scope`.
5. **Ambiguous sections stop the run.** If a section could plausibly be A, B, or C (e.g., it names a verse range in its heading but then comments verse by verse in its body), do not guess. Report the section heading and the ambiguity to the human contributor and ask them to classify it before writing that section.
6. **Sequential individual transclusions only.** Never emit a block-ID range. A group of N verses becomes N consecutive `![[...]]` lines.
7. **Full vault-relative paths.** Every transclusion uses the complete path from the vault root — `1-SOURCES/Text/[lang]-root-text.md#^N-V` — never a bare filename or short wiki-link, per **House conventions** above.
8. **Idempotent.** Before inserting `![[root-text-file#^N-V]]`, check whether it already exists at or near the correct position for that verse in that section. If it does, skip and record it as skipped in the report — never insert a duplicate.
9. **Block IDs must exist.** Every verse ID used must be a real block ID (`^N-V`) present in `root-text-file`. If a verse referenced by the commentary's own numbering has no matching block ID in `root-text-file`, stop and report the missing ID rather than fabricating a link.
10. **Insertion only — no other edits.** This skill never adds, deletes, reorders, or rephrases existing commentary text, and never touches headings, block IDs, or frontmatter already present. The only lines it writes are `![[...]]` transclusion lines and the blank lines needed to keep them as their own Markdown block.
11. **Original language only.** No translation, paraphrase, or `[Ed:...]` note is introduced by this skill. If a genuinely factual observation is needed (e.g. to record why a section was classified as C), that is a separate, human-authored `[Ed:...]` note — not something this skill adds on its own.

---

### Procedure

1. Read `root-text-file` frontmatter. Confirm `file_type` is `root-text` or `translation` and `verse_id_format` is `chapter-verse`. Extract every block ID (`^N-V`) into a lookup `{id → verse_text}`. If the frontmatter checks fail, stop and report.
2. Read `commentary-file` frontmatter. Confirm `file_type: commentary`. Note its `verse_id_format` (for the commentary's own numbering, which may differ from the root text's) and, if present, `covers_verses`.
3. Walk the commentary's `##`/`###`/`####` headings within `section-scope`, in document order.
4. For each section, read its heading text and its full body down to the next heading of equal or higher level. Classify it:
   a. **Category A** if the heading or opening line explicitly names a range or set of verses (e.g. "Verses 1–5", "verses covered: 1-1 to 1-3") and the section's body opens with commentary addressing them collectively before, if ever, treating them individually.
   b. **Category B** if the section's body is organized as a sequence of per-verse blocks, each one clearly attributable to a single verse (by explicit numbering, by direct quotation of that verse, or by an existing but misplaced transclusion).
   c. **Category C** if the section contains no identifiable reference to a specific root verse or verse group.
   d. If none of (a)–(c) applies cleanly, do not classify by default to B or any other category — flag as ambiguous per Rule 5.
5. For every Category A section: determine the verse IDs in the group (from the heading's stated range, cross-checked against `root-text-file`'s block IDs). Insert `![[root-text-file#^N-V]]` for each, in order, directly after the heading line and before the first line of commentary prose. Skip any verse whose transclusion already exists there (Rule 8).
6. For every Category B section: for each verse addressed, locate the first line of commentary specific to that verse and insert `![[root-text-file#^N-V]]` on the line immediately before it. Skip any verse whose transclusion already exists there.
7. For every Category C section: make no edit.
8. Before writing, verify every verse ID used in steps 5–6 exists in the `root-text-file` lookup from step 1. If any is missing, stop and report the missing ID(s) without writing.
9. Write `commentary-file` with the insertions applied. Do not alter any other byte of the file.
10. Produce the run report described under Output: section heading, classification, verses transcluded, verses skipped as duplicate, and any sections left unclassified (with reasons) pending human input.
11. Spot-check the written file: confirm no `![[root-text-file#^N-V]]` block ID appears twice, and that every non-inserted line is byte-identical to the pre-write version.

---

### Completion check

- [ ] `root-text-file` confirmed `root-text`/`translation` with `verse_id_format: chapter-verse`; block-ID lookup built
- [ ] `commentary-file` confirmed `file_type: commentary` in `1-SOURCES/Commentaries/`
- [ ] Every section in `section-scope` classified as exactly one of A / B / C, or flagged and reported as ambiguous — none silently defaulted
- [ ] Category A sections: all group verses transcluded in sequence at the section opening, before any commentary prose
- [ ] Category B sections: exactly one transclusion per verse, immediately before that verse's own commentary
- [ ] Category C sections: zero transclusions inserted
- [ ] No block-ID range syntax used anywhere (always sequential individual transclusions)
- [ ] Every transclusion uses the full vault-relative path
- [ ] No duplicate transclusion inserted; every verse ID confirmed to exist in `root-text-file` before writing
- [ ] No existing commentary text added, removed, reordered, or rephrased (non-inserted lines byte-identical before/after)
- [ ] Run report produced covering every section in scope

---

## Mode 4 — Into a second root-text version

The general placement skill, for root-to-root and simple commentary cases.

This skill inserts `![[file#^block-id]]` transclusion links so that root-text verses appear inline at the right point in a second root-text version or in a commentary. It operationalises two distinct workflows — version-to-version alignment and verse-into-commentary placement — and enforces the vault rule that transclusions are navigation aids added to `1-SOURCES/` files, not interpretive content.

Two transclusion types are supported:

1. **Version-to-version** — align two root-text or translation files verse by verse by inserting transclusions of file A into file B (or bidirectionally). Matching uses Obsidian block IDs where both files have them; falls back to meaning-based position matching when one file lacks IDs, in which case the human must confirm every proposed match before the file is modified.

2. **Verse-into-commentary** — insert a transclusion of the root-text verse(s) at the correct structural position in one or more commentary files. For Tibetan master's commentaries the transclusion is placed on the line immediately before the specific sa-bcad (ས་བཅད།) phrase that introduces the commentary section for those verse(s). For non-Tibetan-master commentaries the transclusion is placed at the very beginning of the passage that discusses those verse(s).

---

### Inputs

#### Type 1 — Version-to-version

| Field | Description | Example |
|---|---|---|
| `source-file` | File whose block IDs drive the matching | `1-SOURCES/Text/<root-text>.md` |
| `target-file` | File to receive the transclusion links | `1-SOURCES/Text/<other-version>.md` |
| `verse-range` | Optional: limit to a specific range | `1-11–1-14`, or `all` (default) |
| `direction` | `source-into-target` (default) or `bidirectional` | `source-into-target` |

#### Type 2 — Verse-into-commentary

| Field | Description | Example |
|---|---|---|
| `verse-ids` | One or more block IDs, comma-separated | `1-11, 1-12, 1-13` |
| `root-text-file` | Full vault-relative path to the root text or translation to transclude from | `1-SOURCES/Text/<root-text>.md` |
| `commentary-files` | One or more commentary file paths to receive the transclusions | `1-SOURCES/Commentaries/<commentary-id>.md` |
| `commentary-type` | `tibetan-master` or `other` | `tibetan-master` |

---

### Output

For both types: the target file(s) are modified in place. No new files are created. The only changes to a file are the insertion of `![[...#^...]]` transclusion lines and the blank lines immediately surrounding them. No existing content is deleted, reordered, or rephrased.

---

### Output file format

#### Transclusion line format

Every inserted transclusion is a standalone line using the full vault-relative path:

```
![[1-SOURCES/Text/<root-text>.md#^1-11]]
```

When two or more consecutive verses are transcluded together (because the commentary section covers a verse group), list them on consecutive lines with no blank line between them:

```
![[1-SOURCES/Text/<root-text>.md#^1-13]]
![[1-SOURCES/Text/<root-text>.md#^1-14]]
```

Surround any transclusion block with blank lines on both sides (unless it is already at the top of the file).

#### Type 1 — bundled scripts

Type 1 is the one case that is fully mechanical (both files carry block IDs, so
the match is an ID join, not a judgment), and three stdlib-only scripts do it:

| Script | Use when |
|---|---|
| `4-SYSTEM/Skills/transclusion/scripts/insert_transclusions.py` | the target puts **one verse per line** (each verse line ends in its own `^N-V`) |
| `4-SYSTEM/Skills/transclusion/scripts/insert_root_transclusions.py` | the target puts **one verse per paragraph** (a blank-line-separated block whose last line carries the `^N-V`) |
| `4-SYSTEM/Skills/transclusion/scripts/remove_transclusions.py` | undoing a run, or clearing transclusions before re-inserting them against a different source |

```bash
# one verse per line — dry run, then apply
python3 4-SYSTEM/Skills/transclusion/scripts/insert_transclusions.py \
  --source "1-SOURCES/Text/<root-text>.md" "<target.md>" --dry-run
python3 4-SYSTEM/Skills/transclusion/scripts/insert_transclusions.py \
  --source "1-SOURCES/Text/<root-text>.md" "<target.md>"

# one verse per paragraph — dry run is the default; --apply writes
python3 4-SYSTEM/Skills/transclusion/scripts/insert_root_transclusions.py \
  --source "1-SOURCES/Text/<root-text>.md" --target "<target.md>"
python3 4-SYSTEM/Skills/transclusion/scripts/insert_root_transclusions.py \
  --source "1-SOURCES/Text/<root-text>.md" --target "<target.md>" --apply

# remove every standalone ![[...]] embed again
python3 4-SYSTEM/Skills/transclusion/scripts/remove_transclusions.py "<target.md>" --dry-run
python3 4-SYSTEM/Skills/transclusion/scripts/remove_transclusions.py "<target.md>"
```

Both inserters are **idempotent** (an ID already preceded by its transclusion is
skipped, so a partially-transcluded file is safe to re-run) and both **skip
structural IDs by design** — the bare title `^0` and any heading ID ending in
`-0` are never transcluded. `--source` is the full vault-relative path written
inside the link; it is required and has no default.

These scripts handle only the both-files-have-IDs case. When the target lacks
block IDs, Rule 6 applies: build the match list by meaning and get human
confirmation before writing anything — no script does that for you.

#### Type 1 placement — version-to-version

Insert the transclusion of `source-file#^N-V` immediately before the corresponding verse block in `target-file`. The result looks like:

```
![[1-SOURCES/Text/<root-text>.md#^1-11]]

सुपरीक्षितमप्रमेयधीभि-र्बहुमूल्यं ... ^1-11
```

#### Type 2 placement — Tibetan master's commentary

For a Tibetan master's commentary, the transclusion is placed on the line **immediately before** the sa-bcad phrase (structural announcement) that introduces the commentary section for those verse(s). The sa-bcad phrase is the Tibetan enumeration phrase that opens a section (e.g., `གཉིས་པ་རིན་པོ་ཆེའི་དཔེས་བསྔགས་པ་ནི།`). A blank line precedes the transclusion block, and no blank line is inserted between the transclusion and the sa-bcad line:

```
ཞེས་པ་ལྟར་རོ། །

![[1-SOURCES/Text/<root-text>.md#^1-11]]
གཉིས་པ་རིན་པོ་ཆེའི་དཔེས་བསྔགས་པ་ནི།
```

If the verse section is introduced by a Markdown heading (e.g., `### 1.2 ...`) rather than an inline sa-bcad, place the transclusion immediately before that heading line instead.

#### Type 2 placement — other commentary

For non-Tibetan-master commentaries, insert the transclusion at the very beginning of the passage identified as discussing those verse(s), preceded and followed by a blank line:

```
![[1-SOURCES/Text/<root-text>.md#^1-11]]

[commentary passage begins here]
```

---

### Rules

1. **Read-only except for navigation links.** `1-SOURCES/` files may receive block IDs, frontmatter, internal navigation links, and `[Ed:...]` editorial notes only. Transclusion links qualify as internal navigation links. No other content may be added, removed, or changed.
2. **Full vault-relative paths only.** Every transclusion link must use the full path from the vault root (e.g., `1-SOURCES/Text/<root-text>.md#^1-11`), never a bare filename or short wiki-link.
3. **Never duplicate an existing transclusion.** Before inserting, check whether `![[source-file#^N-V]]` already appears in the vicinity of the target position. If it does, skip that verse and note it in the report.
4. **Never modify existing content.** Insertions only. Do not reorder, reformat, or delete any existing text.
5. **Block ID mismatch stops execution (Type 1, both-have-IDs case).** If the same block ID (`^N-V`) is present in one file but absent in the other, or if the verse counts differ across the target range, report every mismatch to the human before writing any changes. Do not proceed until the human confirms.
6. **Meaning-based matching requires human confirmation (Type 1, one-lacks-IDs case).** Present the full proposed match list (source verse text → target verse position) before writing. Do not proceed until the human confirms or corrects.
7. **Sa-bcad identification (Type 2, tibetan-master).** The sa-bcad to insert before is identified by:
   a. Markdown headings with block IDs ending in `-0` (e.g., `^1-2-0`, `^1-2-1-0`) — insert immediately before that heading line.
   b. Inline Tibetan structural enumeration phrases — ordinal words (གཅིག་པ་, གཉིས་པ་, གསུམ་པ་, བཞི་པ་, etc. or their equivalents) followed by a topic phrase ending in ནི། or ནི། །. These are the inline sa-bcad phrases. Insert immediately before the matching phrase.
   c. If no sa-bcad can be confidently identified for a verse, report it and ask the human to specify the insertion point before writing.
8. **Commentary-section matching (Type 2).** Identify the correct commentary section by:
   a. First: check whether the commentary has a TOC or explicit structural outline and use it to locate the section for the verse(s).
   b. Second: scan for context clues — verse number mentions, quotations of the verse, or key terms from the verse.
   c. If the correct section cannot be identified with confidence, report the ambiguity and ask the human before writing.
9. **Multiple commentaries.** When `commentary-files` lists more than one file, process each file independently using the same verse-ids. Do not carry state or assumptions from one commentary to the next.
10. **Report after every write.** For each file modified, report: the file path, the verse(s) inserted, and the exact line or phrase before which each transclusion was placed.

---

### Procedure

#### Type 1 — Version-to-version

1. Read the frontmatter of both `source-file` and `target-file`. Confirm both are in `1-SOURCES/` and have `file_type: root-text | translation`. If not, stop and report.
2. Extract all block IDs from `source-file` in the form `^chapter-verse` (e.g., `^1-11`). Build a list: `{block_id → verse_text}`.
3. Extract all block IDs from `target-file` in the same form. Build a parallel list.
4. **If both files have block IDs:**
   a. Intersect the two lists over the requested `verse-range`.
   b. Identify any IDs present in one file but absent in the other. List every mismatch.
   c. If mismatches exist: present the full mismatch report to the human. Ask: "Proceed with matching verses only, or stop?" Do not write until the human responds.
   d. If no mismatches (or the human confirmed): for each matched ID, check if `![[source-file#^N-V]]` already exists adjacent to the target verse block. If yes, skip. If no, insert the transclusion immediately before `^N-V` in `target-file`.
5. **If `target-file` lacks block IDs:**
   a. Align source verses to target verse positions by order and meaning within the requested range.
   b. Produce a numbered match list: `source ^N-V "[first few words of source verse]" → target line N "[first few words of target verse]"`.
   c. Present the full match list to the human. Ask them to confirm or correct before writing.
   d. On confirmation: insert each transclusion at the identified target position.
6. Write the modified `target-file`. Report each insertion made.

#### Type 2 — Verse-into-commentary

1. Read the frontmatter of `root-text-file`. Confirm it is in `1-SOURCES/Text/` or `1-SOURCES/Translations/` and has a `verse_id_format: chapter-verse` field. Record its full vault-relative path for use in transclusion links.
2. For each verse ID in `verse-ids`, confirm the block ID `^N-V` exists in `root-text-file`. If any ID is missing, stop and report which IDs are absent.
3. For each `commentary-file` in `commentary-files`:
   a. Read the commentary file in full.
   b. Determine `commentary-type` for this file (passed as input; default to `tibetan-master` for files with `lang_tag: bo` from `1-SOURCES/Commentaries/`).
   c. **If `commentary-type` is `tibetan-master`:**
      i. Locate the sa-bcad phrase or Markdown heading that introduces the commentary section for each target verse. Use Rule 7 (sa-bcad identification) and Rule 8 (commentary-section matching).
      ii. If a sa-bcad or heading cannot be confidently identified for any verse, report the uncertainty to the human and ask them to specify the insertion line before proceeding.
      iii. Check whether `![[root-text-file#^N-V]]` already appears on the line immediately before the identified sa-bcad. If yes, skip. If no, insert the transclusion on the line immediately before the sa-bcad. Ensure a blank line precedes the transclusion block and no blank line separates the transclusion from the sa-bcad line.
   d. **If `commentary-type` is `other`:**
      i. Locate the beginning of the passage that discusses the target verse(s) using Rule 8.
      ii. If the passage start cannot be identified, report and ask the human.
      iii. Insert the transclusion block at that point, surrounded by blank lines on both sides.
   e. Write the modified commentary file.
   f. Report: file path, verse(s) inserted, and the sa-bcad phrase or passage-start text before/at which each transclusion was placed.

---

### Completion check

- [ ] Both files confirmed to be in `1-SOURCES/` before any write (Type 1), or root-text and commentary files confirmed to exist and be in `1-SOURCES/` (Type 2)
- [ ] All target block IDs verified to exist in `root-text-file` before writing (Type 2)
- [ ] Mismatch report produced and human confirmation obtained before writing when block IDs diverge (Type 1, both-have-IDs)
- [ ] Full match list produced and human confirmation obtained before writing when one file lacks block IDs (Type 1)
- [ ] Sa-bcad or commentary passage correctly identified for every verse; human consulted for any uncertain placements (Type 2, tibetan-master)
- [ ] No existing transclusion duplicated at any insertion point
- [ ] Every inserted transclusion uses the full vault-relative path
- [ ] No existing text deleted, reordered, or rephrased in any file
- [ ] Post-write report produced listing every file modified, every verse inserted, and every insertion position
