"""Assemble one card per additive from the local source files only.

Nothing here is invented. Every field either comes from a downloaded official
source or is left empty for a human to fill.

Three things this does that matter for trust:
  * uses the NEWEST EFSA opinion found by check_freshness.py, not whatever the
    starting taxonomy happened to carry
  * records how old that opinion is, so a reader can see when nobody has looked
    at a substance for fifteen years
  * flags where regulators DISAGREE, instead of quietly picking one to believe

Output: cards/ins-<n>.json + cards/_index.json
"""
import json, csv, re, pathlib, collections, datetime

root = pathlib.Path(__file__).resolve().parent.parent
top = json.loads((root / "data/india_top_additives.json").read_text(encoding="utf-8"))
eu = json.loads((root / "data/eu_efsa_facts.json").read_text(encoding="utf-8"))
us = json.loads((root / "data/us_cfr_facts.json").read_text(encoding="utf-8"))
limits = list(csv.DictReader((root / "data/fssai_appendix_a_limits.csv").open(encoding="utf-8")))

fresh_path = root / "data/eu_opinion_freshness.json"
fresh = ({r["ins"]: r for r in json.loads(fresh_path.read_text(encoding="utf-8"))}
         if fresh_path.exists() else {})

manual_path = root / "data/manual_additions.json"
manual = json.loads(manual_path.read_text(encoding="utf-8")) if manual_path.exists() else {}
manual = {k: v for k, v in manual.items() if not k.startswith("_")}

sent_path = root / "data/plain_sentences.json"
sentences = json.loads(sent_path.read_text(encoding="utf-8")) if sent_path.exists() else {}
sentences = {k: v for k, v in sentences.items() if not k.startswith("_")}

FSSAI_SRC = "https://www.fssai.gov.in/upload/uploadfiles/files/Appendix%20A.pdf"
TODAY = datetime.date.today()
STATUS = {"allowed", "allowed_with_limits", "not_authorised", "under_review", "not_found"}


def key(s):
    return re.sub(r"[^0-9a-z]", "", (s or "").lower())


by_ins = collections.defaultdict(list)
by_name = collections.defaultdict(list)
by_name_raw = collections.defaultdict(list)
for r in limits:
    if r["ins"]:
        by_ins[key(r["ins"])].append(r)
    by_name[key(r["additive_name"])].append(r)
    by_name_raw[re.sub(r"\s+", " ", r["additive_name"])].append(r)


def india_rows(ins, name):
    """FSSAI often regulates a FAMILY ("BENZOATES"), not one chemical. A group
    entry is accepted only when the name ENDS with that family word - a loose
    match once paired sodium benzoate with a truncated cell reading "SODIUM"
    and imported a phosphate limit."""
    k = key(ins)
    if by_ins.get(k):
        return by_ins[k], "exact"
    base = re.match(r"^\d+", k)
    if base and by_ins.get(base.group(0)):
        return by_ins[base.group(0)], "exact"
    nk = (name or "").strip().lower()
    if nk and by_name.get(key(nk)):
        return by_name[key(nk)], "exact"
    for raw, rows in by_name_raw.items():
        g = raw.strip()
        if not g.isupper() or len(g) < 6:
            continue
        singular = re.sub(r"\s+", " ", g.lower()).rstrip("s")
        if nk.endswith(singular) or nk.endswith(singular + "s"):
            return rows, "group:" + g
    return [], "none"


cards = []
index = []

