# -*- coding: utf-8 -*-
# MT2009_PLUS_LANG_V1 - the imported originals of every language: client-patches/lang/<code>/keyed_orig.tsv and
# tm_orig.tsv (langlib.py says how the build uses them). Regenerate after a big content update; never edit the
# *_orig.tsv files by hand (our own texts go to keyed.tsv / tm*.tsv, which win over them).
#
# Sources (the owner allows their reuse):
#   Owsap v6.2.6 client locale/<lang>/ (itemdesc, skilldesc, pet_skill, locale_game / locale_interface and their new_
#   files, description files, guildbuildinglist) and Tools/Dump Proto/share/<lang>/item_names.txt / mob_names.txt -
#   aligned with Owsap's own Polish files by vnum / key: a pair "Owsap Polish -> Owsap <lang>";
#   the upstream release's English layer (x2.2.87 client locale/en next to its locale/pl), English only;
#   our item_proto "name" column where it is plain English (custom items), English only;
#   the T('pl', 'en') pairs of our root python, English only.
# A pair goes to keyed_orig.tsv when OUR Polish text of that vnum / key is the same or close to Owsap's Polish
# (refine "+N" names by their base), to tm_orig.tsv when our client has that exact Polish text anywhere.
# A pair whose <lang> text is just Owsap's English while the Polish one is not (Owsap left it untranslated) is skipped.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/lang/import_originals.py <BASE pack dir> <OUT pack dir> [code ...]
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import langlib as L  # noqa: E402
import build_lang_packs as B  # noqa: E402

OWSAP = '/opt/metin2/cache/owsap/Client/Client/pack/locale/locale/'
OWSAP_NAMES = '/opt/metin2/cache/owsap/Tools/Tools/Dump Proto/share/'
UPSTREAM = '/opt/metin2/cache/tieru-releases/x2.2.87/client_unpacked/locale/locale/'
OWSAP_CP = {'pl': 1250, 'cz': 1250, 'hu': 1250, 'ro': 1250, 'tr': 1254, 'gr': 1253, 'ae': 1256}


def rdtext(path, cp):
    if not os.path.exists(path):
        return None
    return open(path, 'rb').read().decode('cp%d' % cp, 'replace').replace('\r\n', '\n').replace('\r', '\n')


def rows(text):
    return [l.split('\t') for l in text.split('\n')] if text else []


def names(path, cp):
    out = {}
    for c in rows(rdtext(path, cp)):
        if len(c) >= 2 and c[0].strip().isdigit():
            out[int(c[0])] = c[1].strip()
    return out


def kv(text):
    out = {}
    for c in rows(text):
        if len(c) >= 2 and c[0].strip() and not c[0].startswith('#'):
            out[c[0]] = c[1]
    return out


def by_vnum(text, mincols=2):
    out = {}
    for c in rows(text):
        if len(c) >= mincols and c[0].strip().isdigit():
            out[c[0].strip()] = c
    return out


class Side(object):
    """one source language's files (Owsap / upstream layout)"""

    def __init__(self, root, names_root, code, cp):
        self.code = code
        d = root + code + '/'
        self.item = names(names_root + code + '/item_names.txt', cp) if names_root else names(d + 'item_names.txt', cp)
        self.mob = names(names_root + code + '/mob_names.txt', cp) if names_root else names(d + 'mob_names.txt', cp)
        self.idesc = by_vnum(rdtext(d + 'itemdesc.txt', cp) or rdtext(d + 'Itemdesc.txt', cp) or '')
        self.skill = by_vnum(rdtext(d + 'skilldesc.txt', cp) or '', 3)
        self.pet = by_vnum(rdtext(d + 'pet_skill.txt', cp) or '', 3)
        self.gbld = by_vnum(rdtext(d + 'guildbuildinglist.txt', cp) or '', 4)
        self.lgame = kv(rdtext(d + 'locale_game.txt', cp))
        self.lgame.update(kv(rdtext(d + 'new_locale_game.txt', cp)))
        self.lintf = kv(rdtext(d + 'locale_interface.txt', cp))
        self.lintf.update(kv(rdtext(d + 'new_locale_interface.txt', cp)))
        self.files = {}
        for n in L.DESC_FILES:
            t = rdtext(d + n, cp)
            if t:
                self.files[n] = t


