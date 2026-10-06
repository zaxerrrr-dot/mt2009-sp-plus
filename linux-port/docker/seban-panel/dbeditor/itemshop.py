"""MT2009_PLUS_DB_EDITOR_ITEMSHOP_V1: "ItemShop" - the lines of the in-game
item shop (the coin window in the client), for an operator who is not a
programmer: what is sold, how many, for how much, in which currency, from
which level, promotions and flash offers. Tabs stay as the client has them.

What the game reads (db/src/ClientManagerBoot.cpp InitializeItemShop, at the
db core's boot and on "/reload i"):

    SELECT i.index, i.vnum, i.count, i.price, i.currency+0, i.minLevel,
           p.price, p.start_time, p.end_time,                 -- promotion
           t.max_amount, t.account_limit, t.start_time, t.end_time,  -- flash offer
           i.socket0..2
      FROM common.itemshop_items i
      LEFT JOIN common.itemshop_promotions p ON i.index = p.item_index
      LEFT JOIN common.itemshop_time_auctions t ON i.index = t.item_index

  * Every flash offer (itemshop_time_auctions) needs its counter row in
    player.itemshop_time_auction (item_index, buy_count): without it the db
    core does not boot ("item_index N not found in itemshop_time_auction")
    and "/reload i" fails - this editor writes the two together.
  * socket0-2 are read but never given to the item (itemshop_manager.cpp
    GiveItem has only vnum and count): shown, not editable.
  * minLevel is a BYTE in the core (0-255), count a smallint.
  * "/reload i" (an IMPLEMENTOR's command) reloads it live for everybody;
    the panel asks an online IMPLEMENTOR through web_admin.quest
    ISHOP_RELOAD (player.web_admin_queue). Otherwise "Zastosuj" (restart).

Where a line shows in the client (root/uiitemshop.py ITEMSHOP_CATEGORIES,
client-patches/client-2.0.25/root - checked by test_dbeditor_itemshop.py):
only by its index - TABS below; "VIPy" is a fixed list 101-113 there; every
line priced in Smocze Znaki also shows in "Smocze Znaki", every line with a
running promotion in "Polecane", every flash offer in "Oferty
Błyskawiczne". A line outside all of it is in the database but nobody sees
it. The name and icon come from the client's own item_proto by vnum; a few
indexes get a fixed suffix from the client (CLIENT_NAME_SUFFIX).

apply.sh adds the package's own lines once per install (ishop_once,
BOOT_ONCE below - checked against it by the test); until the first full
start after an update a line removed here may come back once.

Every change goes through common_items (history, undo, "Zastosuj", the
world reset's replay, the configuration export/import).
"""
import json
import re
import time

from flask import abort, current_app, flash, jsonify, redirect, render_template, request, url_for

from dbeditor import common_items as common

MARKER = "MT2009_PLUS_DB_EDITOR_ITEMSHOP_V1"

ITEMS = "common.itemshop_items"
PROMO = "common.itemshop_promotions"
AUCTION = "common.itemshop_time_auctions"
AUCTION_COUNT = "player.itemshop_time_auction"
PROTO = "world.item_proto"
TABLES = (ITEMS, PROMO, AUCTION, AUCTION_COUNT)

COIN, MARK = 1, 2  # common.itemshop_items.currency ENUM('DRAGON_COIN','DRAGON_MARK')+0
CURRENCY = {COIN: "SM", MARK: "SZ"}
CURRENCY_LONG = {COIN: "Smocze Monety (SM)", MARK: "Smocze Znaki (SZ)"}

PRICE_MAX = 2000000000
COUNT_MAX = 32767          # smallint
LEVEL_MAX = 255            # TItemShopItem.bMinLevel
INDEX_MAX = 65535          # what the bots scan (PLAYERBOT_ISHOP_MAX_INDEX)

