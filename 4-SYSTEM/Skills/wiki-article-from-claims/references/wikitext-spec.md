# Canonical wikitext output spec — Tibetan Wikipedia (bo.wikipedia)

The authoritative definition of what a generated article must look like. The drafting rules
target it; the verification walk enforces it.

It reconciles several sources that disagree with each other — house drafting prompts, an
earlier 27-rule prompt, a work-article generator, and **what bo.wikipedia actually renders**
(verified live). Where they conflict, live-wiki evidence wins, and the conflict is documented
below so it can be overridden deliberately.

---

## 1. Article skeleton (doctrinal-term profile)

```wikitext
'''<TERM>'''ནི་ ... <ref>...</ref> ... <ref>...</ref>

== ངེས་ཚིག ==
... <ref>...</ref>

== མཚན་ཉིད། ==
... <ref>...</ref>

== དབྱེ་བ། ==
... <ref>...</ref>

== གཞུང་ལུགས་སོ་སོའི་བཤད་པ། ==

'''<TRADITION-OR-COMMENTATOR>་'''ནས་ ... <ref>...</ref>

== བསྡུས་དོན། ==
...

== འབྲེལ་ཡོད་ཤོག་ངོས། ==
* [[<TERM>་]]
* [[<TERM>་]]

== ལུང་ཁུངས། ==
<references />

== དཔྱད་གཞིའི་ཡིག་ཆ། ==
* <AUTHOR>། <TITLE>། <YEAR>།

[[རིགས་དབྱེ།:ནང་བསྟན།]]
```

### Rules

- **The lead has no heading.** It opens with the term in `'''bold'''` and gives a general
  definition. It carries citations like any other section.
- **Sections are emitted only if the sources support them** —
  *ས་བཅད་གསར་པ་གང་ཡང་གསར་བཟོ་བྱས་མི་ཆོག*: never invent a section. A term with no attested
  དབྱེ་བ gets no དབྱེ་བ section. Every section must contain ≥1 citation.
- **The last three sections are fixed and ordered:** `འབྲེལ་ཡོད་ཤོག་ངོས།` → `ལུང་ཁུངས།` →
  `དཔྱད་གཞིའི་ཡིག་ཆ།`.
- **`བསྡུས་དོན།` is optional but recommended** — a summary section at the end of the body.
- All headings use `==`, and **every heading text ends with a shad `།`** except `ངེས་ཚིག`,
  where the term itself carries no shad. Follow the exemplars: `== ངེས་ཚིག ==`,
  `== མཚན་ཉིད། ==`, `== དབྱེ་བ། ==`.
- **Tibetan script and Tibetan numerals only** in the article body. Latin text appears only
  inside `<ref>` URLs.

### Second profile: works and authors

A different entity type — texts, translators, commentaries — needs catalog numbers
(Toh/Peking), translation lineage, and Sanskrit titles. Keep it as a **separate profile**,
selected by entity type. Do not merge the two skeletons: a doctrinal term has no Tohoku
number and a text has no ངེས་ཚིག.

---

## 2. Citations

### The form

**Canonical/primary sources** (Kangyur, Tengyur, Tibetan commentaries) — hand-formatted,
because CS1 injects English furniture (`2 ed.`, `pp.`, `Retrieved`) into Tibetan prose:

```wikitext
<ref>[<URL> <AUTHOR>། <TITLE>། ཤོག་གྲངས་<PAGE>]</ref>
```

**Modern secondary sources** with a real ISBN or DOI — CS1 is fine and preferable:

```wikitext
<ref>{{Cite book |last= |first= |title= |year= |isbn= }}</ref>
```

Never invent an ISBN: CS1 validates the checksum and renders a visible red error plus a
maintenance category. Omit the parameter when unverified.

### Four fields

Every ref carries **author, work title, publication year, page**. Year and page may be
omitted when genuinely unknown — but the review report lists every ref missing them, so gaps
are visible rather than silent.

### Quotation marks

Quoted source text inside the article body goes in `" "`. The quotation is followed
immediately by its `<ref>`.

### The reference section — the one trap that matters most

```wikitext
== ལུང་ཁུངས། ==
<references />
```

**Never `{{Reflist}}`.** bo.wikipedia's `Template:Reflist` source begins with its own
`== ཡོང་ཁུངས། ==` heading, so `== ལུང་ཁུངས། ==` + `{{Reflist}}` renders two stacked
headings. Verified by a live `action=parse` render. This is the single most likely failure
mode, because the `{{Reflist}}` idiom is correct on English Wikipedia and any LLM will reach
for it.

**`<references />` is mandatory whenever any `<ref>` exists.** Roughly 600 bo.wikipedia
articles currently have orphaned footnotes. Blocking lint rule.

### Named refs

`<ref name="...">` for repeat citations of one source is supported, with two cautions: the
first occurrence must carry the full content (`<ref name="x">...</ref>`), later ones the
self-closing form (`<ref name="x" />`); and `<reference>`/`</reference>` — which appears in
some older house prompts — is a **typo** for MediaWiki's `<references />`; do not copy it.

### Source-link resolution

Refs must not ship with placeholder domains. Map each quotation's source to a real URL and
append a text fragment so the link lands on the passage:

```
<URL>#:~:text=<first-6-syllables-pct-encoded>,<last-6-syllables-pct-encoded>
```

Preference order: Wikisource page (via `oldwikisource:` — plain `wikisource:` silently
resolves to **en**.wikisource) → BDRC `bdr:` ID → publisher URL → no link (flagged in the
review report).

