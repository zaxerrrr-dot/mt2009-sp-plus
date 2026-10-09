# =============================================================================
#  Podgląd rynku - wersja eksperymentalna (MT2009_PLUS_MARKET_PREVIEW_V1).
#
#  Every offer of the offline shops (IkarusShop stalls) of all kingdoms - the
#  bots' and the players' - with categories, filters, price bargains, the
#  bonus label, a week's price chart and a teleport of the operator's own
#  character to the stall. Installed from app.py like the database editor:
#
#      market_preview.install(app, {...the panel's helpers...})
#
#      GET /economy/market              the page (login_required)
#      GET /economy/market/api/offers   a page of offers, the counts, the chart
#
#  The teleport is the panel's own POST /api/admin/teleport-me with the
#  stall's x, y and channel (web_admin.quest WARP), the same one-click move
#  the bot card's "Zobacz sklepik" uses. rules.py is what a request means,
#  snapshot.py the data, sheet.py the bots' price list (gen_sheet.py).
# =============================================================================

import json
import re
import threading
import time

from . import rules, snapshot

_state = {"ns": None, "store": None, "limiter": rules.RateLimiter(), "lock": threading.Lock()}

# The stalls' maps by name (the villages); any other by its number.
MAP_NAMES = {1: "Yongan", 21: "Joan", 41: "Pyongmoo", 3: "Jayang", 23: "Bokjung", 43: "Bakra"}
EMPIRE_NAMES = ("Shinsoo", "Chunjo", "Jinno")
EMPIRE_FLAGS = ("shinsoo.png", "chunjo.png", "jinno.png")

TEXTS = {
    "offers_n": "{n} ofert",
    "data_from": "Dane z: {t}",
    "building": "Buduję migawkę rynku – to potrwa kilkanaście sekund…",
    "cat_all": "Wszystko",
    "bad_value": "Błędna wartość – filtr nie jest wysyłany.",
    "only_shop": "Tylko sklep: {name}",
    "only_item": "Tylko przedmiot: {name}",
    "remove": "usuń",
    "from_level": "od {n} lv",
    "bonuses_n": "{n} bonusów",
    "bonuses_1": "1 bonus",
    "bonuses_few": "{n} bonusy",
    "pve_pvp": "PvE {a} / PvP {b}",
    "avg": "ŚR",
    "skl": "UM",
    "stones": "Kamienie duszy",
    "stones_n": "KD: {n}",
    "yang": "yang",
    "per_unit": "{p} yang / szt.",
    "deal": "Okazja: {n}% taniej",
    "rare": "Rzadkie",
    "rare_title": "Rzadkie: {n} szt. na wszystkich otwartych sklepach (mniej niż 10)",
    "icon_none": "Brak ikony",
    "deal_suspect": "Bardzo nisko – możliwy błąd ceny albo słaby przedmiot.",
    "ref_price": "Zwykła cena: {p} yang / szt.",
    "deal_help": "Skąd ta okazja?",
    "deal_box_offer": "Cena tej oferty: {p}",
    "deal_box_usual": "Zwykła cena: {p}",
    "deal_how_sheet": "Liczona z cennika botów × bonusy przedmiotu × przelicznik yang z rat serwera "
                      "(za mało ofert tego przedmiotu z ostatnich 7 dni).",
    "deal_how_week": "Mediana ofert tego przedmiotu z ostatnich 7 dni × bonusy przedmiotu.",
    "deal_box_rule": "Okazja = oferta tańsza o co najmniej {n}% od zwykłej ceny.",
    "dearer": "{n}% drożej niż zwykle",
    "shop_closed": "sklep zamknięty",
    "slip": "podejrzana cena",
    "tp": "⚡ TP",
    "tp_title": "Teleportuj moją postać w grze do tego sklepu",
    "compare_pick": "Zaznacz do porównania",
    "seller_title": "Pokaż cały towar tego sklepu",
    "item_title": "Pokaż wszystkie oferty tego przedmiotu i wykres ceny",
    "map_ch": "{map} · CH{ch}",
    "map_n": "Mapa {n}",
    "tt_level": "Wymagany poziom: {n}",
    "tt_classes": "Klasa: {c}",
    "empty": "Brak ofert dla tych filtrów",
    "load_error": "Nie udało się wczytać ofert. Spróbuj ponownie.",
    "retry": "Spróbuj ponownie",
    "too_fast": "Za dużo zapytań naraz – chwila przerwy.",
    "login": "Sesja panelu wygasła – zaloguj się ponownie.",
    "page_prev": "‹ Poprzednia",
    "page_next": "Następna ›",
    "page_of": "Strona {a} z {b}",
    "per_page": "Na stronie",
    "chart_title": "Cena za sztukę z ostatnich 7 dni (mediana godziny)",
    "chart_none": "Za mało historii na wykres – panel zbiera ceny od pierwszego otwarcia tej karty.",
    "compare": "Porównaj ({n})",
    "compare_max": "Porównać można do 4 ofert.",
    "c_plus": "Ulepszenie",
    "c_level": "Poziom",
    "c_bonuses": "Bonusy",
    "c_price": "Cena",
    "c_deal": "Okazja",
    "c_seller": "Sprzedawca",
    "clear_filters": "Wyczyść filtry",
    "f_bonus_none": "— bonus —",
    "f_bonus_min": "min.",
    "tp_sending": "⏳ Teleportowanie Twojej postaci w grze…",
    "tp_done": "✅ Przeteleportowano {name} do sklepu {shop} (CH{ch}).",
    "tp_offline": "⛔ Żadna Twoja postać nie jest teraz zalogowana w grze.",
    "tp_failed": "⛔ Nie udało się ({why}).",
    "tp_net": "⛔ Błąd sieci.",
}


