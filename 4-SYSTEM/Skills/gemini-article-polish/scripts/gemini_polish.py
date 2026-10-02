#!/usr/bin/env python3
"""Re-compose the Tibetan prose of a fenced-wikitext article.md with the Gemini API.

Rationale: Gemini's native Tibetan composition is stronger than the drafting model's.
This script sends ONLY the article's editable prose (the body before the fixed tail)
to Gemini with every <ref> tag replaced by an opaque placeholder token, asks for a
recomposition that improves flow and register WITHOUT changing any fact, and then
runs deterministic checks so nothing the trust machinery guarantees can drift:

  hard checks (any FAIL -> retry with corrective feedback, then give up loudly):
    C1  every ref placeholder token appears exactly once (none lost, none invented)
    C2  the section heading sequence is unchanged
    C3  every verbatim Tibetan quotation ("…" spans) survives character-for-character
    C4  no comma character (, ， 、) anywhere
    C5  no Latin/ASCII letters in the prose (refs are placeholders, so any letter is drift)
    C6  no punctuation immediately after a ref (shad precedes refs, never follows)
    C7  the bold ('''…''') spans are unchanged (the lead name is not restyled)
  soft checks (reported as warnings for the reviewing agent):
    W1  every paragraph ends with double shad །།
    W2  prose length delta beyond ±25% (tsheg-count proxy)

The fixed tail (== འབྲེལ་ཡོད་ཤོག་ངོས། == onward), the file frontmatter, and the
reviewer callout are never sent to the model and are reattached byte-identical.

The API key is resolved from, in order: the GEMINI_API_KEY environment variable,
a vault-local .env, then the shell profile (export line). It is never printed.

Usage:
    python3 gemini_polish.py <path-to-article.md> --out <output-dir>
                             [--model gemini-3-pro-preview] [--temperature 0.3]
                             [--max-retries 2]

Writes into --out:
    article.md        the polished article (original frontmatter + callout, new fence
                      body, polish provenance fields added to the frontmatter)
    body-before.txt   the original editable prose (refs restored) — for the diff review
    body-after.txt    the polished editable prose (refs restored)
    gemini-report.md  model used, per-check PASS/FAIL/WARN table, length stats

Exit status: 0 = polished with all hard checks passing; 2 = hard checks still failing
after retries (report written, article.md NOT written); 1 = usage/environment error.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

FENCE_RE = re.compile(r"^```wikitext\s*\n(.*?)^```\s*$", re.M | re.S)
REF_RE = re.compile(r"<ref\b[^>]*/>|<ref\b[^>]*>.*?</ref>", re.S)
HEADING_RE = re.compile(r"^\s*(={2,6})\s*(.*?)\s*\1\s*$", re.M)
BOLD_RE = re.compile(r"'''(.*?)'''", re.S)
TIBETAN_QUOTE_RE = re.compile(r"\"([^\"]*[ༀ-࿿][^\"]*)\"")
TOKEN_FMT = "⟦R{}⟧"
TOKEN_RE = re.compile(r"⟦R(\d+)⟧")
TAIL_HEADINGS = ["== འབྲེལ་ཡོད་ཤོག་ངོས། ==", "== ལུང་ཁུངས། =="]

VAULT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MODELS = ["gemini-3.1-pro-preview", "gemini-pro-latest", "gemini-2.5-pro"]

PROMPT_TEMPLATE = """You are a native Tibetan editor revising one article for the Tibetan-language Wikipedia. The article below was drafted by another system. Its FACTS are verified and frozen; your job is purely the WRITING — recompose the prose so it reads as natural, fluent, encyclopedic Tibetan (ཚིག་སྦྱོར་), the register of a well-written reference work.

You may:
- reorder words and clauses within and across sentences for natural Tibetan syntax
- merge choppy sentences or split overlong ones
- replace awkward calque-like phrasing with idiomatic Tibetan of the SAME meaning
- improve discourse connectives and paragraph flow

You must NOT:
- add, remove, weaken, or strengthen any fact, name, number, list item, or doctrinal position
- add any information from your own knowledge, however standard it seems
- change who is said to hold which position, or reword any personal name or text title
- add, remove, or change any title or honorific before a personal name (སློབ་དཔོན་, གྲུབ་ཆེན་, རྗེ་བཙུན་, མཁན་ཆེན་ and the like) — copy every personal name with EXACTLY the words the source uses, no more and no less
- touch the tokens that look like ⟦R7⟧ — each is a frozen citation marker. Every token must appear EXACTLY ONCE in your output, attached to (immediately after) the same statement it supports now. Move a token only together with the statement it belongs to. Never invent, drop, or renumber a token.
- alter anything inside double quotation marks "…" — these are verbatim quotations; copy them character-for-character
- change, add, remove, or reorder the section headings (lines like == … ==)
- restyle the bold '''…''' spans (copy them verbatim)
- use any comma (, ， 、) — the character does not exist in Tibetan; use a shad or nothing
- use any Latin letters or Arabic digits
- end a sentence after a citation token — the shad goes BEFORE the token(s): …བཤད།⟦R3⟧

