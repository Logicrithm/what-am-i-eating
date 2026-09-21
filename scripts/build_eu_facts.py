"""Pull the EU (EFSA) facts out of the Open Food Facts taxonomy into a flat file.

Everything here is already sourced - each row keeps the DOI link to the EFSA
opinion it came from, so every line on a card can be clicked and checked.

Output: data/eu_efsa_facts.json
"""
import json, re, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
tax = json.loads((root / "sources/raw/off_additives.json").read_text(encoding="utf-8"))


def en(entry, field):
    v = entry.get(field)
    if isinstance(v, dict):
        return v.get("en")
    return None


facts = {}
for tag, e in tax.items():
    m = re.match(r"^en:e(\d{3,4}[a-z]*(?:ii|iii|iv|i|v|vi)?)$", tag)
    if not m:
        continue
    ins = m.group(1).upper()
    name = en(e, "name") or ""
    name = re.sub(r"^E\d+[a-z]*\s*-\s*", "", name)

    adi = en(e, "efsa_evaluation_adi")
    over = (en(e, "efsa_evaluation_overexposure_risk") or "").replace("en:", "")
    mean_over = (en(e, "efsa_evaluation_exposure_mean_greater_than_adi") or "").replace("en:", "")
    p95_over = (en(e, "efsa_evaluation_exposure_95th_greater_than_adi") or "").replace("en:", "")

    facts[ins] = {
        "ins": ins,
        "name": name,
        "description": en(e, "description") or "",
        "classes": (en(e, "additives_classes") or "").replace("en:", ""),
        "vegan": en(e, "vegan") or "",
        "vegetarian": en(e, "vegetarian") or "",
        "efsa_adi_mg_per_kg_bw_per_day": adi,
        "efsa_adi_established": en(e, "efsa_evaluation_adi_established"),
        "efsa_opinion_title": en(e, "efsa_evaluation") or "",
        "efsa_opinion_url": en(e, "efsa_evaluation_url") or "",
        "efsa_opinion_date": en(e, "efsa_evaluation_date") or "",
        "efsa_overexposure_risk": over,
        "groups_over_adi_on_average": [g.strip() for g in mean_over.split(",") if g.strip()],
        "groups_over_adi_high_consumers": [g.strip() for g in p95_over.split(",") if g.strip()],
        "wikidata": en(e, "wikidata") or "",
    }

out = root / "data/eu_efsa_facts.json"
out.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")

have_adi = sum(1 for v in facts.values() if v["efsa_adi_mg_per_kg_bw_per_day"])
have_op = sum(1 for v in facts.values() if v["efsa_opinion_url"])
over = sum(1 for v in facts.values() if v["groups_over_adi_on_average"])
print(f"additives            : {len(facts)}")
print(f"with an EFSA ADI     : {have_adi}")
print(f"with an EFSA opinion : {have_op}")
print(f"where EFSA found some group already over the ADI on average : {over}")
print(f"wrote {out}")