def pairs(pl, tr, en=None):
    """aligned (domain, key, Owsap Polish, translation) of two sides"""
    out = []

    def add(dom, key, a, b, e=None):
        if not a or not b or not L.has_text(a) or L.garbled(a) or L.garbled(b, polish=False):
            return
        a2, b2 = a.strip(), b.strip()
        if e is not None and tr.code != 'en' and b2 == e.strip() and a2 != e.strip():
            return  # Owsap kept the English text in this language
        out.append((dom, key, a, b))

    for dom in ('item', 'mob'):
        sp, st = getattr(pl, dom), getattr(tr, dom)
        se = getattr(en, dom) if en else {}
        for v in sp:
            if v in st:
                add(dom, str(v), sp[v], st[v], se.get(v))
    for dom in ('lgame', 'lintf'):
        sp, st = getattr(pl, dom), getattr(tr, dom)
        se = getattr(en, dom) if en else {}
        for k in sp:
            if k in st:
                add(dom, k, sp[k], st[k], se.get(k))
    for v, c in pl.idesc.items():
        t = tr.idesc.get(v)
        e = en.idesc.get(v) if en else None
        if t is None:
            continue
        for i, dom in ((2, 'idesc'), (3, 'isumm'), (1, 'item')):
            if len(c) > i and len(t) > i:
                add(dom, v, c[i], t[i], e[i] if e is not None and len(e) > i else None)
    for dom, src_p, src_t, src_e in (('skill', pl.skill, tr.skill, en.skill if en else {}),
                                     ('pet', pl.pet, tr.pet, en.pet if en else {})):
        for v, c in src_p.items():
            t = src_t.get(v)
            if t is None:
                continue
            e = src_e.get(v)
            for i in range(1, min(len(c), len(t))):
                ok = L.skill_text_col(i, c[i]) if dom == 'skill' else (i in L.PET_TEXT_COLS and L.has_text(c[i]))
                if ok:
                    add(dom, '%s:%d' % (v, i), c[i], t[i], e[i] if e is not None and len(e) > i else None)
    for v, c in pl.gbld.items():
        t = tr.gbld.get(v)
        if t is not None and len(c) > 3 and len(t) > 3:
            add('gbld', v, c[3], t[3])
    for n, txt in pl.files.items():
        if n in tr.files:
            out.append(('file', n, txt, tr.files[n]))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    base, outp = args[:2]
    only = set(args[2:])
    packs = B.Packs(base, outp)
    o_pl = Side(OWSAP, OWSAP_NAMES, 'pl', 1250)
    o_en = Side(OWSAP, OWSAP_NAMES, 'en', 1252)
    enw = set()
    for t in list(o_en.lgame.values()) + list(o_en.lintf.values()) + list(o_en.item.values()) + \
            [c[2] for c in o_en.idesc.values() if len(c) > 2]:
        enw.update(L.words(t))
    cat = B.make_catalog(packs, enw)
    items_en_proto = english_proto_names(packs)
    ours_norm = {}
    for (d, k), t in cat.entries.items():
        ours_norm.setdefault(L.norm_key(t), []).append((d, k))
    for t in cat.py_all:
        ours_norm.setdefault(L.norm_key(t), []).append(('py', None))
    ours_loose = set(k.lower() for k in ours_norm)
    # item / mob base names (refine levels) - an Owsap "Miecz+0" pair teaches "Miecz"
    bases = set()
    for d in ('item', 'mob'):
        for k, t in cat.by_domain(d):
            b, s = L.split_refine(t)
            if s:
                bases.add(L.norm_key(b))
    langs = [c for c, cfg in L.languages()]
    for code in langs:
        if only and code not in only:
            continue
        sides = []
        if os.path.isdir(OWSAP + code):
            sides.append(('owsap', o_pl, Side(OWSAP, OWSAP_NAMES, code, OWSAP_CP.get(code, 1252))))
        if code == 'en' and os.path.isdir(UPSTREAM + 'en'):
            t_pl = Side(UPSTREAM, None, 'pl', 1250)
            t_en = Side(UPSTREAM, None, 'en', 1252)
            # the upstream's item / mob names in English by vnum: their Polish is our item_proto's (same base)
            for v, t in cat.items.items():
                t_pl.item.setdefault(v, t)
            for v, t in cat.mobs.items():
                t_pl.mob.setdefault(v, t)
            sides.append(('upstream', t_pl, t_en))
        keyed, tmc = {}, collections.defaultdict(collections.Counter)
        stats = collections.Counter()
        for src, sp, st in sides:
            for dom, key, a, b in pairs(sp, st, o_en if src == 'owsap' and code != 'en' else None):
                b_clean = b.strip() if dom != 'file' else b
                if L.FORBIDDEN.search(b_clean):
                    stats['forbidden'] += 1
                    continue
                if not L.same_placeholders(a, b_clean):
                    stats['placeholders'] += 1
                    continue
                # keyed: our text of that domain / key is the same or close
                ok = (dom, key) in cat.entries
                if ok:
                    ours = cat.entries[(dom, key)]
                    if dom in ('item', 'mob'):
                        ob, os_ = L.split_refine(ours)
                        ab, as_ = L.split_refine(a)
                        close = L.similar(ob, ab, 0.6) and os_.replace(' ', '') == as_.replace(' ', '')
                    elif dom == 'file':
                        close = L.similar(ours, a, 0.5)
                    else:
                        close = L.similar(ours, a, 0.85)
                    if close and (dom, key) not in keyed:
                        keyed[(dom, key)] = (ours, b_clean)
                        stats['keyed_' + src] += 1
                # tm: our client has this exact Polish text somewhere (or it is a refine base name)
                nk = L.norm_key(a)
                if dom != 'file' and (nk in ours_norm or nk.lower() in ours_loose):
                    tmc[nk][b_clean] += 1
                if dom in ('item', 'mob'):
                    ab, as_ = L.split_refine(a)
                    bb, bs = L.split_refine(b_clean)
                    if as_ and bs and L.norm_key(ab) in bases:
                        tmc[L.norm_key(ab)][bb.strip()] += 1
        if code == 'en':
            for v, en_name in items_en_proto.items():
                if ('item', str(v)) not in keyed and ('item', str(v)) in cat.entries:
                    keyed[('item', str(v))] = (cat.items[v], en_name)
                    stats['keyed_proto_name'] += 1
            for mod, b in B.root_python(packs).items():
                for pl, en_ in L.t_pairs(b):
                    if L.same_placeholders(pl, en_):
                        tmc[L.norm_key(pl)][en_] += 3
                        stats['tpairs'] += 1
        tm = sorted((k, c.most_common(1)[0][0]) for k, c in tmc.items())
        d = os.path.join(L.LANG_DIR, code)
        L.write_rows(os.path.join(d, 'keyed_orig.tsv'),
                     [[dm, k, s, t] for (dm, k), (s, t) in sorted(keyed.items(), key=lambda x: (x[0][0], _nk(x[0][1])))],
                     'GENERATED by tools/lang/import_originals.py - do not edit (our own texts: keyed.tsv)\n'
                     'domain\tkey\tour Polish text\toriginal translation')
        L.write_rows(os.path.join(d, 'tm_orig.tsv'), [[k, t] for k, t in tm],
                     'GENERATED by tools/lang/import_originals.py - do not edit (our own texts: tm.tsv)\n'
                     'Polish text\toriginal translation')
        print(code, dict(stats), 'keyed', len(keyed), 'tm', len(tm))


def _nk(k):
    m = re.match(r'^(\d+)(.*)$', k)
    return (0, int(m.group(1)), m.group(2)) if m else (1, 0, k)


def english_proto_names(packs):
    """vnum -> English name of our item_proto's "name" column where it is plain English (custom items)"""
    import struct
    import m2pack
    out = {}
    b = packs.get('gamedata/item_proto', prefer='dbdata')
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    raw = m2pack.mcoz_decode(b[20:], B.ITEM_KEY)
    for i in range(cnt):
        r = raw[i * stride:(i + 1) * stride]
        v = struct.unpack_from('<I', r, 0)[0]
        nb = r[8:41].split(b'\0')[0]
        lb = r[41:74].split(b'\0')[0]
        if not nb or nb == lb or any(c > 126 or c < 32 for c in nb):
            continue
        n = nb.decode('ascii')
        if not re.search(r'[a-z]{2}', n) or re.match(r'^[a-z0-9_]+$', n):
            continue
        ws = L.words(n)
        if ws and sum(1 for w in ws if w in L.EN_WORDS) * 2 >= len(ws):
            out[v] = n
    return out


if __name__ == '__main__':
    main()
