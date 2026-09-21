# India Additive Atlas

Plain-language, source-backed information about the additives in Indian packaged
food.

**The promise:** *Don't tell me what to eat. Tell me what I'm eating.*

Every line in this dataset links to the official document it came from. If a fact
cannot be linked, it is left blank. Nothing here is generated or guessed.

---

## Why this exists

India has no mandatory front-of-pack warning labels. The Supreme Court directed
FSSAI to finalise them in April 2025; as of February 2026 the matter is still
unresolved, with FSSAI reporting no consensus among stakeholders.

Meanwhile India's packaged food market is growing fast and reaching smaller
towns, and ICMR's 2024 dietary guidelines tell people to cut down on
ultra-processed food — without giving them any way to identify it.

India's own additive rules exist only as PDFs. Nobody has published them as data.
This project does that first, and explains them second.

---

## What is in here

| Path | What it holds |
|---|---|
| `cards/` | One JSON file per additive — the actual dataset |
| `data/` | Machine-readable extracts of the official sources |
| `sources/` | The official documents themselves, as downloaded |
| `scripts/` | Everything that built the above, re-runnable |
| `TEMPLATE.md` | The locked card format and the rules |

### Key data files

- `data/india_top_additives.csv` — additives ranked by how often they appear in
  10,000 real Indian products
- `data/fssai_appendix_a_limits.csv` — India's permitted levels, by food category
- `data/eu_efsa_facts.json` — EU safety reviews and acceptable daily intakes
- `data/us_cfr_facts.json` — US status with 21 CFR citations
- `data/india_vague_label_terms.csv` — how often Indian labels are allowed to stay
  non-specific

---

## The rules this project holds itself to

1. **No source link, no line.** `not_found` is an acceptable answer; guessing is not.
2. **Five words only** for regulatory status: `allowed`, `allowed_with_limits`,
   `not_authorised`, `under_review`, `not_found`.
3. **No opinions.** No "harmful", no "may cause", no "linked to". `scripts/check_cards.py`
   fails the build if those words appear.
4. **No brand names.** Claims attach to ingredients, never to products or companies.
5. **"Not authorised" is not "banned."** Regulators differ for reasons of process
   and petition history as often as for reasons of science. Where the reason is
   not known, the card says so.
6. **No health scores.** Version 1 states facts and shows sources. It does not rate
   food.

---

## Known limits

- Coverage comes from Open Food Facts, which holds roughly 10,000 Indian products.
  That is a small slice of the market, so frequency counts indicate what is common,
  not a national census.
- FSSAI limits are extracted from a 354-page PDF by table detection. Spot-checks
  are clean, but the page number is kept on every row so any value can be verified
  against the original.
- Acceptable daily intakes are mostly EFSA's. Where India or JECFA set a different
  figure, that is not yet captured.

---

## Rebuilding from scratch

```bash
python scripts/harvest_india.py           # 10,000 Indian products
python scripts/build_top_list.py          # rank additives by real-world frequency
python scripts/parse_fssai_appendix_a.py  # India's limits out of the PDF
python scripts/build_eu_facts.py          # EU reviews and daily limits
python scripts/build_us_facts.py          # US status from eCFR
python scripts/build_cards.py             # assemble the cards
python scripts/check_cards.py             # verify schema, wording and every link
```

## Sources

- FSSAI, *Appendix A: List of Food Additives* and the Food Additives Regulations compendium
- EFSA re-evaluation opinions, via the Open Food Facts additives taxonomy (ODbL)
- US 21 CFR Parts 172, 182 and 184, via the eCFR API
- Open Food Facts product database (ODbL)

## Licence

Data: ODbL, matching Open Food Facts, which parts of it derive from.
