# The card template — locked

Every additive gets one file: `cards/ins-<number>.json`.
Same fields, every time. Nothing extra, nothing missing.

## The rules

1. **No source link, no line.** If it cannot be linked, leave it empty.
2. **`not_found` is a correct answer.** Guessing is not.
3. **Status fields accept five words only** — nothing else is valid:
   `allowed` · `allowed_with_limits` · `not_authorised` · `under_review` · `not_found`
4. **No opinions.** No "may cause", no "controversial", no "concerning".
5. **No brand names.** Ever.

## The fields

| Field | What goes in it | Who fills it |
|---|---|---|
| `ins` | India's number, e.g. `211` | script |
| `e_number` | Europe's number, e.g. `E211` | script |
| `name` | Common English name | script |
| `also_called` | Other names people see on packets | script |
| `class` | preservative / colour / emulsifier / … | script |
| `what_it_is` | One plain sentence. Max 200 characters. | human |
| `why_its_added` | One plain sentence. What job it does in the food. | human |
| `status.india` | One of the five words + FSSAI source | script + check |
| `status.eu` | One of the five words + EFSA source | agent |
| `status.usa` | One of the five words + FDA source | agent |
| `safe_daily_limit` | Number + unit + who set it + link | script (EFSA) / agent |
| `india_limits` | Real examples: food type → max level → PDF page | script |
| `found_in_india_products` | How many of the 10,000 Indian products contain it | script |
| `last_checked` | Date | script |

## What is deliberately NOT here

- No health score
- No "good / bad" rating
- No summary of research
- No prediction about long-term effects

Those come later, or never. Version 1 only states facts that a reader can click
and verify for themselves.

## Example shape

```json
{
  "ins": "211",
  "e_number": "E211",
  "name": "Sodium benzoate",
  "also_called": ["benzoate of soda", "INS 211"],
  "class": "preservative",
  "what_it_is": "",
  "why_its_added": "",
  "status": {
    "india": { "value": "", "source": "" },
    "eu":    { "value": "", "source": "" },
    "usa":   { "value": "", "source": "" }
  },
  "safe_daily_limit": {
    "value": null, "unit": "", "set_by": "", "source": ""
  },
  "india_limits": [
    { "food_category": "", "max_level": "", "page": null }
  ],
  "found_in_india_products": null,
  "last_checked": "2026-09-21"
}
```
