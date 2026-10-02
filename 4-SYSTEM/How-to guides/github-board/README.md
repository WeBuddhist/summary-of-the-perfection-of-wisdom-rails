# GitHub project board

An optional project-management layer for a vault. The vault itself tracks *state* in frontmatter (`status: draft | partial | complete`); the board tracks *work* — who is doing which stage of which text, and what is blocked.

Use it when more than two or three people are working on the vault at once, or when several texts are in flight. A single-contributor vault does not need it.

| File | What it is |
| ---- | ---------- |
| [`00-board-spec.md`](00-board-spec.md) | The board's columns, the parent-card-per-text model, the sub-issue set for each pipeline stage, the label scheme, and the mapping from sub-issue to vault folder |
| [`02-new-text-template.md`](02-new-text-template.md) | The parent card and sub-issue titles to create when a new text enters the pipeline |
| [`03-setup-script.md`](03-setup-script.md) | A `gh` script that creates the project, the columns and the labels |

One adaptation worth knowing before you start: for a **prose-only text** — no verses, no second-language original — drop the sub-issues that assume a verse-numbered root and make the rails sub-issues per-section rather than per-verse. The board mirrors the pipeline; where the pipeline changes shape, so does it.
