"""How often does an Indian label use a general word instead of naming the thing,
and does the rule actually allow that?

Two corrections are baked in here, both found by checking rather than assuming:

1. Open Food Facts tags are hierarchical. A product saying "palm oil" also carries
   the parent tag "vegetable oil". Counting the parent counted products that DID
   name their oil, and inflated "vegetable oil" from a true ~6.8% to 19.9%.

2. Not every general word is permitted. The Labelling and Display Regulations 2020
   say a SPECIFIC name shall be used, then list the classes where a class title may
   stand in instead. "Spice and condiments" is on that list. Edible vegetable oil is
   NOT - its entry reads "Give name of the specific edible oil such as mustard oil,
   groundnut oil, etc." And functional additive classes must be declared "together
   with the specific name(s) or recognised INS" number.

So a packet saying only "Edible Vegetable Oil", or only "Emulsifier" with no number,
is not giving what the rule asks for. That is a far more useful thing to tell a
reader than "the label does not have to say".

Output: data/india_vague_label_terms.csv
"""
import json, csv, re, pathlib, collections

root = pathlib.Path(__file__).resolve().parent.parent
products = json.loads((root / "sources/raw/off_india_products.json").read_text(encoding="utf-8"))
tax = json.loads((root / "sources/raw/off_ingredients_taxonomy.json").read_text(encoding="utf-8"))
with_ing = [p for p in products if p.get("ingredients_tags")]

parents = {}
for tag, e in tax.items():
    ps = e.get("parents") or []
    if isinstance(ps, dict):
        ps = ps.get("en", [])
    parents[tag] = list(ps)


def ancestors(tag, seen=None):
    seen = seen if seen is not None else set()
    for p in parents.get(tag, []):
        if p not in seen:
            seen.add(p)
            ancestors(p, seen)
    return seen


ANC = {t: ancestors(t) for t in parents}
ENUM = re.compile(r"^en:e\d{3,4}")

# rule: what the Labelling and Display Regulations 2020 require for this class
CLASS_TITLE_OK = "class_title_allowed"        # the general word is permitted
NEEDS_SPECIFIC = "specific_name_required"     # the rule says name the actual thing
NEEDS_NUMBER = "needs_name_or_ins_number"     # additive class: give the name or INS

TERMS = {
    "en:vegetable-oil":  (NEEDS_SPECIFIC, "Give name of the specific edible oil such as mustard oil, groundnut oil, etc."),
    "en:spice":          (CLASS_TITLE_OK, "Class title 'Spice and condiments, herbs or mixed spices/condiments' is permitted."),
    "en:condiment":      (CLASS_TITLE_OK, "Class title 'Spice and condiments, herbs or mixed spices/condiments' is permitted."),
    "en:flavouring":     (CLASS_TITLE_OK, "Flavourings are declared by their class - natural, nature-identical or artificial."),
    "en:natural-flavouring": (CLASS_TITLE_OK, "Declared by class rather than by the individual substance."),
    "en:artificial-flavouring": (CLASS_TITLE_OK, "Declared by class rather than by the individual substance."),
    "en:nature-identical-flavouring": (CLASS_TITLE_OK, "Declared by class rather than by the individual substance."),
    "en:colour":          (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
    "en:emulsifier":      (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
    "en:stabiliser":      (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
    "en:acidity-regulator": (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
    "en:anticaking-agent": (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
    "en:raising-agent":   (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
    "en:preservative":    (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
    "en:antioxidant":     (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
    "en:thickener":       (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
    "en:sweetener":       (NEEDS_NUMBER, "A functional class must be declared together with the specific name or INS number."),
}

rows = []
for term, (rule, rule_text) in TERMS.items():
    generic = specific = 0
    named_as = collections.Counter()
    for p in with_ing:
        tags = set(p["ingredients_tags"])
        if term not in tags:
            continue
        kids = [t for t in tags if t != term and term in ANC.get(t, ())]
        # for an additive class, ANY INS/E number on the label counts as naming it
        if rule == NEEDS_NUMBER and not kids:
            kids = [t for t in tags if ENUM.match(t)]
        if kids:
            specific += 1
            named_as.update(kids)
        else:
            generic += 1
    total = generic + specific
    if not total:
        continue
    rows.append({
        "term": term.replace("en:", "").replace("-", " "),
        "rule": rule,
        "rule_says": rule_text,
        "left_generic": generic,
        "named_specifically": specific,
        "total_mentions": total,
        "pct_of_products_left_generic": round(100.0 * generic / len(with_ing), 2),
        "pct_of_mentions_left_generic": round(100.0 * generic / total, 1),
        "top_specific_names": "; ".join(k.replace("en:", "") for k, _ in named_as.most_common(3)),
    })

rows.sort(key=lambda r: -r["pct_of_products_left_generic"])
out = root / "data/india_vague_label_terms.csv"
cols = ["term", "rule", "left_generic", "named_specifically", "total_mentions",
        "pct_of_products_left_generic", "pct_of_mentions_left_generic",
        "top_specific_names", "rule_says"]
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

print("products analysed: %d\n" % len(with_ing))
print("%-26s %-26s %7s %7s %8s" % ("term", "what the rule asks", "generic", "named", "% prods"))
for r in rows:
    print("%-26s %-26s %7d %7d %7.1f%%" % (
        r["term"], r["rule"], r["left_generic"], r["named_specifically"],
        r["pct_of_products_left_generic"]))
gap = [r for r in rows if r["rule"] != CLASS_TITLE_OK and r["left_generic"]]
print("\nterms where the rule asks for more than the label gave: %d" % len(gap))
print("wrote %s" % out)
