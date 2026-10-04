---
title: "'Commentary on Precious Qualities: Entering the True Intent of the Buddha''s Mother' — DharmaMitra zero-shot (modern chinese)"
track_type: machine-baseline
target_language: modern chinese
lang_tag: zh
translation_of: 1-SOURCES/Commentaries/bo-mipham-lekshe.md
generator: dharmamitra cat-translate v1
endpoint: https://dharmamitra.org/api-search/cat-translate/v1/translate
rails_used: none
termbase: none
status: draft
seeded: 2026-10-04
---

# zh-dharmamitra-zeroshot — about this track

A **machine baseline**, not a rails-governed translation track.

Every file here is raw output of DharmaMitra's public `cat-translate` endpoint,
produced in small batches of adjacent block IDs by
`4-SYSTEM/Skills/dharmamitra-translate/scripts/dm_translate.py`, then split back
apart on segment markers so each block keeps its own record. Nothing in it
passed through `2-RAILS/`: no verse-context package, no consolidated bilingual
glossary, no per-track `termbase.md`, no human review. It therefore does **not**
satisfy the Translation-track contract in
[`../About Transformations.md`](../About%20Transformations.md) §3, and it is not
eligible to be marked `status: complete` or to be cited by any other
transformation.

## What it is for

- A comparison baseline against which a rails-governed translation can be judged.
- A drafting aid and a source of candidate renderings for
  `2-RAILS/Bilingual-Glossaries/` (via `glossary-extract-raw`).
- A fast first look at a text in a language no track covers yet.

## What governs it

| File | Role |
| --- | --- |
| `style.md` | The `style_instruction` string, sent **verbatim** to the API on every call. Edit it, then re-run with `--force` to regenerate. |
| `context-header.md` | A work-NEUTRAL, track-wide preamble prepended to every call's `context`. The per-text `Work: …` line is derived from each source's own metadata and appended after it. |
| `work/zh.jsonl` | Append-only ledger: one record per API call — source, translation, the exact context sent, timings. The audit trail and the resume point. |
| `bo-mipham-lekshe-zh.md` | The rendered translation, block-ID aligned to the source. |

## Provenance

- Endpoint: `https://dharmamitra.org/api-search/cat-translate/v1/translate` (public, unauthenticated)
- Source: [`1-SOURCES/Commentaries/bo-mipham-lekshe.md`](1-SOURCES/Commentaries/bo-mipham-lekshe.md)
- Granularity: up to 3 adjacent source block IDs per API call, never crossing a
  heading; each block still gets its own ledger record and its own block ID.
- Rolling context: the preceding translated blocks of this same document are
  threaded into each call so terminology and register stay coherent.

Regenerate or extend with:

```bash
python3 4-SYSTEM/Skills/dharmamitra-translate/scripts/dm_translate.py \
  --source "1-SOURCES/Commentaries/bo-mipham-lekshe.md" --lang modern chinese
```
