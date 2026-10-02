Read `4-SYSTEM/Skills/machine-translate/SKILL.md` in full, then execute it on the file(s) or input the user specifies.

Skill purpose: Produce a zero-shot machine-baseline translation of a block-ID'd source text by calling a translation API on small batches of adjacent blocks, threading the document's own preceding translations back in as context, and writing a translation file whose block IDs match the source exactly.