# The client's tabs that list lines by index (id, title, ranges).
TABS = (
    ("wyposazenie", "Wyposażenie", ((1, 99),)),
    ("vip", "VIPy", ((101, 113),)),
    ("malzenstwo", "Małżeństwo", ((201, 299),)),
    ("fryzury", "Fryzury +", ((301, 450), (10000, 19999))),
    ("uszlachetnianie", "Uszlachetnianie", ((451, 459),)),
    ("zwoje", "Zwoje i księgi", ((601, 699),)),
    ("kupony", "Kupony SM", ((901, 905),)),
    ("kostiumy", "Kostiumy", ((20000, 29999),)),
    ("naklady", "Nakładki na broń", ((30000, 39999),)),
    ("pety", "Pety", ((40000, 49999),)),
    ("mounty", "Mounty", ((50000, 59999),)),
)
# Tabs filled by something else than the index; a new line gets a free index
# here, outside every range above.
MARK_TAB = ("znaki", "Smocze Znaki", ((700, 899),))       # every line priced in SZ
AUCTION_TAB = ("blyskawiczne", "Oferty Błyskawiczne", ((906, 999),))  # every flash offer
HIDDEN_TAB = ("niewidoczne", "Niewidoczne w kliencie", ())
TAB_TITLES = {t[0]: t[1] for t in TABS + (MARK_TAB, AUCTION_TAB, HIDDEN_TAB)}
TAB_RANGES = {t[0]: t[2] for t in TABS + (MARK_TAB, AUCTION_TAB)}
TAB_NOTES = {
    "vip": "Klient pokazuje tu tylko indeksy 101–113 (stała lista) – nowy VIP tylko na wolnym z nich.",
    "znaki": "Każda pozycja w Smoczych Znakach jest tu (także z innych zakładek). Nowe dostają indeks 700–899.",
    "blyskawiczne": "Każda oferta błyskawiczna (aukcja czasowa) jest tu. Nowe dostają indeks 906–999 – poza "
                    "innymi zakładkami.",
    "niewidoczne": "Indeks poza zakładkami klienta, waluta SM, bez promocji i bez oferty – gracz tego nie widzi. "
                   "Przenieś do zakładki (zmień indeks) albo usuń.",
}

# root/uiitemshop.py ITEMSHOP_CUSTOM_ITEM_DATA: the client adds this to the
# item's name at that index, whatever the item is.
CLIENT_NAME_SUFFIX = {1: "(30 godzin)", 5: "(7 dni)", 101: "(1 dzień)", 102: "(3 dni)", 103: "(1 dzień)",
                      104: "(3 dni)", 105: "(1 dzień)", 106: "(3 dni)", 107: "(1 dzień)", 108: "(3 dni)",
                      109: "(1 dzień)", 110: "(3 dni)", 111: "(30 dni)", 112: "(30 dni)", 608: "(3+1)",
                      610: "(Paczka 25)"}

# apply.sh (ishop_once NAME ...): the package's lines, written once per
# install after mod/10_ingame_itemshop.sql, marked "ishop:NAME" in
# player.playerbot_migrations. adds: indexes it INSERT IGNOREs; removes:
# what it deletes (vnums / indexes) - checked by test_dbeditor_itemshop.py.
BOOT_ONCE = {
    "marriage_201": {"adds": tuple(range(201, 212)), "note": "strona Małżeństwo (201–211)"},
    "autohunt_rings_6": {"adds": (6, 7, 8), "note": "bilet Auto Łowy i dwa pierścienie"},
    "newpet_40901": {"adds": (40901, 40902, 40903, 40904, 40905, 40906, 40907, 40908, 40909, 40920, 40924,
                              40925, 40926, 40927, 40928), "note": "New Pet System – jajka i zaopatrzenie"},
    "owner_prices_pets": {"adds": (), "remove_vnums": (55009, 55032, 55035),
                          "note": "Smakołyk, Smakołyk+ i Skrzynia Ksiąg Peta znikają ze sklepu"},
    "wheel_ticket_9": {"adds": (9,), "note": "Bilet Koła Fortuny"},
    "quiver_10": {"adds": (10, 13), "remove_indexes": (11, 12, 14, 15), "note": "Kołczan i rękawica"},
    "king03_20212": {"adds": (20212, 30054), "note": "Zbroja Króla Wojowników+ i Święty Miecz Bogów+"},
    "monster_cards_617": {"adds": (617, 618), "note": "Karty Potworów (Nowego Początku / Układu)"},
    "collector_item_16": {"adds": (16,), "note": "Kolekcjoner – okno Kolekcjonera z dowolnego miejsca"},
}


# ---- the rules ------------------------------------------------------------------------

def index_tabs(index):
    """The tabs whose index ranges hold this index."""
    return [t[0] for t in TABS if any(lo <= int(index) <= hi for lo, hi in t[2])]


def line_tabs(line):
    """Every tab of the client the line shows in (empty: nobody sees it)."""
    tabs = index_tabs(line["index"])
    if int(line.get("currency") or COIN) == MARK:
        tabs.append(MARK_TAB[0])
    if line.get("auction"):
        tabs.append(AUCTION_TAB[0])
    return tabs


def tab_ranges(tab):
    return TAB_RANGES.get(tab, ())


def in_tab(tab, index):
    return any(lo <= int(index) <= hi for lo, hi in tab_ranges(tab))


def free_index(tab, taken):
    for lo, hi in tab_ranges(tab):
        for index in range(lo, hi + 1):
            if index not in taken:
                return index
    return None


def boot_block(index=None, vnum=None):
    """(name, info) of the apply.sh block that writes this index / removes this vnum."""
    for name, info in BOOT_ONCE.items():
        if index is not None and (int(index) in info.get("adds", ()) or int(index) in info.get("remove_indexes", ())):
            return name, info
        if vnum is not None and int(vnum) in info.get("remove_vnums", ()):
            return name, info
    return None, None


