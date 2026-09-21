"""Join India additive frequency with the Open Food Facts taxonomy to produce the
prioritised working list of additives for the Atlas."""
import json, re, collections, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
hits = json.loads((root / "sources/raw/off_india_products.json").read_text(encoding="utf-8"))
tax = json.loads((root / "sources/raw/off_additives.json").read_text(encoding="utf-8"))

with_ing = [p for p in hits if p.get("ingredients_tags")]
counts = collections.Counter()
for p in with_ing:
    counts.update(set(p["ingredients_tags"]))

def en(entry, field):
    v = entry.get(field)
    return v.get("en") if isinstance(v, dict) else None

def name_en(tag):
    e = tax.get(tag) or tax.get(tag.replace("en:", "en:"))
    if not e:
        return None, None, None
    nm = (e.get("name") or {}).get("en")
    if nm:
        nm = re.sub(r"^E\d+[a-z]*\s*-\s*", "", nm)
    return nm, en(e, "additives_classes"), en(e, "efsa_evaluation_adi")

rows = []
for tag, n in counts.items():
    if not re.match(r"^en:e\d{3}", tag):
        continue
    nm, cls, adi = name_en(tag)
    ins = tag.split(":")[-1].upper().replace("E", "")
    rows.append({
        "ins": ins,
        "tag": tag,
        "name": nm or "",
        "classes": (cls or "").replace("en:", ""),
        "efsa_adi": adi or "",
        "india_products": n,
        "pct": round(100.0 * n / len(with_ing), 2),
    })

rows.sort(key=lambda r: -r["india_products"])
for i, r in enumerate(rows, 1):
    r["rank"] = i

out_csv = root / "data/india_top_additives.csv"
cols = ["rank", "ins", "name", "classes", "efsa_adi", "india_products", "pct", "tag"]
with out_csv.open("w", encoding="utf-8", newline="") as f:
    f.write(",".join(cols) + "\n")
    for r in rows:
        f.write(",".join('"' + str(r[c]).replace('"', "'") + '"' for c in cols) + "\n")

(root / "data/india_top_additives.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

# vague-label evidence: ingredients the label is allowed to keep non-specific
vague = ["en:flavouring", "en:nature-identical-flavouring", "en:natural-flavouring",
         "en:artificial-flavouring", "en:spice", "en:condiment", "en:colour",
         "en:vegetable-oil", "en:edible-vegetable-oil", "en:emulsifier",
         "en:stabiliser", "en:acidity-regulator", "en:anticaking-agent",
         "en:raising-agent", "en:preservative", "en:antioxidant"]
vlines = [(t, counts.get(t, 0), round(100.0 * counts.get(t, 0) / len(with_ing), 2))
          for t in vague if counts.get(t)]
vlines.sort(key=lambda x: -x[1])
with (root / "data/india_vague_label_terms.csv").open("w", encoding="utf-8", newline="") as f:
    f.write("term,product_count,pct_of_products\n")
    for t, n, p in vlines:
        f.write(f"{t},{n},{p}\n")

print(f"products analysed        : {len(with_ing)}")
print(f"distinct E-coded additives: {len(rows)}")
print(f"wrote {out_csv.name}, india_top_additives.json, india_vague_label_terms.csv\n")
print(f"{'#':>3} {'INS':<6} {'name':<42} {'class':<26} {'n':>4} {'%':>6}")
for r in rows[:50]:
    print(f"{r['rank']:>3} {r['ins']:<6} {r['name'][:42]:<42} {r['classes'][:26]:<26} {r['india_products']:>4} {r['pct']:>5}%")