Punctuation contract: every sentence ends with a shad །. The final sentence of every paragraph ends with a double shad །། . Keep classical shad orthography as the text already practises it (e.g. ང་། with tsheg, no shad doubled after ཀ/ག).

Output ONLY the revised article text — no explanations, no code fences, no preamble.

ARTICLE:
{body}
"""

RETRY_ADDENDUM = """

YOUR PREVIOUS ATTEMPT FAILED THESE MECHANICAL CHECKS — fix them and output the full corrected text again:
{failures}
"""


def resolve_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    env_file = VAULT_ROOT / "4-SYSTEM" / "Pipelines" / "wikipedia" / ".env"
    for source in (env_file, Path.home() / ".zshrc"):
        try:
            for line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
                m = re.match(r"\s*(?:export\s+)?GEMINI_API_KEY\s*=\s*[\"']?([^\"'#\s]+)", line)
                if m:
                    return m.group(1)
        except OSError:
            continue
    return None


def call_gemini(prompt: str, model: str, key: str, temperature: float) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": 65536},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                wait = 30 * (attempt + 1)
                print(f"  429 rate-limited; sleeping {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("unreachable")


def strip_wrapping_fence(text: str) -> str:
    text = text.strip()
    m = re.match(r"\A```[a-zA-Z]*\s*\n(.*?)\n```\s*\Z", text, re.S)
    return m.group(1) if m else text


def tokenize_refs(body: str) -> tuple[str, list[str]]:
    refs: list[str] = []

    def repl(m: re.Match) -> str:
        refs.append(m.group(0))
        return TOKEN_FMT.format(len(refs))

    return REF_RE.sub(repl, body), refs


def restore_refs(body: str, refs: list[str]) -> str:
    return TOKEN_RE.sub(lambda m: refs[int(m.group(1)) - 1], body)


def split_tail(fence_body: str) -> tuple[str, str]:
    """(editable prose, frozen tail). Tail starts at the first fixed-tail heading."""
    for h in TAIL_HEADINGS:
        idx = fence_body.find(h)
        if idx != -1:
            return fence_body[:idx], fence_body[idx:]
    raise ValueError("no fixed-tail heading found — is this a spec-conformant article?")


def run_checks(orig_tok: str, cand_tok: str, n_refs: int) -> tuple[list[str], list[str]]:
    """Returns (hard failures, warnings); both empty means clean."""
    fails: list[str] = []
    warns: list[str] = []

    tokens = [int(t) for t in TOKEN_RE.findall(cand_tok)]
    missing = sorted(set(range(1, n_refs + 1)) - set(tokens))
    extra = sorted(set(tokens) - set(range(1, n_refs + 1)))
    dupes = sorted({t for t in tokens if tokens.count(t) > 1})
    if missing:
        fails.append(f"C1 ref tokens missing: {['⟦R%d⟧' % t for t in missing]}")
    if extra:
        fails.append(f"C1 ref tokens invented: {['⟦R%d⟧' % t for t in extra]}")
    if dupes:
        fails.append(f"C1 ref tokens duplicated: {['⟦R%d⟧' % t for t in dupes]}")
    if re.search(r"⟦(?!R\d+⟧)", cand_tok):
        fails.append("C1 malformed placeholder bracket found")

    if HEADING_RE.findall(orig_tok) != HEADING_RE.findall(cand_tok):
        fails.append("C2 section heading sequence changed")

    for q in TIBETAN_QUOTE_RE.findall(orig_tok):
        if f'"{q}"' not in cand_tok:
            fails.append(f"C3 verbatim quotation altered or lost: \"{q[:30]}…\"")

    commas = sorted(set(re.findall(r"[,，、]", cand_tok)))
    if commas:
        fails.append(f"C4 comma character(s) present: {commas}")

    latin = sorted(set(re.findall(r"[A-Za-z]", TOKEN_RE.sub("", cand_tok))))
    if latin:
        fails.append(f"C5 Latin letters in prose: {latin}")

    if re.search(r"⟦R\d+⟧[།༎]", cand_tok):
        fails.append("C6 punctuation after a ref token (shad must precede refs)")

    if BOLD_RE.findall(orig_tok) != BOLD_RE.findall(cand_tok):
        fails.append("C7 bold '''…''' spans changed")

    for i, para in enumerate(p for p in re.split(r"\n\s*\n", cand_tok) if p.strip()):
        line = TOKEN_RE.sub("", para.strip())
        if HEADING_RE.match(line):
            continue
        if not re.search(r"[།༎]།?\s*$", line) or not line.rstrip().endswith("།།"):
            warns.append(f"W1 paragraph {i + 1} does not end with double shad ('…{line[-20:]}')")

    def tshegs(s: str) -> int:
        return s.count("་")

    before, after = tshegs(orig_tok), tshegs(cand_tok)
    if before and abs(after - before) / before > 0.25:
        warns.append(f"W2 length delta {before}→{after} tshegs ({(after - before) / before:+.0%})")
    return fails, warns


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("article", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--model", default=None, help="Gemini model id (default: try "
                    + ", ".join(DEFAULT_MODELS) + ")")
    ap.add_argument("--temperature", type=float, default=0.3)
    ap.add_argument("--max-retries", type=int, default=2)
    args = ap.parse_args()

    key = resolve_api_key()
    if not key:
        print("error: GEMINI_API_KEY not found (env, pipeline .env, ~/.zshrc)", file=sys.stderr)
        return 1

    text = args.article.read_text(encoding="utf-8")
    m = FENCE_RE.search(text)
    if not m:
        print("error: no ```wikitext fence in input", file=sys.stderr)
        return 1
    fence_body = m.group(1)
    editable, tail = split_tail(fence_body)
    orig_tok, refs = tokenize_refs(editable)

    models = [args.model] if args.model else DEFAULT_MODELS
    prompt = PROMPT_TEMPLATE.format(body=orig_tok)
    args.out.mkdir(parents=True, exist_ok=True)

    cand_tok, fails, warns, model_used, attempts = None, ["not run"], [], None, 0
    for model in models:
        try:
            attempt_prompt = prompt
            for attempt in range(args.max_retries + 1):
                attempts += 1
                print(f"calling {model} (attempt {attempt + 1})…", file=sys.stderr)
                cand_tok = strip_wrapping_fence(call_gemini(attempt_prompt, model, key,
                                                            args.temperature))
                fails, warns = run_checks(orig_tok, cand_tok, len(refs))
                if not fails:
                    break
                attempt_prompt = prompt + RETRY_ADDENDUM.format(
                    failures="\n".join(f"- {f}" for f in fails))
            model_used = model
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  {model} not available (404); trying next", file=sys.stderr)
                continue
            raise
    if model_used is None:
        print("error: no configured Gemini model is available", file=sys.stderr)
        return 1

    today = datetime.date.today().isoformat()
    (args.out / "body-before.txt").write_text(editable, encoding="utf-8")
    (args.out / "body-after.txt").write_text(restore_refs(cand_tok, refs), encoding="utf-8")

    status = "PASS" if not fails else "FAIL"
    report = [
        f"# Gemini polish report — {args.article}",
        "",
        f"- date: {today}",
        f"- model: `{model_used}`  (temperature {args.temperature}, attempts {attempts})",
        f"- refs frozen as tokens: {len(refs)}",
        f"- hard checks: **{status}**",
        "",
        "## Hard-check failures" if fails else "## Hard checks",
        *([f"- {f}" for f in fails] or ["- C1–C7 all PASS"]),
        "",
        "## Warnings (reviewing agent must resolve)",
        *([f"- {w}" for w in warns] or ["- none"]),
        "",
        "The semantic diff (fact-by-fact comparison of body-before.txt vs body-after.txt)",
        "is the reviewing agent's job — this script only guarantees the mechanical frame.",
    ]
    (args.out / "gemini-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    if fails:
        print("hard checks failing after retries — article.md not written; see "
              f"{args.out / 'gemini-report.md'}", file=sys.stderr)
        return 2

    # Gemini frequently trims trailing whitespace/newlines from its response. Since the
    # tail (starting at a TAIL_HEADINGS heading) is reattached verbatim right after the
    # polished body, a trimmed boundary glues "...last sentence.== heading ==" onto one
    # line, which MediaWiki does not parse as a heading. None of C1-C7 can catch this —
    # they only inspect the editable body, never the reassembled tail boundary. Normalize
    # the join here so it can never regress, regardless of what Gemini trims.
    new_fence = restore_refs(cand_tok, refs).rstrip("\n") + "\n\n" + tail.lstrip("\n")
    new_text = text[:m.start(1)] + new_fence + text[m.end(1):]
    def _amend_frontmatter(fm: re.Match) -> str:
        head = fm.group(1)
        # a polished copy is always a draft for review; keep the source's status on record
        sm = re.search(r"^status:\s*(.+?)\s*$", head, re.M)
        if sm and sm.group(1) != "draft":
            head = (head[:sm.start()] + "status: draft\nsource_status: " + sm.group(1)
                    + head[sm.end():])
        return (head
                + f"\npolished_by: gemini-article-polish\npolish_model: {model_used}"
                + f"\npolish_date: '{today}'\npolish_source: {args.article}"
                + fm.group(2))

    new_text = re.sub(r"\A(---\n.*?)(\n---\n)", _amend_frontmatter, new_text,
                      count=1, flags=re.S)
    (args.out / "article.md").write_text(new_text, encoding="utf-8")
    print(f"wrote {args.out / 'article.md'} ({status}; {len(warns)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
