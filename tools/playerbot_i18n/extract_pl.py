#!/usr/bin/env python3
"""Collect the Polish lines the bots can say, for the translation catalogs.

Scans the playerbot overlay's C++ sources, joins adjacent string literals,
decodes them (the sources are CP1250 / ASCII with \\xNN escapes) and keeps the
ones that read like speech. printf specs become {1}..{n} in order, $NAME
placeholders stay as they are - both are slots to the runtime matcher
(playerbot_i18n.h).

    extract_pl.py [--src DIR] [--out FILE]

The output (UTF-8 TSV: pl text, the files it is in) is the key list every
chat_<lang>.tsv is checked against by check_catalog.py.
"""
import argparse, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC = os.path.join(ROOT, 'linux-port/overlays/playerbot/src/game/src')
OUT = os.path.join(ROOT, 'linux-port/docker/game/playerbot_i18n/catalog_pl.tsv')

# Files with no bot speech in them (protocol, tables, logs only) or not the
# bots' (engine systems the quest/server translation covers).
SKIP_FILES = {
    'json.hpp', 'playerbot_shop_names.h', 'playerbot_price_tables.h',
    'playerbot_ishop3_catalogue_data.h', 'playerbot_monster_card_data.h',
    'playerbot_relikty_table.h', 'playerbot_conv_text.h', 'playerbot_conv_lexicon.h',
    'playerbot_conv_aliases.h', 'mt2009_language.cpp', 'mt2009_language.h', 'playerbot_i18n.h',
    # the over-head status tail: its own pl/en pair (PBT), drawn by the client
    'playerbot_status.h', 'playerbot_config.h',
}
# Player systems that live in the overlay but are not bot talk: their notices
# are the server's own texts (the quest/server translation), not a bot's line.
SKIP_PREFIX = (
    'growth_pet', 'balathor', 'weapon_element', 'remote_call', 'guildsys', 'dr_farm_session', 'fish_',
    'konie_', 'auction_house', 'irremovable', 'npc_location_helper', 'ikashop_qol', 'mt2009_',
    'playerbot_relikty', 'playerbot_titles', 'playerbot_addeq', 'playerbot_changelook', 'playerbot_ekwipunek',
    'playerbot_aura', 'playerbot_skillcolor', 'playerbot_hidecostume', 'playerbot_skillhack',
    'playerbot_collector', 'playerbot_element_stones', 'playerbot_bonus67', 'playerbot_skill9',
    'playerbot_arrange', 'playerbot_riposty', 'playerbot_switchbot', 'playerbot_yohara_gear',
    'playerbot_zodiac_ext', 'playerbot_zodiac_char', 'playerbot_zodiac_questlua', 'playerbot_zodiac_temple',
    'playerbot_champion', 'playerbot_ship_defense', 'playerbot_community', 'playerbot_mlodzi',
    'playerbot_dungeon_panel', 'playerbot_wheel', 'playerbot_rank_points', 'playerbot_weekly_rank',
    'playerbot_battlepass', 'playerbot_voucher', 'playerbot_catchking', 'playerbot_yutnori', 'playerbot_rumi',
    'playerbot_flower', 'playerbot_seonhae', 'playerbot_monster_card', 'playerbot_dungeon_reset',
    'playerbot_digi_qol', 'playerbot_newpet', 'playerbot_ingame_events', 'playerbot_worldboss',
    'playerbot_buffi', 'playerbot_events.h', 'playerbot_catacomb', 'playerbot_minigames',
)
# A line with one of these is a log, a query, a path or a command - never speech.
SKIP_LINE = re.compile(
    r'sys_err|sys_log|SELECT |INSERT |UPDATE |DELETE |REPLACE INTO|DirectQuery|AsyncQuery|ReturnQuery|'
    r'fprintf|#\s*include|#\s*define|_FILE\b|_PATH\b|Query\(|LogPlayer|__FILE__|cmdchat|ChatPacket\(CHAT_TYPE_COMMAND|'
    r'strcmp|strncmp|strcasecmp|strncasecmp|StartsWith|Has\(|Find\(|find\(|IsWord|HasWord|Contains|Matches|'
    r'PlayerBotWeightNameEquals|getenv|fopen|sscanf|\.Log\(|DebugLog')
LIT = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
PRINTF = re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?(?:hh|h|ll|l|z|L)?[sdiufxXcgeE])')
WORD = re.compile(r'[A-Za-zÀ-ſ]{2,}')


