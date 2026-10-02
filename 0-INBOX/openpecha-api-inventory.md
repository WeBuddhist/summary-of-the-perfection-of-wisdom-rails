---
title: "OpenPecha API download — Summary of the Perfection of Wisdom (Sañcayagāthā)"
status: draft
source_description: "Index of the verbatim OpenPecha backend API v2 download in 0-INBOX/raw-data/openpecha-api/: the Tibetan root text, every translation and commentary linked to it, and their alignment annotations. Scratch — not a source, never cited."
---

# OpenPecha API download — Summary of the Perfection of Wisdom (Sañcayagāthā)

**Root:** འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པའི་ཚིགས་སུ་བཅད་པ་བཞུགས་སོ། (`w8KgwzbKElDAWf2gSN5a1`, BDRC `WA0RK0013`)

**Downloaded:** 2026-10-02 from the old OpenPecha backend (`https://api-aq25662yyq-uc.a.run.app`, API 0.1.0 @ `ecdf248`). The root text's files were copied from the earlier full download in `Nalanda-texts-rails/0-INBOX/raw-data/openpecha-api/` (downloaded 2026-09-27); everything else was fetched fresh. Every file under `raw-data/openpecha-api/` is the API response exactly as received.

**Contents:** 6 texts. That is the root, no translations and 5 commentaries. 1 of the 5 derived texts carries an alignment upstream. Nothing here has been converted or checked yet.

## Texts

`#` is the row number; "translation of #4" means the text is aligned to row 4, not to the root. **Chars** and **Segs** are for the critical instance: character count, and the number of segments in its segmentation annotation. **Alignment** gives the number of spans on the derived text ↔ the number of spans on its parent.

| # | Relation | Language | Title | Text ID | Source · licence | Chars | Segs | Alignment | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 0 | **root** | Tibetan | འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པའི་ཚིགས་སུ་བཅད་པ་བཞུགས་སོ། | `w8KgwzbKElDAWf2gSN5a1` | bdrc.io · Public Domain Mark | 54,564 | 232 |  | translator: སྐ་བ་དཔལ་བརྩེགས། |
| 1 | commentary | Tibetan | འཕགས་པ་མདོ་སྡུད་པའི་འགྲེལ་པ་རྒྱས་པ་སྦས་དོན་གསལ་བའི་སྒྲོན་མེ། | `MPkDoRMbe5oEq8zvsIccF` | bdrc.io · unknown | 177,058 | 1072 | — none upstream | **same content as #2** |
| 2 | commentary | Tibetan | འཕགས་པ་མདོ་སྡུད་པའི་འགྲེལ་པ་རྒྱས་པ་སྦས་དོན་གསལ་བའི་སྒྲོན་མེ། ། | `A5BQinnk1IncTy0YV2gbZ` | bdrc.io · Public Domain Mark | 177,058 | 1072 | — none upstream | **same content as #1** |
| 3 | commentary | Tibetan | འཕགས་པ་ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་སྡུད་པ་ཚིགས་སུ་བཅད་པའི་ཊཱི་ཀ་ཡིད་བཞིན་གྱི་ནོར་བུ་རིན་པོ་ཆེ་ལྟ་བུ་ཕ་རོལ་ཏུ་ཕྱིན་པ་རྒྱ་མཚོའི་སྡེ་ཞེས་བྱ་བ་བཞུགས་སོ། | `Jx0X0zaiFYjc5OHsIWJit` | bdrc.io · Public Domain Mark | 135,407 | 1562 | ✓ 224 ↔ 224 |  |
| 4 | commentary | Tibetan | ཡོན་ཏན་རིན་ཆེན་སྡུད་པའི་འགྲེལ་པ་རྒྱལ་བའི་ཡུམ་གྱི་དགོངས་དོན་ལ་ཕྱིན་ཅི་མ་ལོག་པར་འཇུག་པའི་ལེགས་བཤད་ཅེས་བྱ་བ་བཞུགས། | `XkTFVp0RDzdMk0fe6vDL8` | bdrc.io · Public Domain Mark | 243,232 | 1021 | — none upstream |  |
| 5 | commentary | Tibetan | ཡོན་ཏན་རིན་པོ་ཆེ་སྡུད་པ་ཚིགས་སུ་བཅད་པའི་འགྲེལ་བ་ཟབ་མོ་རྟེན་འབྱུང་གི་དེ་ཁོ་ན་ཉིད་གསལ་བར་བྱེད་པའི་ནོར་བུའི་སྒྲོན་མ་སྐལ་བཟང་རེ་སྐོང་ཞེས་བྱ་བ་བཞུགས་སོ། | `iomd5mo5cFrdUS7Ue4h4f` | bdrc.io · Public Domain Mark | 320,583 | 1816 | — none upstream |  |

## Not downloaded

Texts linked to this tree upstream but titled "Delete this" (test records):

- none

## Layout

```
0-INBOX/raw-data/openpecha-api/
  manifest.json                         run metadata (API base and version, dates, counts)
  tree.json                             every text with its parent and relationship; every
                                        derived→parent pair with its instance IDs and alignment file
  texts.json                            the GET /v2/texts entries for these texts
  categories.json                       category titles (bo, en), copied from Nalanda-texts-rails
  texts/<text_id>/
    text.json                           GET /v2/texts/<id>
    instances.json                      GET /v2/texts/<id>/instances
    instances/<instance_id>.json        GET /v2/instances/<id>?content=true&annotation=true
    annotations/<annotation_id>.json    GET /v2/annotations/<id>   (segmentation, bibliography, …)
    related/<instance_id>.json          GET /v2/instances/<id>/related
    alignments/<annotation_id>.json     GET /v2/annotations/<id>   (type alignment, derived text only)
```

**Reading an alignment.** The spans in an alignment file's `alignment_annotation` are character offsets into this text's critical-instance `content`. Each span's `aligned_segments` lists IDs from `target_annotation`, whose spans are offsets into the **parent** instance's `content`. `tree.json` → `pairs` names both instance IDs.

**Next step.** In `Nalanda-texts-rails`, the `json-to-source-text` skill's `openpecha_api_v2.py` converter reads this exact layout (`text.json` / `instances/` / `annotations/`, plus `manifest.json` and `categories.json`). It is not yet installed in this vault. It renders original texts, so the alignment-driven intake of translations and commentaries is still to be decided.
