You are fact-checking an English translation of the Tibetan Ratnaguṇasaṃcayagāthā (the Verse Summary of the Perfection of Wisdom, a sūtra in verse spoken by the Buddha), segment by segment. Another model translated it; your job is to catch where the English does not say what the Tibetan says. Work only from the input file named below; do not read any other file and do not use web search.

Input: /Users/tashitsering/Desktop/work/Obsidian/KF-project/summary-of-the-perfection-of-wisdom-rails/0-INBOX/kf-pilot/factcheck/academic-a1/batches/batch-04.json
A JSON list of segments. Each has `id`, `tibetan` (the source), `sanskrit` (the aligned Sanskrit, may be null), `commentaries` (passages from three Tibetan commentaries aligned to this segment — Ju Mipham `bo-mipham`, Karmapa Rangjung Dorjé `bo-rangjung`, Khenrab Jamyang `bo-khenrab`; a passage may cover several segments), `locked_terms` (the glossary rendering the translator was required to use), and `translation` (the English to check).

For each segment, compare the translation with the Tibetan first, using the Sanskrit and the commentaries to settle what the Tibetan means. Report an issue only when you can point to the evidence. Issue types:
- `mistranslation`: the English says something the Tibetan does not (wrong referent, wrong logic, negation, number, person, tense that changes meaning).
- `omission` / `addition`: content missing from, or added to, the Tibetan.
- `terminology`: a locked term not rendered with its locked rendering, or a term rendered so that it means something else.
- `doctrinal`: a reading the commentaries clearly contradict.
- `ambiguity`: the English allows a reading the Tibetan excludes.
- `fluency`: English that is ungrammatical or hard to parse (minor unless it hides the meaning).
- `form`: a verse whose line count differs from the Tibetan, or a question and its answer merged so that it changes who asserts what (minor unless it changes the meaning).

Severity: `critical` = meaning reversed or core teaching misstated; `major` = meaning changed or content missing/added; `minor` = imprecise, awkward, or a better rendering exists but the meaning is intact. Do not report matters of taste. The translation is a study translation (academic register): it should be faithful and precise, not paraphrased.

For each issue give: `type`, `severity`, `span` (the English words at fault, or "—" for an omission), `evidence` (what the Tibetan / Sanskrit / commentary shows — quote the Tibetan words and name the commentary passage id if you use one), `fix` (a corrected English wording for that span).
`verdict` is "fail" when the segment has at least one critical or major issue, otherwise "pass".

Write UTF-8 JSON to: /Users/tashitsering/Desktop/work/Obsidian/KF-project/summary-of-the-perfection-of-wisdom-rails/0-INBOX/kf-pilot/factcheck/academic-a1/agents/batch-04.json
{"batch": "batch-04", "segments": [{"id": "7-28", "verdict": "pass", "issues": []}]}

Every input segment must appear, in order. Before finishing, run this check, fix every problem, and repeat until it prints OK:

    python3 /Users/tashitsering/Desktop/work/Obsidian/KF-project/summary-of-the-perfection-of-wisdom-rails/0-INBOX/kf-pilot/factcheck/check.py /Users/tashitsering/Desktop/work/Obsidian/KF-project/summary-of-the-perfection-of-wisdom-rails/0-INBOX/kf-pilot/factcheck/academic-a1/batches/batch-04.json /Users/tashitsering/Desktop/work/Obsidian/KF-project/summary-of-the-perfection-of-wisdom-rails/0-INBOX/kf-pilot/factcheck/academic-a1/agents/batch-04.json

Final reply: one line — segments, pass, fail, and issue counts by severity.
