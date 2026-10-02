#!/usr/bin/env python3
"""
pali_biterm_extraction.py — two-pass bilingual term extractor (no Pali stemming)
=================================================================================
Produces bilingual frequency tables from a block-aligned Pali source file and an
English translation file.  Three output modes:

  YAML mode:
    asava: taints-23, cankers-12
    phasso: contact-45
    sammaditthi: right view-62, wisdom-58

  term-file mode (default, with --focus TERM):
    Produces a flat draft .md file per term in <output-dir>/:
      {term}-draft.md  — one section per Pāli declension form with English
                         frequency counts and an example phrase from the corpus.
    Claude then applies semantic grouping (Step 3 in SKILL.md) to produce
    the final {term}.md in benchmark format.

  keywords-only mode (--keywords-only):
    Runs Pass 1 only on an English file; writes a ranked keyword list.
    Usage: python3 ... <en_file> <output.md> --keywords-only

Pass 1  TF-IDF on the English blocks selects domain keywords — terms that recur
        in this translation but are rare in general English, using the Google-10k
        Zipf-law IDF table in en_freq.py (or wordfreq if installed).

        Before scoring, multi-word compound terms ("right view", "initial
        application", "right concentration") are detected and treated as single
        tokens.  A phrase qualifies when: (a) all component words have high IDF;
        (b) it appears in >= min_phrase_df blocks; (c) it appears in this word
        order at least order_ratio x more often than reversed; and (d) it
        accounts for >= 30% of the rarest component's occurrences.

Pass 2  Each aligned block is split on Ka/Kha/Ga markers before alignment so
        triad entries map line-by-line.  For each English keyword (unigram or
        phrase), weighted Pali co-occurrence is accumulated
        (weight = 1 / |unique Pali tokens in that sub-block|).
        Pali tokens appearing in > max_pi_df of all pairs are suppressed.

No Pali stemming — exact token forms are used throughout.

Usage
-----
    # term-file mode (default — one draft .md per focus term):
    python3 pali_biterm_extraction.py <pali_file> <en_file> bilingual-glossary/ \\
        --focus <term>

    # YAML mode (for glossary-combine pipeline):
    python3 pali_biterm_extraction.py <pali_file> <en_file> output.yaml \\
        --format yaml

    # keywords-only mode (Pass 1 only):
    python3 pali_biterm_extraction.py <en_file> <output.md> --keywords-only

Options
-------
    --top N           English keywords to consider (default 600)
    --min-co N        Minimum raw co-occurrence count (default 2)
    --min-score F     Minimum weighted alignment score (default 0.25)
    --max-pi-df F     Maximum Pali doc-freq fraction (default 0.99 in term-file; 0.30 in yaml)
    --max-pi-per-kw N Maximum Pali tokens linked to one English keyword (default 20 in term-file; 2 in yaml)
    --max-phrase N    Maximum phrase length in words (default 4)
    --focus TERM      Root term to focus on; filters output to its morphological family
    --format {yaml,term-file}  Output format (default: term-file)
    --keywords-only   Pass 1 only: extract English keywords from the first positional arg
"""

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import en_freq

# ---------------------------------------------------------------------------
# Pali function-word stop list (exact token forms, no stemming)
# ---------------------------------------------------------------------------
PALI_STOP = {
    "ca", "kho", "pana", "ceva", "va", "na", "no", "nu", "hi", "tu",
    "pi", "api", "atha", "ti", "iti", "eva", "yeva",
    "yo", "ya", "yam", "yad", "ye", "yani",
    "yasmin", "yassa",
    "so", "sa", "tam", "tad", "te", "tani",
    "ayam", "idam", "ime", "ima", "imani",
    "eso", "esa", "etam", "etad", "ete", "etani",
    "tesam",
    "aññepi", "añño", "añña", "aññam", "aññe",
    "tattha", "tatra", "yattha", "idha", "ettha",
    "tatha", "yatha", "seyyatha",
    "puna", "tena", "evam",
    "tasmin", "tasmim", "tasma",
    "samaye", "samayam",
    "katame", "katamo", "katamam",
    "hoti", "honti", "ahosi", "atthi", "santi",
    "vuccati", "vuccanti",
    "neva", "nava",
    "ka", "kha", "ga",
}

