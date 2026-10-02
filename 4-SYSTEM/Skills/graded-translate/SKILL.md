---
name: graded-translate
description: >
  Produce an audience-graded, term-consistent translation of a block-ID'd verse
  text into any target language: first build a per-grade keyword termbase for
  that language on top of the keyword-extract output or the rails' own concept
  lists (beginner / general / intermediate / advanced, rank-cut and
  register-adapted, optionally seeded from an attested human translation), then
  translate chapter by chapter with every termbase rendering locked, then run
  the mechanical drift check.

  Trigger on "translate to <language> by audience level", "beginner Hindi version",
  "scholarly English translation", "term-consistent Vietnamese", "grade-level
  keywords", "build the <language> termbase", "standardise the vocabulary before
  translating", "check the translation for termbase drift".

  This is the vocabulary-standardised path. Use `machine-translate` or
  `zeroshot-translate` Mode 2 for a rough first look; use this skill for anything
  that will be published or fact-checked.
---

# Graded, term-locked translation

| Phase | Does | Input | Output |
|---|---|---|---|
| 1 — Keyword grade | Builds the target-language termbase, one file per audience grade, on top of the source-enriched keyword inventory | keyword source (see below) · base termbase · optional attested translation | the track's `termbase.md` (canonical) + `2-RAILS/Termbases/<src>_<tgt>_keyword_<grade>.json` (build cache) |
| 2 — Translate | Translates chapter by chapter at the grade's register with every termbase rendering locked | one grade file from Phase 1 + the track contract | `3-TRANSFORMATIONS/Translations/<tgt>-<grade>/<text-id>-<tgt>-<grade>.md` |
| 3 — Drift check | Mechanically verifies that every locked rendering actually appears in every verse that needs it | termbase + translation (+ verse rails) | pass / MISSING table |

Run the phase asked for. Phase 2 refuses to run without its Phase 1 file — it
must not improvise term choices. Phase 3 is the check that makes "term-consistent"
a claim rather than a hope; `commentary-fact-check` is the separate accuracy
backstop that runs after it.

**Why this exists.** A zero-shot translation renders each verse (or each API
batch) independently. The same source term can come out three different ways
across a long text and nothing flags it. Locking the vocabulary *before*
translating — at the register the audience needs — is what makes the output
publishable and checkable. One vault's end-to-end run of the chain is written
up in [`references/worked-example.md`](references/worked-example.md); it is a
history, not a contract.

**Language is a parameter, not a fork.** The original vault had one skill pair
per language that differed only in the target code and the register table. Here
`<src>` is the source-language tag and `<tgt>` the target ISO code (`en`, `hi`,
`vi`, `zh`, `ne`, `mn`, …), the JSON fields are `<tgt>` / `<tgt>_text`, and the
per-language register tables live in §Registers below. To add a language, add
its register table; do not copy the skill.

**The pivot is an input.** Phase 1 keys its termbase on a **pivot translation**:
any block-ID-aligned translation of the same text. That is normally a reviewed
human translation in `1-SOURCES/Translations/`, but a `zeroshot-translate` **Mode 2**
unconstrained draft will do when no human translation exists — that is exactly
what Mode 2 is for. Name the pivot in the run and record it in the output
frontmatter. Nothing here requires the pivot to be English; English is simply
the most commonly available pivot.

---

## Inputs

