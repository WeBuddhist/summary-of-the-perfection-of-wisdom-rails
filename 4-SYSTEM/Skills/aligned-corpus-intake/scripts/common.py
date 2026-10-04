"""Shared helpers for the aligned-corpus-intake adapters."""
import hashlib
import pathlib
import re
import unicodedata

from project import is_letter

# Digits of an alignment number: Arabic (ASCII or full-width), never Tibetan.
# A paragraph opening with Tibetan numerals ("༥༽", "༡)") is an enumeration
# in the text itself, not a reference the aligners typed.
_D = r"[^\D\u0F20-\u0F29]"

# A typed alignment reference at the start of a line, Pecha convention
# (4-SYSTEM/Skills/aligned-corpus-intake/references/pecha-conventions.md):
#   "12."  "12-15."  "1-3,5,6."  "17-19 "   — a single number needs its dot,
# a range may omit it. An optional Tibetan tsheg may follow the dot.
# Whitespace around a typed number, including the zero-width spaces Google
# Docs leaves after a shad ("\u200b46 དང་པོ་ནི།").
_S = r"[\s\u200b\ufeff]"

REF_PREFIX = re.compile(
    rf"^(?P<all>{_S}*(?P<refs>{_D}+(?:\s*[-–~]\s*{_D}+)?(?:\s*[,，、]\s*{_D}+(?:\s*[-–~]\s*{_D}+)?)*)"
    rf"(?P<dot>\s*[\.．])?་?{_S}*)")


# Bare style (Tibetan commentaries): "14 ", "1-3 ", "198,199,201 " — never
# followed by a dot (a dotted number there is a heading's outline number).
REF_PREFIX_BARE = re.compile(
    rf"^(?P<all>{_S}*(?P<refs>{_D}+(?:\s*[-–~]\s*{_D}+)?(?:\s*[,，、]\s*{_D}+(?:\s*[-–~]\s*{_D}+)?)*)(?![\d.．]){_S}*)")


def parse_ref_prefix(line, style="dotted"):
    """Return (refs, prefix, rest) or (None, "", line).
    refs is the expanded, ordered list of ints."""
    m = (REF_PREFIX_BARE if style == "bare" else REF_PREFIX).match(line)
    if not m:
        return None, "", line
    refs_s = m.group("refs")
    is_range = bool(re.search(r"[-–~,，、]", refs_s))
    if style != "bare" and not m.group("dot") and not is_range:
        return None, "", line
    rest = line[m.end():]
    if not rest.strip():
        return None, "", line
    out = []
    for part in re.split(r"\s*[,，、]\s*", refs_s):
        bounds = [int(x) for x in re.split(r"\s*[-–~]\s*", part)]
        if len(bounds) == 2 and bounds[0] <= bounds[1]:
            out.extend(range(bounds[0], bounds[1] + 1))
        else:
            out.extend(bounds)
    seen = []
    for x in out:
        if x not in seen:
            seen.append(x)
    return seen, m.group("all"), rest


def letters_only(s):
    return "".join(ch for ch in s if is_letter(ch))


def _norm_name(s):
    return " ".join(unicodedata.normalize("NFC", s).replace("\u00a0", " ").split())


def raw_path(root, rel):
    """Resolve a manifest path under the raw root. Drive exports put
    no-break spaces after IDs and may store names decomposed; a manifest
    written with plain spaces still finds the file, component by component.
    Ambiguous or missing components raise FileNotFoundError."""
    root = pathlib.Path(root)
    p = root / rel
    if p.exists():
        return p
    cur = root
    for part in pathlib.PurePosixPath(rel).parts:
        nxt = cur / part
        if not nxt.exists():
            hits = [c for c in cur.iterdir() if _norm_name(c.name) == _norm_name(part)] if cur.is_dir() else []
            if len(hits) != 1:
                raise FileNotFoundError(root / rel)
            nxt = hits[0]
        cur = nxt
    return cur


def sha1(path):
    return hashlib.sha1(pathlib.Path(path).read_bytes()).hexdigest()


class LetterIndex:
    """Locate pieces of a reference text by their letters.

    Built over the blocks of an already-rendered work (id -> text). `find`
    returns the ids whose letters overlap the first occurrence of `piece` at
    or after `hint` (falling back to a search from the start). Order-free, so
    it survives the passage reordering some human alignments contain.
    """

    def __init__(self, blocks):
        self.ids, self.starts, buf = [], [], []
        n = 0
        for bid, text in blocks:
            letters = letters_only(text)
            self.ids.append(bid)
            self.starts.append(n)
            buf.append(letters)
            n += len(letters)
        self.text = "".join(buf)
        self.ends = self.starts[1:] + [n]

    def locate(self, piece, hint=0):
        p = letters_only(piece)
        if not p:
            return None
        pos = self.text.find(p, hint)
        if pos == -1:
            pos = self.text.find(p)
        if pos != -1:
            return pos, pos + len(p)
        # Tolerant fallback for a piece with a small internal difference
        # (an omitted or added phrase): anchor its first and last letters.
        k = min(8, len(p) // 2)
        if k < 4:
            return None
        head, tail = p[:k], p[-k:]
        s = self.text.find(head, hint)
        if s == -1:
            s = self.text.find(head)
        if s == -1:
            return None
        e = self.text.find(tail, s)
        if e == -1 or (e + k - s) > 2 * len(p) + 40:
            return None
        return s, e + k

    def ids_for(self, start, end):
        return [bid for bid, s, e in zip(self.ids, self.starts, self.ends) if s < end and e > start]

    def find(self, piece, hint=0):
        loc = self.locate(piece, hint)
        if loc is not None:
            return self.ids_for(*loc), loc[1]
        # Last resort for a row whose clauses were reordered by the aligner:
        # locate each punctuation-delimited clause on its own.
        clauses = [c for c in re.split(r"[。！？；：，、「」『』\u0f0d\u0f0e]+", piece) if len(letters_only(c)) >= 4]
        if len(clauses) < 2:
            return None, hint
        ids, end = [], hint
        for c in clauses:
            l = self.locate(c, hint)
            if l is None:
                return None, hint
            ids += [i for i in self.ids_for(*l) if i not in ids]
            end = max(end, l[1])
        return ids, end
