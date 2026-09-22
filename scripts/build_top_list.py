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
    # "en:e322-from-soy" is a sourcing note, not a separate additive. A few
    # sub-form tags also carry no usable name. Neither belongs in a ranked list
    # of substances - they were appearing as entries called "?".
    if re.search(r"-from-|-de-|_", tag):
        continue
    nm, cls, adi = name_en(tag)
    if not nm:
        continue
    # strip ONLY the leading E. replace("E","") stripped every one, so the tag
    # en:e472e collapsed to "472" and quietly merged a sub-form into its parent.
    ins = re.sub(r"^E", "", tag.split(":")[-1].upper())
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

# The vague-label table used to be written here too, from a naive count.
# It now belongs to build_vague_terms.py, which knows what the labelling
# rule actually asks for. Two scripts writing one file meant the good
# version kept being overwritten by the bad one.

print(f"products analysed        : {len(with_ing)}")
print(f"distinct E-coded additives: {len(rows)}")
print(f"wrote {out_csv.name}, india_top_additives.json, india_vague_label_terms.csv\n")
print(f"{'#':>3} {'INS':<6} {'name':<42} {'class':<26} {'n':>4} {'%':>6}")
for r in rows[:50]:
    print(f"{r['rank']:>3} {r['ins']:<6} {r['name'][:42]:<42} {r['classes'][:26]:<26} {r['india_products']:>4} {r['pct']:>5}%")