def strip_comments(text):
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == '"' or c == "'":
            q = c; j = i + 1
            while j < n and text[j] != q:
                if text[j] == '\\':
                    j += 1
                if text[j] == '\n':
                    break
                j += 1
            out.append(text[i:j + 1]); i = j + 1
        elif text.startswith('//', i):
            j = text.find('\n', i); j = n if j < 0 else j
            i = j
        elif text.startswith('/*', i):
            j = text.find('*/', i + 2); j = n if j < 0 else j + 2
            out.append('\n' * text.count('\n', i, j)); i = j
        else:
            out.append(c); i += 1
    return ''.join(out)


def decode(lit):
    b = bytearray(); i = 0
    raw = lit.encode('latin-1')
    while i < len(raw):
        c = raw[i]
        if c == 0x5c and i + 1 < len(raw):
            d = chr(raw[i + 1])
            if d == 'x':
                m = re.match(rb'[0-9a-fA-F]{1,2}', raw[i + 2:i + 4])
                b.append(int(m.group(0), 16)); i += 2 + len(m.group(0)); continue
            b.extend({'n': b'\n', 't': b'\t', '"': b'"', '\\': b'\\', "'": b"'", '0': b''}.get(d, d.encode()))
            i += 2; continue
        b.append(c); i += 1
    return bytes(b).decode('cp1250', 'replace')


def to_key(s):
    n = [0]
    def rep(m):
        if m.group(0) == '%%':
            return '%'
        n[0] += 1
        return '{%d}' % n[0]
    return PRINTF.sub(rep, s)


def speechlike(s):
    if '\n' in s or '\t' in s or '`' in s or ('|' in s and '|h' not in s and ' | ' not in s):
        return False
    words = WORD.findall(s)
    tokens = re.findall(r'[A-Za-z\u00c0-\u017f]+', s)
    # "w Joan", "do Joan": a preposition and a name are a phrase too.
    if len(words) < 2 and not (len(tokens) >= 2 and words) and \
            not (len(words) == 1 and len(s) >= 3 and s[0].isupper() and s.rstrip()[-1:] in '!?.'):
        return False
    if re.fullmatch(r'[A-Z0-9_ ]+', s):          # MACRO_LIKE
        return False
    if re.search(r'[a-z]_[a-z]|\w=\S|=%|\.(txt|tsv|py|lua|sql|cpp|h)\b|^/|::', s):
        return False
    return True


def collect(src):
    found = collections.OrderedDict()
    for f in sorted(os.listdir(src)):
        if not f.endswith(('.h', '.cpp')) or f in SKIP_FILES or f.startswith(SKIP_PREFIX):
            continue
        raw = open(os.path.join(src, f), 'rb').read()
        try:
            raw.decode('ascii')
            enc = 'ascii'
        except UnicodeDecodeError:
            try:
                raw.decode('utf-8'); enc = 'utf-8'
            except UnicodeDecodeError:
                enc = 'cp1250'
        if enc == 'utf-8':
            # Re-encode to CP1250 so decode() below reads every file alike.
            raw = raw.decode('utf-8').encode('cp1250', 'replace')
        text = strip_comments(raw.decode('latin-1'))
        # Join adjacent literals ("a" "b") across whitespace and newlines.
        text = re.sub(r'"\s*\n\s*"', '', text)
        text = re.sub(r'"[ \t]+"', '', text)
        for line in text.split('\n'):
            if SKIP_LINE.search(line):
                continue
            for m in LIT.finditer(line):
                s = decode(m.group(1))
                if not speechlike(s):
                    continue
                k = to_key(s).strip()
                found.setdefault(k, set()).add(f)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=SRC)
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    found = collect(a.src)
    manual = os.path.join(HERE, 'manual_pl.tsv')
    for line in open(manual, encoding='utf-8'):
        if line.startswith('#') or '\t' not in line:
            continue
        found.setdefault(line.split('\t')[0], set()).add('manual_pl.tsv')
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, 'w', encoding='utf-8', newline='\n') as fp:
        fp.write('# pl\tfiles - generated by tools/playerbot_i18n/extract_pl.py, do not edit\n')
        for k, fs in found.items():
            fp.write('%s\t%s\n' % (k, ','.join(sorted(fs))))
    print('%d lines -> %s' % (len(found), a.out))


if __name__ == '__main__':
    main()
