"""Check every card before it is published. Costs nothing, catches most mistakes.

Runs four checks:
  1. schema    - every required field present, no extra fields
  2. vocabulary- status fields only ever use the five allowed words
  3. no-opinion- banned words that turn facts into fear
  4. links     - every source URL actually resolves

Usage: python scripts/check_cards.py [--no-network]
"""
import json, pathlib, re, sys, urllib.request, urllib.error, collections

root = pathlib.Path(__file__).resolve().parent.parent
SKIP_NET = "--no-network" in sys.argv

STATUS = {"allowed", "allowed_with_limits", "not_authorised", "under_review", "not_found"}
REQUIRED = {"ins", "e_number", "name", "also_called", "class", "what_it_is",
            "why_its_added", "status", "safe_daily_limit", "eu_exposure_finding",
            "india_limits", "found_in_india_products", "pct_of_india_products", "india_match", "related_forms", "disagreement_tested_on", "regulators_disagree", "permission_wording_differs", "vegetarian_status", "acute_limit", "people_reports",
            "last_checked"}
# words that turn a fact into a feeling - banned by the project's own rules
BANNED = re.compile(r"\b(danger\w*|harmful|toxic|poison\w*|carcinogen\w*|cancer|"
                    r"avoid|unhealthy|bad for|risky|scary|alarming|shocking|"
                    r"may cause|linked to|concerning)\b", re.I)

problems = collections.defaultdict(list)
urls = collections.defaultdict(set)
cards = sorted(root.glob("cards/ins-*.json"))

for f in cards:
    c = json.loads(f.read_text(encoding="utf-8"))
    ins = c.get("ins", f.stem)

    missing = REQUIRED - c.keys()
    if missing:
        problems[ins].append(f"missing fields: {sorted(missing)}")
    extra = c.keys() - REQUIRED
    if extra:
        problems[ins].append(f"unexpected fields: {sorted(extra)}")

    for country, v in (c.get("status") or {}).items():
        val = v.get("value")
        if val not in STATUS:
            problems[ins].append(f"status.{country} = '{val}' is not an allowed word")
        # rule 1: a real status claim must carry a source
        if val not in ("not_found",) and not v.get("source"):
            problems[ins].append(f"status.{country} claims '{val}' with no source link")
        if v.get("source"):
            urls[v["source"]].add(ins)

    sdl = c.get("safe_daily_limit") or {}
    if sdl.get("value") and not sdl.get("source"):
        problems[ins].append("safe_daily_limit has a number but no source link")
    if sdl.get("source"):
        urls[sdl["source"]].add(ins)

    for field in ("what_it_is", "why_its_added"):
        txt = c.get(field) or ""
        if len(txt) > 200:
            problems[ins].append(f"{field} is {len(txt)} chars (max 200)")
        hit = BANNED.search(txt)
        if hit:
            problems[ins].append(f"{field} uses banned word '{hit.group(0)}'")

    for lim in c.get("india_limits") or []:
        if not lim.get("page"):
            problems[ins].append("an india_limits row has no page number to check against")

print(f"cards checked: {len(cards)}")
print(f"distinct source links: {len(urls)}")

DOI = re.compile(r'(10\.\d{4,9}/[^\s"<>]+)')
BLOCKS_BOTS = ("wiley.com", "doi.org", "sciencedirect", "springer")


def verify_doi(doi):
    """Confirm a DOI is registered, and return its real title, via Crossref."""
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/")
    req = urllib.request.Request(url, headers={
        "User-Agent": "IndiaAdditiveAtlas/0.1 (mailto:krishna.met@nitjsr.ac.in)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        msg = json.load(r)["message"]
    return (msg.get("title") or [""])[0]


dead, blocked = [], []
if not SKIP_NET and urls:
    print("\nchecking links...")
    for u in sorted(urls):
        m = DOI.search(u)
        if m:
            doi = m.group(1).rstrip(".)").replace("/epdf", "")
            try:
                title = verify_doi(doi)
                print(f"  [ok ] DOI registered: {doi}")
                print(f"         -> {title[:88]}")
            except Exception as e:
                dead.append((u, f"DOI not registered ({type(e).__name__})", sorted(urls[u])))
                print(f"  [DEAD] {doi} could not be confirmed with Crossref")
            continue
        try:
            req = urllib.request.Request(u, method="HEAD",
                                         headers={"User-Agent": "IndiaAdditiveAtlas/0.1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:
            code = f"ERR {type(e).__name__}"
        ok = isinstance(code, int) and code < 400
        if not ok:
            if code == 403 and any(b in u for b in BLOCKS_BOTS):
                blocked.append((u, sorted(urls[u])))     # blocks robots, not broken
                print(f"  [warn] {code} (site blocks automated checks) {u[:66]}")
                continue
            dead.append((u, code, sorted(urls[u])))
        print(f"  [{'ok ' if ok else 'DEAD'}] {code} {u[:88]}")

print("\n" + "=" * 60)
if problems:
    print(f"CARDS WITH PROBLEMS: {len(problems)}")
    for ins, errs in sorted(problems.items()):
        print(f"  INS {ins}")
        for e in errs:
            print(f"      - {e}")
else:
    print("no schema / vocabulary / wording problems")

if dead:
    print(f"\nDEAD LINKS: {len(dead)}")
    for u, code, who in dead:
        print(f"  {code}  {u}  (used by INS {', '.join(who)})")
elif not SKIP_NET:
    print("all links resolve or are confirmed registered")

if blocked:
    print("")
    print(f"not machine-checkable ({len(blocked)}) - the site refuses robots, open by hand:")
    for u, who in blocked:
        print(f"  {u}  (INS {', '.join(who)})")

sys.exit(1 if (problems or dead) else 0)
