"""Is the EU opinion on each card still the current one?

Why this exists: the free taxonomy we started from carries EFSA's 2016 opinion on
titanium dioxide (E171). EFSA replaced it in 2021 with a finding that E171 can no
longer be considered safe, and the EU banned it in food in 2022. A card built on
the old opinion would quietly tell someone the wrong thing.

Matching is by E NUMBER, not by name. A name match previously paired potassium
sorbate with a paper on potassium PHOSPHONATES, and acetic acid with
DIFLUOROacetic acid.

Output: data/eu_opinion_freshness.json
"""
import json, re, time, pathlib, urllib.request, urllib.parse

root = pathlib.Path(__file__).resolve().parent.parent
cards = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(root.glob("cards/ins-*.json"))]
eu = json.loads((root / "data/eu_efsa_facts.json").read_text(encoding="utf-8"))

EFSA_ISSN = "1831-4732"
UA = {"User-Agent": "IndiaAdditiveAtlas/0.1 (mailto:krishna.met@nitjsr.ac.in)"}
EXCLUDE = re.compile(
    r"feed additive|novel food|pesticide|smoke flavour|plain language summary|"
    r"food contact|nutrient source|health claim|maximum residue level|MRLs?|"
    r"technological additive|silage|for cats|for dogs|animal species", re.I)
RELEVANT = re.compile(
    r"re-?evaluation|safety assessment|scientific opinion|follow-?up|"
    r"exposure assessment|statement|safety of", re.I)


def pub_date(item):
    for k in ("published", "published-print", "published-online", "issued", "created"):
        parts = (item.get(k) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            y = parts[0][0]
            m = parts[0][1] if len(parts[0]) > 1 else 1
            return f"{y}-{m:02d}"
    return None


def search(name, ins):
    q = urllib.parse.urlencode({"query.title": name, "rows": 20})
    url = f"https://api.crossref.org/journals/{EFSA_ISSN}/works?{q}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            items = json.load(r)["message"]["items"]
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

    num = re.match(r"^(\d{3,4})", ins)
    if not num:
        return [], None
    enum = re.compile(r"E\s*" + num.group(1) + r"\s*[a-z]{0,3}(?![\d])", re.I)

    hits = []
    for it in items:
        title = (it.get("title") or [""])[0]
        if not title or EXCLUDE.search(title) or not RELEVANT.search(title):
            continue
        if not enum.search(title):
            continue
        d = pub_date(it)
        if not d:
            continue
        hits.append({"doi": it["DOI"], "title": re.sub(r"\s+", " ", title),
                     "date": d, "url": "https://doi.org/" + it["DOI"]})
    hits.sort(key=lambda h: h["date"], reverse=True)
    return hits, None


report, stale, newfound, nothing, errors = [], [], [], [], []
for c in cards:
    ins, name = c["ins"], c["name"]
    have = eu.get(ins.upper(), {})
    have_date = (have.get("efsa_opinion_date") or "").replace("/", "-")[:7]
    have_title = have.get("efsa_opinion_title") or ""

    hits, err = search(name, ins)
    time.sleep(0.5)
    if err:
        errors.append((ins, err))
        continue

    newest = hits[0] if hits else None
    if newest and have_date:
        verdict = "superseded" if newest["date"] > have_date else "current"
    elif newest:
        verdict = "found_opinion_we_did_not_have"
    else:
        verdict = "no_efsa_opinion_found"
        nothing.append(ins)

    row = {"ins": ins, "name": name, "verdict": verdict,
           "we_have": {"date": have_date, "title": have_title[:120]},
           "newest_found": newest, "also_found": hits[1:4]}
    report.append(row)
    if verdict == "superseded":
        stale.append(row)
    elif verdict == "found_opinion_we_did_not_have":
        newfound.append(row)

(root / "data/eu_opinion_freshness.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"checked                 : {len(report)}")
print(f"OUT OF DATE             : {len(stale)}")
print(f"opinion we were missing : {len(newfound)}")
print(f"no EFSA opinion found   : {len(nothing)}")
print(f"errors                  : {len(errors)}")

if stale:
    print("\n=== OUT OF DATE ===")
    for r in stale:
        print(f"  INS {r['ins']:<6} {r['name'][:28]}")
        print(f"      we have: {r['we_have']['date']}  {r['we_have']['title'][:70]}")
        print(f"      NEWER  : {r['newest_found']['date']}  {r['newest_found']['title'][:70]}")
        print(f"               {r['newest_found']['url']}")
if newfound:
    print("\n=== EU OPINION WE DID NOT HAVE ===")
    for r in newfound:
        print(f"  INS {r['ins']:<6} {r['name'][:22]:<22} {r['newest_found']['date']}  {r['newest_found']['title'][:58]}")
