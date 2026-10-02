---
name: wiki-article-from-claims
description: Draft a cited, readable Tibetan Wikipedia article from one consolidated claims topic page — claims-only drafting, fixed claim-resolution chain, verbatim character-verified quotations — in encyclopedic wikivoice with at most 3 refs per statement, at most 2 commentary quotations per article, the Tibetan punctuation contract (sentence-final shad, paragraph-final double shad, no commas), and in-prose author names from the human-curated author_in_use key; plus a generated read-only footnote preview for reviewers.
---

# wiki-article-from-claims

Produces a publish-ready Tibetan wikitext article for one topic — a canonical spine slot, or a keyword subject (e.g. `mudra`) — from its consolidated claims topic page in `2-RAILS/Claims/`. The consolidated page supplies the facts (consensus + ⚑ divergences + unique claims, in English, with attestation counts); the raw tree-guided claims files supply the verbatim original-language text (each claim's `**Original:**` field) and the `1-SOURCES/` block citations behind every attestation. The skill exists so that article prose is never drafted from source files directly and never from parametric knowledge — the failure modes it prevents are added facts, flattened divergences, and quotations that are not character-for-character real.

Correct output is an article a Tibetan reader experiences as connected encyclopedic prose in wikivoice — commentator names appearing only where positions genuinely diverge — whose fence body passes every blocking rule of the wikitext spec; a `citations.md` that lets a reviewer trace every `<ref>` back to claim IDs and source blocks without opening the model's head; and an `article-preview.md` the reviewer can read in Obsidian with citations collapsed to footnote superscripts.

**Version history.** An earlier version drafted a term batch with the full trust machinery but literature-review-style prose. A Tibetan-linguist review of that batch produced the style rules now in Rules 5–9 (wikivoice, citation cap, quotation budget, prose-before-fragments, readability), and a second review round added Rules 15–17 (the punctuation contract and `author_in_use` naming). Those were merged back into this skill, which is the sole version in use.

This skill writes vault files only. It never publishes — publishing stays behind an explicit human gate.

---

## Inputs

1. **Topic ID(s)** — one of:
   - a spine slot ID from the registry in the vault annex, section "Canonical spine slots", **or**
   - a keyword/term topic (e.g. `mudra`, `lotus`) whose consolidated page exists at `2-RAILS/Claims/<topic>.md`.

   A **multi-topic article** joins several topic pages into one article: e.g. the global slots `structure` + `benefits` together → one article on the root text itself (a *work* article), or an `origin` slot plus the origin material in a spine slot → the article on the text's principal subject. For these, `<topic>` in output paths is the joined slug (`structure-benefits`, `origin`). If the consolidated page for a requested topic does not exist, stop and report — never substitute another page.
2. **The consolidated page's raw sources** — every file listed in its `sources:` frontmatter (paths under `2-RAILS/Claims/raw/tree-guided/`). These resolve claim IDs to the claim's `**Original:**` field, English gloss, and `Cite:` targets. If a listed file is missing, stop and report.
3. **The wikitext output contract** — `4-SYSTEM/Skills/wiki-article-from-claims/references/wikitext-spec.md`, bundled with this skill. Read it in full before drafting; its blocking validator rules (V1–V12) are this skill's acceptance criteria.
4. **Commentary metadata** — from each raw claims file's own frontmatter (`author`, `title`, `author_in_use`, `author_in_english`/`title_in_english` where present). **`author_in_use` is set by `author-metadata-sync`**, which is what propagates the human-curated in-article name form from the commentary's own frontmatter into the claims files; if it has not been run for this corpus, run it first. If a raw claims file predates the `author_in_use` key, read that one key from the frontmatter of the commentary named in its `source_file` — a metadata-only lookup, never a reason to reopen the commentary body. Never from memory.

## Output

Three files per article:

```
3-TRANSFORMATIONS/Wikipedia/<text-slug>/term-articles/<topic>/article.md          (keyword topics)
3-TRANSFORMATIONS/Wikipedia/<text-slug>/term-articles/<topic>/citations.md
3-TRANSFORMATIONS/Wikipedia/<text-slug>/term-articles/<topic>/article-preview.md

3-TRANSFORMATIONS/Wikipedia/<text-slug>/slot-articles/<topic>/article.md          (spine-slot topics)
3-TRANSFORMATIONS/Wikipedia/<text-slug>/slot-articles/<topic>/citations.md
3-TRANSFORMATIONS/Wikipedia/<text-slug>/slot-articles/<topic>/article-preview.md
```

**Obsidian-viewability convention (a human contributor decision):** the article file is `.md`, not `.wiki`, so it is viewable and reviewable inside Obsidian. It consists of a small YAML frontmatter (`topic`, `article_kind`, `format`, `status`), a callout explaining the format, and the publishable wikitext inside a single ```` ```wikitext ```` fence — verbatim, byte-identical to what would be published. A raw `.wiki` file is invisible to Obsidian, and raw wikitext in an unfenced `.md` misrenders and pollutes the vault graph with fake `[[…]]` links. Reviewers edit **inside the fence only**; the publish step extracts the fence body and ships exactly that.

`article-preview.md` is **generated, read-only output** — produced by `scripts/make_preview.py` from `article.md`, never hand-edited, regenerated after every edit to `article.md`. It exists solely so a human reviewer can read the article in Obsidian's reading view with citations rendered as clickable footnote superscripts instead of inline `<ref>` blocks. Footnote labels show the **author's name** (a slug of the commentary's `author_in_english`, read live from the `1-SOURCES/Commentaries/` frontmatter — e.g. `[^jetsun-yama-sonam]`), never the internal ref key / `registered_id`, which stays frozen in the wikitext itself. It is not published, not cited from anywhere, and carries `generated: true` frontmatter plus a warning callout. The script also runs standalone on any existing `article.md` drafted before the preview convention existed, so previews can be produced without redrafting.

### `citations.md` — the audit trail

```markdown
---
topic: <topic>
article: article.md
method: wiki-article-from-claims
context_packages:
  - 2-RAILS/Claims/<topic>.md
rails_status: <status of the consolidated page at generation time>
raw_sources_cited:
  - 2-RAILS/Claims/raw/tree-guided/<registered-id>.md
date: <YYYY-MM-DD>
status: draft
---

# Citations — <topic>

## Reference map

| Ref | Commentary | Claim ID(s) | Quotation (verbatim original language, if quoted) | Source block |
|---|---|---|---|---|
| 1 | taranatha | c-1-5 | ཐུགས་དམིགས་པ་མེད་པའི་... | 1-SOURCES/Commentaries/<file>.md#^0-4 |

## Claims used but not quoted

<claim IDs whose content entered the prose paraphrased, listed per section>

## Full attestation beyond in-article refs

<for each consensus statement cited to 2–3 representative refs: the claim IDs of every OTHER
commentary that also attests it, so no attestation is lost by the citation cap>

## Unresolvable attestations

<any consolidated-page attestation whose claim ID could not be found in its raw file — each one
dropped from the article, never guessed>

## Warnings

<rails_status not `complete`; refs missing year/page; refs with no public URL; missing
`author_in_use` keys; anything else a reviewer must see>

## Verification

<result of the quotation check: every quotation located character-for-character in its cited
1-SOURCES file — list each quote → PASS/FAIL>
```

The *Full attestation beyond in-article refs* section exists because the article cites only representative sources (Rule 7) — the full support must be preserved here so nothing is lost by the cap.

---

## Output file format

Three skeletons, chosen by topic kind. Section headings are a menu, not a quota — emit a section only when the consolidated page attests material for it, and never invent a section the sources do not support. A body section whose material the topic page organises differently may take a different Tibetan heading, provided it ends with a shad and its content is claim-backed. The lead has no heading. The last three sections are fixed and ordered: `འབྲེལ་ཡོད་ཤོག་ངོས།` → `ལུང་ཁུངས།` → `དཔྱད་གཞིའི་ཡིག་ཆ།`.

### Keyword/term topics — doctrinal-term skeleton

Use the doctrinal-term skeleton of `4-SYSTEM/Skills/wiki-article-from-claims/references/wikitext-spec.md` §1 as-is.

### Spine-slot topics — deity-profile skeleton

The fenced wikitext body (everything inside the ```` ```wikitext ```` fence — the file's own frontmatter/callout wrapper is vault furniture, never published): pure wikitext, Tibetan script and Tibetan numerals only in the body. The doctrinal-term skeleton does not fit a deity; this profile adapts it while keeping the spec's lead rule, fixed tail, citation form, and every validator rule:

```wikitext
'''<NAME>'''ནི་ <identification and one-sentence summary, cited><ref>...</ref>

== མཚན་གྱི་ངེས་ཚིག ==
<etymology of the name(s), from the consolidated page's etymology material><ref>...</ref>

== སྐུ་ཡི་རྣམ་པ། ==
<iconography / form — emit only if attested><ref>...</ref>

== ཕྲིན་ལས་དང་ནུས་མཐུ། ==
<activity, function, powers — emit only if attested><ref>...</ref>

== ལོ་རྒྱུས། ==
<origin narrative — emit only if attested><ref>...</ref>

== གཞུང་ལུགས་སོ་སོའི་བཤད་པ། ==
<the ⚑ divergence material: each position attributed by commentator, never synthesised><ref>...</ref>

== བསྡུས་དོན། ==
<optional short summary>

== འབྲེལ་ཡོད་ཤོག་ངོས། ==
* [[<related term>་]]

== ལུང་ཁུངས། ==
<references />

== དཔྱད་གཞིའི་ཡིག་ཆ། ==
* <AUTHOR>། <TITLE>།

[[རིགས་དབྱེ།:<category from the spec §5 allowlist>]]
```

### `structure` + `benefits` — work-article skeleton

For the *work* article on the root text itself, the body sections become: identification of the text (lead), its structure (སྟོད་ཆའི་ས་བཅད། or as attested), the benefits section (ཕན་ཡོན།), and transmission/colophon (ལོ་རྒྱུས། or as attested) — same lead rule, same fixed tail.

### `article-preview.md` format (written by the script, shown for reference)

```markdown
---
topic: <topic>
article_kind: term-article-preview
generated: true
generated_from: article.md
generated_by: 4-SYSTEM/Skills/wiki-article-from-claims/scripts/make_preview.py
---

> [!warning] Generated preview — do not edit
> This file is rendered from `article.md` for review reading only. Citations appear as
> footnotes. Any correction belongs in `article.md` (inside the wikitext fence); then
> regenerate this preview. This file is never published.

**<NAME>**ནི་ … <lead prose>[^drepa-ratreng-sungrab-tulku]

## ངེས་ཚིག
… <body prose with footnote markers> …

[^drepa-ratreng-sungrab-tulku]: འབྲས་ཕ་ར་གྲྭ་སྨད་གསུང་རབ་སྤྲུལ་སྐུ། སྒྲོལ་མ་ཉི་ཤུ་རྩ་གཅིག་གི་རྣམ་བཤད།
```

---

## Rules

Rules 1–4 and 10–14 are the trust machinery, unchanged since v1. Rules 5–9 are the 2026-08-18 style delta (first linguist review round). Rules 15–17 are the second-round linguist feedback: the punctuation contract and the author-naming rule.

1. **Claims-only drafting.** Every statement in the article body traces to a claim on the consolidated topic page. No parametric knowledge — no dates, Sanskrit forms, iconographic details, or doctrinal framings that are not in a claim, however standard they seem. If it cannot be cited, it does not go in.
2. **The resolution chain is fixed.** Consolidated attestation `commentary:claim-id` → that commentary's file under `2-RAILS/Claims/raw/tree-guided/` → the claim's **Original** field, English gloss, and `Cite:` target. An attestation that does not resolve is dropped and logged under *Unresolvable attestations* — never guessed, never cited anyway.
3. **Quotations are verbatim or absent.** Direct quotations come only from the **Original** field of a resolved claim, character-for-character, wrapped in `" "`, each followed immediately by its `<ref>`. Never quote from memory of the source, never smooth a quotation's spelling or punctuation.
4. **Every quotation is verified before completion** — located character-for-character (whitespace-collapsed) in the `1-SOURCES/` file its claim's `Cite:` names, PASS/FAIL recorded per quote in `citations.md`. A FAIL is fixed or the quotation removed. This is the spec's blocking rule V1 and is not optional.
5. **Wikivoice for consensus.** ⭐ Any claim the consolidated page marks as consensus (or majority-attested and uncontested) is stated as plain declarative fact — no commentator names, no "མཁས་པ་མང་པོས་…བཤད" / "…གིས་གསུངས" framing, no quotation. The sentence asserts; the `<ref>`s carry the support. Inline attribution ("ཏཱ་ར་ནཱ་ཐས་…") is **reserved** for ⚑ divergences (every position attributed) and for unique claims worth including. Attribution-heavy material concentrates in `གཞུང་ལུགས་སོ་སོའི་བཤད་པ།`; the other sections stay in wikivoice.
6. **Quotation budget: at most 2 verbatim commentary quotations per article.** ⭐ Spend them only where the exact wording is itself the point (a contested formulation, a definition whose phrasing matters). Root-text verse quotation in the lead (the established practice for deity articles) does not count against the budget. Everything else is paraphrased into prose — still claim-backed, still cited.
7. **Citation cap: at most 3 `<ref>`s on any statement.** ⭐ For consensus claims, cite 2–3 *representative* commentaries — prefer refs already named elsewhere in the article, so the reference list stays compact. Never attach the full attestation set to a sentence. Attestation breadth may be asserted in prose ("འགྲེལ་པ་བཅུ་དྲུག་ཀ་…") when the consolidated page's count supports it, backed by 2–3 refs; the complete list of supporting claim IDs goes in `citations.md` §*Full attestation beyond in-article refs*, so nothing is lost.
8. **Prose before fragments.** ⭐ Draft each section as connected paragraphs with topic sentences, not one-claim-one-sentence sequences. Merging several related claims into one flowing sentence is encouraged — the sentence then cites the union's representative refs (still ≤3). Connective tissue (discourse markers, transitions) needs no citation but must carry zero factual content.
9. **Readability is a completion criterion.** ⭐ Before verification, reread the whole article start to finish as a Tibetan encyclopedia reader: if any passage reads as a list of who-said-what outside the divergence section, redraft it under Rules 5–8.
10. **Due weight follows attestation counts** — consensus forms the backbone, unique claims are attributed inline, ⚑ divergences present every position with attribution, never flattened, never adjudicated.
11. **Ref form, spec mechanics, and tail are unchanged from v1**: hand-formatted `<ref><AUTHOR>། <TITLE>།</ref>` built from raw-file frontmatter (year/page appended when attested; no URLs exist for these sources yet — never fabricate one, never emit `dummy.com`; the missing URL goes in *Warnings*), named refs on reuse (`<ref name="...">` full form first, `<ref name="..." />` after), `== ལུང་ཁུངས། ==` + `<references />` (never `{{Reflist}}`), Tibetan-only body (Tibetan script and numerals; Latin only inside ref URLs), tsheg at every `'''` and `[[` boundary, wikilink targets end in tsheg never shad, ≥1 citation per section, ≥1 category from the spec §5 allowlist and no invented category names, fixed last-three-section order. Validator rules V1–V12 are blocking.
12. **The preview is derived, never authored.** `article-preview.md` is written only by `scripts/make_preview.py`. Never hand-edit it; never edit it in place of `article.md`; regenerate it after any change to `article.md`. It is excluded from the citation chain and from publishing.
13. **Read-only outside the output folder.** This skill never modifies `1-SOURCES/`, `2-RAILS/`, or anything in `4-SYSTEM/`. It writes only under the topic's output folder.
14. **Output is always `status: draft`**; the consolidated page's `status` is recorded as `rails_status` in `citations.md`, with a prominent warning when it is not `complete` — the vault rule is that transformations generate from complete rails, and a human contributor accepts that risk explicitly when running this skill on a draft page. No publishing, no network.
15. **Sentence-final shad, paragraph-final double shad.** ⭐ Every Tibetan sentence in the body ends with a shad `།`. The final sentence of every paragraph — including the lead and single-sentence paragraphs — ends with a double shad `།།` (ཉིས་ཤད). Where classical orthography adjusts the shad after particular final letters (a bare ང takes tsheg + shad: `…ང་།`; a final ཀ or ག suppresses the immediately following shad), follow the practice attested in the source commentaries themselves — never improvise an orthographic rule. Punctuation always comes **before** the `<ref>` tag(s) it closes over: `…བཤད།<ref … />`, never `…བཤད<ref … />།`.
16. **No commas — the character does not exist in Tibetan.** ⭐ Neither ASCII `,` nor any comma variant (`，`, `、`) may appear anywhere in the fence body. At every point where a draft reaches for a comma: if the position is a genuine clause or sentence boundary, write a shad `།`; if it is not, write nothing and let the tsheg-joined syntax carry the connection. The `<ref name="…" />,` pattern is always wrong — delete the comma, and when a boundary is needed there, place the shad before the refs (Rule 15). Latin punctuation survives only inside `<ref>` content, per the spec.
17. **In-prose author names come from `author_in_use`.** ⭐ Wherever the prose names a commentator — unique claims, ⚑ divergence positions, `གཞུང་ལུགས་སོ་སོའི་བཤད་པ།` — use that commentary's `author_in_use` frontmatter value: the human-curated, respectful in-article form of the name (e.g. རྒྱལ་བ་དགེ་འདུན་གྲུབ་, not the bare catalog name, not the `registered_id`, not a romanisation), with whatever grammatical particle the sentence requires appended after it. Never invent, translate, or upgrade an honorific — `author_in_use` is authored and reviewed by a human contributor in the source commentary's frontmatter, and the model's only job is to copy it. Resolution order: the raw claims file's `author_in_use` → (frontmatter-only lookup) the `source_file` commentary's own frontmatter → if absent in both, fall back to `author` verbatim **and** add a line to `citations.md` §Warnings naming the commentary whose `author_in_use` is missing. Stored values vary in final punctuation (some end `་`, some `།`, some in a bare letter): strip a trailing shad before using the name mid-sentence, and join the following particle with a tsheg — the shad never survives inside prose. `<ref>` content and the `དཔྱད་གཞིའི་ཡིག་ཆ།` bullets keep the formal `author` + `title` unchanged — `author_in_use` is for prose mentions only.

---

## Procedure — Mode A (full draft from the consolidated claims page)

Use Mode A when no article exists yet for the topic, or when the consolidated claims page has changed materially since the last draft.

1. **Load the contracts.** Read `4-SYSTEM/Skills/wiki-article-from-claims/references/wikitext-spec.md` in full. Read the consolidated page `2-RAILS/Claims/<topic>.md` in full; record its `status` and `sources:` list. For a multi-topic article, read every constituent page.
2. **Build the claim-resolution table.** Collect every attestation ID cited anywhere on the consolidated page (`commentary:claim-id`). For each, open the commentary's raw tree-guided file and extract: the claim's **Original** field, its English line, its `Cite:` path and block ID, and the raw file's `author`/`title`/`author_in_use` frontmatter (with the Input 4 fallback for raw files that predate the key). Record every ID that fails to resolve — the unresolvables must be known up front so nothing is built on them.
3. **Classify for register.** Mark each claim: **backbone** (consensus/majority, uncontested → wikivoice, Rule 5), **unique-attributed** (worth including, attributed inline), or **⚑ divergence** (destined for `གཞུང་ལུགས་སོ་སོའི་བཤད་པ།`, every position attributed). Select the ≤2 quotations the article will carry (Rule 6) and, for each backbone statement, its 2–3 representative refs (Rule 7) — preferring commentaries that recur across statements. Take the article's title/lead name from the consolidated page's own Tibetan heading, never from an unattested variant.
4. **Outline, then draft.** Map the consolidated page's sections onto the skeleton. Draft the lead (bold name with tsheg surviving the `'''` boundary, identification, one–two cited sentences). Draft each body section as connected wikivoice prose per Rules 5–8, attaching ≤3 refs per statement; put attributed material where Rule 5 sends it. Apply the punctuation contract (Rules 15–16) and the `author_in_use` naming rule (Rule 17) as you draft, not as an afterthought.
5. **Readability pass** (Rule 9): reread the full article; redraft any who-said-what passage outside the divergence section.
6. **Assemble the tail** — related pages (for a spine slot in a numbered series: the adjacent slots' articles and the root text's article; targets end in tsheg; red links expected), `ལུང་ཁུངས།` + `<references />`, `དཔྱད་གཞིའི་ཡིག་ཆ།` (one bullet per commentary actually cited, `<AUTHOR>། <TITLE>།` from frontmatter), one allowlisted category.
7. **Write `citations.md`** per the format above — reference map, claims-used list, §*Full attestation beyond in-article refs* for every capped consensus statement, unresolvables, warnings.
8. **Verify** — (a) every quotation character-for-character against its cited `1-SOURCES/` file, PASS/FAIL recorded; (b) every `<ref>` appears in the reference map; (c) walk validator rules V1–V12 against the fence body; (d) style self-check: no statement carries >3 refs, ≤2 commentary quotations in the whole article, no inline attribution of consensus material; (e) punctuation walk: no comma character anywhere in the fence body, every paragraph ends with `།།`, no punctuation after a `<ref>` tag; (f) naming walk: every in-prose commentator name is an `author_in_use` value (or the logged `author` fallback).
9. **Generate the preview.** Run `python3 4-SYSTEM/Skills/wiki-article-from-claims/scripts/make_preview.py <path-to-article.md>` — it writes `article-preview.md` beside the article. Confirm the preview opens clean in Obsidian terms: no `<ref>` tags remaining, no `[[…]]` vault links leaked from wikitext, footnotes present for every named ref.
10. **Report.** State the three files written, rails_status, counts (refs, quotations, backbone vs attributed statements), verification results, and every warning — the human reviewer decides what happens next.

---

## Procedure — Mode B (revision-in-place from an existing article)

Use Mode B when a verified `article.md` + `citations.md` already exists for the topic (produced by this skill or an earlier version of it) and only the **register** needs to change — not the facts. Mode B never returns to `2-RAILS/Claims/` or the raw tree-guided files: the existing claim-resolution and quote-verification work is treated as settled, which is what makes it far cheaper than Mode A. One exception: resolving `author_in_use` (Rule 17) may read the **frontmatter only** of the raw claims files or their `source_file` commentaries — metadata lookup, never claim content.

**Inputs (replace Mode A's Inputs 1–2):** the existing `article.md` (fenced wikitext) and `citations.md` for the topic.

**Output — in place (human-contributor decision, 2026-08-19; the separate pilot stage is retired):** write directly to the topic's canonical folder — `term-articles/<topic>/` or `slot-articles/<topic>/` — replacing `article.md` and `citations.md` and regenerating `article-preview.md`. No side-copy is kept: the previous versions are preserved by git via the vault's auto-backup. Nothing is published by this skill; the `/publish` gate and its human review still stand between any rewritten article and bo.wikipedia.

**Batch runs (parallel agents).** When rewriting many topics, dispatch one agent per topic (or a small group of topics per agent), in parallel. Each agent needs only its own topic's `article.md` + `citations.md`, this SKILL.md, and frontmatter-only lookups for Rule 17 — it must do the work itself, never fan out per-commentary subagents within a topic (2026-08-14 batch lesson), and never write outside its own topic folder(s). After the batch, a human reviewer spot-checks a sample before any `/publish`.

1. **Read the source.** Load the existing `article.md` fence body and `citations.md` reference map in full. Every claim ID, quotation, and `Cite:` target already there is verified ground truth — do not re-derive it.
2. **Classify existing statements** per Rule 5: content already in `གཞུང་ལུགས་སོ་སོའི་བཤད་པ།` (or attributed to one commentator making a genuinely distinctive point) stays attributed; everything else is a candidate for wikivoice conversion.
3. **Rewrite for register.** Merge one-claim-one-sentence sequences into connected wikivoice prose (Rules 5, 8), applying the punctuation contract (Rules 15–16) and swapping every in-prose commentator name to its `author_in_use` form (Rule 17) as you go. The rewrite may only use claim IDs that already appear in the source `citations.md` — introducing a new claim ID in Mode B is not permitted; that requires Mode A.
4. **Apply the quotation budget (Rule 6).** Keep at most 2 verbatim quotations in the whole article. For every quotation cut, convert its content to paraphrase using the same claim's English gloss / meaning already on record — never invent phrasing not grounded in the existing claim.
5. **Apply the citation cap (Rule 7).** Where a statement carries more than 3 refs, keep the 2–3 most representative (prefer refs already reused elsewhere in the article) and move the rest into a new `citations.md` section, *Full attestation beyond in-article refs*, keyed by the statement they support.
6. **Spot-verify, don't re-verify from scratch.** For each of the ≤2 quotations retained, confirm it is an unchanged, exact substring of the quotation already marked PASS in the source `citations.md` — a text diff, not a fresh `1-SOURCES/` lookup. Do not touch quotations that are being removed; they need no re-check.
7. **Readability + punctuation pass (Rules 9, 15–17).** Reread start to finish; redraft any remaining who-said-what fragment sequence outside the divergence section. Then walk the punctuation contract: no comma anywhere, every paragraph closed with `།།`, no punctuation after a `<ref>` tag, every in-prose name an `author_in_use` value.
8. **Write the revised `citations.md`** — carry forward the source file's reference map and verification table unchanged for retained refs, add *Full attestation beyond in-article refs*, and add a header noting `revision_mode: B`, the source article's path, and revision date.
9. **Generate the preview**: `python3 4-SYSTEM/Skills/wiki-article-from-claims/scripts/make_preview.py <path-to-revised-article.md>`.
10. **Report** the topic, source path, output path, ref-count and quotation-count before/after, and confirmation that no claim ID appears in the revision that wasn't already in the source `citations.md`.

---

## Completion check

- [ ] `article.md`, `citations.md`, and `article-preview.md` written under the topic's output folder; nothing outside it modified; nothing published
- [ ] Every statement traces to a claim on the consolidated page (no parametric additions); unresolvables listed and unused
- [ ] Every quotation verified character-for-character with PASS recorded; **at most 2 commentary quotations in the article**
- [ ] **No statement carries more than 3 refs**; capped consensus statements have their remaining attestations listed in `citations.md` §Full attestation beyond in-article refs
- [ ] **Consensus material is in wikivoice** — inline commentator attribution appears only on unique claims and in the divergence section; ⚑ divergences all-positions-attributed, never flattened
- [ ] Readability pass done: article reads as connected encyclopedic prose start to finish
- [ ] **Punctuation contract holds**: no comma character anywhere in the fence body; every sentence ends with a shad `།`; every paragraph ends with a double shad `།།`; punctuation precedes `<ref>` tags, never follows them
- [ ] **Every in-prose commentator name is that commentary's `author_in_use`** — or the `author` fallback with a warning line in `citations.md` naming the commentary whose key is missing
- [ ] Spec validator rules V1–V12 walked and passing; `<references />` present; no `{{Reflist}}` anywhere; allowlisted category; fixed tail order
- [ ] `article-preview.md` generated by the script (not hand-written), carries `generated: true` + warning callout, contains no `<ref>` tags and no wikitext `[[…]]` links
- [ ] `citations.md` frontmatter records `context_packages`, `rails_status`, `status: draft`; warnings list rails_status if not `complete` and every ref missing year/page/URL

---

## Dependencies

- **`author_in_use`** must be present in the raw claims files' frontmatter. It is set by
  `author-metadata-sync`; run that first if it is missing (Input 4 gives the per-file
  fallback and the warning it must log).
- **The wikitext contract** ships with this skill at `4-SYSTEM/Skills/wiki-article-from-claims/references/wikitext-spec.md` —
  the skill does not depend on any external pipeline for it.
- **`scripts/make_preview.py`** — Python 3 standard library only.
- **No network access and no API key** are needed to draft. Checking whether the target
  article already exists is `wiki-article-inventory`'s job (read-only Wikipedia + Wikidata
  API access, no key); polishing the register is `gemini-article-polish`'s job
  (`GEMINI_API_KEY`).