---

## 3. Wikilinks

```wikitext
[[རྡོ་རྗེ་]]            correct — trailing tsheg, no shad
[[རྡོ་རྗེ།]]            wrong — shad in the link target
[[རྡོ་རྗེ་|རྡོ་རྗེ།]]     piped — target must match the wiki page exactly; display may carry a shad
```

Red links are **expected and useful** — they mark terms whose articles have not been created
yet, and blue-vs-red doubles as a manual existence check.

**Title variants are a live hazard.** `སངས་རྒྱས་` (tsheg), `སངས་རྒྱས།` (shad) and bare
`སངས་རྒྱས` all exist as separate pages on bo.wikipedia, one of them a broken redirect. Probe
all three variants before creating anything. ❓ *Which variant to create at is a per-vault
decision — record it in the vault annex.*

---

## 4. Bold and the tsheg-boundary rule

Sub-headings and emphasised terms use `'''...'''`.

**The tsheg must survive at every markup boundary:**

```wikitext
'''བྱང་ཆུབ་སེམས་'''ནི་      ✅ tsheg inside the bold
'''བྱང་ཆུབ་སེམས'''་ནི་      ✅ tsheg outside the bold
'''བྱང་ཆུབ་སེམས'''ནི་       ❌ no tsheg at the boundary
```

The third form is a spelling error and breaks line-wrapping, because Tibetan lines may only
break after a tsheg. bo.wikipedia's parser treats all three identically, so **this will never
surface as a wiki error** — only a linter catches it. The same rule applies at `[[...]]`
boundaries.

---

## 5. Categories

Namespace is `རིགས་དབྱེ།`. **Curated allowlist only — never invent a category name**, because
the live namespace contains misspellings (`ནང་པ་སངས་རྒྱངས་ཀྱི་ལྷ།`) and shad typos
(`ནང་པ་སངས་རྒྱས།།`).

Seed allowlist: `ནང་ཆོས།` · `ནང་བསྟན།` · `ནང་པ་སངས་རྒྱས་ཆོས་ལུགས།` · `བསྟན་བཅོས།` ·
`ཤེར་ཕྱིན།` · `ཆོས་ལུགས།`

At least one category is a blocking lint rule (80% of bo.wikipedia articles have none).

---

## 6. Wikidata

Creating or linking a Wikidata item is a pipeline step, not an afterthought — without one, an
article gets no interwiki links and `{{Databox}}` renders empty.

Do **not** emit `[[en:...]]` interwiki wikitext; that mechanism is obsolete.

---

## 7. Validator rules (blocking)

Verification fails on any of these. They are the acceptance criteria for a draft.

| # | Rule |
|---|---|
| V1 | Every quotation appears character-for-character in its cited source file |
| V2 | Every `<ref>` resolves to a declared source |
| V3 | `<references />` present iff any `<ref>` present |
| V4 | No `{{Reflist}}` anywhere preceded by a heading |
| V5 | All `<ref>` tags balanced and closed; named refs have exactly one full definition |
| V6 | ≥1 `==` heading |
| V7 | ≥1 category, all from the allowlist |
| V8 | Every section contains ≥1 citation (no unsourced sections) |
| V9 | Tibetan script only outside `<ref>` URLs and template parameters |
| V10 | Tsheg present at every `'''` and `[[` boundary |
| V11 | Last three sections are `འབྲེལ་ཡོད་ཤོག་ངོས།`, `ལུང་ཁུངས།`, `དཔྱད་གཞིའི་ཡིག་ཆ།` in that order |
| V12 | No placeholder domains, no placeholder text, no leftover model chatter |

V12 also covers English Wikipedia's G15 speedy-deletion triggers (fabricated refs, leftover
assistant text) — not binding on bo.wikipedia, but the standard to hold to.

Warnings (non-blocking, surfaced in the review report): ref missing year or page; unlinked
ref; section with only one citation; article shorter than 1,500 Tibetan syllables.

---

## 8. Conflicts resolved here — confirm or override

| Question | Sources disagree | Decision | Evidence |
|---|---|---|---|
| Reference heading | `ལུང་ཁུངས།` vs `དཔེ་ཁུངས།` vs `ཁུངས།` | **`ལུང་ཁུངས།`** | 738 articles use it; `དཔེ་ཁུངས།` appears **0** times on the wiki; `ཁུངས།` appears once |
| Refs display | `{{Reflist}}` vs `<references />` | **`<references />`** | Reflist injects its own heading — live render test |
| See-also heading | `འབྲེལ་ཡོད་ཤོག་ངོས།` (13) vs `ད་དུང་གཟིགས།` (3,834) vs `གཞན་ཡང་གཟིགས།` (1) | **`འབྲེལ་ཡོད་ཤོག་ངོས།`** | Attested, and the house form; `ད་དུང་གཟིགས།` is mostly bot-stub skeleton |
| Sub-heading markup | `'''bold'''` vs `==` | **`'''bold'''` inside a `==` section** | Matches the live `སངས་རྒྱས།` article |
| Gloss length | <10 ཚེག་བར vs ≥10 | ❓ **needs a per-vault call** | The house specs contradict each other; record the decision in the vault annex |
| Citation template | CS1 vs hand-formatted | **Both, by source type** | CS1 exists but emits English furniture |
| Title variant to create at | tsheg vs shad vs bare | ❓ **needs a per-vault call** | All three exist for `སངས་རྒྱས`; probing all is agreed, choosing one is not |
