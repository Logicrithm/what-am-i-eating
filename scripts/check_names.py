"""Cross-check every card's name against FSSAI's own INS-to-name table.

Why: the Open Food Facts taxonomy calls E490 "Propylene glycol". FSSAI's
compendium states plainly that propylene glycol is INS 1520. We had written a
card describing propylene glycol under INS 490 - an upstream naming error that we
then compounded with our own sentence.

The compendium repeats a specification block for each additive:

    Common Name
    <name>
    INS No.
    <number>

so those pairs are India's own answer to "what is this number", and they are the
right thing to trust inside an Indian dataset.

Output: data/fssai_ins_names.json, plus a report of disagreements.
"""
import json, re, pathlib, difflib

root = pathlib.Path(__file__).resolve().parent.parent
txt = (root / "sources/fssai_additives_compendium.txt").read_text(encoding="utf-8")
lines = [re.sub(r"\s+", " ", l).strip() for l in txt.split("\n")]

pairs = {}
for i, l in enumerate(lines):
    if l.lower() != "common name":
        continue
    # name sits on the next non-empty line; "INS No." follows, then the number
    name = next((x for x in lines[i + 1:i + 4] if x), "")
    j = next((k for k in range(i + 1, min(i + 9, len(lines)))
              if lines[k].lower().startswith("ins no")), None)
    if j is None or not name:
        continue
    num = next((x for x in lines[j + 1:j + 4] if x), "")
    num = re.sub(r"\s+", "", num)
    if not re.match(r"^\d{3,4}", num):
        continue
    key = re.sub(r"[^0-9a-z]", "", num.lower()).upper()
    pairs.setdefault(key, name.strip())

(root / "data/fssai_ins_names.json").write_text(
    json.dumps(pairs, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
print("INS -> name pairs taken from FSSAI's own compendium: %d\n" % len(pairs))


def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


cards = [json.loads(p.read_text(encoding="utf-8"))
         for p in sorted(root.glob("cards/ins-*.json"))]

agree = notlisted = 0
bad = []
for c in cards:
    ins = c["ins"].upper()
    fssai = pairs.get(ins) or pairs.get(re.match(r"^\d+", ins).group(0))
    if not fssai:
        notlisted += 1
        continue
    a, b = norm(c["name"]), norm(fssai)
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    if a in b or b in a or ratio > 0.6:
        agree += 1
    else:
        bad.append((c["ins"], c["name"], fssai, round(ratio, 2)))

print("cards checked against FSSAI's table : %d" % len(cards))
print("  names agree                       : %d" % agree)
print("  FSSAI does not list that number    : %d" % notlisted)
print("  NAMES DISAGREE                    : %d" % len(bad))
for ins, ours, theirs, r in sorted(bad):
    print("\n   INS %-7s we say  %r" % (ins, ours[:44]))
    print("               FSSAI says %r   (similarity %.2f)" % (theirs[:44], r))