def history_formatter(col, value):
    if col == "currency":
        try:
            return CURRENCY_LONG.get(int(value), value)
        except (TypeError, ValueError):
            return value
    if col == common.ROW_COL and value:
        try:
            row = json.loads(value)
        except ValueError:
            return value
        if "vnum" in row:
            return (f"poz. {row['index']}: przedmiot {row['vnum']} ×{row['count']} · {row['price']} "
                    f"{CURRENCY.get(row.get('currency'), '?')} · od poz. {row.get('minLevel', 0)}")
        if "max_amount" in row:
            return (f"oferta poz. {row['item_index']}: {row['max_amount']} szt., limit konta {row['account_limit']}, "
                    f"{_when(row['start_time'])} – {_when(row['end_time'])}")
        if "price" in row:
            return f"promocja poz. {row['item_index']}: {row['price']}, {_when(row['start_time'])} – {_when(row['end_time'])}"
        if "item_index" in row:
            return f"licznik oferty poz. {row['item_index']}"
    return None


def _when(ts):
    try:
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(int(ts)))
    except (TypeError, ValueError, OverflowError, OSError):
        return str(ts)


def register():
    common.register_table(ITEMS, "index", {
        "vnum": {"kind": "int", "min": 1, "max": 4294967295, "label": "Przedmiot (VNUM)"},
        "count": {"kind": "int", "min": 1, "max": COUNT_MAX, "label": "Ilość"},
        "price": {"kind": "int", "min": 1, "max": PRICE_MAX, "label": "Cena"},
        "currency": {"kind": "int", "min": 1, "max": 2, "label": "Waluta", "select": "`currency`+0"},
        "minLevel": {"kind": "int", "min": 0, "max": LEVEL_MAX, "label": "Od poziomu"},
    }, "ItemShop", formatter=history_formatter,
        row_cols=("index", "vnum", "count", "price", "currency", "minLevel", "socket0", "socket1", "socket2"),
        row_label="pozycja ItemShopu", row_exprs={"currency": ("`currency`+0", "%s")})
    times = {"start_time": ("UNIX_TIMESTAMP(`start_time`)", "FROM_UNIXTIME(%s)"),
             "end_time": ("UNIX_TIMESTAMP(`end_time`)", "FROM_UNIXTIME(%s)")}
    common.register_table(PROMO, "item_index", {}, "ItemShop – promocja", formatter=history_formatter,
                          row_cols=("item_index", "price", "start_time", "end_time"), row_label="promocja",
                          row_exprs=times)
    common.register_table(AUCTION, "item_index", {}, "ItemShop – oferta błyskawiczna", formatter=history_formatter,
                          row_cols=("item_index", "max_amount", "account_limit", "start_time", "end_time"),
                          row_label="oferta błyskawiczna", row_exprs=times)
    # Only the key: the core counts the sales in buy_count, the editor never compares it.
    common.register_table(AUCTION_COUNT, "item_index", {}, "ItemShop – licznik oferty", formatter=history_formatter,
                          row_cols=("item_index",), row_label="licznik oferty")


# ---- reading --------------------------------------------------------------------------------

def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_lines(rows):
    """{index: line} - every line with its promotion, flash offer and counter."""
    lines = {}
    for r in rows(f"SELECT `index`, vnum, `count`, price, `currency`+0 AS currency, minLevel, socket0, socket1, socket2 "
                  f"FROM {ITEMS} ORDER BY `index`"):
        index = _int(r["index"])
        lines[index] = {"index": index, "vnum": _int(r["vnum"]), "count": _int(r["count"]), "price": _int(r["price"]),
                        "currency": _int(r["currency"], COIN), "minLevel": _int(r["minLevel"]),
                        "sockets": [_int(r.get(f"socket{k}")) for k in range(3)], "promo": None, "auction": None}
    for r in rows(f"SELECT item_index, price, UNIX_TIMESTAMP(start_time) AS start_time, "
                  f"UNIX_TIMESTAMP(end_time) AS end_time FROM {PROMO}"):
        line = lines.get(_int(r["item_index"]))
        if line is not None:
            line["promo"] = {"price": _int(r["price"]), "start_time": _int(r["start_time"]),
                             "end_time": _int(r["end_time"])}
    counters = {}
    try:
        for r in rows(f"SELECT item_index, buy_count FROM {AUCTION_COUNT}"):
            counters[_int(r["item_index"])] = _int(r["buy_count"])
    except Exception:  # never break the page over the counters
        pass
    for r in rows(f"SELECT item_index, max_amount, account_limit, UNIX_TIMESTAMP(start_time) AS start_time, "
                  f"UNIX_TIMESTAMP(end_time) AS end_time FROM {AUCTION}"):
        line = lines.get(_int(r["item_index"]))
        if line is not None:
            index = line["index"]
            line["auction"] = {"max_amount": _int(r["max_amount"]), "account_limit": _int(r["account_limit"]),
                               "start_time": _int(r["start_time"]), "end_time": _int(r["end_time"]),
                               "sold": counters.get(index), "counter": index in counters}
    return lines


