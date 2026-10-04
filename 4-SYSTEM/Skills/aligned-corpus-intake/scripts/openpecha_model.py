#!/usr/bin/env python3
"""Reader for a verbatim OpenPecha backend (API v2) download.

Expected layout (one folder per text, exactly as the API returned it):

    <root>/texts/<text_id>/text.json
    <root>/texts/<text_id>/instances/<instance_id>.json      content + annotation list
    <root>/texts/<text_id>/annotations/<annotation_id>.json  segmentation, durchen, bibliography, …
    <root>/texts/<text_id>/alignments/<annotation_id>.json   derived text only
    <root>/tree.json                                          parent/child pairs

`load(root, text_id)` returns a JSON-able model:

    {"text_id", "meta": <text.json>, "instance_id", "instance_meta",
     "content": str,
     "segments":  [{"id", "start", "end"}],          # the segmentation annotation
     "notes":     [{"id", "start", "end", "note"}],  # durchen (variant readings)
     "bibliography": [{"id", "start", "end", "type"}],
     "alignment": {"parent_text", "parent_instance",
                   "pairs": [{"id", "start", "end",            # span in THIS content
                              "target_id", "target_start", "target_end"}]}  # span in parent
                  | None}

Spans are character offsets, end-exclusive, exactly as upstream. Nothing is
dropped: annotations of a type this reader does not know are returned under
"other_annotations". A text with several instances is read from the one
tree.json pairs it by (else its only critical instance); `instance_id`
overrides.
"""
import json
import pathlib
import sys


def _j(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def _spans(data, extra=()):
    out = []
    for d in data:
        s = {"id": d["id"], "start": d["span"]["start"], "end": d["span"]["end"]}
        for k in extra:
            if k in d:
                s[k] = d[k]
        out.append(s)
    return sorted(out, key=lambda x: (x["start"], x["end"]))


def _pick_instance(root, text_id, inst_files, instance_id=None):
    """Choose the instance to read when a text has several (e.g. a critical
    edition plus a placeholder diplomatic one): the one asked for, else the
    one tree.json pairs this text by, else the only 'critical' one."""
    by_id = {f.stem: f for f in inst_files}
    if instance_id:
        return by_id[instance_id]
    if len(inst_files) == 1:
        return inst_files[0]
    tree = _j(root / "tree.json") if (root / "tree.json").exists() else {"pairs": []}
    used = {p["parent_instance"] for p in tree.get("pairs", []) if p.get("parent_text") == text_id}
    used |= {p["derived_instance"] for p in tree.get("pairs", []) if p.get("derived_text") == text_id}
    used &= set(by_id)
    if len(used) == 1:
        return by_id[used.pop()]
    critical = [f for f in inst_files if _j(f)["metadata"].get("type") == "critical"]
    if len(critical) == 1:
        return critical[0]
    raise ValueError(f"{text_id}: {len(inst_files)} instances and no single paired or critical one; pass instance_id")


def load(root, text_id, instance_id=None):
    root = pathlib.Path(root)
    tdir = root / "texts" / text_id
    meta = _j(tdir / "text.json")
    inst_files = sorted((tdir / "instances").glob("*.json"))
    if not inst_files:
        raise ValueError(f"{text_id}: no instance")
    inst = _j(_pick_instance(root, text_id, inst_files, instance_id))
    model = {
        "text_id": text_id, "meta": meta,
        "instance_id": inst["metadata"]["id"], "instance_meta": inst["metadata"],
        "content": inst["content"],
        "segments": [], "notes": [], "bibliography": [], "search_segments": [],
        "other_annotations": {}, "alignment": None,
    }
    for a in inst.get("annotations") or []:
        f = tdir / "annotations" / f"{a['annotation_id']}.json"
        if not f.exists():
            continue
        ann = _j(f)
        typ = ann.get("type")
        if typ == "segmentation":
            model["segments"] = _spans(ann["data"])
        elif typ == "durchen":
            model["notes"] = _spans(ann["data"], ("note",))
        elif typ == "bibliography":
            model["bibliography"] = _spans(ann["data"], ("type",))
        elif typ == "search_segmentation":
            model["search_segments"] = _spans(ann["data"])
        else:
            model["other_annotations"][a["annotation_id"]] = ann
    tree = _j(root / "tree.json") if (root / "tree.json").exists() else {"pairs": []}
    for pair in tree.get("pairs", []):
        if pair["derived_text"] != text_id or not pair.get("alignment_file"):
            continue
        aln = _j(root / pair["alignment_file"])["data"]
        targets = {t["id"]: t["span"] for t in aln["target_annotation"]}
        pairs = []
        for a in aln["alignment_annotation"]:
            for tid in a["aligned_segments"]:
                t = targets[tid]
                pairs.append({"id": a["id"], "start": a["span"]["start"], "end": a["span"]["end"],
                              "target_id": tid, "target_start": t["start"], "target_end": t["end"]})
        model["alignment"] = {"parent_text": pair["parent_text"],
                              "parent_instance": pair["parent_instance"],
                              "annotation_id": pair["alignment_annotation"],
                              "pairs": sorted(pairs, key=lambda x: (x["start"], x["end"]))}
    return model


if __name__ == "__main__":
    m = load(sys.argv[1], sys.argv[2])
    if "--json" in sys.argv:
        json.dump(m, sys.stdout, ensure_ascii=False, indent=1)
    else:
        a = m["alignment"]
        print(f"{m['text_id']} lang={m['meta'].get('language')} chars={len(m['content'])} "
              f"segments={len(m['segments'])} notes={len(m['notes'])} "
              f"alignment={len(a['pairs']) if a else 0} -> {a['parent_text'] if a else '-'}")
