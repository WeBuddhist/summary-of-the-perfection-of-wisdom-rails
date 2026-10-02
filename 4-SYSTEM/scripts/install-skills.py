#!/usr/bin/env python3
"""Install skills from the shared skill library into this vault.

The library keeps one canonical copy of each skill and refers to locations by
logical name (`$COMMENTARIES`, `$WORK`, `$SECTIONS`) so that one copy can serve
every vault. This script resolves those names to this vault's real paths,
copies the skill folder in, and writes the matching slash-command stub.

    python3 4-SYSTEM/scripts/install-skills.py --from ../Webuddhist-Skills
    python3 4-SYSTEM/scripts/install-skills.py --from ../Webuddhist-Skills --only verse-context,toc-generate
    python3 4-SYSTEM/scripts/install-skills.py --from ../Webuddhist-Skills --dry-run

It is idempotent: re-run it whenever the library changes. It does NOT touch
`SKILLS-CATALOG.md` — catalog entries are written by hand (or by `create-skill`)
because they carry a human description of what the skill is for. Run
`vault-audit` afterwards: its first check is exactly this registration triple.

Skills marked `profile: vault-local` in the library are skipped — they belong to
one text and are not shared.
"""
import argparse, os, re, shutil, sys

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Logical name -> path in this vault. Longest names first, so that
# $SECTIONS_RAW is resolved before $SECTIONS and $GLOSSARIES_RAW before
# $GLOSSARIES. Keep in step with 4-SYSTEM/Guidelines/skill-locations.md.
RESOLVE = [
    ("$SECTIONS_RAW",    "2-RAILS/Sections/Raw"),
    ("$GLOSSARIES_RAW",  "2-RAILS/Bilingual-Glossaries/Raw"),
    ("$SOURCE_TEXTS",    "1-SOURCES/Text"),
    ("$COMMENTARIES",    "1-SOURCES/Commentaries"),
    ("$TRANSLATIONS",    "1-SOURCES/Translations"),
    ("$REFERENCES",      "1-SOURCES/References"),
    ("$TRANSFORMATIONS", "3-TRANSFORMATIONS"),
    ("$LOCAL_WIKI",      "2-RAILS/Local-Wiki"),
    ("$GLOSSARIES",      "2-RAILS/Bilingual-Glossaries"),
    ("$TERMBASES",       "2-RAILS/Termbases"),
    ("$KEYWORDS",        "2-RAILS/Keywords"),
    ("$SECTIONS",        "2-RAILS/Sections"),
    ("$SOURCES",         "1-SOURCES"),
    ("$VERSES",          "2-RAILS/Verses"),
    ("$CLAIMS",          "2-RAILS/Claims"),
    ("$SKILLS",          "4-SYSTEM/Skills"),
    ("$SYSTEM",          "4-SYSTEM"),
    ("$RAILS",           "2-RAILS"),
    ("$WORK",            "0-INBOX/temp"),
    ("$INBOX",           "0-INBOX"),
]

# Library-relative documents -> their vault equivalents.
DOCS = [
    ("rails/PROFILES.md",    "4-SYSTEM/Guidelines/skill-locations.md"),
    ("rails/CONVENTIONS.md", "4-SYSTEM/Guidelines/annotation-conventions.md"),
    ("PROFILES.md",          "4-SYSTEM/Guidelines/skill-locations.md"),
    ("CONVENTIONS.md",       "4-SYSTEM/Guidelines/annotation-conventions.md"),
]

SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", ".venv",
                              ".env", ".env.*", "*.lock", "guard.lock")

# The "> **Locations.**" note tells a library reader to resolve $NAMEs. Once
# they are resolved there is nothing left to resolve, so it is dropped.
LOCATIONS_NOTE = re.compile(r"^> \*\*Locations\.\*\*[\s\S]*?\n\s*\n", re.M)


