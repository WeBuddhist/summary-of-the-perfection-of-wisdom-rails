#!/usr/bin/env python3
"""
check_day_file.py — mechanically verify one plan day file against the plan's
own section-type declaration.

Everything this script checks comes from a JSON spec written once per plan
(the machine-readable form of the table in `About <plan-name>.md`). Nothing
about any particular text, language or plan is hard-coded here.

  python3 check_day_file.py --spec <plan-spec.json> [--verses 2-35,2-36] \\
      [--frontmatter day,chapter,verses,status] <day-file.md> [...]

Checks performed
----------------
  * frontmatter keys present
  * every required section heading present, spelled exactly as declared
  * declared section order respected (sections allowed to be absent may be
    missing, but the ones present must be in order)
  * no heading outside the declared vocabulary at the declared level
  * per-section ceilings in words or syllables (hard limit -> ERROR)
  * per-section bands (diagnostic -> warning, never an error)
  * required opening / closing formula per section
  * block IDs in the verse section: present, contiguous, equal to the expected
    list (from --verses or from the `verses:` frontmatter)
  * forbidden elements, by regex, outside exempted sections
  * the category tag: present, correctly wrapped, drawn from the allowed list

Exits non-zero on any ERROR ("fail loud"). Warnings never fail the run.

Spec format
-----------
{
  "heading_level": 2,
  "default_unit": "words",
  "sections": [
    {"id": "opening",  "heading": "## Opening", "required": true,
     "ceiling": 60, "unit": "words", "band": [40, 60],
     "opens_with": "Today's practice is based on"},
    {"id": "verses",   "heading": "## Today's Verses", "required": true,
     "verbatim": true},
    {"id": "practice", "heading": "## Today's Practice", "required": true,
     "count_from_label": "**Actual Practice:**", "ceiling": 30,
     "unit": "syllables"}
  ],
  "forbidden": [
    {"name": "em dash in body prose", "regex": "\\u2014"},
    {"name": "emoji in body text",    "regex": "[\\U0001F300-\\U0001FAFF]"}
  ],
  "forbidden_exempt_sections": ["verses"],
  "block_id_section": "verses",
  "category_tag": {"section": "practice", "regex": "_\\(([^)]+)\\)_",
                   "allowed": ["Doing good", "Patience"]}
}

Stdlib only.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from count_syllables import count  # noqa: E402

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
VERSE_ID = re.compile(r"\^(\d+)-(\d+)\b")


def split_frontmatter(text):
    m = re.match(r"^(---\n.*?\n---\n)(.*)$", text, re.DOTALL)
    if m:
        return m.group(1), m.group(2)
    return "", text


def normalise_heading(line):
    """Strip heading marks, emoji, numerals and trailing punctuation so two
    spellings of the same heading compare equal."""
    s = line.strip()
    s = re.sub(r"^#{1,6}\s*", "", s)
    s = re.sub(r"[\U0001F000-\U0001FAFF☀-➿️]", "", s)
    s = re.sub(r"^[\s\d༠-༳०-९.)།]+", "", s)
    s = s.rstrip(" :།༎")
    return s.strip()


def split_sections(body, specs):
    """Return [(section-spec-or-None, heading-line, [content lines])] in order."""
    by_norm = {}
    for s in specs:
        by_norm.setdefault(normalise_heading(s["heading"]), s)

    lines = body.split("\n")
    head_idx = [i for i, l in enumerate(lines) if HEADING.match(l)]
    out = []
    if not head_idx:
        return out
    for k, hi in enumerate(head_idx):
        end = head_idx[k + 1] if k + 1 < len(head_idx) else len(lines)
        spec = by_norm.get(normalise_heading(lines[hi]))
        if spec is not None:
            out.append((spec, lines[hi], lines[hi + 1:end]))
        else:
            out.append((None, lines[hi], lines[hi + 1:end]))
    # merge unrecognised (sub-)headings into the enclosing declared section
    merged = []
    for spec, head, content in out:
        if spec is None and merged:
            merged[-1][2].append(head)
            merged[-1][2].extend(content)
        else:
            merged.append([spec, head, list(content)])
    return [tuple(x) for x in merged]


def content_after_label(content, label):
    text = "\n".join(content)
    i = text.find(label)
    if i < 0:
        return None
    rest = text[i + len(label):]
    stop = re.search(r"\n\s*(?:\*\*[^*]+:\*\*|#{1,6}\s)", rest)
    return rest[:stop.start()] if stop else rest


def expected_ids_from_frontmatter(fm):
    m = re.search(r'(?m)^verses:\s*"?(\d+)-(\d+)\s+to\s+(\d+)-(\d+)"?', fm)
    if m:
        ch = m.group(1)
        return ["%s-%d" % (ch, n) for n in range(int(m.group(2)), int(m.group(4)) + 1)]
    m = re.search(r'(?m)^verses?:\s*"?(\d+)-(\d+)"?\s*$', fm)
    if m:
        return ["%s-%s" % (m.group(1), m.group(2))]
    return None


def check(path, spec, expected_verses, fm_keys):
    errors, warnings, notes = [], [], []
    raw = open(path, encoding="utf-8").read()
    fm, body = split_frontmatter(raw)

    if not fm:
        errors.append("missing YAML frontmatter")
    else:
        for key in fm_keys:
            if not re.search(r"(?m)^%s\s*:" % re.escape(key), fm):
                errors.append("frontmatter missing `%s:`" % key)
        if re.search(r"(?m)^status:\s*complete", fm):
            errors.append("`status: complete` — a generator never sets complete; "
                          "only a domain specialist does")

    specs = spec["sections"]
    sections = split_sections(body, specs)
    present = [s[0]["id"] for s in sections if s[0]]

    for s in specs:
        if s.get("required", True) and s["id"] not in present:
            errors.append("required section `%s` (%s) is missing"
                          % (s["id"], s["heading"]))
        if not s.get("required", True) and s["id"] not in present:
            notes.append("section `%s` is absent — state in the report why the "
                         "source had nothing for it" % s["id"])

    order = [s["id"] for s in specs]
    got = [i for i in present if i in order]
    if got != sorted(got, key=order.index):
        errors.append("sections out of declared order: %s (declared: %s)"
                      % (got, order))

    seen = set()
    for i in present:
        if i in seen:
            errors.append("section `%s` appears more than once" % i)
        seen.add(i)

    for sec, head, content in sections:
        if sec is None:
            m = HEADING.match(head)
            if m and len(m.group(1)) == spec.get("heading_level", 2):
                warnings.append('heading not in the declared vocabulary: "%s"'
                                % head.strip())
            continue
        if sec["heading"].strip() != head.strip():
            errors.append('section `%s`: heading is "%s", declared "%s"'
                          % (sec["id"], head.strip(), sec["heading"].strip()))

        text = "\n".join(content)
        counted = text
        if sec.get("count_from_label"):
            sub = content_after_label(content, sec["count_from_label"])
            if sub is None:
                errors.append("section `%s`: label %r not found"
                              % (sec["id"], sec["count_from_label"]))
                sub = ""
            counted = sub

        unit = sec.get("unit", spec.get("default_unit", "words"))
        if sec.get("ceiling") or sec.get("band"):
            n = count(counted, unit)
            notes.append("section `%s`: %d %s" % (sec["id"], n, unit))
            if sec.get("ceiling") and n > sec["ceiling"]:
                errors.append("section `%s`: %d %s exceeds the ceiling of %d"
                              % (sec["id"], n, unit, sec["ceiling"]))
            band = sec.get("band")
            if band and not (band[0] <= n <= band[1]):
                warnings.append("section `%s`: %d %s is outside its band %d-%d "
                                "— report why, do not pad or trim"
                                % (sec["id"], n, unit, band[0], band[1]))

        if sec.get("opens_with"):
            first = next((l for l in content if l.strip()), "")
            probe = content_after_label(content, sec["count_from_label"]) \
                if sec.get("count_from_label") else None
            hay = (probe or first).lstrip()
            if sec["opens_with"] not in hay[:len(sec["opens_with"]) + 40]:
                errors.append("section `%s`: does not open with the required "
                              "formula %r" % (sec["id"], sec["opens_with"]))
        if sec.get("ends_with"):
            last = next((l for l in reversed(content) if l.strip()), "")
            if not last.rstrip().endswith(sec["ends_with"]):
                errors.append("section `%s`: does not close with the required "
                              "formula %r" % (sec["id"], sec["ends_with"]))

    # ---- block IDs in the verse section
    bsec = spec.get("block_id_section")
    if bsec:
        blk = next((c for s, _h, c in sections if s and s["id"] == bsec), None)
        if blk is None:
            if any(s.get("id") == bsec and s.get("required", True) for s in specs):
                errors.append("verse section `%s` not found — cannot check block IDs"
                              % bsec)
        else:
            found = ["%s-%s" % (m.group(1), m.group(2))
                     for m in VERSE_ID.finditer("\n".join(blk))]
            exp = expected_verses or expected_ids_from_frontmatter(fm)
            if not found:
                errors.append("section `%s`: no `^C-V` block IDs found — verse "
                              "text must be inlined with its block ID" % bsec)
            elif exp and found != exp:
                errors.append("section `%s`: block IDs %s != expected %s"
                              % (bsec, found, exp))
            elif not exp:
                warnings.append("no expected verse range given and none derivable "
                                "from frontmatter; block IDs found: %s" % found)
            if found:
                nums = [int(f.split("-")[1]) for f in found]
                if nums != list(range(nums[0], nums[0] + len(nums))):
                    errors.append("section `%s`: block IDs are not contiguous: %s"
                                  % (bsec, found))

    # ---- forbidden elements
    exempt = set(spec.get("forbidden_exempt_sections", []))
    scan = "\n".join("\n".join(c) for s, _h, c in sections
                     if not (s and s["id"] in exempt))
    for rule in spec.get("forbidden", []):
        m = re.search(rule["regex"], scan)
        if m:
            snippet = scan[max(0, m.start() - 30):m.end() + 30].replace("\n", " ")
            errors.append("forbidden element — %s: ...%s..." % (rule["name"], snippet))

    # ---- category tag
    ct = spec.get("category_tag")
    if ct:
        blk = next((c for s, _h, c in sections if s and s["id"] == ct["section"]), None)
        if blk is not None:
            text = "\n".join(blk)
            m = re.search(ct["regex"], text)
            if not m:
                bare = re.search(r"[\[(]([^\])]+)[\])]", text)
                hint = (" — found %r, which is the wrong wrapper" % bare.group(0)
                        if bare else "")
                errors.append("section `%s`: no category tag matching %s%s"
                              % (ct["section"], ct["regex"], hint))
            elif ct.get("allowed") and m.group(1).strip() not in ct["allowed"]:
                errors.append("section `%s`: category %r is not in the plan's "
                              "allowed list" % (ct["section"], m.group(1).strip()))
            else:
                notes.append("category tag: %s" % m.group(1).strip())

    ok = not errors
    print("[%s] %s" % ("PASS" if ok else "FAIL", path))
    for e in errors:
        print("  ERROR:   %s" % e)
    for w in warnings:
        print("  warning: %s" % w)
    for n in notes:
        print("  note:    %s" % n)
    return ok


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--spec", required=True, help="the plan's section spec JSON")
    p.add_argument("--verses", help="expected block IDs, e.g. '2-35,2-36'")
    p.add_argument("--frontmatter", default="day,chapter,verses,status",
                   help="comma-separated frontmatter keys that must be present")
    p.add_argument("files", nargs="+")
    args = p.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
    expected = [v.strip() for v in args.verses.split(",")] if args.verses else None
    fm_keys = [k.strip() for k in args.frontmatter.split(",") if k.strip()]

    ok = True
    for f in args.files:
        ok = check(f, spec, expected, fm_keys) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