def ns():
    return _state["ns"]


def store():
    return _state["store"]


def say(key, **fields):
    text = TEXTS[key]
    for name, value in fields.items():
        text = text.replace("{" + name + "}", str(value))
    return text


def _json(payload, status=200):
    from flask import Response
    return Response(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), status=status,
                    mimetype="application/json")


def _gate():
    """None when the request may go on; the JSON answer that refuses it."""
    from flask import request, session
    key = session.get("seban_update_csrf") or request.remote_addr or "?"
    with _state["lock"]:                            # gunicorn's threads share it
        allowed = _state["limiter"].allow(key)
    if not allowed:
        return _json({"ok": False, "error": "rate", "message": say("too_fast")}, 429)
    return None


# -----------------------------------------------------------------------------
#  What an offer row says
# -----------------------------------------------------------------------------
_PLACEHOLDER = re.compile(r"\s*[:+]?\s*[+-]?%[-+ ]?\d*(?:\.\d+)?[df](?:%%)?")


def _apply_entry(point):
    panel = ns()
    key = int(point or 0)
    if panel.get("engine_mt2009", True):
        key = panel["point_to_apply"].get(key, key)
    return panel["apply_labels"].get(key)


def apply_label(point, value=None):
    """A bonus line as the panel writes it elsewhere ("Silny przeciw
    zwierzętom +20%"); the line's name alone when `value` is None."""
    entry = _apply_entry(point)
    if not entry:
        row = rules.sheet.BONUS_TIERS.get(int(point or 0))
        name = row[4] if row else "Bonus #%d" % int(point or 0)
        return name if value is None else "%s %+d" % (name, int(value))
    name, suffix = entry
    return name if value is None else "%s %+d%s" % (name, int(value), suffix)


def _base_lines(proto):
    """A piece's own lines for the tooltip: attack, defence, the proto's applies."""
    if proto is None:
        return []
    v = proto.values
    out = []
    if proto.type == rules.ITEM_WEAPON:
        if v[3] or v[4]:
            out.append("Wartość ataku: %d - %d" % (v[3] + v[5], v[4] + v[5]))
        if v[1] or v[2]:
            out.append("Wartość ataku magicznego: %d - %d" % (v[1] + v[5], v[2] + v[5]))
        if v[0] > 0:
            out.append("Szybkość ataku: +%d%%" % v[0])
    elif proto.type == rules.ITEM_ARMOR:
        defence = {0: v[1] + v[5] * 2, 1: v[1] + v[5], 2: v[1] + v[5] * 2, 4: v[1] + v[5]}.get(proto.subtype, 0)
        if defence > 0:
            out.append("Obrona: %d" % defence)
    for point, value in proto.applies:
        if point and value:
            out.append(apply_label(point, value))
    return out


