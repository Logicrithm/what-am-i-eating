"""Build the lookup the website uses to read a real ingredient list.

Indian labels write additives in several ways on the same packet:
    "Preservative (INS 211)"      "INS211"      "E 211"
    "Acidity Regulator (330)"     "Sodium Benzoate"    "INS 322(i)"

So this collects, for every additive we know of:
  - its INS number and the variants of it
  - its English names and synonyms
  - whether we actually have a card for it yet

That last flag matters. We know of 306 additives from the Indian product data
but have written cards for 50. When someone pastes a label we must say
"recognised, no card yet" rather than pretending we did not see it.

It also collects the vague label terms - the words a label is allowed to use
INSTEAD of naming an ingredient.

Output: data/recognition.json
"""
import json, re, csv, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
top = json.loads((root / "data/india_top_additives.json").read_text(encoding="utf-8"))
tax = json.loads((root / "sources/raw/off_additives.json").read_text(encoding="utf-8"))
have_cards = {p.stem.replace("ins-", "").upper() for p in root.glob("cards/ins-*.json")}


def clean_name(s):
    s = re.sub(r"^E\s?\d+[a-z]*\s*[-–]\s*", "", s or "")
    return re.sub(r"\s+", " ", s).strip()


# English names and synonyms out of the taxonomy
names_by_ins = {}
for tag, e in tax.items():
    m = re.match(r"^en:e(\d{3,4}[a-z]*)$", tag)
    if not m:
        continue
    ins = m.group(1).upper()
    got = set()
    v = (e.get("name") or {}).get("en")
    if v:
        for part in str(v).split(","):
            c = clean_name(part)
            if c and len(c) > 2:
                got.add(c)
    d = (e.get("description") or {}).get("en", "")
    m2 = re.match(r"^([A-Z][A-Z\s\-,]{3,40})\s+is\b", d or "")
    if m2:
        got.add(clean_name(m2.group(1).title()))
    if got:
        names_by_ins[ins] = sorted(got)

entries = []
for t in top:
    ins = t["ins"].upper()
    names = set(names_by_ins.get(ins, []))
    if t.get("name"):
        names.add(clean_name(t["name"]))
    base = re.match(r"^(\d{3,4})", ins)
    entries.append({
        "ins": ins,
        "base": base.group(1) if base else ins,
        "names": sorted(n for n in names if n),
        "class": t.get("classes", ""),
        "products": t.get("india_products", 0),
        "has_card": ins in have_cards,
    })

# The words a label may use instead of naming the ingredient.
vague = {}
vp = root / "data/india_vague_label_terms.csv"
if vp.exists():
    for r in csv.DictReader(vp.open(encoding="utf-8")):
        term = r["term"].replace("en:", "").replace("-", " ")
        vague[term] = {
            "term": term,
            "pct_of_products": float(r["pct_of_products"]),
            "product_count": int(r["product_count"]),
        }

out = {
    "additives": entries,
    "vague_terms": sorted(vague.values(), key=lambda v: -v["pct_of_products"]),
    "note": ("An additive listed here with has_card false was recognised from the Indian "
             "product data but has no written card yet."),
}
(root / "data/recognition.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

withname = sum(1 for e in entries if e["names"])
print("additives recognised : %d" % len(entries))
print("  with a written card: %d" % sum(1 for e in entries if e["has_card"]))
print("  with a usable name : %d" % withname)
print("vague label terms    : %d" % len(vague))
print("wrote data/recognition.json")