for t in top[:50]:
    ins = t["ins"]
    e = eu.get(ins.upper(), {})
    rows, match_kind = india_rows(ins, t["name"])

    # ---------- India ----------
    if not rows:
        india_status = "not_found"
        india_note = "Not located in Appendix A yet - needs a human check."
    elif all(r["limit_type"] == "gmp" for r in rows):
        india_status = "allowed"
        india_note = ("Permitted at GMP level - used as needed, "
                      "no fixed numeric cap in the categories found.")
    else:
        india_status = "allowed_with_limits"
        india_note = "Maximum level depends on the food. Examples below."

    if match_kind.startswith("group:"):
        family = match_kind.split(":", 1)[1]
        india_note = ("FSSAI sets these limits for the " + family + " family as a whole, "
                      "not for this one substance. ") + india_note

    # ---------- EU: prefer the newest opinion the freshness check found ----------
    f = fresh.get(ins) or {}
    newest = f.get("newest_found")
    superseded = None
    if newest and f.get("verdict") in ("superseded", "found_opinion_we_did_not_have"):
        eu_title = newest["title"]
        eu_src = newest["url"]
        eu_date = newest["date"]
        if f.get("verdict") == "superseded":
            superseded = {"date": f["we_have"]["date"], "title": f["we_have"]["title"]}
    else:
        eu_title = e.get("efsa_opinion_title", "")
        eu_src = e.get("efsa_opinion_url", "")
        eu_date = (e.get("efsa_opinion_date") or "").replace("/", "-")[:7]

    eu_status = "allowed_with_limits" if eu_src else "not_found"

    opinion_age = None
    if eu_date:
        try:
            opinion_age = TODAY.year - int(eu_date[:4])
        except ValueError:
            opinion_age = None

    # ---------- USA ----------
    us_hit = None
    for cand in [t["name"], e.get("name", "")]:
        k = key(cand)
        if k and k in us:
            us_hit = us[k]
            break

    adi = e.get("efsa_adi_mg_per_kg_bw_per_day")
    no_adi_meaning = ""
    if not adi and eu_src:
        no_adi_meaning = ("EFSA has not set a number for this one. That can mean it is "
                          "considered safe enough not to need a limit, or that the evidence "
                          "was not sufficient to set one. The opinion itself says which.")

    # A real disagreement is one regulator PERMITTING while another RESTRICTS.
    # "allowed" vs "allowed_with_limits" is a difference in how each authority
    # writes its rules, not a conflict - flagging that as disagreement would
    # manufacture alarm, which is exactly what this project refuses to do.
    PERMISSIVE = {"allowed", "allowed_with_limits"}
    RESTRICTIVE = {"not_authorised", "under_review"}
    statuses = [india_status, eu_status, us_hit["status"] if us_hit else "not_found"]
    known = [s for s in statuses if s != "not_found"]
    disagree = bool(set(known) & PERMISSIVE) and bool(set(known) & RESTRICTIVE)
    permission_differs = len(set(known) & PERMISSIVE) > 1

    card = {
        "ins": ins,
        "e_number": "E" + ins,
        "name": t["name"] or e.get("name", ""),
        "also_called": [x for x in [e.get("name")] if x and x != t["name"]],
        "class": t["classes"] or e.get("classes", ""),
        "what_it_is": (sentences.get(ins) or {}).get("what_it_is", ""),
        "why_its_added": (sentences.get(ins) or {}).get("why_its_added", ""),
        "status": {
            "india": {
                "value": india_status,
                "note": india_note,
                "source": FSSAI_SRC if rows else "",
            },
            "eu": {
                "value": eu_status,
                "note": eu_title,
                "source": eu_src,
                "opinion_date": eu_date,
                "opinion_age_years": opinion_age,
                "replaced_an_older_opinion": superseded,
            },
            "usa": {
                "value": us_hit["status"] if us_hit else "not_found",
                "note": (us_hit["note"] + " (" + us_hit["citation"] + ")") if us_hit else "",
                "source": us_hit["source"] if us_hit else "",
            },
        },
        "regulators_disagree": disagree,
        "permission_wording_differs": permission_differs,
        # In India this is not a side note. A green-dot "vegetarian" pack can
        # legally contain an additive whose source is animal - the label is not
        # required to say which source was used. "maybe" means exactly that:
        # it depends on how the manufacturer made it, and you cannot tell.
        "vegetarian_status": {
            "vegetarian": e.get("vegetarian", "") or "not_known",
            "vegan": e.get("vegan", "") or "not_known",
            "means": ("Can be made from either plant or animal sources. The label is not "
                      "required to say which one was used."
                      if e.get("vegetarian") == "maybe" or e.get("vegan") == "maybe" else ""),
        },
        "safe_daily_limit": {
            "value": float(adi) if adi else None,
            "unit": "mg per kg of body weight per day" if adi else "",
            "set_by": "EFSA (European Food Safety Authority)" if adi else "",
            "source": eu_src if adi else "",
            "no_number_means": no_adi_meaning,
        },
        # Some harm is not about a daily average at all - it is about ONE serving.
        # Glycerol taught us this: children were hurt by a single slush drink while
        # every daily-intake figure looked fine. A schema that can only express
        # "per day" cannot warn anybody about that.
        "acute_limit": (manual.get(ins) or {}).get("acute_limit") or {
            "value": None, "unit": "", "set_by": "", "source": "",
            "means": ["No single-serving limit has been found for this substance. "
                      "That is not the same as there being no risk from one large serving - "
                      "it means nobody has published a number."],
        },
        # LAYER 2, kept strictly apart from everything above.
        # Above this line: what authorities published, sourced and dated.
        # Below this line: what people reported. Counted, never interpreted by us.
        # The two must never be merged - a report is not a finding, and a finding
        # is not a vote. But when reports pile up and no authority has looked,
        # that gap is itself worth showing. It is how glycerol surfaced.
        "people_reports": {
            "count": 0,
            "reports": [],
            "status": "not open yet",
            "rule": ("Reports are shown as reports. We count them. We never turn them "
                     "into a health claim, and we never let them change the sourced "
                     "facts above."),
        },
        "eu_exposure_finding": {
            "groups_over_limit_on_average": e.get("groups_over_adi_on_average", []),
            "groups_over_limit_high_consumers": e.get("groups_over_adi_high_consumers", []),
            "source": e.get("efsa_opinion_url", ""),
        },
        "india_limits": [
            {
                "food_category": (re.sub(r"\s+", " ", r["food_category"]).strip()
                                  or "(not captured - see page " + r["page"] + " of the PDF)"),
                "max_level": r["max_level"],
                "page": int(r["page"]),
            }
            for r in rows[:12]
        ],
        "found_in_india_products": t["india_products"],
        "pct_of_india_products": t["pct"],
        "india_match": match_kind,
        "last_checked": TODAY.isoformat(),
    }

    for c in ("india", "eu", "usa"):
        assert card["status"][c]["value"] in STATUS, "bad status on " + ins

    (root / ("cards/ins-" + ins.lower() + ".json")).write_text(
        json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    cards.append(card)
    index.append({
        "ins": ins, "name": card["name"], "class": card["class"],
        "india": india_status, "disagree": disagree, "products": t["india_products"],
    })

(root / "cards/_index.json").write_text(
    json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

n = len(cards)


def count(pred):
    return sum(1 for c in cards if pred(c))


print("cards written             : " + str(n))
print("  India status found      : %d/%d" % (count(lambda c: c["status"]["india"]["value"] != "not_found"), n))
print("  EU opinion found        : %d/%d" % (count(lambda c: c["status"]["eu"]["source"]), n))
print("  US status found         : %d/%d" % (count(lambda c: c["status"]["usa"]["value"] != "not_found"), n))
print("  safe daily limit        : %d/%d" % (count(lambda c: c["safe_daily_limit"]["value"]), n))
print("  REGULATORS DISAGREE     : %d/%d" % (count(lambda c: c["regulators_disagree"]), n))
print("  EU opinion was updated  : %d/%d" % (count(lambda c: c["status"]["eu"]["replaced_an_older_opinion"]), n))

old = [c for c in cards if (c["status"]["eu"]["opinion_age_years"] or 0) >= 12]
print("  EU opinion 12+ yrs old  : " + str(len(old)) + "  -> " + ", ".join(c["ins"] for c in old))