def load_items(rows, vnums):
    """{vnum: {vnum, name, stack}}."""
    wanted = sorted({int(v) for v in vnums if int(v or 0) > 0})
    found = {}
    for start in range(0, len(wanted), 500):
        part = wanted[start:start + 500]
        marks = ",".join(["%s"] * len(part))
        for r in rows(f"SELECT vnum, CAST(locale_name AS BINARY) AS locale_name, stack FROM {PROTO} "
                      f"WHERE vnum IN ({marks})", part):
            found[int(r["vnum"])] = {"vnum": int(r["vnum"]),
                                     "name": (common.text_of(r["locale_name"]) or "").strip() or f"Przedmiot {r['vnum']}",
                                     "stack": max(1, _int(r.get("stack"), 1))}
    return found


def boot_marks(rows):
    """{block name: True when apply.sh already wrote it on this install}."""
    try:
        found = {r["name"] for r in rows("SELECT name FROM player.playerbot_migrations WHERE name LIKE %s",
                                         ("ishop:%",))}
    except Exception:
        return {}
    return {name: f"ishop:{name}" in found for name in BOOT_ONCE}


def promo_running(promo, now=None):
    now = time.time() if now is None else now
    return bool(promo) and promo["start_time"] <= now < promo["end_time"]


# ---- form values ----------------------------------------------------------------------------

def parse_time(rows, text, label):
    """(unix time, error) of a "YYYY-MM-DD HH:MM" / "YYYY-MM-DDTHH:MM" text, by the database's clock."""
    text = (text or "").strip().replace("T", " ")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?", text):
        return None, f"{label}: podaj datę i godzinę (RRRR-MM-DD GG:MM)."
    if len(text) == 16:
        text += ":00"
    found = rows("SELECT UNIX_TIMESTAMP(%s) AS t", (text,))
    value = _int((found[0] if found else {}).get("t"), 0)
    if value <= 0:
        return None, f"{label}: nieprawidłowa data „{text}”."
    return value, None


def time_text(rows, ts):
    """The "YYYY-MM-DDTHH:MM" of a unix time, by the database's clock (for <input type=datetime-local>)."""
    if not ts:
        return ""
    found = rows("SELECT FROM_UNIXTIME(%s) AS t", (int(ts),))
    value = (found[0] if found else {}).get("t")
    text = value.strftime("%Y-%m-%d %H:%M") if hasattr(value, "strftime") else str(value or "")[:16]
    return text.replace(" ", "T")


def check_line(values, items, label):
    """Errors and warnings of one line's values (already numbers)."""
    errors, warnings = [], []
    item = items.get(values["vnum"])
    if item is None:
        errors.append(f"{label}: nie ma przedmiotu {values['vnum']} w bazie (item_proto).")
    elif values["count"] > item["stack"]:
        warnings.append(f"{label}: {values['count']} szt. to więcej niż jeden stos przedmiotu ({item['stack']}) – "
                        "sprawdź w grze, czy dojdzie cała ilość.")
    return errors, warnings


# ---- the pages ------------------------------------------------------------------------------

