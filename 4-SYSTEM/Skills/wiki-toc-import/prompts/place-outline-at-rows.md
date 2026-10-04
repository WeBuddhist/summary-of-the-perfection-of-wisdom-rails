# Placement pass — put a Wikipedia outline on a row-segmented text

You are placing a table of contents onto a text cut into numbered alignment rows. Work read-only except for the one output file named below.

## You are given

- **The text**: `<placed_on_text>` — one numbered item per row (`N. text`; a row continues on following lines until the next `N.`; text before `1.` is row 0; an empty item is a row with no text on this side). Rows are long single lines: read with `sed -n` / `grep -n` in pieces.
- **The paired text**, when the text is a commentary: `<target_side>` — row N is the root passage that commentary row N comments on (empty = no root passage paired). Strong evidence, not the only evidence.
- **The outline**: `<draft outline>` (nodes, paths, labels) and `<section.wiki>` (the Wikipedia section, whose prose says what each node covers).

## Task

For every node, give the row **before which its heading stands**. Rows are indivisible; headings go only between rows. A parent and its first child may share a row.

1. Decide from the Wikipedia prose what each node covers, then find where that content begins in the text. For a commentary, read the commentary row itself: a row with no paired root text that introduces the next passage belongs to the section it introduces.
2. Front matter that the outline does not cover (titles, homage, a translator's or commentator's preamble) gets no heading — say which rows those are. Do not stretch node 1 over it unless the Wikipedia prose clearly includes it.
3. A row that mixes two sections: keep it where most of its content belongs, mark it MID and explain.
4. Never re-word a label. If a draft candidate is not an outline node (a stray bold phrase), say so and leave it out; if nesting is wrong, say what it should be.
5. Do not open any existing TOC of the same text in `1-SOURCES/` or `2-RAILS/` — it is a different outline and would bias you.

## Output — `<output path>`

1. TSV: `path | label | start_row | START/MID | first ~15 syllables of that row verbatim | paired root row start (or EMPTY) | one-line justification`.
2. The rows before node 1 and what they contain.
3. Judgement calls and doubts.

Final reply: the TSV and the doubts, short.
