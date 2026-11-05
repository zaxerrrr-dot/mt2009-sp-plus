#!/usr/bin/env python3
"""extract_server_texts.py - the Polish texts of OUR server code that the hand dictionaries translate
(MT2009_PLUS_LANGUAGE_V1, server-patches/language/README.md).

  quest   every string literal of our quests and quest libraries that reads as text (linux-port/docker/game/**/*.quest,
          *.lua, files/*.quest) -> tools/i18n/data/quest_custom_pl.tsv
  server  the texts our engine code says to a player: the literals of ChatPacket(CHAT_TYPE_INFO / NOTICE /
          BIG_NOTICE / TALKING ...), SendNotice, BroadcastNotice, SendNoticeMap calls of the overlay
          (linux-port/overlays/playerbot/src/game/src) and of the server patches' new code (server-patches/*/edits.json)
          -> tools/i18n/data/server_custom_pl.tsv

Each output line: Polish<TAB>where (file:line, the first few). The stock texts (share translate.lua, locale_string.txt)
are build_server_lang.py's. A literal that is only a piece of a concatenation ("Koszt: " .. n) cannot be found again
at runtime; those are listed in tools/i18n/data/quest_concat_pl.tsv to be rewritten as string.format.
--check <lang>: the texts of the lists the language's hand files (30_quest_custom.tsv, 40_server_custom.tsv) lack.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GAME = os.path.join(REPO, "linux-port", "docker", "game")
DATA = os.path.join(HERE, "data")
LANG = os.path.join(GAME, "lang")

# Not texts: identifiers, flags, paths, SQL, tags.
SKIP_CALLS = {"sys_log", "sys_err", "pc.getqf", "pc.setqf", "pc.getf", "pc.setf", "game.get_event_flag",
              "game.set_event_flag", "getf", "setf", "pc.delqf", "cmdchat", "dofile", "mysql_direct_query",
              "mysql_query", "string.find", "string.gsub", "string.gfind", "string.match", "pc.get_special_flag",
              "pc.set_special_flag", "set_quest_state", "q.getcurrentquestindex", "pc.setqf2", "pc.getqf2",
              "affect.add_collect", "require", "loadfile", "pcall", "raw_script", "setbgimage", "addimage",
              "pc.give_item2_select", "d.setf", "d.getf", "d.set_regen_file", "d.regen_file", "d.spawn_group",
              "d.set_unique", "d.unique_set_maxhp", "d.unique_get_hp_perc", "d.is_unique_dead", "d.kill_unique",
              "d.purge_unique", "d.setqf2", "d.getqf2", "server_timer", "server_loop_timer", "timer", "loop_timer",
              "cleartimer", "clear_server_timer", "game.drop_item_with_ownership", "npc.get_race", "d.new_jump_party",
              "d.new_jump_all", "d.new_jump", "d.join", "string.len", "split", "tonumber", "print", "error"}

TEXTY = re.compile(r"[A-Za-z\u0080-\uffff]{2}")


def is_text(s):
    t = s.strip()
    if len(t) < 2 or not TEXTY.search(t):
        return False
    if re.match(r"^\[[A-Z_]+[^\]]*\]$", t):		# [ENTER], [DELAY ...]
        return False
    if re.match(r"^[a-z0-9_.]+$", t):			# flags, keys, actions
        return False
    if re.match(r"^[A-Za-z0-9_]+$", t) and "_" in t:	# CONSTANT_NAMES, flag_names
        return False
    if re.match(r"^[\w./\\-]+\.(lua|txt|quest|tga|dds|png|mse|msm|py|sub)$", t, re.I):
        return False
    if re.match(r"^(SELECT|INSERT|UPDATE|DELETE|REPLACE|CREATE|ALTER)\b", t):
        return False
    if t.startswith("/") and " " not in t:			# a chat command
        return False
    if re.search(r"(=\s*'|\b(AND|WHERE|FROM|LIMIT|VALUES)\b)", t):	# SQL
        return False
    return True


def lua_strings(src):
    """(text, line, call, concat) of every string literal of a Lua / quest source."""
    out = []
    i, n, line = 0, len(src), 1
    tokens = []		# (kind, value, line) - kind: s (string), n (name), o (operator)
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if src.startswith("--[[", i):
            j = src.find("]]", i + 4)
            j = n if j < 0 else j + 2
            line += src.count("\n", i, j)
            i = j
            continue
        if src.startswith("--", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("[[", i):
            j = src.find("]]", i + 2)
            j = n if j < 0 else j + 2
            tokens.append(("s", src[i + 2:j - 2], line))
            line += src.count("\n", i, j)
            i = j
            continue
        if c in "\"'":
            j = i + 1
            buf = []
            while j < n and src[j] != c and src[j] != "\n":
                if src[j] == "\\" and j + 1 < n:
                    e = src[j + 1]
                    if e == "n":
                        buf.append("\n")
                        j += 2
                    elif e == "t":
                        buf.append("\t")
                        j += 2
                    elif e.isdigit():
                        m = re.match(r"\d{1,3}", src[j + 1:])
                        buf.append(bytes([int(m.group(0)) & 0xFF]).decode("cp1250", errors="replace"))
                        j += 1 + len(m.group(0))
                    else:
                        buf.append(e)
                        j += 2
                    continue
                buf.append(src[j])
                j += 1
            tokens.append(("s", "".join(buf), line))
            i = j + 1
            continue
        m = re.match(r"(?:0x[0-9a-fA-F]+|\d+(?:\.\d+)?)", src[i:])
        if m:
            tokens.append(("d", m.group(0), line))
            i += len(m.group(0))
            continue
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*(?:\s*[.:]\s*[A-Za-z_][A-Za-z0-9_]*)*", src[i:])
        if m:
            tokens.append(("n", re.sub(r"\s+", "", m.group(0)), line))
            i += len(m.group(0))
            continue
        if src.startswith("..", i):
            tokens.append(("o", "..", line))
            i += 2
            continue
        if not c.isspace():
            tokens.append(("o", c, line))
        i += 1
    # The call each string is an argument of: the name before the nearest unclosed '('.
    stack = []
    calls = []
    for k, (kind, val, ln) in enumerate(tokens):
        calls.append(stack[-1] if stack else "")
        if kind == "o" and val == "(":
            prev = tokens[k - 1] if k else None
            stack.append(prev[1] if prev and prev[0] == "n" else "")
        elif kind == "o" and val == ")":
            if stack:
                stack.pop()
        elif kind == "s":
            concat = (k > 0 and tokens[k - 1][1] == "..") or (k + 1 < len(tokens) and tokens[k + 1][1] == "..")
            out.append((val, ln, stack[-1] if stack else "", concat))
    lua_strings.templates = concat_templates(tokens, calls)
    return out


KEYWORDS = {"and", "or", "not", "then", "do", "end", "return", "local", "if", "elseif", "else", "function", "while",
            "for", "in", "repeat", "until", "begin", "when", "with", "break"}


def _match(tokens, i, open_, close):
    depth = 0
    while i < len(tokens):
        v = tokens[i][1] if tokens[i][0] == "o" else None
        if v == open_:
            depth += 1
        elif v == close:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(tokens) - 1


def _operand(tokens, i):
    """The end (exclusive) of the operand starting at i (arithmetic included, '..' not), or -1."""
    n = len(tokens)
    while i < n and ((tokens[i][0] == "o" and tokens[i][1] in ("-", "#")) or (tokens[i][0] == "n" and tokens[i][1] == "not")):
        i += 1
    if i >= n:
        return -1
    kind, val = tokens[i][0], tokens[i][1]
    if kind in ("s", "d") or (kind == "n" and val not in KEYWORDS):
        i += 1
    elif kind == "o" and val == "(":
        i = _match(tokens, i, "(", ")") + 1
    elif kind == "o" and val == "{":
        i = _match(tokens, i, "{", "}") + 1
    else:
        return -1
    while i < n and tokens[i][0] == "o" and tokens[i][1] in ("(", "["):
        i = _match(tokens, i, tokens[i][1], ")" if tokens[i][1] == "(" else "]") + 1
    while i < n and tokens[i][0] == "o" and tokens[i][1] in ("+", "-", "*", "/", "%", "^"):
        j = _operand(tokens, i + 1)
        if j < 0:
            return -1
        i = j
    return i


def concat_templates(tokens, calls):
    """(template, line, call) of every concatenation with a text literal: the literals as they are (% as %%), every
    other operand %s - "Za "..n.." sekund." is "Za %s sekund." - the runtime finds the glued line by it."""
    out = []
    used = set()
    for k, t in enumerate(tokens):
        if t[0] != "o" or t[1] != ".." or k in used:
            continue
        start = -1
        for j in range(k - 1, max(-1, k - 60), -1):
            if _operand(tokens, j) == k:
                prev = tokens[j - 1] if j > 0 else None
                if prev is None or (prev[0] == "o" and prev[1] in (",", "(", "{", "=", "[", ";")) or (prev[0] == "n" and prev[1] in KEYWORDS) or prev[0] in ("s", "d", "n"):
                    if prev is not None and prev[0] in ("s", "d", "n") and prev[1] not in KEYWORDS and prev[2] == tokens[j][2]:
                        continue	# the middle of something
                    start = j
        if start < 0:
            continue
        parts = []
        i = start
        while True:
            e = _operand(tokens, i)
            if e < 0:
                parts = []
                break
            if e == i + 1 and tokens[i][0] == "s":
                parts.append(("s", tokens[i][1]))
            else:
                parts.append(("v", None))
            if e < len(tokens) and tokens[e][0] == "o" and tokens[e][1] == "..":
                used.add(e)
                i = e + 1
                continue
            break
        if len(parts) < 2:
            continue
        lits = "".join(p[1] for p in parts if p[0] == "s")
        if not any(p[0] == "v" for p in parts):
            continue
        visible = re.sub(r"\[[A-Z_]+[^\]]*\]", "", lits)
        if len(re.findall(r"[A-Za-z\u0080-\uffff]", visible)) < 4:
            continue
        tpl = "".join(p[1].replace("%", "%%") if p[0] == "s" else "%s" for p in parts)
        tpl = re.sub(r"(%s){2,}", "%s", tpl)	# two values side by side are one
        if " " not in tpl.strip() and not re.search(r"[\u0080-\uffff]", tpl):
            continue	# a file name, a flag
        out.append((tpl, tokens[start][2], calls[start]))
    return out


def c_literal_bytes(lit):
    """The bytes of a C string literal body (escapes \\xNN, \\NNN, \\n...)."""
    out = bytearray()
    i = 0
    while i < len(lit):
        ch = lit[i]
        if ch == "\\" and i + 1 < len(lit):
            e = lit[i + 1]
            if e == "x":
                m = re.match(r"[0-9a-fA-F]{1,2}", lit[i + 2:])
                out.append(int(m.group(0), 16))
                i += 2 + len(m.group(0))
                continue
            if e in "01234567":
                m = re.match(r"[0-7]{1,3}", lit[i + 1:])
                out.append(int(m.group(0), 8) & 0xFF)
                i += 1 + len(m.group(0))
                continue
            out += {"n": b"\n", "t": b"\t", "r": b"\r", "0": b"\0"}.get(e, e.encode("latin-1"))
            i += 2
            continue
        out += ch.encode("cp1250", errors="replace") if ord(ch) > 255 else bytes([ord(ch)])
        i += 1
    return bytes(out)


CALL = re.compile(r"(ChatPacket\s*\(\s*CHAT_TYPE_(?:INFO|NOTICE|BIG_NOTICE|TALKING|FANCY_NOTICE|DICE_INFO|MISSION|SUB_MISSION)\b"
                  r"|SendNotice\s*\(|BroadcastNotice\s*\(|SendNoticeMap\s*\(|SendBigNotice\s*\(|->Notice\s*\()")


def c_strings(src):
    """(text, line) of the literals inside the argument lists of the calls of CALL."""
    out = []
    for m in CALL.finditer(src):
        i = m.end()
        depth = 1 if m.group(0).endswith("(") else 0
        if depth == 0:
            # ChatPacket(CHAT_TYPE_X - the '(' is part of the match
            depth = 1
        j = i
        while j < len(src) and depth > 0:
            ch = src[j]
            if ch == '"':
                k = j + 1
                while k < len(src) and src[k] != '"':
                    k += 2 if src[k] == "\\" else 1
                j = k + 1
                continue
            if ch == "'":
                k = j + 1
                while k < len(src) and src[k] != "'":
                    k += 2 if src[k] == "\\" else 1
                j = k + 1
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == ";" and depth > 0:
                break
            j += 1
        args = src[i:j]
        line = src.count("\n", 0, m.start()) + 1
        # adjacent literals "a" "b" are one
        for g in re.finditer(r'"((?:[^"\\\n]|\\.)*)"(?:\s*"((?:[^"\\\n]|\\.)*)")*', args):
            parts = re.findall(r'"((?:[^"\\\n]|\\.)*)"', g.group(0))
            b = b"".join(c_literal_bytes(p) for p in parts)
            out.append((b.decode("cp1250", errors="replace"), line))
    return out


def decode(path):
    b = open(path, "rb").read()
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1250", errors="replace")


def add(table, text, where):
    w = table.setdefault(text, [])
    if len(w) < 3 and where not in w:
        w.append(where)


def quest_sources():
    files = []
    for pat in ("**/*.quest", "**/*.lua"):
        files += glob.glob(os.path.join(GAME, pat), recursive=True)
    files += glob.glob(os.path.join(REPO, "files", "*.quest"))
    # web_admin is the panel's helper (no player sees it), gm_profile a game master's tool.
    skip = ("mt2009_language.lua", "m2_difficulty.lua", "web_admin.quest", "gm_profile.quest")
    return sorted(f for f in files if os.path.basename(f) not in skip and "/lang/" not in f)


def extract():
    quest, concat, templates = {}, {}, {}
    for f in quest_sources():
        rel = os.path.relpath(f, REPO)
        strings = lua_strings(decode(f))
        for tpl, line, call in lua_strings.templates:
            if call not in SKIP_CALLS:
                add(templates, tpl, "%s:%d" % (rel, line))
        for text, line, call, cat in strings:
            if call in SKIP_CALLS or not is_text(text):
                continue
            # A literal glued to something ("Koszt: " .. n) is a fragment unless it is also said alone somewhere.
            add(concat if cat else quest, text, "%s:%d" % (rel, line))
    server = {}
    for f in sorted(glob.glob(os.path.join(REPO, "linux-port", "overlays", "playerbot", "src", "game", "src", "*.*"))):
        if not f.endswith((".cpp", ".h")) or os.path.basename(f).startswith("mt2009_language"):
            continue
        src = open(f, "rb").read().decode("latin-1")
        rel = os.path.relpath(f, REPO)
        for text, line in c_strings(src):
            if is_text(text) and (" " in text.strip() or re.search(r"[^\x00-\x7f]", text)):
                add(server, text, "%s:%d" % (rel, line))
    for f in sorted(glob.glob(os.path.join(REPO, "server-patches", "*", "edits.json"))):
        try:
            edits = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        rel = os.path.relpath(f, REPO)
        for e in edits if isinstance(edits, list) else []:
            new = e.get("new", "") if isinstance(e, dict) else ""
            for text, line in c_strings(new):
                if is_text(text) and " " in text.strip():
                    add(server, text, "%s (%s)" % (rel, e.get("marker", "")))
    extract.templates = templates
    return quest, server, concat


def write(path, table):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fp:
        fp.write("# generated by tools/i18n/extract_server_texts.py - Polish<TAB>where\n")
        for k in sorted(table, key=lambda x: (x.lower(), x)):
            fp.write("%s\t%s\n" % (k.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n"), " ".join(table[k])))


def load_hand(lang, name):
    res = {}
    p = os.path.join(LANG, lang, name)
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.rstrip("\n")
            if line and not line.startswith("#") and "\t" in line:
                a, b = line.split("\t", 1)
                res[a.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")] = b
    return res


def main():
    quest, server, concat = extract()
    if len(sys.argv) > 2 and sys.argv[1] == "--check":
        lang = sys.argv[2]
        stock = load_hand(lang, "10_quest_stock.tsv")
        stock.update(load_hand(lang, "20_server_locale.tsv"))
        concat = {k: v for k, v in concat.items() if k not in quest}
        templates = {k: v for k, v in extract.templates.items() if k not in quest}
        for name, table, hand in (("quest", quest, "30_quest_custom.tsv"), ("templates", templates, "32_quest_templates.tsv"),
                                  ("fragments", concat, "35_quest_fragments.tsv"),
                                  ("server", server, "40_server_custom.tsv")):
            have = load_hand(lang, hand)
            missing = [k for k in table if k not in have and k not in stock]
            print("%s %s: %d of %d translated, %d missing" % (lang, name, len(table) - len(missing), len(table), len(missing)))
        return
    write(os.path.join(DATA, "quest_custom_pl.tsv"), quest)
    write(os.path.join(DATA, "server_custom_pl.tsv"), server)
    concat = {k: v for k, v in concat.items() if k not in quest}
    write(os.path.join(DATA, "quest_fragments_pl.tsv"), concat)
    templates = {k: v for k, v in extract.templates.items() if k not in quest}
    write(os.path.join(DATA, "quest_templates_pl.tsv"), templates)
    print("glued lines as templates %d" % len(templates))
    print("quest texts %d, fragments (glued pieces) %d, server texts %d" % (len(quest), len(concat), len(server)))


if __name__ == "__main__":
    main()