# ---------------------------------------------------------------------------
# English formula-word stop list
# ---------------------------------------------------------------------------
EN_FORMULA_STOP = {
    "which", "what", "whatever", "whichever", "that", "this", "these",
    "those", "who", "whom", "whose",
    "are", "were", "been", "being", "have", "has", "had",
    "will", "would", "could", "should", "may", "might", "shall",
    "there", "here", "then", "when", "while", "thus", "hence",
    "therein", "herein", "wherein", "thereby",
    "having", "being", "yet", "still", "also", "both", "neither",
    "nor", "either", "whether", "however", "moreover",
}

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------
BLOCK_ID_RE      = re.compile(r"\^[\w\-]+")
FRONTMATTER_RE   = re.compile(r"^---\s*$")
HEADING_RE       = re.compile(r"^#{1,6}\s+")
BRACKET_RE       = re.compile(r"\[.*?\]")
SUB_SPLIT_RE     = re.compile(r"(?=\([KkGgAaBb][a-z]*\))")
SECTION_STRIP_RE = re.compile(r"^\([KkGgAaBb][a-z]*\)\s*")
_PUNCT = str.maketrans("", "", r""".,;:!?()"'`''""—–-_/\\[]{}""")
_PALI_RE = re.compile(r"[\wĀ-žḀ-ỿ]+")

# Module-level phrase set — populated by build_phrases() before Pass 1
_PHRASES: set = set()