| Input | Phase | Required | Description |
|---|---|---|---|
| **Target language** `<tgt>` | 1, 2, 3 | ✓ | ISO code. Determines file names and which register table applies. |
| **Grade(s)** | 1, 2 | ✓ | `beginner`, `general`, `intermediate`, `advanced`, or `all` (Phase 1 only). Ask if not given. |
| **Source root text** | 1 | ✓ | The root text this vault translates, **per `4-SYSTEM/Guidelines/vault-annex.md`** — canonical verse text with `^verse-id` markers under `1-SOURCES/Text/`. |
| **Pivot translation** | 1 | ✓ | Any block-ID-aligned translation of the same text: a human translation in `1-SOURCES/Translations/`, or a `zeroshot-translate` Mode 2 draft from `0-INBOX/temp/zeroshot/`. Its keys are what the termbase is keyed on. |
| **Keyword source** | 1 | ✓ | **Either** `keyword-extract`'s enriched output in `2-RAILS/Keywords/` (`{verse_id: {text, keywords:[…]}}` with a source-language meaning per keyword), **or** the rails: the `concepts_in_verse:` and `concepts_in_commentary:` lists in `2-RAILS/Verses/<id>.md`. Use the rails when no keyword-extract run exists — they are the descriptive record of which terms each verse turns on, which is exactly what the cutoff is applied to. Say in the report which source was used. |
| **Base termbase** | 1 | ✓ (built if absent) | `2-RAILS/Termbases/<src>-<pivot>-<tgt>-termbase-general.json`. If missing, build it from another language's base (same pivot key set), dropping that language's field and filling `<tgt>` per §Registers. |
| **Track contract** | 1, 2 | ✓ | `3-TRANSFORMATIONS/Translations/<tgt>-<grade>/` must carry `requirements.md`, `audience.md` and `termbase.md`. If the folder or any contract file is missing, create the folder and the three files first (register/grade from §Registers, audience from the grade's row) — a track without its contract is not a track. |
| **Attested translation** | 1 | optional | An existing human or reviewed translation in `<tgt>`, block-ID aligned. Its renderings are authoritative and override the base termbase. Its frontmatter `track:` may name the grade it seeds (default: general/intermediate). |
| **Source text to translate** | 2 | ✓ | The `<src>_text` (source language) or the pivot `text` field of the grade file. Prefer the source language when the translator can read it; say which in the output frontmatter. |
| **Verse scope** | 2, 3 | optional | Chapter(s) or verse IDs. Default: all. |

---

## Phase 1 — Keyword grade: build the per-grade termbase

### Grade levels

| Grade | Audience | Keyword rank cutoff |
|---|---|---|
| `beginner` | General public, new to Buddhism | rank ≤ 200 |
| `general` | Educated general reader | rank ≤ 500 |
| `intermediate` | Students with basic Buddhist study | rank ≤ 500 |
| `advanced` | Scholars, monks, serious practitioners | all ranks |

Rank comes from the keyword source: `keyword-extract`'s corpus-level TF-IDF /
YAKE rank where that run exists, otherwise a rank derived from the rails —
count how many verses list each term in `concepts_in_verse:` /
`concepts_in_commentary:` and rank by descending frequency, ties broken by
first occurrence. The cutoff controls how much vocabulary the grade *exposes as
locked terms*; it does not change which verses are translated.

### Grade classification — keywords

**beginner** — terms a newcomer understands after one teaching:
> buddha, dharma, karma, compassion, virtue, mind, suffering, body, death, birth, joy, faith, peace

**intermediate** — terms requiring study of basic Buddhist philosophy:
> bodhichitta, bodhisattva, emptiness, samsara, nirvana, merit, refuge, precepts, mindfulness,
> attachment, afflictions, wisdom, samadhi, dedication, renunciation, patience, diligence

**advanced** — technical Abhidharma, Madhyamaka, or tantric terminology:
> dharmakaya, tathagatagarbha, alayavijnana, dependent origination (technical), two truths,
> trikaya, prajnaparamita, madhyamaka, shamatha, vipashyana, any transliterated Skt/Tib term

When a keyword sits on a boundary, assign the lower (more accessible) grade.

### Termbase structures

**The canonical termbase is the track's `termbase.md`.** It is the contract the
rest of the vault reads, the thing `translation-qa` checks against, and the file
a human reviews. The JSON files below are a **build cache**: they exist so a
long run is resumable and machine-checkable, they live under `2-RAILS/Termbases/`, and
they are regenerable from the markdown. When the two disagree, the markdown
wins — regenerate the cache, never the reverse.

Track termbase — `3-TRANSFORMATIONS/Translations/<tgt>-<grade>/termbase.md`:

```markdown
| Source lemma | Locked <tgt> rendering | Gloss | Verses |
|---|---|---|---|
| <lemma> | <rendering> | <short gloss> | 1-1, 2-3 |
```

Base termbase cache — `2-RAILS/Termbases/<src>-<pivot>-<tgt>-termbase-general.json`:

```json
{
  "keyword_pivot": {
    "<src>": "source-language meaning",
    "<tgt>": "target-language meaning at general level",
    "rank": 0,
    "verse_ids": ["1-1", "2-3"]
  }
}
```

`verse_ids` is populated from the keyword source in Step 2 and lets every term
be traced back to the verses it occurs in.

Grade file cache — `2-RAILS/Termbases/<src>_<tgt>_keyword_<grade>.json` (also Phase 2's
input and write-back target):

```json
{
  "verse_id": {
    "text": "Pivot translation — unchanged",
    "<src>_text": "Source-language lines — added",
    "<tgt>_text": "Translation at this grade — added (Phase 2 fills it)",
    "keywords": [
      {
        "key": "pivot_term",
        "rank": 0, "score": 0.0, "count": 0,
        "<src>": "source-language meaning — unchanged",
        "<tgt>": "target-language meaning at this grade — added",
        "grade": "beginner"
      }
    ]
  }
}
```

When the target language *is* the pivot language, the base `text` is the pivot
translation and `<tgt>_text` is the *graded* rewrite; the two are different
fields on purpose.

### Procedure

**Step 0 — Check the track contract.** Confirm
`3-TRANSFORMATIONS/Translations/<tgt>-<grade>/` exists with `requirements.md`,
`audience.md` and `termbase.md`. Create any that are missing before going on:
the requirements from the grade's register row, the audience from the grade's
audience row, and an empty `termbase.md` with the table header above.

**Step 1 — Load the base termbase.** If
`2-RAILS/Termbases/<src>-<pivot>-<tgt>-termbase-general.json` does not exist, build it:
take the key set of any existing base for another target language (same pivot
key set), drop that language's field, and fill `<tgt>` for each key using the
register table and — first — any attested translation supplied.

**Step 2 — Load the keyword source and populate `verse_ids`.** From
`keyword-extract`'s enriched JSON, or from the rails' `concepts_in_verse:` /
`concepts_in_commentary:` lists: for every keyword in every verse, add the verse
ID to the termbase entry; create a stub (`<src>` from the keyword, `<tgt>`
empty, `rank`, `verse_ids`) for any keyword not yet in the termbase.

**Step 3 — Parse the pivot and the attested translation (if given).** Build
`{verse_id → text}` for each. Two parse rules matter and are easy to get wrong:

- **Skip any line that starts with `![[` or `#`.** A transclusion line is
  structural, not content, and a heading is editorial. Folding either into a
  verse's text poisons every downstream match.
- Join the lines of a multi-line verse into one block; the verse ID is the
  trailing `^id` on the block's last line. Skip closing notes and colophon
  prose that carries no verse ID.

**Step 4 — Extend the termbase from the attested translation.** For each verse,
for each of its keywords: if the base rendering occurs in the attested text,
confirm it; if a different rendering is attested, replace the base value with
the attested form and log the change; if the base value is empty, read the
rendering off the attested text. Attested beats base beats invented.

**Ignore any keyword whose rendering is identical to its key.** An entry whose
`<tgt>` value is just the pivot key echoed back is not a translation — it is an
unfilled cell that looks filled. Treat it as empty, and report it among the
keywords still needing a rendering.

Save the updated base termbase cache **and** write the confirmed rows into the
track's `termbase.md`.

**Step 5 — Parse the source root text** into `{verse_id → <src>_text}`, joining
the lines of a multi-line verse and applying the same two parse rules as Step 3
(skip lines starting with `![[` or `#`).

**Step 6 — Derive grade variants** of every `<tgt>` value from the general base,
using the adaptation rules in §Registers (general → beginner strips jargon and
glosses; general → intermediate keeps the technical term, may add a precision
qualifier; general → advanced adds the Sanskrit/technical form in parentheses).
Keep values short (1–6 words); match the Buddhist sense, not the dictionary
sense; prefer an attested form over a new one.

**Step 7 — Build the grade files.** For each requested grade: every verse gets
`text`, `<src>_text`, `<tgt>_text` (attested text for the grade it seeds, otherwise
empty until Phase 2), and the keywords that survive the rank cutoff, each with
its grade-adapted `<tgt>` and `grade`.

**Step 8 — Save and verify.** Write each file to a temp path, then copy into
`2-RAILS/Termbases/` and re-load it to confirm it parses. Export the grade's locked
rows into the track's `termbase.md`. Print per grade: verse count, keyword
count, and every keyword whose `<tgt>` is still empty (or equal to its key) —
those must be filled before Phase 2 uses the file.

Phase 1 writes only to `2-RAILS/Termbases/` and the track's `termbase.md`. It never
modifies `1-SOURCES/Text/`, `1-SOURCES/Translations/`, the keyword source, or the attested
translation.

### Completion check — Phase 1

- [ ] Track folder exists with `requirements.md`, `audience.md` and `termbase.md`.
- [ ] Base termbase loaded (or built and saved) for `<tgt>`.
- [ ] `verse_ids` populated from the keyword source; the report says which source was used.
- [ ] Pivot and attested translation parsed with lines starting `![[` or `#` skipped.
- [ ] Attested translation's renderings folded into the termbase; changes logged.
- [ ] `<src>_text` set for every verse.
- [ ] Every keyword in every grade file has a `<tgt>` that is non-empty **and not equal to its key**, plus a `grade`; rank cutoff applied.
- [ ] Track `termbase.md` updated from the grade rows — it, not the JSON, is the contract.
- [ ] Files re-loaded after writing; nothing outside `2-RAILS/Termbases/` and the track folder touched.

---

## Phase 2 — Translate with the termbase locked

**Step 1 — Load the grade file** `2-RAILS/Termbases/<src>_<tgt>_keyword_<grade>.json`
and build a flat `key → <tgt>` dict (first occurrence wins), **skipping any
entry whose rendering equals its key** — that is an unfilled cell, not a
rendering. Reconcile the dict against the track's `termbase.md`; where they
disagree, the markdown wins. This dict is the single source of truth for
terminology in this run. **If the grade file does not exist, stop and say Phase
1 must be run first** — do not choose renderings ad hoc.

**Step 2 — Group verses by chapter** (first segment of the verse ID) and process
chapters in the text's own order. Read the chapter set off the root text's
`^N-0` headings — never assume a chapter count or numbering. A text may have a
chapter `0`, roman-numeral front matter, and lettered back matter.

**Step 3 — Translate chapter by chapter.** For each chapter:

1. **Lock the terms** — scan the chapter's verses for termbase keys. Their
   `<tgt>` renderings are fixed; no synonyms, no register-driven substitutions.
2. **Translate each verse** from `<src>_text` (or regrade the pivot `text`),
   writing at the grade's register (§Registers) and within the track's
   `requirements.md`, with locked terms substituted.

Rules: locked terms override register · translate line by line · never add
content · inflection and natural target-language word order are allowed.

**Step 4 — Consistency pass.** Re-scan the whole output for every locked term;
fix any verse that used a non-termbase form. Write each verse's `<tgt>_text`
back into the grade file.

**Step 5 — Write the markdown.** One block per verse, translated text followed
by its block ID, blank line between blocks; headings (`id` ends in `-0`) as
`## <text> ^<id>`:

```
<tgt_text> ^<verse_id>
```

Path: `3-TRANSFORMATIONS/Translations/<tgt>-<grade>/<text-id>-<tgt>-<grade>.md`.
Body is target language only — no source, no metadata in the body. Provenance
goes in the frontmatter:

```yaml
---
title: "<work title> — <tgt> (<grade>)"
transformation_type: translation
track: <tgt>-<grade>
lang_tag: <tgt>
root_text: 1-SOURCES/Text/<lang>-root-text.md
pivot_translation: <path to the pivot used>
translated_from: <src>_text | text        # say which field was the base
grade_file: 2-RAILS/termbases/<src>_<tgt>_keyword_<grade>.json
context_packages:
  - 3-TRANSFORMATIONS/Translations/<tgt>-<grade>/requirements.md
  - 3-TRANSFORMATIONS/Translations/<tgt>-<grade>/termbase.md
  - 3-TRANSFORMATIONS/Translations/<tgt>-<grade>/audience.md
  - 2-RAILS/Verses/<verse-id>.md            # every rail consulted
covers_verses: "<A>–<B>"
generation_date: <YYYY-MM-DD>
status: draft
---
```

If the vault's translation convention is the transclusion layout (root block
transcluded above each translated block — see `4-SYSTEM/Guidelines/annotation-conventions.md` and the
vault's own linter), produce that layout instead; the block-ID contract is
identical.

### Adapting between grades

- **general → beginner**: strip parenthetical and untranslated technical terms;
  replace them with the beginner termbase's plain forms; gloss on first use if
  unavoidable.
- **general → advanced**: add the Sanskrit/technical term in parentheses; use
  the advanced termbase's more precise equivalents.
- Always switch to the **target grade's** file — never mix entries from two grades.

### Completion check — Phase 2

- [ ] Grade specified; the matching grade file loaded (or the run stopped because it is missing).
- [ ] Locked-term dict built from the whole file, first occurrence wins, key-equals-rendering entries skipped.
- [ ] Dict reconciled against the track's `termbase.md`; markdown wins on any conflict.
- [ ] Chapters read off the root's `^N-0` headings and processed in the text's own order; locked terms identified per chapter before translating.
- [ ] Register matches the grade table for `<tgt>` and the track's `requirements.md`.
- [ ] Consistency pass done; same rendering for the same term throughout.
- [ ] Markdown written, one verse per block, `^id` on the same line, headings as `## … ^N-0`.
- [ ] Output frontmatter carries `transformation_type: translation`, `track`, `context_packages`, `covers_verses`, `generation_date`, `status: draft`.
- [ ] No JSON modified except the grade file's own `<tgt>_text` write-back.

---

## Phase 3 — Mechanical drift check

```bash
python3 4-SYSTEM/Skills/graded-translate/scripts/check_termbase_consistency.py \
    --termbase   3-TRANSFORMATIONS/Translations/<track>/termbase.md \
    --translation 3-TRANSFORMATIONS/Translations/<track>/<file>.md \
    --rails-dir  2-RAILS/Verses \
    --verses 1-1 1-2 1-3
```

The script parses a `termbase.md` table (`| source lemma | locked rendering |
note |`, several source variants per row separated by ` / `, parenthetical
glosses accepted as alternate surface forms), reads each verse rail's
`concepts_in_verse:` (fallback `concepts_in_commentary:`) to learn which lemmas
are load-bearing in that verse, splits the translation on trailing `^id`
markers (footnote bodies are folded into the verse that cites them), and
reports per (verse, lemma): **EXACT**, **LOOSE** (article-stripped,
de-pluralised), or **MISSING**. MISSING is a human-look item — a legitimate
paraphrase or real drift.

Two things to know:

- It reads the **markdown termbase**, the `termbase.md` a track keeps under
  `3-TRANSFORMATIONS/Translations/<track>/`. That file is the contract and Phase
  1 Step 8 already wrote it; the grade JSON is only the build cache. If the two
  have drifted, regenerate the cache from the markdown and re-run — do not
  check against the JSON instead.
- It needs verse rails (`2-RAILS/Verses/<id>.md` with `concepts_in_verse:`) to know
  which lemmas to expect in which verse. Where no rails exist yet, use the
  keyword source's own per-verse keyword lists as the expectation instead —
  that is exactly what Phase 2 Step 4 does by hand.

Every MISSING must be either fixed or explained in the translation's notes
before the file is handed to `commentary-fact-check`.

---

## Registers

Locked terms override register in every case. The tables give the *style* of
the surrounding prose and the *shape* of a grade-adapted term.

### English (`en`)

| Grade | Style |
|---|---|
| **beginner** | Plain modern English. No unglossed Sanskrit/Pali/Tibetan. Gloss any unavoidable technical term inline: "the wish to awaken for the sake of all beings (bodhichitta)". |
| **general** | Standard English prose. Common Buddhist loanwords used freely (bodhichitta, karma, nirvana) without gloss. |
| **intermediate** | English + untranslated Sanskrit/Pali terms for technical concepts (kleśas, prajñā) used without gloss. |
| **advanced** | Sanskrit/Pali-rich technical register. Full Abhidharma/Madhyamaka vocabulary; parenthetical Sanskrit/Tibetan for key terms. |

| Concept | beginner | general | advanced |
|---|---|---|---|
| bodhichitta | the wish to awaken for the sake of all beings | bodhichitta | bodhichitta (bodhicitta) |
| suffering | suffering | suffering | suffering (duḥkha; three types of duḥkhatā) |
| emptiness | the lack of any fixed, separate self in things | emptiness | emptiness (śūnyatā; niḥsvabhāvatā) |
| merit | good karma from virtuous action | merit | merit (puṇya) |
| liberation | freedom from suffering | liberation | liberation (mokṣa; vimokṣa) |

When `<tgt>` equals the pivot language, the base `text` is already in that
language, so Phase 2 is a *regrade* unless translating from `<src>_text`. The
pivot's keyword set is the one every target language's termbase is keyed on —
so a vault should pick one pivot and keep it.

### Hindi (`hi`)

| Grade | Style |
|---|---|
| **beginner** | Plain Hindustani, everyday words, no unglossed Sanskrit. Gloss Sanskrit on first use: बोधिचित्त (सबके भले की इच्छा). |
| **general** | Modern standard Hindi. Sanskrit Buddhist terms used freely. Flowing prose. |
| **intermediate** | Hindi + classical Sanskrit. Terms like क्लेश, प्रज्ञा used without glosses. Precise but readable. |
| **advanced** | Sanskrit-rich. Full Abhidharma/Madhyamaka vocabulary. Parenthetical expansions welcome. |

| English | beginner | general | intermediate | advanced |
|---|---|---|---|---|
| compassion | दया | करुणा | करुणा | करुणा / अनुकम्पा |
| emptiness | खालीपन | शून्यता | शून्यता | शून्यता (सर्वधर्मनिःस्वभावता) |
| merit | पुण्य | पुण्य | पुण्य / कुशल | कुशलकर्म |
| bodhichitta | सबके भले की इच्छा | बोधिचित्त | बोधिचित्त | बोधिचित्त (संवोधिचित्त) |
| suffering | दुःख | दुःख | दुःख | दुःख (सर्वसंस्कारदुःखता) |
| liberation | मुक्ति | मुक्ति | मुक्ति | विमोक्ष |

Adaptation: general → beginner replaces Sanskrit with plain Hindi
(`बोधिचित्त` → `सबके भले की इच्छा`, `करुणा` → `दया`, `शून्यता` → `खालीपन`);
general → intermediate keeps the Sanskrit and may add a qualifier
(`पुण्य` → `पुण्य / कुशल`); general → advanced adds the technical Sanskrit in
parentheses (`शून्यता` → `शून्यता (सर्वधर्मनिःस्वभावता)`). Keep values 1–5 words.

### Vietnamese (`vi`)

| Grade | Style |
|---|---|
| **beginner** | Plain modern Vietnamese, short sentences. Sino-Vietnamese/Sanskrit terms glossed in parentheses on first use: tâm bồ đề (lòng mong muốn giúp tất cả chúng sinh thoát khổ). |
| **general** | Modern standard Vietnamese. Common Sino-Vietnamese Buddhist terms used freely (Phật, Pháp, Bồ Tát, từ bi, hồi hướng). Flowing prose. |
| **intermediate** | Vietnamese + precise Sino-Vietnamese terms. Terms like phiền não, ba-la-mật used without glosses. Readable but exact. |
| **advanced** | Sino-Vietnamese/Sanskrit-rich. Full Abhidharma/Madhyamaka vocabulary, Sanskrit terms transliterated or parenthesised. |

| English | beginner | general | intermediate | advanced |
|---|---|---|---|---|
| compassion | lòng thương người | từ bi | từ bi | từ bi (đại bi tâm) |
| emptiness | sự trống rỗng của mọi thứ | tánh không | tánh không | tánh không (vô tự tính) |
| merit | việc tốt, phước đức | công đức | công đức / phước đức | phước đức, công đức |
| bodhichitta | tâm muốn giúp tất cả mọi người | tâm bồ đề | tâm bồ đề | tâm bồ đề (bồ đề tâm) |
| suffering | khổ, nỗi khổ | khổ đau | khổ đau | khổ đau (khổ đế) |
| bodhisattva | vị Bồ Tát, người phát nguyện cứu giúp chúng sinh | Bồ Tát | Bồ Tát | Bồ Tát (Bồ-đề-tát-đỏa) |
| samsara | vòng sinh tử luân hồi | luân hồi | luân hồi | luân hồi (sinh tử luân hồi) |
| nirvana | sự giải thoát hoàn toàn khỏi khổ đau | niết bàn | niết bàn | Niết-bàn (Nirvāṇa) |
| afflictions (kleshas) | cảm xúc xấu | phiền não | phiền não | phiền não (kleśa) |
| mindfulness | luôn để ý, tỉnh táo | chánh niệm | chánh niệm | chánh niệm (smṛti) |
| dedication | chia sẻ công đức cho người khác | hồi hướng | hồi hướng | hồi hướng công đức |
| patience | kiên nhẫn, nhịn nhục | nhẫn nhục | nhẫn nhục | nhẫn nhục ba-la-mật |
| diligence | cố gắng, chăm chỉ | tinh tấn | tinh tấn | tinh tấn ba-la-mật |
| refuge | nương tựa | quy y | quy y, nương tựa | quy y Tam Bảo |

Adaptation: general → beginner replaces Sino-Vietnamese/Sanskrit with plain
Vietnamese or a short gloss (`tâm bồ đề` → `tâm muốn giúp tất cả mọi người`);
general → intermediate keeps the Sino-Vietnamese term, may add a qualifier
(`công đức` → `công đức / phước đức`); general → advanced adds the Sanskrit/Pali
form in parentheses (`tánh không` → `tánh không (vô tự tính)`). Keep values 1–6
words; prefer a form attested in an existing Vietnamese translation over a new
one. Natural Vietnamese particles (rồi, thì, mà, vậy) are allowed in prose.

### Adding a language

Add a register table with the four grades, a short adaptation paragraph, and a
handful of anchor terms (compassion, emptiness, merit, bodhichitta, suffering at
least). Build the base termbase per Phase 1 Step 1. Nothing else changes.

---

## Provenance

Consolidated 2026-09-21 from one vault's per-language skill pairs (a
`keyword-grade` + `translate` pair per target language) and its
`termbase-consistency-check/` script, which were identical apart from the target
code and the register table. That vault's end-to-end production run is written
up in [`references/worked-example.md`](references/worked-example.md) as a
history, not a contract. Its two English-track glossary scripts hard-coded that
vault's track names and paths and were not carried over; `bilingual-glossary`
Phase 4 is the general form of that step.

## After this skill

`translation-qa` grades the output against the source and the verse packages;
`commentary-fact-check` checks that each verse says what the commentaries say it
means. Both should run before a graded translation is uploaded.
