"""Harvest every Open Food Facts product sold in India and count additive frequency.

Writes:
  sources/raw/off_india_products.json  - raw hits (code, additives_tags, ingredients_tags, brands)
  data/india_additive_frequency.csv    - additive tag -> number of India products containing it
"""
import json, time, urllib.parse, urllib.request, collections, pathlib, sys

BASE = "https://search.openfoodfacts.org/search"
UA = "IndiaAdditiveAtlas/0.1 (research; krishna.met@nitjsr.ac.in)"
PAGE_SIZE = 500
FIELDS = "code,product_name,brands,additives_tags,ingredients_tags"

root = pathlib.Path(__file__).resolve().parent.parent


def fetch(page):
    qs = urllib.parse.urlencode({
        "q": 'countries_tags:"en:india"',
        "page_size": PAGE_SIZE,
        "page": page,
        "fields": FIELDS,
    })
    req = urllib.request.Request(f"{BASE}?{qs}", headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:
            print(f"  page {page} attempt {attempt + 1} failed: {e}", flush=True)
            time.sleep(5 * (attempt + 1))
    return None


hits, page = [], 1
while True:
    d = fetch(page)
    if d is None:
        print(f"giving up at page {page}", flush=True)
        break
    got = d.get("hits") or []
    hits.extend(got)
    total = d.get("count", 0)
    print(f"page {page}: +{len(got)} (running {len(hits)}/{total})", flush=True)
    if not got or len(hits) >= total:
        break
    page += 1
    time.sleep(1)

(root / "sources/raw/off_india_products.json").write_text(
    json.dumps(hits, ensure_ascii=False), encoding="utf-8")

counts = collections.Counter()
with_additives = 0
for p in hits:
    tags = p.get("additives_tags") or []
    if tags:
        with_additives += 1
    counts.update(set(tags))

out = root / "data/india_additive_frequency.csv"
with out.open("w", encoding="utf-8", newline="") as f:
    f.write("additive_tag,e_number,product_count,pct_of_products_with_additives\n")
    for tag, n in counts.most_common():
        e = tag.split(":")[-1].upper()
        pct = (100.0 * n / with_additives) if with_additives else 0
        f.write(f"{tag},{e},{n},{pct:.2f}\n")

print(f"\nproducts harvested      : {len(hits)}")
print(f"products with additives : {with_additives}")
print(f"distinct additives      : {len(counts)}")
print(f"wrote {out}")