def _icon(vnum):
    try:
        return ns()["item_icon_url"](vnum) or ""
    except Exception:                                # noqa: BLE001 - no icon is the grey "?"
        return ""


def _flag_url(emp):
    from flask import url_for
    if 1 <= int(emp or 0) <= 3:
        return url_for("static", filename="empires/" + EMPIRE_FLAGS[int(emp) - 1])
    return ""


def render_row(snap, row):
    proto = snap.protos.get(row["vnum"])
    name, plus = rules.split_plus(snap.names.get((row["vnum"], row["var"])) or (proto.name if proto else ""))
    plus = row["plus"] if row["plus"] >= 0 else plus
    shop = snap.shops.get(row["owner"], {})
    classes = [i for i, bit in enumerate(rules.CLASS_BITS) if row["cls"] & bit]
    bonuses = []
    for k in range(7):
        point, value = row["a%d" % k], row["v%d" % k]
        if not point or not value or point in snapshot.DAMAGE_POINTS:
            continue
        pve, pvp = rules.tier_pair(point)
        bonuses.append({"p": point, "v": value, "t": apply_label(point, value),
                        "max": rules.is_max_line(point, value, snap.tops), "pve": pve, "pvp": pvp})
    stones = [{"v": s, "n": snap.names.get((s, 0)) or (snap.protos[s].name if s in snap.protos else "#%d" % s)}
              for s in (row["s0"], row["s1"], row["s2"]) if s]
    deal = row["bkey"] if row["bkey"] > rules.NO_REFERENCE_KEY else None
    map_name = MAP_NAMES.get(shop.get("map", 0)) or say("map_n", n=shop.get("map", 0))
    return {
        "id": row["id"], "vnum": row["vnum"], "var": row["var"], "name": name, "plus": plus,
        "cnt": row["cnt"], "price": row["price"], "unit": round(row["unit"], 2), "lvl": row["lvl"],
        "classes": classes, "cls_all": row["cls"] == rules.ALL_CLASSES, "owner": row["owner"],
        "seller": shop.get("seller") or "", "bot": bool(row["bot"]), "emp": row["emp"], "flag": _flag_url(row["emp"]),
        "shop_name": shop.get("name") or "", "ch": row["ch"], "map": row["map"],
        "x": shop.get("x", 0), "y": shop.get("y", 0),
        "where": say("map_ch", map=map_name, ch=row["ch"]), "running": bool(row["running"]),
        "ref": round(row["ref"] or 0), "deal": deal, "slip": bool(row["slip"]), "rsrc": int(row["rsrc"] or 0),
        "rare": bool(row["rare"]), "rcnt": int(row["rcnt"] or 0), "icon": _icon(row["vnum"]),
        "bonuses": bonuses, "avg": row["avg"], "skl": row["skl"], "stones": stones,
        "base": _base_lines(proto),
    }


def _counts_json(counts):
    out = {"all": sum(counts.values()), "cats": {}}
    for key, cid, _name, subs in rules.CATEGORIES:
        entry = {"n": sum(n for (c, _s), n in counts.items() if c == cid), "subs": {}}
        for skey, sid, _sname in subs:
            entry["subs"][skey] = counts.get((cid, sid), 0)
        out["cats"][key] = entry
    return out


