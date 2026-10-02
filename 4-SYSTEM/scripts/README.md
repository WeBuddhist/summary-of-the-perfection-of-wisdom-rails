# 4-SYSTEM/scripts

Standalone scripts that are not bundled inside a single skill — either because several skills use them, or because they are vault-maintenance tools rather than steps in a workflow.

A script that belongs to exactly one skill lives in that skill's own `scripts/` folder instead, so the skill stays self-contained and can be installed anywhere.

| Script | What it does |
| ------ | ------------ |
| `install-skills.py` | Installs skills from the shared skill library into `4-SYSTEM/Skills/`, resolving the library's logical location names to this vault's paths and writing the `.claude/commands/` stubs. See [`../How-to guides/Sync with rails-template.md`](../How-to%20guides/Sync%20with%20rails-template.md). |

## Conventions

**Vendored code records its upstream.** If you copy a tool in from another repository rather than writing it here, put an `UPSTREAM.md` beside it recording the source repository, the path, the commit it was pinned at, and the date. Make the first commit byte-identical to upstream so that every later commit reads as your delta — then a re-sync is a diff rather than an archaeology exercise. Say in the same file *why* it was forked, and whether the changes should be offered back upstream.

**Nothing here writes to `1-SOURCES/` in place.** Scripts may create whole files from reviewed inbox material; they may not rewrite a source file's content.

**Credentials never live in the repository.** A script that needs one reads it from the environment or from a `.env` file that is git-ignored, and ships a `.env.example` containing **placeholders only** — never a real address, password or token, even an expired one.

**Generated output goes to `0-INBOX/`**, not into this folder.
