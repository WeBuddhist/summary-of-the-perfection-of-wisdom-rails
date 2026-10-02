#!/usr/bin/env python3
"""
day_package_tools.py — lock and enforce the day-package format.

Subcommands:

  validate <file.md> [...]   Check a day-package file against the locked
                             contract. Exits non-zero and prints every
                             violation ("fail loud"). Structural problems are
                             ERRORS; softer issues are WARNINGS.

  conform  <file.md> [...]   Rewrite a day-package file in place to match the
                             contract: insert machine anchors before every
                             recognized heading, and consolidate inline
                             citation links into a single `Sources:` line per
                             leaf section. Never rewords prose. Tables are left
                             untouched (their Source column is legitimate
                             structured provenance).

  guard record               Record sha256 of every protected file (listed in
                             the guard paths file) into the guard lock. Run
                             this after an APPROVED change so the baseline
                             stays current.
  guard check                Re-hash the protected files and report any that
                             changed / went missing since the last `record`.
                             Exits non-zero on any drift ("fail loud"). This is
                             advisory drift-detection, not enforcement.

The section vocabulary — top-level sections, per-verse subsections, challenge
sub-blocks, the required frontmatter keys — is read from a JSON spec, one per
plan, so nothing about a particular text is baked into this script. See
`../templates/package-spec.json`.

Stdlib only.

PROTECTED SOURCE-OF-TRUTH TOOL — the copy installed in a vault should not be
edited, moved or deleted without explicit human confirmation. The canonical
spec lives in the plan's package template; this script and that document must
agree.
"""
import argparse
import hashlib
import json
import os
import re
import sys

# sentinel: this heading's machine id lives in its <!-- cm:/story: --> anchor,
# not in the visible heading text (which is display-only: name + work).
PRESERVE = "\x00PRESERVE"

CITATION = re.compile(r"\[\[[^\]]*\]\]")
# an inline citation "wrapper": optional arrow, then (link link ...) of links only
CIT_WRAPPER = re.compile(r"\s*(?:→\s*)?\(\s*(?:\[\[[^\]]*\]\]\s*)+\)")
ANCHOR = re.compile(r"^<!--\s*([a-z]+:[A-Za-z0-9._:-]+)\s*-->\s*$")
HEADING = re.compile(r"^(#{2,5})\s+(.*?)\s*$")

DEFAULT_SPEC = {
    "top_sections": [],
    "challenge_subs": {},
    "verse_subs": [],
    "verse_heading_prefix": "Verse ",
    "divergence_prefix": "Divergences",
    "frontmatter_required": ["day:", "chapter:", "verses:", "status:",
                             "language:", "document_type:"],
}


def load_spec(path):
    spec = dict(DEFAULT_SPEC)
    if path:
        with open(path, encoding="utf-8") as fh:
            spec.update({k: v for k, v in json.load(fh).items()
                         if not k.startswith("_")})
    return spec


