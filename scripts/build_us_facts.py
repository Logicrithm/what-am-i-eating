"""Parse the US rules (21 CFR) downloaded from eCFR into a name -> status lookup.

Part 182 / 184 = GRAS (generally recognised as safe)      -> allowed
Part 172       = additives permitted subject to conditions -> allowed_with_limits

Every entry keeps its eCFR section link, so each US line on a card is clickable.

Output: data/us_cfr_facts.json
"""
import re, json, pathlib, html

root = pathlib.Path(__file__).resolve().parent.parent
SECTION = re.compile(r'<DIV8 N="([\d.]+)"[^>]*TYPE="SECTION"[^>]*>\s*<HEAD>\s*&#xA7;\s*([\d.]+)\s+(.*?)\.?\s*</HEAD>', re.S)

PARTS = {
    "172": ("allowed_with_limits", "Permitted as a food additive, subject to the conditions in this section"),
    "182": ("allowed", "Generally Recognised As Safe (GRAS)"),
    "184": ("allowed", "Generally Recognised As Safe (GRAS) for direct addition to food"),
    "73":  ("allowed_with_limits", "Listed colour additive, exempt from batch certification"),
    "74":  ("allowed_with_limits", "Listed colour additive, subject to batch certification"),
}

facts = {}
for part, (status, note) in PARTS.items():
    f = root / f"sources/raw/us_21cfr{part}.xml"
    if not f.exists():
        continue
    s = f.read_text(encoding="utf-8", errors="replace")
    for _, sec, title in SECTION.findall(s):
        name = html.unescape(re.sub(r"<[^>]+>", "", title)).strip().rstrip(".")
        if not name or len(name) > 90:
            continue
        key = re.sub(r"[^a-z0-9]", "", name.lower())
        if not key:
            continue
        aliases = {key}
        simple = re.sub(r"^(tert|n|o|p|d|l|dl)-", "", name.lower())
        aliases.add(re.sub(r"[^a-z0-9]", "", simple))
        core = re.sub(r"\s*\(.*?\)\s*", " ", name.lower())
        aliases.add(re.sub(r"[^a-z0-9]", "", core))
        entry = {
            "name": name,
            "status": status,
            "note": note,
            "citation": f"21 CFR {sec}",
            "source": f"https://www.ecfr.gov/current/title-21/section-{sec}",
        }
        for a in aliases:
            if a:
                facts.setdefault(a, entry)

out = root / "data/us_cfr_facts.json"
out.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"US entries parsed : {len(facts)}")
for probe in ["guargum", "xanthangum", "sodiumbenzoate", "citricacid", "potassiumsorbate"]:
    e = facts.get(probe)
    print(f"  {probe:<18} -> {(e['citation'] + ' / ' + e['status']) if e else 'not found'}")
print(f"wrote {out}")