def resolve_paths(body, skill):
    body = body.replace("$SKILL/", f"4-SYSTEM/Skills/{skill}/")
    body = body.replace("`$SKILL`", f"`4-SYSTEM/Skills/{skill}`")
    for name, path in RESOLVE:
        body = body.replace(name + "/", path + "/")
        body = body.replace("`" + name + "`", "`" + path + "/`")
        body = body.replace(name, path)
    for lib, vault in DOCS:
        body = body.replace(lib, vault)
    body = LOCATIONS_NOTE.sub("", body, count=1)
    return body


def split_frontmatter(raw):
    m = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
    return (m.group(1), raw[m.end():]) if m else (None, raw)


def strip_library_keys(fm):
    """Drop `supersedes:` (library history) and `profile:` (library routing)."""
    out, skipping = [], False
    for line in fm.split("\n"):
        if re.match(r"^supersedes:", line):
            skipping = True
            continue
        if re.match(r"^profile:", line):
            skipping = False
            continue
        if skipping:
            if line.startswith((" ", "\t", "-")):
                continue
            skipping = False
        out.append(line)
    return "\n".join(out).strip("\n")


def first_sentence(fm):
    m = re.search(r"^description:\s*(?:>-?|\|-?)?\s*\n((?:[ \t]+\S.*\n?)+)", fm, re.M)
    if m:
        text = " ".join(l.strip() for l in m.group(1).splitlines())
    else:
        m = re.search(r"^description:\s*(.+)$", fm, re.M)
        text = m.group(1).strip().strip('"\'') if m else ""
    return re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0].strip()


def profile_of(fm):
    m = re.search(r"^profile:\s*(\S+)", fm, re.M)
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True,
                    help="path to the shared skill library checkout")
    ap.add_argument("--only", help="comma-separated skill names (default: all)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rails = os.path.join(a.src, "rails")
    if not os.path.isdir(rails):
        sys.exit(f"no rails/ folder under {a.src}")

    names = ([n.strip() for n in a.only.split(",")] if a.only else
             sorted(d for d in os.listdir(rails)
                    if os.path.isfile(os.path.join(rails, d, "SKILL.md"))))

    installed, skipped = 0, []
    for skill in names:
        src = os.path.join(rails, skill)
        skill_md = os.path.join(src, "SKILL.md")
        if not os.path.isfile(skill_md):
            skipped.append((skill, "no SKILL.md")); continue

        raw = open(skill_md, encoding="utf-8").read()
        fm, body = split_frontmatter(raw)
        if fm is None:
            skipped.append((skill, "no frontmatter — cannot be discovered")); continue
        if profile_of(fm) == "vault-local":
            skipped.append((skill, "vault-local")); continue

        # Frontmatter carries paths too — the description routinely names the
        # skill's input and output locations — so it is resolved as well.
        new_fm = resolve_paths(strip_library_keys(fm), skill)
        new_md = f"---\n{new_fm}\n---\n{resolve_paths(body, skill)}"
        stub = (f"Read `4-SYSTEM/Skills/{skill}/SKILL.md` in full, then execute it on "
                f"the file(s) or input the user specifies.\n\n"
                f"Skill purpose: {first_sentence(fm)}\n")

        if a.dry_run:
            print(f"would install {skill}"); installed += 1; continue

        dst = os.path.join(VAULT, "4-SYSTEM", "Skills", skill)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=SKIP)
        open(os.path.join(dst, "SKILL.md"), "w", encoding="utf-8").write(new_md)

        cmd_dir = os.path.join(VAULT, ".claude", "commands")
        os.makedirs(cmd_dir, exist_ok=True)
        open(os.path.join(cmd_dir, f"{skill}.md"), "w", encoding="utf-8").write(stub)
        print(f"installed {skill}")
        installed += 1

    print(f"\n{installed} skill(s) {'to install' if a.dry_run else 'installed'}")
    for name, why in skipped:
        print(f"  skipped {name}: {why}")
    if not a.dry_run and installed:
        print("\nNext: add a SKILLS-CATALOG.md entry for anything new, then run vault-audit.")


if __name__ == "__main__":
    main()