def split_frontmatter(text):
    m = re.match(r"^(---\n.*?\n---\n)(.*)$", text, re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return "", text


def heading_anchor(spec, level, text):
    """Return the anchor slug a heading should carry, or None if not tracked."""
    if level == 2:
        m = re.match(r"^\d+\.\s+(.*)$", text)
        core = m.group(1) if m else text
        for entry in spec["top_sections"]:
            _key, htext, slug = entry
            if core.startswith(htext):
                return slug
        return None
    if level == 3:
        prefix = spec["verse_heading_prefix"]
        if prefix and text.startswith(prefix):
            return "verse:%s" % text[len(prefix):].strip()
        for htext, slug in spec["challenge_subs"].items():
            if text == htext:
                return slug
        return None
    if level == 4:
        core4 = text.lstrip("⚑ ").strip()
        if core4.startswith(spec["divergence_prefix"]):
            return "sub:divergences"
        for entry in spec["verse_subs"]:
            htext, slug = entry[0], entry[1]
            if text.startswith(htext):
                return slug
        return None
    if level == 5:
        core5 = text.lstrip("⚑ ").strip()
        if core5.startswith(spec["divergence_prefix"]):
            return "div:divergences"
        # commentator / story block. The visible heading is display-only
        # (Name + Work, or story Title); the machine id lives in the
        # `<!-- cm:.. -->` / `<!-- story:.. -->` anchor above. Preserve it.
        return PRESERVE
    return None


# ---------------------------------------------------------------- validate --

def validate(path, spec):
    errors, warnings = [], []
    raw = open(path, encoding="utf-8").read()
    fm, body = split_frontmatter(raw)

    if not fm:
        errors.append("missing YAML frontmatter")
    else:
        for key in spec["frontmatter_required"]:
            if not re.search(r"(?m)^" + re.escape(key), fm):
                errors.append("frontmatter missing `%s`" % key)

    lines = body.split("\n")

    # no unresolved Obsidian transclusions
    for i, ln in enumerate(lines, 1):
        if "![[" in ln:
            errors.append("line %d: unresolved transclusion `![[...]]` "
                          "(inline the text instead)" % i)

    # every tracked heading must be immediately preceded by its correct anchor
    top_seen, verse_ids = [], []
    for i, ln in enumerate(lines):
        m = HEADING.match(ln)
        if not m:
            continue
        level, text = len(m.group(1)), m.group(2)
        want = heading_anchor(spec, level, text)
        if want is None:
            if level in (2, 4):
                warnings.append('heading not in locked vocabulary: "%s"' % ln.strip())
            continue
        prev = lines[i - 1].strip() if i > 0 else ""
        am = ANCHOR.match(prev)
        if want is PRESERVE:
            if not am:
                errors.append('line %d: H5 heading "%s" missing its `<!-- cm:… -->` / '
                              '`<!-- story:… -->` anchor on preceding line' % (i + 1, text))
            elif not re.match(r"^(cm|story):[A-Za-z0-9._:-]+$", am.group(1)):
                errors.append('line %d: H5 heading "%s" has anchor `%s`, expected a '
                              '`cm:…` / `story:…` id' % (i + 1, text, am.group(1)))
            continue
        if not am:
            errors.append('line %d: heading "%s" missing anchor `<!-- %s -->` on '
                          'preceding line' % (i + 1, text, want))
        elif am.group(1) != want:
            errors.append('line %d: heading "%s" has anchor `%s`, expected `%s`'
                          % (i + 1, text, am.group(1), want))
        if want.startswith("sec:"):
            top_seen.append(want)
        if want.startswith("verse:"):
            verse_ids.append(want.split(":", 1)[1])

    # top-level sections present and in order
    want_order = [e[2] for e in spec["top_sections"]]
    if want_order and top_seen != want_order:
        errors.append("top-level sections %s != required %s" % (top_seen, want_order))

    # verse ids match frontmatter `verses:`
    vm = re.search(r'(?m)^verses:\s*"?([0-9]+)-([0-9]+)\s+to\s+([0-9]+)-([0-9]+)"?', fm)
    if not vm:
        vm2 = re.search(r'(?m)^verses:\s*"?([0-9]+)-([0-9]+)"?', fm)
        expect = ["%s-%s" % (vm2.group(1), vm2.group(2))] if vm2 else []
    else:
        ch = vm.group(1)
        expect = ["%s-%d" % (ch, n) for n in range(int(vm.group(2)), int(vm.group(4)) + 1)]
    if expect and verse_ids != expect:
        errors.append("verse blocks %s != frontmatter range %s" % (verse_ids, expect))

    # required per-verse subsections present
    blocks = re.split(r"(?m)^<!-- verse:", body)
    for blk in blocks[1:]:
        vid = blk.split(" ", 1)[0].split("-->", 1)[0].strip()
        for entry in spec["verse_subs"]:
            htext, req = entry[0], (entry[2] if len(entry) > 2 else False)
            if req and (("#### " + htext) not in blk):
                errors.append("verse %s: missing required subsection `%s`" % (vid, htext))

    # stray inline citations outside a Sources: line or a table row
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith("|"):
            continue                      # table cell provenance is allowed
        if ln.strip().startswith("Sources:"):
            continue
        if CITATION.search(ln):
            errors.append("line %d: inline citation link outside a `Sources:` line: %s"
                          % (i, ln.strip()[:70]))

    ok = not errors
    print("[%s] %s" % ("PASS" if ok else "FAIL", path))
    for e in errors:
        print("  ERROR:   %s" % e)
    for w in warnings:
        print("  warning: %s" % w)
    return ok


# ----------------------------------------------------------------- conform --

def conform(path, spec):
    raw = open(path, encoding="utf-8").read()
    fm, body = split_frontmatter(raw)

    orig_lines = body.split("\n")
    # capture, in document order, the anchor immediately preceding each heading.
    # Commentator/story H5 ids are not derivable from the (display-only) heading,
    # so their anchor must be preserved rather than regenerated.
    orig_anchor_by_heading = []
    for i, ln in enumerate(orig_lines):
        if HEADING.match(ln):
            prev = orig_lines[i - 1].strip() if i > 0 else ""
            am = ANCHOR.match(prev)
            orig_anchor_by_heading.append(am.group(1) if am else None)

    # strip ALL existing anchors first; they are regenerated deterministically
    lines = [ln for ln in orig_lines if not ANCHOR.match(ln.strip())]

    # segment the body by headings; segment 0 is the preamble (before 1st heading)
    head_idxs = [i for i, ln in enumerate(lines) if HEADING.match(ln)]
    segments = []
    if not head_idxs:
        segments.append((None, lines))
    else:
        if head_idxs[0] > 0:
            segments.append((None, lines[:head_idxs[0]]))
        for k, hi in enumerate(head_idxs):
            end = head_idxs[k + 1] if k + 1 < len(head_idxs) else len(lines)
            segments.append((hi, lines[hi:end]))

    out = []
    heading_i = -1
    for head_pos, seg in segments:
        if head_pos is None:
            out.extend(seg)                       # preamble, verbatim
            continue

        heading_i += 1
        head_line = seg[0]
        m = HEADING.match(head_line)
        want = heading_anchor(spec, len(m.group(1)), m.group(2))
        if want is PRESERVE:
            # reuse the id from the anchor that was already there (display-only heading)
            want = orig_anchor_by_heading[heading_i]
        content = list(seg[1:])

        # peel trailing blanks and a trailing "---" rule (remembered, re-added last)
        trailing_sep = False
        while content and content[-1].strip() == "":
            content.pop()
        if content and content[-1].strip() == "---":
            trailing_sep = True
            content.pop()
            while content and content[-1].strip() == "":
                content.pop()

        has_table = any(l.lstrip().startswith("|") for l in content)
        toks = []
        if not has_table:
            rebuilt = []
            for l in content:
                if not CITATION.search(l):
                    rebuilt.append(l)             # no citation -> verbatim (keeps breaks)
                    continue
                for t in CITATION.findall(l):
                    if t not in toks:
                        toks.append(t)
                if l.lstrip().startswith("Sources:"):
                    continue                      # drop old Sources line (rebuilt below)
                s = CIT_WRAPPER.sub("", l).rstrip()
                if s.strip() == "" and l.strip() != "":
                    continue                      # drop citation-only line
                rebuilt.append(s)
            content = rebuilt
            while content and content[-1].strip() == "":
                content.pop()

        if want:
            out.append("<!-- %s -->" % want)
        out.append(head_line)
        out.extend(content)
        if toks and not has_table:
            out.append("")
            out.append("Sources: " + " ".join(toks))
        if trailing_sep:
            out.append("")
            out.append("---")
        out.append("")

    new_body = "\n".join(out)
    new_body = re.sub(r"\n{3,}", "\n\n", new_body).rstrip() + "\n"
    open(path, "w", encoding="utf-8").write(fm + new_body)
    print("conformed: %s" % path)


# ------------------------------------------------------------------- guard --
# Advisory drift-detection for the protected source-of-truth files. Not
# enforcement: it cannot stop an edit, only make an unauthorized one loud.

def protected_files(root, guard_paths):
    """Expand the guard paths file (globs, relative to root) into files."""
    import glob
    files = []
    if not os.path.exists(guard_paths):
        return files
    for line in open(guard_paths, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for p in sorted(glob.glob(os.path.join(root, line))):
            if os.path.isfile(p):
                files.append(os.path.relpath(p, root))
    return sorted(set(files))


def _sha256(root, rel):
    with open(os.path.join(root, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _load_lock(lock_path):
    lock = {}
    if os.path.exists(lock_path):
        for line in open(lock_path, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            h, _, rel = line.partition("  ")
            lock[rel] = h
    return lock


def guard_record(root, guard_paths, lock_path):
    files = protected_files(root, guard_paths)
    with open(lock_path, "w", encoding="utf-8") as fh:
        fh.write("# guard.lock — sha256 baseline of protected source-of-truth files.\n")
        fh.write("# Regenerate ONLY after an approved change: `guard record`.\n")
        for rel in files:
            fh.write("%s  %s\n" % (_sha256(root, rel), rel))
    print("recorded %d protected files -> %s" % (len(files), lock_path))
    return 0


def guard_check(root, guard_paths, lock_path):
    lock = _load_lock(lock_path)
    current = {rel: _sha256(root, rel) for rel in protected_files(root, guard_paths)}
    changed = [r for r in current if r in lock and current[r] != lock[r]]
    missing = [r for r in lock if r not in current]        # moved/deleted/renamed
    added = [r for r in current if r not in lock]          # new, not yet baselined
    for r in changed:
        print("  CHANGED: %s" % r)
    for r in missing:
        print("  MISSING (moved/deleted?): %s" % r)
    for r in added:
        print("  warning: untracked protected file (run `guard record`): %s" % r)
    if not lock:
        print("[guard] no baseline yet — run `guard record` first.")
        return 1
    if changed or missing:
        print("[guard] DRIFT DETECTED — %d changed, %d missing. If unauthorized, "
              "restore from version control; if approved, re-run `guard record`."
              % (len(changed), len(missing)))
        return 1
    print("[guard] OK — %d protected files match the baseline." % len(current))
    return 0


# -------------------------------------------------------------------- main --

def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("validate", "conform"):
        sp = sub.add_parser(name)
        sp.add_argument("--spec", required=True, help="the plan's package-spec JSON")
        sp.add_argument("files", nargs="+")

    gp = sub.add_parser("guard")
    gp.add_argument("mode", choices=["record", "check"])
    gp.add_argument("--root", default=".", help="vault root the guard globs are relative to")
    gp.add_argument("--guard-paths", default=None,
                    help="default: <root>/4-SYSTEM/scripts/day-package/guard.paths")
    gp.add_argument("--guard-lock", default=None,
                    help="default: beside the guard paths file, named guard.lock")

    args = p.parse_args()

    if args.cmd == "guard":
        root = os.path.abspath(args.root)
        gpath = args.guard_paths or os.path.join(
            root, "4-SYSTEM", "scripts", "day-package", "guard.paths")
        lock = args.guard_lock or os.path.join(os.path.dirname(gpath), "guard.lock")
        if not os.path.exists(gpath):
            print("no guard paths file at %s — create one (see the skill's "
                  "scripts/guard.paths example)" % gpath)
            return 2
        return guard_record(root, gpath, lock) if args.mode == "record" \
            else guard_check(root, gpath, lock)

    spec = load_spec(args.spec)
    ok = True
    for f in args.files:
        if args.cmd == "validate":
            ok = validate(f, spec) and ok
        else:
            conform(f, spec)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