def _plain(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------
# Block parser
# ---------------------------------------------------------------------------
def parse_blocks(path: str) -> dict:
    blocks: dict = {}
    pending: list = []
    in_fm, fm_count = False, 0
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if FRONTMATTER_RE.match(line):
                fm_count += 1
                in_fm = (fm_count == 1)
                if fm_count >= 2:
                    in_fm = False
                continue
            if in_fm:
                continue
            m = BLOCK_ID_RE.search(line)
            if m:
                bid = m.group()[1:]
                pending.append(line[:m.start()].strip())
                full = HEADING_RE.sub("", " ".join(pending).strip())
                blocks[bid] = full
                pending = []
            else:
                pending.append(line)
    return blocks


# ---------------------------------------------------------------------------
# Sub-block splitter
# ---------------------------------------------------------------------------
def split_subblocks(text: str) -> list:
    parts = SUB_SPLIT_RE.split(text.strip())
    result = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = SECTION_STRIP_RE.match(part)
        if m:
            label = part[m.start():m.end()].strip("() ")
            body  = part[m.end():].strip()
        else:
            label, body = "", part
        if body:
            result.append((label, body))
    return result or [("", text)]


def build_subblock_pairs(src_blocks: dict, tgt_blocks: dict) -> list:
    pairs = []
    for bid in sorted(set(src_blocks) & set(tgt_blocks)):
        src_subs = {lbl: body for lbl, body in split_subblocks(src_blocks[bid])}
        tgt_subs = {lbl: body for lbl, body in split_subblocks(tgt_blocks[bid])}
        if len(src_subs) == 1 and "" in src_subs:
            tgt_body = tgt_subs.get("") or (list(tgt_subs.values())[0] if tgt_subs else "")
            pairs.append((src_subs[""], tgt_body))
        else:
            for lbl, src_body in src_subs.items():
                if lbl in tgt_subs:
                    pairs.append((src_body, tgt_subs[lbl]))
    return pairs


# ---------------------------------------------------------------------------
# Tokenisers
# ---------------------------------------------------------------------------
def _raw_en_words(text: str) -> list:
    """Lowercased word list, formula-stop removed, no phrase merging."""
    text = BRACKET_RE.sub("", text)
    text = HEADING_RE.sub("", text)
    text = text.translate(_PUNCT).lower()
    return [t for t in text.split()
            if t and not t.isdigit() and len(t) >= 3
            and t not in EN_FORMULA_STOP]


def en_tokens(text: str) -> list:
    """
    English tokens with greedy longest-match phrase merging.
    At each position tries to consume the longest phrase in _PHRASES first.
    """
    words = _raw_en_words(text)
    if not _PHRASES:
        return words
    result = []
    i = 0
    while i < len(words):
        matched = False
        for n in range(min(4, len(words) - i), 1, -1):
            phrase = " ".join(words[i:i + n])
            if phrase in _PHRASES:
                result.append(phrase)
                i += n
                matched = True
                break
        if not matched:
            result.append(words[i])
            i += 1
    return result


def pali_tokens(text: str) -> list:
    """Exact Pali tokens — no stemming."""
    text = BRACKET_RE.sub("", text)
    out = []
    for tok in _PALI_RE.findall(text):
        tok_lc = tok.lower()
        if tok_lc.isdigit() or len(tok_lc) < 2:
            continue
        plain = _plain(tok_lc)
        if plain in PALI_STOP or tok_lc in PALI_STOP:
            continue
        if tok_lc.isascii() and len(tok_lc) <= 3:
            continue
        out.append(tok_lc)
    return out


# ---------------------------------------------------------------------------
# N-gram phrase detection
# ---------------------------------------------------------------------------
def build_phrases(
    tgt_blocks: dict,
    max_n: int = 4,
    min_df: int = 3,
    idf_threshold: float = 3.5,
    order_ratio: float = 4.0,
    min_coverage: float = 0.30,
) -> set:
    """Detect multi-word compound terms of length 2..max_n."""
    global _PHRASES

    unigram_block_df: dict = defaultdict(int)
    for text in tgt_blocks.values():
        words = _raw_en_words(text)
        for w in set(words):
            if en_freq.get_idf(w) >= idf_threshold:
                unigram_block_df[w] += 1

    raw_count:   dict = defaultdict(int)
    block_count: dict = defaultdict(int)

    for text in tgt_blocks.values():
        words = _raw_en_words(text)
        seen_in_block: set = set()
        for n in range(2, max_n + 1):
            for i in range(len(words) - n + 1):
                chunk = words[i:i + n]
                if not all(en_freq.get_idf(w) >= idf_threshold for w in chunk):
                    continue
                phrase = " ".join(chunk)
                raw_count[phrase] += 1
                if phrase not in seen_in_block:
                    block_count[phrase] += 1
                    seen_in_block.add(phrase)

    qualified: set = set()
    for phrase, df in block_count.items():
        if df < min_df:
            continue
        words = phrase.split()
        consistent = True
        for j in range(len(words) - 1):
            fwd = raw_count.get(f"{words[j]} {words[j+1]}", 0)
            rev = raw_count.get(f"{words[j+1]} {words[j]}", 0)
            if fwd < order_ratio * max(rev, 1):
                consistent = False
                break
        if not consistent:
            continue
        min_comp_df = min(unigram_block_df.get(w, 1) for w in words)
        if df / min_comp_df < min_coverage:
            continue
        qualified.add(phrase)

    pruned: set = set()
    for phrase in qualified:
        dominated = any(
            phrase != longer and phrase in longer
            for longer in qualified
            if len(longer.split()) > len(phrase.split())
        )
        if not dominated:
            pruned.add(phrase)

    _PHRASES = pruned
    return _PHRASES


# ---------------------------------------------------------------------------
# Pass 1: TF-IDF English keyword selection
# ---------------------------------------------------------------------------
def select_en_keywords(
    tgt_blocks: dict,
    top_n: int = 600,
    min_df: int = 2,
    max_phrase: int = 4,
) -> list:
    """
    1. Build multi-word phrases (populates _PHRASES).
    2. Score every English token/phrase by (block_df / N) x IDF.
    Return [(token, score), ...] sorted descending, capped at top_n.
    """
    phrases = build_phrases(tgt_blocks, max_n=max_phrase)
    print(f"         {len(phrases)} compound phrases detected", file=sys.stderr)
    if phrases:
        sample = sorted(phrases, key=lambda p: -len(p.split()))[:10]
        print(f"         sample (longest first): {sample}", file=sys.stderr)

    df: dict = defaultdict(int)
    for text in tgt_blocks.values():
        seen: set = set()
        for tok in en_tokens(text):
            if tok not in seen:
                df[tok] += 1
                seen.add(tok)

    N = max(len(tgt_blocks), 1)
    scored = []
    for tok, doc_freq in df.items():
        if doc_freq < min_df or tok in EN_FORMULA_STOP:
            continue
        if " " in tok:
            idf = min(en_freq.get_idf(w) for w in tok.split())
        else:
            idf = en_freq.get_idf(tok)
        if idf < 3.5:
            continue
        scored.append((tok, (doc_freq / N) * idf))

    scored.sort(key=lambda x: -x[1])
    return scored[:top_n]


# ---------------------------------------------------------------------------
# Pass 2: weighted co-occurrence
# ---------------------------------------------------------------------------
def build_cooccurrence(
    pairs: list,
    keywords: list,
    max_pi_df: float = 0.30,
) -> tuple:
    kw_set = {kw for kw, _ in keywords}
    N = len(pairs)

    pi_df_pre: dict = defaultdict(int)
    for pi_text, _ in pairs:
        for pt in set(pali_tokens(pi_text)):
            pi_df_pre[pt] += 1

    pi_freq_limit = max_pi_df * N
    weighted_co: dict = defaultdict(lambda: defaultdict(float))
    raw_co:      dict = defaultdict(lambda: defaultdict(int))
    pi_df:       dict = defaultdict(int)

    for pi_text, en_text in pairs:
        pi_toks = set(pali_tokens(pi_text))
        en_toks = set(en_tokens(en_text))
        en_hits = en_toks & kw_set
        if not en_hits or not pi_toks:
            continue
        pi_toks = {pt for pt in pi_toks if pi_df_pre[pt] <= pi_freq_limit}
        if not pi_toks:
            continue
        w = 1.0 / len(pi_toks)
        for pt in pi_toks:
            pi_df[pt] += 1
            for ek in en_hits:
                weighted_co[pt][ek] += w
                raw_co[pt][ek] += 1

    return weighted_co, raw_co, pi_df


# ---------------------------------------------------------------------------
# Glossary builder
# ---------------------------------------------------------------------------
def build_glossary(
    keywords: list,
    weighted_co: dict,
    raw_co: dict,
    min_co: int = 2,
    min_score: float = 0.25,
    max_pi_per_kw: int = 2,
) -> dict:
    """Returns {english_keyword: {pali_token: count, ...}, ...}"""
    glossary: dict = defaultdict(dict)
    for kw, _ in keywords:
        pali_scores = sorted(
            ((pt, weighted_co[pt].get(kw, 0.0)) for pt in weighted_co),
            key=lambda x: -x[1],
        )
        kept = 0
        for pt, score in pali_scores:
            if score < min_score:
                break
            count = raw_co[pt].get(kw, 0)
            if count < min_co:
                continue
            glossary[kw][pt] = count
            kept += 1
            if kept >= max_pi_per_kw:
                break
    return {
        kw: dict(sorted(pi_dict.items(), key=lambda x: -x[1]))
        for kw, pi_dict in sorted(glossary.items())
        if pi_dict
    }


# ---------------------------------------------------------------------------
# YAML writer
# ---------------------------------------------------------------------------
def write_yaml(glossary: dict, out_path: str, src_path: str, tgt_path: str) -> None:
    sorted_entries = sorted(
        glossary.items(),
        key=lambda kv: sum(kv[1].values()),
        reverse=True,
    )
    lines = [
        "# English keyword → Pāli equivalents (frequency-weighted)",
        "# Method: English TF-IDF (Google-10k Zipf IDF) + weighted sub-block co-occurrence",
        "# Pali: exact token forms, no stemming; compound phrases merged (n-gram)",
        f"# source: {src_path}",
        f"# target: {tgt_path}",
        "# Generated by 4-SYSTEM/Skills/pali-biterm-extraction/scripts/pali_biterm_extraction.py",
        "",
    ]
    for kw, pi_dict in sorted_entries:
        value = ", ".join(f"{pt}-{cnt}" for pt, cnt in pi_dict.items())
        lines.append(f"{kw}: {value}")
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Keywords-only writer (Pass 1 output)
# ---------------------------------------------------------------------------
def write_keywords_only(
    tgt_blocks: dict,
    out_path: str,
    top_n: int = 600,
    max_phrase: int = 4,
) -> None:
    """Write ranked keyword list (Pass 1 only) to out_path."""
    keywords = select_en_keywords(tgt_blocks, top_n=top_n, max_phrase=max_phrase)
    N = len(tgt_blocks)
    lines = [
        "# English keywords",
        "# Method: block-level TF-IDF × Google-10k Zipf IDF; compound phrases via n-gram detection",
        f"# {N} blocks, {len(keywords)} keywords selected",
        "",
    ]
    for kw, score in keywords:
        lines.append(f"{kw}: {score:.2f}")
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"output : {out_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Example phrase extraction (for term-file mode)
# ---------------------------------------------------------------------------
def _extract_short_phrase(text: str, target: str, window: int = 5) -> str:
    """Extract a window of words around target from a Pāli sub-block."""
    text = BLOCK_ID_RE.sub("", text).strip()
    text = SECTION_STRIP_RE.sub("", text).strip()
    words = text.split()
    target_plain = _plain(target.lower())
    # Find the token position
    for i, w in enumerate(words):
        w_clean = _plain(w.lower().translate(_PUNCT))
        if w_clean == target_plain:
            start = max(0, i - 1)
            end   = min(len(words), i + window - 1)
            return " ".join(words[start:end]).rstrip(".,;:")
    # Fallback: whole sub-block (trimmed)
    trimmed = " ".join(words[:window]).rstrip(".,;:")
    return trimmed


def _extract_short_en(text: str, window: int = 6) -> str:
    """Take a short representative clause from an English sub-block."""
    text = BLOCK_ID_RE.sub("", text).strip()
    text = SECTION_STRIP_RE.sub("", text).strip()
    # Try splitting on em-dash or period first
    for sep in [" — ", " - ", "; "]:
        if sep in text:
            part = text.split(sep)[0].strip()
            words = part.split()
            if 2 <= len(words) <= 8:
                return part.rstrip(".,;:")
    words = text.split()
    return " ".join(words[:window]).rstrip(".,;:")


def find_example_phrases(pairs: list, focus_plain: str) -> dict:
    """
    For each Pāli focus-family token, find the first aligned sub-block where
    it appears and extract a short representative example phrase.
    Returns {pali_token: (pali_clause, english_clause)}.
    Prefers shorter sub-blocks (more specific examples).
    """
    examples: dict     = {}
    block_len: dict    = {}  # pali_token -> length of chosen example (prefer shorter)

    for pi_text, en_text in pairs:
        pi_toks_all = pali_tokens(pi_text)
        focus_toks  = [t for t in pi_toks_all if focus_plain in _plain(t)]
        for ft in focus_toks:
            phrase_len = len(pi_text.split())
            if ft in examples and block_len.get(ft, 999) <= phrase_len:
                continue  # keep shorter example
            pi_phrase = _extract_short_phrase(pi_text, ft)
            en_phrase = _extract_short_en(en_text)
            if pi_phrase and en_phrase:
                examples[ft]   = (pi_phrase, en_phrase)
                block_len[ft]  = phrase_len

    return examples


# ---------------------------------------------------------------------------
# Focused keyword supplement (for focus mode)
# ---------------------------------------------------------------------------
def select_focused_keywords(pairs: list, focus_plain: str, min_df: int = 1) -> list:
    """
    Return (keyword, idf) pairs from English blocks whose Pāli side contains
    at least one focus-family token.  Supplements global TF-IDF keywords so
    that terms rare globally but specific to the focus cluster are captured.
    """
    focused_en: list = [
        en_text for pi_text, en_text in pairs
        if any(focus_plain in _plain(pt) for pt in pali_tokens(pi_text))
    ]
    if not focused_en:
        return []

    df: dict = defaultdict(int)
    for text in focused_en:
        seen: set = set()
        for tok in en_tokens(text):
            if tok not in seen:
                df[tok] += 1
                seen.add(tok)

    return [
        (tok, en_freq.get_idf(tok))
        for tok, cnt in df.items()
        if cnt >= min_df and en_freq.get_idf(tok) >= 3.5 and tok not in EN_FORMULA_STOP
    ]


# ---------------------------------------------------------------------------
# Term-file draft writer
# ---------------------------------------------------------------------------
def write_term_file_draft(
    term: str,
    focus_plain: str,
    pairs: list,
    glossary: dict,
    out_dir: str,
) -> str:
    """
    Write a single flat-draft .md file for TERM to {out_dir}/{term}-draft.md.

    The draft has one section per Pāli declension form with:
      - An example phrase from the corpus (Pāli — "English")
      - English renderings ranked by raw co-occurrence count

    Claude then applies semantic grouping (SKILL.md Step 3) to produce
    the final {term}.md in benchmark format.

    Returns the output path.
    """
    # Build pali-centric view: {pali_token: {en_kw: count}}
    pali_centric: dict = defaultdict(dict)
    for kw, pi_dict in glossary.items():
        for pt, cnt in pi_dict.items():
            if focus_plain in _plain(pt.lower()):
                pali_centric[pt][kw] = cnt

    # Include focus-family tokens that appeared in the corpus even if not in
    # the main glossary (e.g. rare forms with count below min_co threshold)
    # — they still need an entry in Declensions section.
    # Collect all focus-family tokens from pairs directly.
    all_focus_toks: set = set()
    for pi_text, _ in pairs:
        for pt in pali_tokens(pi_text):
            if focus_plain in _plain(pt):
                all_focus_toks.add(pt)

    # For tokens not yet in pali_centric, add an empty entry so the
    # Declensions section still lists them (with example but no counts).
    for ft in all_focus_toks:
        if ft not in pali_centric:
            pali_centric[ft] = {}

    # Find example phrases for each declension
    examples = find_example_phrases(pairs, focus_plain)

    # Sort by total raw co-occurrence count desc; ties: alphabetical
    sorted_decl = sorted(
        pali_centric.items(),
        key=lambda kv: (-sum(kv[1].values()), kv[0]),
    )

    lines = [
        f"# {term}",
        "",
        "<!-- flat draft — Claude applies semantic grouping to produce final format -->",
        "<!-- Step 3: group declensions into senses, aggregate counts, write benchmark format -->",
        "",
    ]

    for pt, en_dict in sorted_decl:
        pi_ex, en_ex = examples.get(pt, ("", ""))
        lines.append(f"## Declension: {pt}")
        if pi_ex and en_ex:
            lines.append(f"Example: {pi_ex} — \"{en_ex}\"")
        if en_dict:
            for kw, cnt in sorted(en_dict.items(), key=lambda x: -x[1]):
                lines.append(f"{kw}: {cnt}")
        else:
            lines.append("<!-- no co-occurrence counts above threshold -->")
        lines.append("")

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = str(Path(out_dir) / f"{term}-draft.md")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="Pali-English bilingual term extraction")
    p.add_argument("pali",
                   help="Pāli source markdown file (or English file if --keywords-only)")
    p.add_argument("english",
                   help="English translation markdown file (or output path if --keywords-only)")
    p.add_argument("output",  nargs="?", default=None,
                   help="Output path or directory (omit if --keywords-only)")
    p.add_argument("--top",           type=int,   default=600,  help="English keywords to consider")
    p.add_argument("--min-co",        type=int,   default=2,    help="Min raw co-occurrence count")
    p.add_argument("--min-score",     type=float, default=0.25, help="Min weighted alignment score")
    p.add_argument("--max-pi-df",     type=float, default=None,
                   help="Max Pali doc-freq fraction (default 0.99 in term-file; 0.30 in yaml)")
    p.add_argument("--max-pi-per-kw", type=int,   default=None,
                   help="Max Pali tokens per English keyword (default 20 in term-file; 2 in yaml)")
    p.add_argument("--max-phrase",    type=int,   default=4,    help="Max phrase length in words")
    p.add_argument("--focus",         default=None,
                   help="Root term to focus on (required for term-file mode)")
    p.add_argument("--format",        choices=["yaml", "term-file"], default="term-file",
                   help="Output format (default: term-file)")
    p.add_argument("--keywords-only", action="store_true",
                   help="Pass 1 only: first arg = English file, second arg = output path")
    args = p.parse_args()

    # ---- keywords-only mode -----------------------------------------------
    if args.keywords_only:
        en_file  = args.pali     # first positional = English file
        out_file = args.english  # second positional = output path
        print(f"english: {en_file}", file=sys.stderr)
        print(f"mode   : keywords-only (Pass 1)", file=sys.stderr)
        tgt_blocks = parse_blocks(en_file)
        print(f"blocks : {len(tgt_blocks)}", file=sys.stderr)
        print("Pass 1 : TF-IDF keyword extraction ...", file=sys.stderr)
        write_keywords_only(tgt_blocks, out_file, top_n=args.top, max_phrase=args.max_phrase)
        return

    # ---- normal modes -------------------------------------------------------
    if args.output is None:
        p.error("output argument is required (omit only with --keywords-only)")

    # Apply mode-aware defaults
    term_file_mode = args.format == "term-file"
    max_pi_df      = args.max_pi_df     if args.max_pi_df     is not None else (0.99 if term_file_mode else 0.30)
    max_pi_per_kw  = args.max_pi_per_kw if args.max_pi_per_kw is not None else (20   if term_file_mode else 2)

    print(f"source : {args.pali}",    file=sys.stderr)
    print(f"target : {args.english}", file=sys.stderr)
    if args.focus:
        print(f"focus  : {args.focus}", file=sys.stderr)
    print(f"format : {args.format}",  file=sys.stderr)

    src_blocks = parse_blocks(args.pali)
    tgt_blocks = parse_blocks(args.english)
    print(f"blocks : {len(src_blocks)} src / {len(tgt_blocks)} tgt", file=sys.stderr)

    aligned_ids = set(src_blocks) & set(tgt_blocks)
    print(f"aligned: {len(aligned_ids)} block pairs", file=sys.stderr)
    if not aligned_ids:
        print("ERROR: no aligned block pairs", file=sys.stderr)
        sys.exit(1)

    print("Pass 1 : TF-IDF keyword extraction ...", file=sys.stderr)
    keywords = select_en_keywords(tgt_blocks, top_n=args.top, max_phrase=args.max_phrase)
    print(f"         {len(keywords)} keywords selected", file=sys.stderr)
    if keywords:
        print(f"         top 10: {[kw for kw, _ in keywords[:10]]}", file=sys.stderr)

    print("Building sub-block pairs ...", file=sys.stderr)
    pairs = build_subblock_pairs(src_blocks, tgt_blocks)
    print(f"         {len(pairs)} sub-block pairs", file=sys.stderr)

    # Supplement global keywords with terms specific to focus-family blocks
    if args.focus:
        focus_plain = _plain(args.focus.lower())
        focused_kws = select_focused_keywords(pairs, focus_plain)
        global_kw_set = {k for k, _ in keywords}
        extra_kws = [(k, s) for k, s in focused_kws if k not in global_kw_set]
        keywords = keywords + extra_kws
        if extra_kws:
            print(f"         +{len(extra_kws)} focused keywords added for '{args.focus}'", file=sys.stderr)

    print("Pass 2 : weighted co-occurrence ...", file=sys.stderr)
    weighted_co, raw_co, pi_df = build_cooccurrence(
        pairs, keywords, max_pi_df=max_pi_df
    )

    glossary = build_glossary(
        keywords, weighted_co, raw_co,
        min_co=args.min_co,
        min_score=args.min_score,
        max_pi_per_kw=max_pi_per_kw,
    )
    print(f"terms  : {len(glossary)} English terms in output", file=sys.stderr)

    if term_file_mode:
        if not args.focus:
            p.error("--focus TERM is required for --format term-file")
        focus_plain = _plain(args.focus.lower())
        out_path = write_term_file_draft(
            term=args.focus,
            focus_plain=focus_plain,
            pairs=pairs,
            glossary=glossary,
            out_dir=args.output,
        )
        print(f"output : {out_path}", file=sys.stderr)
        # Summary of matched English keywords
        matched_kws = [
            kw for kw, pi_dict in glossary.items()
            if any(focus_plain in _plain(pt.lower()) for pt in pi_dict)
        ]
        print(f"focus  : {len(matched_kws)} English keywords matched — {matched_kws[:10]}", file=sys.stderr)
    else:
        write_yaml(glossary, args.output, args.pali, args.english)
        print(f"output : {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
