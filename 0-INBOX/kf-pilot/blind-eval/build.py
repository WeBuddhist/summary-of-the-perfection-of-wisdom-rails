#!/usr/bin/env python3
"""Blind MQM comparison: governed academic vs zero-shot vs human, on a fixed sample of segments.

  python3 build.py [--n 40] [--per-agent 20] [--seed 7]

Picks n text segments spread evenly over the text (one at random from each of n equal slices), the same ids in
every language, each with a T229 line. Per language the candidates are:
  en: governed academic, DharmaMitra zero-shot, Gemini zero-shot
  zh: governed academic, Gemini zero-shot, T229 佛母寶德藏般若波羅蜜經 (human, classical Chinese verse)
  hi: governed academic, Gemini zero-shot
Each segment's candidates are shuffled to letters A, B, C (seeded). Annotators see the Tibetan, the Sanskrit and the
commentaries — no glossary and no English reference, which would favour the governed version. Writes
sample-<lang>-NN.json (what annotators see), key.json (letter -> system, never shown), prompts/<lang>-NN.md.
"""
import argparse
import importlib.util
import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
KF = HERE.parent
sys.path.insert(0, str(KF / "context"))
from segment_context import build_context  # noqa: E402

_spec = importlib.util.spec_from_file_location("tr", KF / "translate" / "gm_variant_translate.py")
tr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tr)

LANG_NAMES = {"en": "English", "zh": "Chinese", "hi": "Hindi"}


def t229_lines():
    """{Tibetan segment id: T229 classical Chinese} via the zh file's transclusions (one zh block may cover two verses)."""
    from segment_context import blocks  # noqa: E402
    text, above = blocks("1-SOURCES/Translations/zh-ratnagunasancayagatha.md", with_trans=True)
    out = {}
    for zid, t in text.items():
        for rid in above.get(zid) or []:
            out[rid] = (out.get(rid, "") + " " + t).strip()
    return out


def candidates(lang, segs):
    gov = {i: r["translation"] for i, r in tr.latest(tr.work_file(lang, "academic")).items()}
    gm = tr.zero_shot_lines(lang)
    if lang == "en":
        return {"governed": gov, "zeroshot-dharmamitra": {s["id"]: s["dm"] for s in segs},
                "zeroshot-gemini": {s["id"]: s["gm"] for s in segs}}
    if lang == "zh":
        return {"governed": gov, "zeroshot-gemini": gm, "human-t229": t229_lines()}
    return {"governed": gov, "zeroshot-gemini": gm}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--per-agent", type=int, default=20)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--max-comm", type=int, default=1500)
    a = p.parse_args()
    segs = json.loads((tr.TERM_RUN / "segments.json").read_text(encoding="utf-8"))
    segmap = {s["id"]: s for s in segs}
    cands = {lang: candidates(lang, segs) for lang in ("en", "zh", "hi")}
    eligible = [s["id"] for s in segs if not s["heading"]
                and all((t.get(s["id"]) or "").strip() for c in cands.values() for t in c.values())]
    rng = random.Random(a.seed)
    k = len(eligible) / a.n
    ids = [eligible[int(j * k) + rng.randrange(max(1, int(k)))] for j in range(a.n)]
    ctx = build_context(tr.ROOT)
    key = {}
    for lang, systems in cands.items():
        items = []
        for i in ids:
            c = ctx.get(i, {})
            comms = {cid: [q["text"] if len(q["text"]) <= a.max_comm else q["text"][:a.max_comm] + " …" for q in ps]
                     for cid, ps in (c.get("commentaries") or {}).items()}
            order = list(systems)
            random.Random(f"{a.seed}:{lang}:{i}").shuffle(order)
            letters = dict(zip("ABC", order))
            key[f"{lang}:{i}"] = letters
            pos = [x["id"] for x in segs].index(i)
            items.append({"id": i, "tibetan": segmap[i]["bo"],
                          "tibetan_previous_segment": segs[pos - 1]["bo"] if pos else None,
                          "tibetan_next_segment": segs[pos + 1]["bo"] if pos + 1 < len(segs) else None,
                          "sanskrit": " ".join(x["text"] for x in c.get("sa", [])) or None,
                          "commentaries": comms,
                          "candidates": {L: systems[s][i] for L, s in letters.items()}})
        for b in range(0, len(items), a.per_agent):
            n = b // a.per_agent + 1
            path = HERE / f"sample-{lang}-{n:02d}.json"
            path.write_text(json.dumps(items[b:b + a.per_agent], ensure_ascii=False, indent=1), encoding="utf-8")
            rubric = (HERE / "rubric-mqm.md").read_text(encoding="utf-8").format(
                lang_name=LANG_NAMES[lang], n_cand=len(systems), letters=", ".join("ABC"[:len(systems)]))
            prompt = (HERE / "prompt-mqm.md").read_text(encoding="utf-8").format(
                rubric=rubric.strip(), input_path=path, out_path=HERE / "claude" / f"{lang}-{n:02d}.json",
                check_script=HERE / "check.py")
            (HERE / "prompts").mkdir(exist_ok=True)
            (HERE / "prompts" / f"{lang}-{n:02d}.md").write_text(prompt, encoding="utf-8")
    (HERE / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "claude").mkdir(exist_ok=True)
    (HERE / "gemini").mkdir(exist_ok=True)
    print(f"eligible={len(eligible)} sample={len(ids)}: {ids}")


if __name__ == "__main__":
    main()
