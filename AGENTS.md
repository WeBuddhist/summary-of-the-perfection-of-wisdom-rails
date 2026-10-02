# AGENTS.md — instructions for AI agents in this repository

1. **Read [`4-SYSTEM/CLAUDE.md`](4-SYSTEM/CLAUDE.md) in full before doing anything.** It holds the operational rules, the folder write-permissions, the citation chain, and the skill-lookup step for this vault.

2. **Check for a skill before starting any task.** Open [`4-SYSTEM/Skills/SKILLS-CATALOG.md`](4-SYSTEM/Skills/SKILLS-CATALOG.md), find the skill that matches, and follow its `SKILL.md` exactly. A task done without its skill must be redone.

3. 🔒 **Protected files — confirm before touching.** Do not edit, move, rename or delete any file marked `PROTECTED — SOURCE OF TRUTH` (a banner at the top of the file, and `protected: true` in its frontmatter) without explicit human confirmation. State the file and the exact change, and wait for approval. Regenerating such a file counts as editing it. The full policy is in `4-SYSTEM/CLAUDE.md`.

4. **Never write to `1-SOURCES/`** except the permitted additions (block IDs, frontmatter, navigation links, `[Ed: …]` factual notes) through a skill, and never edit an existing source file in place beyond those. **Never change a rule in `4-SYSTEM/`** — skills and scripts are the one exception.

5. **Cite everything.** Every claim in `2-RAILS/` cites a block in `1-SOURCES/`; every claim in `3-TRANSFORMATIONS/` cites a package in `2-RAILS/`. If a claim cannot be cited, it is not made. Prefer the vault's own `Local-Wiki/` and `Bilingual-Glossaries/` over general knowledge or a web search.

6. **Never mark your own output `status: complete`.** Domain specialists do that.

This file exists because some AI tools read `AGENTS.md` rather than `CLAUDE.md`. Both point to the same rules.
