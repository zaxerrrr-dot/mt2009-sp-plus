#!/usr/bin/env python3
"""ref_from_xlsx.py - turn the owner's filled price sheet (the reference server's market, read 28.10.2026) into
reference_prices_20261028.json, the data file gen_yohara_prices.py prices the Yohara items from.

    python3 tools/yohara_prices/ref_from_xlsx.py ceny-dia-filled.xlsx [out.json]

Needs openpyxl (the generator itself does not). What it keeps, per vnum of our world:
  * the sheet's own number (Yang a piece: "the average of at most 3 cheapest offers", won x 100 000 000 added),
  * the offers it was made from (sheet "Oferty Nite": Yang a piece and their bonus lines) and their median,
    which the generator uses - one wild offer (a 1 000 000 000 next to two of 100 000 000) moves a mean, not a median,
  * the plus the price is for ("Plus / ilosc u nich"; every price of the sheet is already a piece's),
  * whether the offers carry extra bonuses ("Brak czystych ofert" - no clean offer was found),
  * group, name, level, our price and how ours was made, as the sheet shows them (for the review only).
The key items sheet ("Kluczowe przedmioty") goes in as it is: name, vnum, ours, theirs, the notes.
"""
import json
import os
import re
import statistics
import sys

import openpyxl

WON = 100000000          # the sheet's assumption, kept by the owner (sheet "Oferty Nite": "1 Won w Yang")
YOHARA_SHEET = "Yohara – wszystkie przedmioty"


def clean(text):
    """The sheet's notes without the market site's name (and its 'official name' wording)."""
    text = re.sub(r"\s*Metin\d\w*,?\s*", " ", str(text or ""), flags=re.I)
    text = re.sub(r"nazwie ofic\w*", "nazwie z katalogu", text, flags=re.I)
    return re.sub(r"\s{2,}", " ", text).strip()


def num(x):
    return float(x) if isinstance(x, (int, float)) else None


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                             "reference_prices_20261028.json")
    wb = openpyxl.load_workbook(src, data_only=True)
    offers = {}
    for r in list(wb["Oferty Nite"].iter_rows(values_only=True)):
        if r[0] not in ("Kluczowe przedmioty", YOHARA_SHEET) or not isinstance(r[2], int):
            continue
        per = num(r[8])
        if per is None:
            continue
        offers.setdefault((r[0], r[1]), []).append({"yang": round(per), "bonus": r[9] or ""})
    won = wb["Oferty Nite"].cell(3, 3).value
    if won != WON:
        sys.exit("ref_from_xlsx: the sheet says 1 won = %r Yang, not %d - check it" % (won, WON))

    keys = []
    ws = wb["Kluczowe przedmioty"]
    for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not r[0] or r[0] == "Przedmiot":
            continue
        theirs = None
        if num(r[3]) is not None or num(r[4]) is not None:
            theirs = (num(r[3]) or 0) + (num(r[4]) or 0) * WON
        keys.append({"row": i, "name": r[0], "vnum": r[1], "ours": r[2], "theirs": round(theirs) if theirs else None,
                     "note": clean(r[5])})

    items = {}
    ws = wb[YOHARA_SHEET]
    for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not isinstance(r[1], int):
            continue
        sheet = None
        if num(r[8]) is not None or num(r[9]) is not None:
            sheet = (num(r[8]) or 0) + (num(r[9]) or 0) * WON
        plus = None
        m = re.match(r"\s*\+(\d+)", str(r[10] or ""))
        if m:
            plus = int(m.group(1))
        offs = offers.get((YOHARA_SHEET, i), [])
        note = clean(r[12])
        it = {"row": i, "group": r[0], "name": r[2], "level": r[3], "plus_range": r[4], "ours": r[6], "ours9": r[7],
              "how": r[11] or "", "note": note, "plus": plus,
              "sheet": round(sheet) if sheet else None,
              "offers": offs,
              "median": round(statistics.median(o["yang"] for o in offs)) if offs else None,
              "bonus": "Brak czystych ofert" in note}
        if it["sheet"] and not offs:
            it["median"] = it["sheet"]
        items[str(r[1])] = it

    json.dump({"source": "the reference server's market (28.10.2026), the owner's sheet ceny-dia-filled.xlsx",
               "won_yang": WON, "key_items": keys, "items": items},
              open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
    print("%s: %d key items, %d items (%d with a reference price)" % (
        out, len(keys), len(items), sum(1 for v in items.values() if v["median"])), file=sys.stderr)


if __name__ == "__main__":
    main()
