# Place a sa-bcad tree at row boundaries — pointer pass

You are given two files:

- **TREE** — a finished ས་བཅད table of contents for one commentary, built by the
  `toc-generate` skill (Phases A–C/D): a nested bullet list, one node per line,
  `* N.N.N title`, indentation = depth.
- **SOURCE** — that commentary exactly as `toc-generate` read it: line 1 is
  `# title`, then one paragraph per **row**, paragraphs separated by blank lines.
  A row is a unit of a human alignment (the commentary's text for one stretch of
  the root text). **Rows are indivisible**: a heading can stand only *between*
  rows — never inside one.

Your one task: for every node of TREE, decide the line number of the row before
which that node's heading must stand.

## How to decide

1. Find the clause in SOURCE that opens the node: normally its ordinal and topic
   (`དང་པོ་ནི།`, `གཉིས་པ་ … ནི།`, `… ལ་གཉིས་ཏེ།`) or the clause that restates the
   node's title near-verbatim. Read the prose; do not match by arithmetic.
2. If that clause **starts** its row (nothing of the previous section's content
   comes before it in the row), the pointer is that row.
3. If the clause **ends** its row (the row's earlier text belongs to the previous
   section, and nothing of the new section but the announcement itself follows in
   that row), the pointer is the **next** row.
4. If the clause is in the **middle** of a row, point to that row when more of the
   row belongs to the new section than to the previous one, otherwise to the next
   row.
5. A parent and its first child normally open on the same sentence and share one
   row. Pointers never decrease as you go down the tree.
6. A depth-1 node that is only the work's own title (the text of line 1): point to
   line 3, the first row.
7. If no clause in SOURCE opens a node, write `?` — never guess a place.

A pointer is the 1-based line number, in SOURCE, of the **first line** of the
row's paragraph (some rows are several lines long — a verse, say). Line numbers
count every line of the file, the `# title` line and blank lines included; check
them with `grep -n` or `awk '{print NR": "$0}'`, never by counting in your head.

## Output

Write one file, to the path you are given:

1. TREE exactly as given, with ` [[N]]` (or ` [[?]]`) appended to every node line.
   Change nothing else: not the numbering, not a title, not the indentation, not
   the heading line `## དཀར་ཆག / Table of Contents`.
2. A line `---`.
3. For every node, in tree order, one tab-separated line:
   `decimal<TAB>N<TAB>START|END->NEXT|MID|?<TAB>the opening clause, copied verbatim from SOURCE (at most 120 characters)`

Read SOURCE with `sed`/`awk` through the shell (its lines are long; a file viewer
may truncate them). Do no other task; reply only with the path you wrote.
