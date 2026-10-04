#!/usr/bin/env python3
"""Fetch a whole Wikisource Index (its revision and every Page: page, pinned)
into 0-INBOX/raw-data/wikisource-<id>/pages.json — raw data for a commentary
that exists only on Wikisource.   python3 fetch_wikisource_text.py <id> "<Index:…>" """
import datetime, json, pathlib, sys
sys.path.insert(0, "4-SYSTEM/Skills/wiki-toc-import/scripts")
from fetch_wiki_outline import api, page_title
oid, index = sys.argv[1], page_title(sys.argv[2])
host = "wikisource.org"
q = api(host, action="query", titles=index, prop="revisions", rvprop="ids|timestamp|content", rvslots="main", redirects=1)
pg = q["query"]["pages"][0]
irev = pg["revisions"][0]
ns = api(host, action="query", meta="siteinfo", siprop="namespaces")["query"]["namespaces"]
pns = next(v["id"] for v in ns.values() if v.get("canonical") == "Page")
fname = pg["title"].split(":", 1)[1]
listing = api(host, action="query", list="allpages", apnamespace=pns, apprefix=fname + "/", aplimit=500)
titles = sorted((p["title"] for p in listing["query"]["allpages"]), key=lambda t: int(t.rsplit("/", 1)[1]))
pages = []
for i in range(0, len(titles), 4):
    r = api(host, action="query", titles="|".join(titles[i:i + 4]), prop="revisions", rvprop="ids|content", rvslots="main")
    for p in r["query"]["pages"]:
        if "revisions" in p:
            pages.append({"title": p["title"], "revid": p["revisions"][0]["revid"],
                          "content": p["revisions"][0]["slots"]["main"]["content"]})
pages.sort(key=lambda p: int(p["title"].rsplit("/", 1)[1]))
out = pathlib.Path(f"0-INBOX/raw-data/wikisource-{oid}")
out.mkdir(parents=True, exist_ok=True)
(out / "pages.json").write_text(json.dumps({
    "index_page": pg["title"], "index_revid": irev["revid"], "index_content": irev["slots"]["main"]["content"],
    "retrieved": datetime.date.today().isoformat(), "pages": pages}, ensure_ascii=False, indent=1), encoding="utf-8")
print(pg["title"], irev["revid"], len(pages), "pages ->", out / "pages.json")