def install(bp, ctx):
    import dbeditor

    common.init(ctx)
    register()
    common.install_history(bp, ctx)
    login_required = ctx["login_required"]

    def rows(sql, params=()):
        return common.ctx()["rows"](sql, params)

    def pending_ishop():
        try:
            return [c for c in common.pending_changes() if c["tbl"] in TABLES]
        except Exception:
            return []

    def page_context():
        try:
            context = common.pending_context()
        except Exception:
            context = {"pending_total": 0}
        context["ishop_pending"] = len(pending_ishop())
        return context

    def label_of_line(lines, items):
        def label(key):
            line = lines.get(_int(str(key).split(":")[0]))
            if not line:
                return f"ItemShop poz. {key}"
            item = items.get(line["vnum"])
            return f"{item['name'] if item else line['vnum']} (poz. {line['index']})"
        return label

    def overview(lines):
        tabs = []
        for tab_id, title, ranges in TABS + (MARK_TAB, AUCTION_TAB):
            count = sum(1 for l in lines.values() if tab_id in line_tabs(l))
            tabs.append({"id": tab_id, "title": title, "count": count,
                         "ranges": ", ".join(f"{lo}–{hi}" for lo, hi in ranges)})
        hidden = sum(1 for l in lines.values() if not line_tabs(l))
        if hidden:
            tabs.append({"id": HIDDEN_TAB[0], "title": HIDDEN_TAB[1], "count": hidden, "ranges": ""})
        return tabs

    @bp.route("/itemshop")
    @login_required
    def itemshop():
        lines = load_lines(rows)
        tab = request.args.get("tab") or "wyposazenie"
        if tab not in TAB_TITLES:
            tab = "wyposazenie"
        query = (request.args.get("q") or "").strip()
        items = load_items(rows, {l["vnum"] for l in lines.values()})
        if query:
            needle = query.casefold()
            shown = [l for l in lines.values() if query == str(l["vnum"]) or query == str(l["index"])
                     or needle in items.get(l["vnum"], {}).get("name", "").casefold()]
        elif tab == HIDDEN_TAB[0]:
            shown = [l for l in lines.values() if not line_tabs(l)]
        else:
            shown = [l for l in lines.values() if tab in line_tabs(l)]
        shown.sort(key=lambda l: l["index"])
        marks = boot_marks(rows)
        now = time.time()
        for line in shown:
            line["item"] = items.get(line["vnum"]) or {"vnum": line["vnum"], "name": f"NIEZNANY PRZEDMIOT {line['vnum']}",
                                                       "stack": 1, "unknown": True}
            line["tabs"] = [TAB_TITLES[t] for t in line_tabs(line)]
            line["suffix"] = CLIENT_NAME_SUFFIX.get(line["index"])
            line["promo_running"] = promo_running(line["promo"], now)
            name, info = boot_block(index=line["index"])
            line["boot"] = info["note"] if info and marks.get(name) is False else None
        try:
            history = common.history_batches(10, ITEMS)
        except Exception:
            history = []
        return render_template("dbeditor/itemshop.html", lines=shown, tab=tab, tab_title=TAB_TITLES.get(tab),
                               tab_note=TAB_NOTES.get(tab), tabs=overview(lines), query=query,
                               new_tabs=[(t[0], t[1]) for t in TABS + (MARK_TAB, AUCTION_TAB)],
                               currency=CURRENCY, history=history, can_add=tab != HIDDEN_TAB[0],
                               url_map_endpoints=set(current_app.view_functions),
                               dbe_csrf=common.csrf_token(), **common.template_helpers(), **page_context())

    @bp.post("/itemshop")
    @login_required
    def itemshop_save():
        tab = request.form.get("tab") or "wyposazenie"
        back = url_for("dbeditor.itemshop", tab=tab, q=request.form.get("q") or None)
        if not common.check_csrf():
            return redirect(back)
        action = request.form.get("action", "save")
        lines = load_lines(rows)
        if action == "add":
            return add_line(lines, tab, back)
        return save_tab(lines, back)

    def save_tab(lines, back):
        form = request.form
        errors, warnings = [], []
        updates, deletes = [], []
        indexes = [_int(v, -1) for v in form.getlist("line")]
        new_vnums = set()
        for index in indexes:
            if index not in lines:
                continue
            if form.get(f"del_{index}") == "1":
                deletes.append(index)
                continue
            values = {}
            for col in ("vnum", "count", "price", "currency", "minLevel"):
                spec = common.TABLES[ITEMS]["cols"][col]
                value, error = common.validate(spec, form.get(f"{col}_{index}"), f"poz. {index} · {spec['label']}")
                if error:
                    errors.append(error)
                else:
                    values[col] = value
            if len(values) < 5:
                continue
            changed = {c: v for c, v in values.items() if v != lines[index][c]}
            if changed:
                updates.append((index, changed, values))
                new_vnums.add(values["vnum"])
        items = load_items(rows, new_vnums | {l["vnum"] for l in lines.values()})
        for index, changed, values in updates:
            e, w = check_line(values, items, f"poz. {index}")
            errors += e
            if "vnum" in changed or "count" in changed:
                warnings += w
            if "vnum" in changed and index in CLIENT_NAME_SUFFIX:
                warnings.append(f"poz. {index}: klient dopisuje tu do nazwy „{CLIENT_NAME_SUFFIX[index]}” – "
                                "zostanie przy nowym przedmiocie.")
        if errors:
            for error in errors[:12]:
                flash(error, "error")
            return redirect(back)
        if not updates and not deletes:
            flash("Brak zmian do zapisania.", "success")
            return redirect(back)
        label = label_of_line(lines, items)
        batch = None
        try:
            if updates:
                batch, _changed = common.save_rows(ITEMS, [(i, c) for i, c, _v in updates], note="ItemShop: zmiany",
                                                   label_of=label)
            if deletes:
                batch = remove_lines(lines, deletes, label, batch, note="ItemShop: usunięcie")
        except Exception as exc:
            flash(f"Nie udało się zapisać: {exc}", "error")
            return redirect(back)
        for warning in warnings[:8]:
            flash(warning, "warning")
        marks = boot_marks(rows)
        for index in deletes:
            name, info = boot_block(index=index)
            if info and marks.get(name) is False:
                flash(f"poz. {index} ({info['note']}): apply.sh doda ją jeszcze raz przy najbliższym pełnym starcie "
                      "serwera (raz na instalację) – usuń ją wtedy ponownie.", "warning")
        flash(f"Zapisano: zmienione pozycje {len(updates)}, usunięte {len(deletes)}. "
              "W grze po „Odśwież sklep w grze” albo po „Zastosuj” (restart).", "success")
        return redirect(back)

    def remove_lines(lines, indexes, label, batch=None, note=""):
        """Removes lines with their promotion, flash offer and counter, one batch."""
        promo = [{"item_index": i} for i in indexes if lines[i]["promo"]]
        auction = [{"item_index": i} for i in indexes if lines[i]["auction"]]
        counters = [{"item_index": i} for i in indexes if lines[i]["auction"] and lines[i]["auction"]["counter"]]
        batch, _ = common.write_rows(ITEMS, deletes=[{"index": i} for i in indexes], note=note, label_of=label,
                                     batch=batch)
        if promo:
            common.write_rows(PROMO, deletes=promo, note=note, label_of=label, batch=batch)
        if auction:
            common.write_rows(AUCTION, deletes=auction, note=note, label_of=label, batch=batch)
        if counters:
            common.write_rows(AUCTION_COUNT, deletes=counters, note=note, label_of=label, batch=batch)
        return batch

    def read_new(form, prefix=""):
        values, errors = {}, []
        for col in ("vnum", "count", "price", "currency", "minLevel"):
            spec = common.TABLES[ITEMS]["cols"][col]
            value, error = common.validate(spec, form.get(prefix + col), spec["label"])
            if error:
                errors.append(error)
            else:
                values[col] = value
        return values, errors

    def add_line(lines, tab, back):
        form = request.form
        new_tab = form.get("new_tab") or tab
        if new_tab not in TAB_RANGES:
            flash("Wybierz zakładkę.", "error")
            return redirect(back)
        values, errors = read_new(form, "new_")
        if new_tab == MARK_TAB[0]:
            values["currency"] = MARK
        text = (form.get("new_index") or "").strip()
        if text:
            index, error = common.validate({"kind": "int", "min": 1, "max": INDEX_MAX}, text, "Indeks")
            if error:
                errors.append(error)
            elif not in_tab(new_tab, index):
                errors.append(f"Indeks {index} nie leży w zakładce „{TAB_TITLES[new_tab]}” "
                              f"({', '.join(f'{lo}–{hi}' for lo, hi in tab_ranges(new_tab))}).")
            elif index in lines:
                errors.append(f"Indeks {index} jest już zajęty.")
        else:
            index = free_index(new_tab, set(lines))
            if index is None:
                errors.append(f"W zakładce „{TAB_TITLES[new_tab]}” nie ma wolnego indeksu.")
        items = load_items(rows, [values["vnum"]] if "vnum" in values else [])
        if not errors:
            e, w = check_line(values, items, "Nowa pozycja")
            errors += e
        else:
            w = []
        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(back)
        row = dict(values, index=index, socket0=0, socket1=0, socket2=0)
        name = items[values["vnum"]]["name"]
        try:
            common.write_rows(ITEMS, inserts=[row], note="ItemShop: nowa pozycja",
                              label_of=lambda key: f"{name} (poz. {index})")
        except Exception as exc:
            flash(f"Nie udało się dodać: {exc}", "error")
            return redirect(back)
        for warning in w:
            flash(warning, "warning")
        if index in CLIENT_NAME_SUFFIX:
            flash(f"poz. {index}: klient dopisuje tu do nazwy „{CLIENT_NAME_SUFFIX[index]}”.", "warning")
        if new_tab == AUCTION_TAB[0]:
            flash("Dodano pozycję – ustaw jej ofertę błyskawiczną (czas i ilość), inaczej gracz jej nie zobaczy.",
                  "warning")
            return redirect(url_for("dbeditor.itemshop_line", index=index))
        flash(f"Dodano „{name}” ×{values['count']} za {values['price']} {CURRENCY[values['currency']]} "
              f"(poz. {index}, zakładka {TAB_TITLES[new_tab]}).", "success")
        return redirect(url_for("dbeditor.itemshop", tab=new_tab))

    # -------------------------------------------------------------- one line ---
    @bp.route("/itemshop/<int:index>", methods=["GET", "POST"])
    @login_required
    def itemshop_line(index):
        lines = load_lines(rows)
        line = lines.get(index)
        if line is None:
            abort(404)
        if request.method == "POST":
            if not common.check_csrf():
                return redirect(url_for("dbeditor.itemshop_line", index=index))
            return save_line(lines, line)
        items = load_items(rows, [line["vnum"]])
        line["item"] = items.get(line["vnum"]) or {"vnum": line["vnum"], "name": f"NIEZNANY PRZEDMIOT {line['vnum']}",
                                                   "stack": 1, "unknown": True}
        line["tabs"] = [TAB_TITLES[t] for t in line_tabs(line)]
        line["suffix"] = CLIENT_NAME_SUFFIX.get(index)
        line["promo_running"] = promo_running(line["promo"])
        marks = boot_marks(rows)
        name, info = boot_block(index=index)
        line["boot"] = info["note"] if info and marks.get(name) is False else None
        now = int(time.time())
        times = {
            "promo_start": time_text(rows, line["promo"]["start_time"] if line["promo"] else now),
            "promo_end": time_text(rows, line["promo"]["end_time"] if line["promo"] else now + 7 * 86400),
            "auction_start": time_text(rows, line["auction"]["start_time"] if line["auction"] else now),
            "auction_end": time_text(rows, line["auction"]["end_time"] if line["auction"] else now + 86400),
        }
        try:
            history = [b for b in common.history_batches(80, None) if any(
                r["tbl"] in TABLES and str(r["row_key"]) == str(index) for r in b["rows"])][:8]
        except Exception:
            history = []
        return render_template("dbeditor/itemshop_line.html", line=line, times=times, currency=CURRENCY,
                               new_tabs=[(t[0], t[1]) for t in TABS + (MARK_TAB, AUCTION_TAB)],
                               history=history, url_map_endpoints=set(current_app.view_functions),
                               dbe_csrf=common.csrf_token(), **common.template_helpers(), **page_context())

    def save_line(lines, line):
        form = request.form
        index = line["index"]
        here = url_for("dbeditor.itemshop_line", index=index)
        action = form.get("action", "")
        items = load_items(rows, [line["vnum"]])
        label = label_of_line(lines, items)
        try:
            if action == "move":
                return move_line(lines, line, form, here)
            if action == "promo":
                return save_promo(line, form, here, label)
            if action == "promo_del" and line["promo"]:
                common.write_rows(PROMO, deletes=[{"item_index": index}], note="ItemShop: koniec promocji",
                                  label_of=label)
                flash("Usunięto promocję.", "success")
                return redirect(here)
            if action == "auction":
                return save_auction(line, form, here, label)
            if action == "auction_del" and line["auction"]:
                batch, _ = common.write_rows(AUCTION, deletes=[{"item_index": index}], note="ItemShop: koniec oferty",
                                             label_of=label)
                if line["auction"]["counter"]:
                    common.write_rows(AUCTION_COUNT, deletes=[{"item_index": index}], note="ItemShop: koniec oferty",
                                      label_of=label, batch=batch, force=True)
                flash("Usunięto ofertę błyskawiczną (pozycja została w sklepie).", "success")
                return redirect(here)
        except Exception as exc:
            flash(f"Nie udało się zapisać: {exc}", "error")
            return redirect(here)
        flash("Nieznana akcja.", "error")
        return redirect(here)

    def save_promo(line, form, here, label):
        index = line["index"]
        price, error = common.validate({"kind": "int", "min": 1, "max": PRICE_MAX}, form.get("promo_price"),
                                       "Cena w promocji")
        start, error2 = parse_time(rows, form.get("promo_start"), "Początek")
        end, error3 = parse_time(rows, form.get("promo_end"), "Koniec")
        errors = [e for e in (error, error2, error3) if e]
        if not errors and end <= start:
            errors.append("Koniec promocji musi być po jej początku.")
        if not errors and price >= line["price"]:
            errors.append(f"Cena w promocji ({price}) powinna być niższa niż zwykła ({line['price']}).")
        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(here)
        new = {"item_index": index, "price": price, "start_time": start, "end_time": end}
        old = dict(line["promo"], item_index=index) if line["promo"] else None
        if old == new:
            flash("Brak zmian do zapisania.", "success")
            return redirect(here)
        common.write_rows(PROMO, inserts=[new], deletes=[{"item_index": index}] if old else [],
                          note="ItemShop: promocja", label_of=label)
        flash(f"Zapisano promocję: {price} {CURRENCY[line['currency']]} zamiast {line['price']}. Gracze widzą ją w "
              "„Polecane”, gdy trwa.", "success")
        return redirect(here)

    def save_auction(line, form, here, label):
        index = line["index"]
        amount, e1 = common.validate({"kind": "int", "min": 1, "max": 2147483647}, form.get("max_amount"),
                                     "Ilość w ofercie")
        limit, e2 = common.validate({"kind": "int", "min": 0, "max": 2147483647}, form.get("account_limit") or "0",
                                    "Limit na konto")
        start, e3 = parse_time(rows, form.get("auction_start"), "Początek")
        end, e4 = parse_time(rows, form.get("auction_end"), "Koniec")
        errors = [e for e in (e1, e2, e3, e4) if e]
        if not errors and end <= start:
            errors.append("Koniec oferty musi być po jej początku.")
        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(here)
        new = {"item_index": index, "max_amount": amount, "account_limit": limit, "start_time": start, "end_time": end}
        old = None
        if line["auction"]:
            old = {k: line["auction"][k] for k in ("max_amount", "account_limit", "start_time", "end_time")}
            old["item_index"] = index
        if old == new and line["auction"]["counter"]:
            flash("Brak zmian do zapisania.", "success")
            return redirect(here)
        batch = None
        if old != new:
            batch, _ = common.write_rows(AUCTION, inserts=[new], deletes=[{"item_index": index}] if old else [],
                                         note="ItemShop: oferta błyskawiczna", label_of=label)
        if not (line["auction"] or {}).get("counter"):
            # the db core does not boot without it (see the module's docstring)
            common.write_rows(AUCTION_COUNT, inserts=[{"item_index": index}], note="ItemShop: oferta błyskawiczna",
                              label_of=label, batch=batch, force=True)
        flash(f"Zapisano ofertę błyskawiczną: {amount} szt.{f', najwyżej {limit} na konto' if limit else ''}. "
              "Gracze widzą ją w „Oferty Błyskawiczne”.", "success")
        return redirect(here)

    def move_line(lines, line, form, here):
        index = line["index"]
        new_tab = form.get("move_tab") or ""
        if new_tab not in TAB_RANGES:
            flash("Wybierz zakładkę.", "error")
            return redirect(here)
        text = (form.get("move_index") or "").strip()
        taken = set(lines)
        if text:
            target, error = common.validate({"kind": "int", "min": 1, "max": INDEX_MAX}, text, "Nowy indeks")
            if error:
                flash(error, "error")
                return redirect(here)
            if not in_tab(new_tab, target):
                flash(f"Indeks {target} nie leży w zakładce „{TAB_TITLES[new_tab]}”.", "error")
                return redirect(here)
            if target in taken:
                flash(f"Indeks {target} jest już zajęty.", "error")
                return redirect(here)
        else:
            target = free_index(new_tab, taken)
            if target is None:
                flash(f"W zakładce „{TAB_TITLES[new_tab]}” nie ma wolnego indeksu.", "error")
                return redirect(here)
        items = load_items(rows, [line["vnum"]])
        name = items.get(line["vnum"], {}).get("name", str(line["vnum"]))
        label = lambda key: f"{name} (poz. {str(key).split(':')[0]})"
        note = f"ItemShop: przeniesienie {index} → {target}"
        row = {"index": target, "vnum": line["vnum"], "count": line["count"], "price": line["price"],
               "currency": MARK if new_tab == MARK_TAB[0] else line["currency"], "minLevel": line["minLevel"],
               "socket0": line["sockets"][0], "socket1": line["sockets"][1], "socket2": line["sockets"][2]}
        batch = remove_lines(lines, [index], label, note=note)
        common.write_rows(ITEMS, inserts=[row], note=note, label_of=label, batch=batch)
        if line["promo"]:
            common.write_rows(PROMO, inserts=[dict(line["promo"], item_index=target)], note=note, label_of=label,
                              batch=batch)
        if line["auction"]:
            auction = {k: line["auction"][k] for k in ("max_amount", "account_limit", "start_time", "end_time")}
            common.write_rows(AUCTION, inserts=[dict(auction, item_index=target)], note=note, label_of=label,
                              batch=batch)
            common.write_rows(AUCTION_COUNT, inserts=[{"item_index": target}], note=note, label_of=label,
                              batch=batch, force=True)
        flash(f"Przeniesiono „{name}” na indeks {target} (zakładka {TAB_TITLES[new_tab]}).", "success")
        return redirect(url_for("dbeditor.itemshop_line", index=target))

    # -------------------------------------------------------------- live reload ---
    @bp.post("/itemshop/odswiez")
    @login_required
    def itemshop_reload():
        back = url_for("dbeditor.itemshop", tab=request.form.get("tab") or None)
        if not common.check_csrf():
            return redirect(back)
        queue = common.ctx().get("queue_gm_command")
        done = False
        if queue is not None:
            try:
                done = queue("ISHOP_RELOAD")
            except Exception as exc:
                flash(f"Nie udało się poprosić gry o odświeżenie: {exc}", "error")
                return redirect(back)
        if done:
            try:
                common.mark_applied_tables(TABLES)
            except Exception:
                pass
            flash("Sklep odświeżony w grze (IMPLEMENTOR w grze wykonał /reload i) – gracze widzą nowe pozycje i ceny.",
                  "success")
        else:
            flash("Żaden IMPLEMENTOR (GM poziomu 5) nie był w grze, żeby wykonać /reload i. Zmiany w ItemShopie "
                  "wejdą po „Zastosuj” (restart gry) albo gdy GM wpisze w grze /reload i.", "warning")
        return redirect(back)

    @bp.route("/itemshop/api/free")
    @login_required
    def itemshop_free():
        tab = request.args.get("tab") or ""
        if tab not in TAB_RANGES:
            return jsonify({"ok": False})
        taken = {_int(r["index"]) for r in rows(f"SELECT `index` FROM {ITEMS}")}
        return jsonify({"ok": True, "index": free_index(tab, taken)})

    dbeditor.add_section("dbeditor.itemshop", "🪙", "ItemShop",
                         "co sprzedaje okno monety w grze: ceny w SM/SZ, ilości, poziom, promocje i oferty "
                         "błyskawiczne – w istniejących zakładkach")