# -----------------------------------------------------------------------------
#  Routes
# -----------------------------------------------------------------------------
def _page():
    from flask import render_template, url_for
    st = store()
    st.viewed()
    st.start()
    snap = st.current
    bonus_points = snap.bonus_points if snap else tuple(sorted(rules.sheet.BONUS_TIERS))
    bonuses = sorted(({"p": p, "t": apply_label(p)} for p in bonus_points), key=lambda b: rules.normalize(b["t"]))
    stones = [{"v": v, "n": snap.names.get((v, 0)) or (snap.protos[v].name if v in snap.protos else "#%d" % v)}
              for v in (snap.stones if snap else ())]
    data = {
        "texts": TEXTS, "defaults": rules.DEFAULTS, "bonuses": bonuses,
        "deal_badge": rules.DEAL_BADGE_PCT, "deal_suspect": rules.DEAL_SUSPECT_PCT,
        "classes": list(rules.CLASS_NAMES), "empires": list(EMPIRE_NAMES),
        "categories": [{"key": key, "name": name, "subs": [{"key": sk, "name": sn} for sk, _sid, sn in subs]}
                       for key, _cid, name, subs in rules.CATEGORIES],
        "api": url_for("market_api_offers"), "teleport": url_for("api_admin_teleport_me"),
        "player": url_for("player", pid=0).rsplit("/", 1)[0] + "/",
    }
    return render_template("market_preview.html", data=data, sorts=rules.SORT_NAMES, class_keys=rules.CLASS_KEYS,
                           class_names=rules.CLASS_NAMES, empires=EMPIRE_NAMES, stones=stones)


def _api_offers():
    from flask import request
    refused = _gate()
    if refused is not None:
        return refused
    started = time.time()
    st = store()
    st.viewed()
    st.start()
    if request.args.get("refresh") == "1":
        st.request_refresh()
    snap = st.current
    if snap is None:
        st.request_refresh()
        return _json({"ok": True, "generated_at": 0, "building": True, "error": st.last_error, "rows": [],
                      "total": 0, "counts": None, "page": 1, "pages": 1, "per": rules.DEFAULT_PER, "errors": {}})
    f, errors = rules.parse_filters(request.args, snap.bonus_points)
    rows, total, counts, page_no, pages = snap.page(f)
    out = {
        "ok": True, "generated_at": int(snap.generated_at),
        "generated_text": time.strftime("%H:%M:%S", time.localtime(snap.generated_at)),
        "building": st.building, "error": st.last_error, "total": total, "page": page_no, "pages": pages,
        "per": f["per"], "counts": _counts_json(counts), "errors": errors,
        "rows": [render_row(snap, r) for r in rows],
    }
    if "shop" in f:
        shop = snap.shops.get(f["shop"], {})
        out["shop"] = {"label": "%s · %s" % (shop.get("seller") or "#%d" % f["shop"], shop.get("name") or "")}
    if "vnum" in f:
        var = f.get("var", 0)
        name = snap.names.get((f["vnum"], var)) or (snap.protos[f["vnum"]].name if f["vnum"] in snap.protos else
                                                     "#%d" % f["vnum"])
        out["item"] = name
        proto = snap.protos.get(f["vnum"])
        plus = proto.plus if proto is not None else rules.split_plus(name)[1]
        try:
            points = st.history.chart(f["vnum"], plus, var)
        except Exception:                            # noqa: BLE001
            points = []
        out["chart"] = {"name": name, "points": [[t, round(m, 2), round(lo, 2), n] for t, m, lo, n in points]}
    out["ms"] = int((time.time() - started) * 1000)
    return _json(out)


def install(app, helpers):
    """Called once from app.py. `helpers`: db, login_required, item_icon_url,
    apply_labels, point_to_apply, engine_mt2009, read_rates, spool,
    item_name(vnum, socket0, base_name)."""
    if _state["ns"] is not None:
        raise RuntimeError("market preview already installed")
    _state["ns"] = helpers

    def yang_rate():
        return int(helpers["read_rates"]().get("yang", 100) or 100)

    def names(proto, vnum, socket0):
        base = proto.name if proto is not None else "#%d" % vnum
        try:
            return helpers["item_name"](vnum, socket0, base)
        except Exception:                            # noqa: BLE001
            return base

    _state["store"] = snapshot.Store(snapshot.DbSource(helpers["db"], yang_rate),
                                     snapshot.default_history_path(helpers["spool"]), names=names,
                                     logger=app.logger)
    login_required = helpers["login_required"]
    app.add_url_rule("/economy/market", "market_preview", login_required(_page), methods=["GET"])
    app.add_url_rule("/economy/market/api/offers", "market_api_offers", login_required(_api_offers),
                     methods=["GET"])
    return app
