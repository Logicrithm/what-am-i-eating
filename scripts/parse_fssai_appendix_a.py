"""FSSAI Appendix A -> structured limits.

Why this reads rows by CONTENT rather than by column position:
the PDF's cells drift between columns from row to row, so a fixed column map
silently drops rows (guar gum, xanthan gum, carrageenan all vanished that way).

Within one row the order is always the same:
    [food category code] [food category name] <additive> [INS] <limit> [note]
so the limit cell is used as the anchor - whatever sits before it describes the
additive, whatever sits after it is the footnote. A limit can therefore never be
attached to an additive from a different row.

Output: data/fssai_appendix_a_limits.csv
"""
import re, csv, pathlib, fitz

root = pathlib.Path(__file__).resolve().parent.parent
doc = fitz.open(root / "sources/raw/fssai_appendix_a.pdf")

AMEND = re.compile(r"^\s*\d+\[|\]\s*$")
LIMIT = re.compile(r"^\s*(\d[\d,]*(?:\.\d+)?)\s*(mg/kg|g/kg|mg/l|g/l|%)\s*$", re.I)
GMP   = re.compile(r"^\s*GMP\s*$", re.I)
INS   = re.compile(r"^\d{3,4}\s?[a-z]{0,3}(?:\s?\([ivx]+\))?$", re.I)
FCS   = re.compile(r"^\d+(\.\d+)+$")
WORDY = re.compile(r"[A-Za-z]{3}")
HEADERISH = re.compile(r"food additive|maximum level|ins no|food category", re.I)


def clean(c):
    return re.sub(r"\s+", " ", (c or "").replace("\n", " ")).strip()


def parse_row(cells):
    """Return (fcs, fcn, name, ins, level, unit, kind, note) or None."""
    vals = [(i, AMEND.sub("", c).strip()) for i, c in enumerate(cells) if clean(c)]
    vals = [(i, c) for i, c in vals if c]
    if not vals:
        return None

    anchor = None
    for i, c in vals:
        if LIMIT.match(c) or GMP.match(c):
            anchor = i
            break
    if anchor is None:
        return None

    raw = next(c for i, c in vals if i == anchor)
    if GMP.match(raw):
        level, unit, kind = "GMP", "", "gmp"
    else:
        m = LIMIT.match(raw)
        level, unit, kind = m.group(1), m.group(2).lower(), "numeric"

    before = [c for i, c in vals if i < anchor]
    after = [c for i, c in vals if i > anchor]

    fcs = next((c for c in before if FCS.match(c)), "")
    rest = [c for c in before if not FCS.match(c)]

    ins = ""
    if rest and INS.match(rest[-1]):
        ins = re.sub(r"\s+", "", rest.pop())

    wordy = [c for c in rest if WORDY.search(c)]
    if not wordy:
        return None
    name = wordy[-1]
    fcn = " ".join(wordy[:-1]).strip()
    if HEADERISH.search(name):
        return None

    note = next((c for c in after if re.match(r"^[\d,\s]+$", c)), "")
    return fcs, fcn, name, ins, level, unit, kind, note


rows, tables_used = [], 0
for pno in range(doc.page_count):
    try:
        tables = doc[pno].find_tables().tables
    except Exception:
        continue
    for t in tables:
        data = t.extract()
        if not data:
            continue
        got, fcs_c, fcn_c = [], "", ""
        for r in data:
            parsed = parse_row(r)
            if not parsed:
                continue
            fcs, fcn, name, ins, level, unit, kind, note = parsed
            if fcs:
                fcs_c = fcs
            if fcn:
                fcn_c = fcn
            got.append({
                "ins": ins,
                "additive_name": name,
                "food_category_code": fcs or fcs_c,
                "food_category": fcn or fcn_c,
                "max_level": f"{level} {unit}".strip(),
                "limit_type": kind,
                "note": note,
                "page": pno + 1,
            })
        if len(got) >= 2:          # a real additive table, not a stray match
            tables_used += 1
            rows.extend(got)

out = root / "data/fssai_appendix_a_limits.csv"
with out.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ins", "additive_name", "food_category_code",
                                      "food_category", "max_level", "limit_type",
                                      "note", "page"])
    w.writeheader()
    w.writerows(rows)

print(f"tables used     : {tables_used}")
print(f"limit rows      : {len(rows)}")
print(f"  numeric       : {sum(1 for r in rows if r['limit_type']=='numeric')}")
print(f"  GMP           : {sum(1 for r in rows if r['limit_type']=='gmp')}")
print(f"  with an INS no: {sum(1 for r in rows if r['ins'])}")
print(f"wrote {out}")
