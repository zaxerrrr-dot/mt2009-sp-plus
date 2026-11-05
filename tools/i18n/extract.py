#!/usr/bin/env python3
"""Collect every text the web pages can show, as translation sources.

MT2009_PLUS_WEB_I18N_V1. The panels and the ItemShop print Polish written
where it stands (templates, app.py, PHP pages, scripts) - see m2i18n.py: the
finished page is translated, not the code. This finds what there is to
translate:

  exact     a whole text: a template's text between tags, a title/placeholder,
            a Python/JS/PHP string literal that reads like Polish
  patterns  a text with live values in it: "{{ n }} graczy" in a template,
            f"Zabito {n}" in Python, `${n} szt.` in a script -> "{0} graczy"

and writes tools/i18n/source/<app>.json. The classic panel (panel/app) is
English-based for every language but Polish (its own t() tables carry
pl/en/de/tr), so for it the English of those tables is collected too.

    python3 tools/i18n/extract.py            # all apps
    python3 tools/i18n/extract.py seban      # one

Never run on a server; it only reads the repository.
"""
import ast
import html
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCKER = os.path.join(ROOT, "linux-port", "docker")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source")

PL_CHARS = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
PL_WORDS = set("""
i w z na nie się do jest to że od po za dla jak co ten ta te tym tej tego są być został została zostało
już tylko albo lub oraz przez przy pod nad bez gdy gdzie kiedy który która które których którym
czy jeszcze teraz tutaj tu tam też także więc bo ale aby żeby można musi może będzie był była było
gracz gracze graczy postać postaci przedmiot przedmioty przedmiotów potwór potwory potworów
konto hasło zapisz usuń dodaj zmień pokaż ukryj wróć dalej anuluj szukaj brak wszystkie wszystko
dzień dni godzin godziny minut minuty sekund tydzień tygodnia mapa mapy serwer serwera kanał
włącz wyłącz włączone wyłączone tak nie zapisano usunięto dodano zmieniono nowy nowa nowe
poziom poziomu bonus bonusy szansa szanse cena ceny sklep sklepu kup kupić sprzedaj ilość
""".split())
WORD = re.compile(r"[A-Za-zÀ-žĄ-ż]+")


def polish(text):
    if PL_CHARS.search(text):
        return True
    words = [w.lower() for w in WORD.findall(text)]
    if len(words) < 2:
        return False
    hits = sum(1 for w in words if w in PL_WORDS)
    return hits >= 2 or (hits >= 1 and len(words) <= 4 and words[0] in PL_WORDS)


def human(text):
    """Text a person reads, not code: letters, and not an identifier, a path,
    a CSS value or a URL."""
    t = text.strip()
    if len(t) < 2 or not re.search(r"[A-Za-zÀ-ž]{2}", t):
        return False
    if re.fullmatch(r"[\w.\-/:#%]+", t) and not PL_CHARS.search(t) and " " not in t:
        # one token: keep a capitalised word (a label), drop code-ish ones
        if not re.fullmatch(r"[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+", t):
            return False
    if t.startswith(("http://", "https://", "/", "./", "#", "data:")):
        return False
    if re.search(r"===|!==|\|\||&&|\);|' ?\+|\+ ?'|\" ?\+|\+ ?\"|\\x|\?>|->|::|\$\(|\(\)|^[=)\]}]|[(\[{]$|\w\.\w+\(", t):
        return False
    if re.search(r"\S{40,}", t) and " " not in t:
        return False
    letters = len(re.findall(r"[^\W\d_]|\s", t))
    if len(t) > 8 and letters / len(t) < 0.6:
        return False
    if re.search(r"[{};]\s*$|^\s*[.#][\w-]+\s*\{|=>|\bfunction\b|\breturn\b|\bvar\b|\bconst\b", t):
        return False
    if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\b.*\b(FROM|SET|INTO|WHERE|VALUES)\b", t):
        return False
    return True


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


class Bag:
    def __init__(self):
        self.exact = {}
        self.patterns = {}

    def add(self, text, origin, placeholders=False):
        t = norm(html.unescape(text))
        if not t or not human(re.sub(r"\{\d+\}", "", t)):
            return
        if placeholders and re.search(r"\{\d+\}", t):
            literal = re.sub(r"\{\d+\}", "", t)
            if len(re.findall(r"[A-Za-zÀ-ž]", literal)) < 3:
                return
            self.patterns.setdefault(t, origin)
        else:
            self.exact.setdefault(t, origin)


# ---------------------------------------------------------------- Jinja/HTML
JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)
SCRIPT_STYLE = re.compile(r"<(script|style)\b[^>]*>(.*?)</\1>", re.S | re.I)
TAG = re.compile(r"""<(?:[^>"']|"[^"]*"|'[^']*')*>""")
ATTR = re.compile(r"""\b(title|alt|placeholder|aria-label|data-confirm|data-tip|data-title|value)\s*=\s*("([^"]*)"|'([^']*)')""", re.I)
JINJA_EXPR = re.compile(r"\{\{.*?\}\}", re.S)
JINJA_STMT = re.compile(r"\{%.*?%\}", re.S)
PHP_BLOCK = re.compile(r"<\?(?:php|=)?.*?(?:\?>|$)", re.S)
QUOTED = re.compile(r"""'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)\"""")


def template_text(seg, bag, origin, expr_re):
    """A run of text between tags, with {{ }}/<?= ?> turned into {n}."""
    n = [0]

    def ph(m):
        # string literals inside the expression are texts of their own
        for q in QUOTED.finditer(m.group(0)):
            s = q.group(1) if q.group(1) is not None else q.group(2)
            if s and (polish(s) or (" " in s and human(s))):
                bag.add(s, origin)
        k = n[0]
        n[0] += 1
        return "{%d}" % k
    text = expr_re.sub(ph, seg)
    bag.add(text, origin, placeholders=n[0] > 0)


def scan_markup(src, bag, origin, kind="jinja"):
    if kind == "jinja":
        src = JINJA_COMMENT.sub(" ", src)
        expr_re = JINJA_EXPR
        stmt_re = JINJA_STMT
    else:
        expr_re = re.compile(r"<\?(?:=|php\s+(?:print|echo))\s.*?\?>", re.S)
        stmt_re = PHP_BLOCK
    for m in SCRIPT_STYLE.finditer(src):
        if m.group(1).lower() == "script":
            scan_js(m.group(2), bag, origin)
    src = SCRIPT_STYLE.sub(" <x> ", src)
    # statements split text (an {% if %} inside a sentence gives two texts)
    if kind == "jinja":
        for m in stmt_re.finditer(src):
            for q in QUOTED.finditer(m.group(0)):
                s = q.group(1) if q.group(1) is not None else q.group(2)
                if s and (polish(s) or (" " in s and human(s) and re.search(r"[a-z]", s))):
                    bag.add(s, origin)
        src = stmt_re.sub(" <x> ", src)
    else:
        # PHP code blocks: their strings, then out of the markup
        for m in PHP_BLOCK.finditer(src):
            if expr_re.fullmatch(m.group(0)):
                continue
            scan_php_code(m.group(0), bag, origin)
        src = PHP_BLOCK.sub(lambda m: m.group(0) if expr_re.fullmatch(m.group(0)) else " <x> ", src)
    pos = 0
    for m in TAG.finditer(src):
        seg = src[pos:m.start()]
        if seg.strip():
            template_text(seg, bag, origin, expr_re)
        tag = m.group(0)
        is_button = re.match(r"<input\b", tag, re.I) and re.search(r"type\s*=\s*['\"]?(submit|button)", tag, re.I)
        for a in ATTR.finditer(tag):
            if a.group(1).lower() == "value" and not is_button:
                continue
            val = a.group(3) if a.group(3) is not None else a.group(4)
            if val:
                template_text(val, bag, origin, expr_re)
        pos = m.end()
    seg = src[pos:]
    if seg.strip():
        template_text(seg, bag, origin, expr_re)


# ---------------------------------------------------------------- JS
JS_STR = re.compile(r"""'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"|`((?:[^`\\]|\\.)*)`""", re.S)
JS_LINE_COMMENT = re.compile(r"(^|[^:\\'\"])//[^\n]*")
JS_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def js_unescape(s):
    return re.sub(r"\\(.)", lambda m: {"n": " ", "t": " "}.get(m.group(1), m.group(1)), s)


def scan_js(src, bag, origin):
    src = JS_BLOCK_COMMENT.sub(" ", src)
    src = JS_LINE_COMMENT.sub(r"\1", src)
    for m in JS_STR.finditer(src):
        if m.group(3) is not None:
            raw = m.group(3)
            n = [0]

            def ph(_m):
                k = n[0]
                n[0] += 1
                return "{%d}" % k
            text = re.sub(r"\$\{[^}]*\}", ph, raw)
            if "<" in text and ">" in text:
                # markup built in a script: its texts
                for piece in re.split(r"<[^>]*>", text):
                    if polish(piece):
                        bag.add(js_unescape(piece), origin, placeholders=True)
                continue
            if polish(text):
                bag.add(js_unescape(text), origin, placeholders=n[0] > 0)
            continue
        s = m.group(1) if m.group(1) is not None else m.group(2)
        if not s:
            continue
        if "<" in s and ">" in s:
            for piece in re.split(r"<[^>]*>", s):
                if polish(piece):
                    bag.add(js_unescape(piece), origin)
            continue
        if polish(s):
            bag.add(js_unescape(s), origin)


# ---------------------------------------------------------------- PHP
def scan_php_code(src, bag, origin):
    src = JS_BLOCK_COMMENT.sub(" ", src)
    src = re.sub(r"(^|\s)(//|#)[^\n]*", r"\1", src)
    for m in QUOTED.finditer(src):
        s = m.group(1) if m.group(1) is not None else m.group(2)
        if not s:
            continue
        if "<" in s and ">" in s:
            for piece in re.split(r"<[^>]*>", s):
                if polish(piece):
                    bag.add(piece, origin)
            continue
        if polish(s):
            # "...$var..." in double quotes
            n = [0]

            def ph(_m):
                k = n[0]
                n[0] += 1
                return "{%d}" % k
            text = re.sub(r"\{?\$[A-Za-z_][\w\[\]'\"\->]*\}?", ph, s) if m.group(2) is not None else s
            bag.add(text.replace("\\'", "'").replace('\\"', '"'), origin, placeholders=n[0] > 0)


# ---------------------------------------------------------------- Python
class PyScan(ast.NodeVisitor):
    def __init__(self, bag, origin, english=False):
        self.bag = bag
        self.origin = origin
        self.english = english   # classic panel: also every "en" text
        self.skip = 0

    def _doc(self, node):
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            return body[0].value
        return None

    def generic_visit(self, node):
        doc = self._doc(node) if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) else None
        if doc is not None:
            doc._is_doc = True
        super().generic_visit(node)

    def visit_Call(self, node):
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
        if name in ("debug", "info", "warning", "error", "exception", "log", "execute", "executemany", "compile", "match",
                    "search", "sub", "fullmatch", "findall", "split", "startswith", "endswith", "strftime", "strptime"):
            if name in ("error", "warning", "info", "debug", "exception", "log", "execute", "executemany"):
                if isinstance(f, ast.Attribute) and isinstance(f.value, (ast.Name, ast.Attribute)):
                    owner = f.value.id if isinstance(f.value, ast.Name) else f.value.attr
                    if owner in ("logger", "log", "logging", "cur", "cursor", "c", "db", "conn", "self"):
                        return
        self.generic_visit(node)

    def visit_Dict(self, node):
        for k, v in zip(node.keys, node.values):
            key = k.value if isinstance(k, ast.Constant) else None
            if key == "pl" or key in ("de", "tr"):
                # the Polish of a language table is shown on Polish pages only
                if self.english:
                    continue
                if key in ("de", "tr"):
                    continue
            if key == "en" and self.english:
                self._english(v)
                continue
            if k is not None:
                self.visit(k)
            self.visit(v)

    def _english(self, v):
        for sub in ast.walk(v):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                s = sub.value
                if "{" in s and re.search(r"\{\w*\}", s):
                    # "{n} players": a format placeholder
                    s2 = re.sub(r"\{\w*(?:[:!][^}]*)?\}", "{9}", s)
                    s2 = renumber(s2)
                    self.bag.add(s2, self.origin, placeholders=True)
                if "<" in s and ">" in s and ("{{" in s or "{%" in s):
                    scan_markup(s, self.bag, self.origin)
                elif "<" in s and ">" in s:
                    for piece in re.split(r"<[^>]*>", s):
                        self.bag.add(piece, self.origin)
                else:
                    self.bag.add(s, self.origin)
            elif isinstance(sub, ast.JoinedStr):
                self.visit_JoinedStr(sub, force=True)

    def visit_Assign(self, node):
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if any(n.endswith("_PL") for n in names) and self.english:
            return
        if any(n.endswith("_EN") for n in names) and self.english:
            self._english(node.value)
            return
        self.generic_visit(node)

    def visit_Constant(self, node):
        s = node.value
        if not isinstance(s, str) or getattr(node, "_is_doc", False):
            return
        if ("{{" in s or "{%" in s) and "<" in s:
            scan_markup(s, self.bag, self.origin)
            return
        if "<" in s and ">" in s and re.search(r"</?[a-z]", s):
            scan_markup(s, self.bag, self.origin, kind="jinja")
            return
        if polish(s):
            if re.search(r"\{\w*(?:[:!][^}]*)?\}", s) and not re.search(r"\{\{", s):
                # "...{n}..." for .format()
                s2 = renumber(re.sub(r"\{\w*(?:[:!][^}]*)?\}", "{9}", s))
                self.bag.add(s2, self.origin, placeholders=True)
                return
            if "%s" in s or "%d" in s or re.search(r"%\(\w+\)[sd]", s):
                s2 = renumber(re.sub(r"%(?:\(\w+\))?[-+0-9.]*[sdif]", "{9}", s))
                self.bag.add(s2, self.origin, placeholders=True)
                return
            self.bag.add(s, self.origin)

    def visit_JoinedStr(self, node, force=False):
        parts = []
        k = 0
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(str(v.value))
            else:
                parts.append("{%d}" % k)
                k += 1
                # string constants inside the expression
                self.visit(v)
        s = "".join(parts)
        if "<" in s and ">" in s:
            for piece in re.split(r"<[^>]*>", s):
                if force or polish(piece):
                    self.bag.add(renumber(piece), self.origin, placeholders=True)
            return
        if force or polish(s):
            self.bag.add(s, self.origin, placeholders=k > 0)


def renumber(s):
    n = [0]

    def ph(_m):
        k = n[0]
        n[0] += 1
        return "{%d}" % k
    return re.sub(r"\{\d+\}", ph, s)


def scan_py(path, bag, origin, english=False):
    src = open(path, encoding="utf-8").read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print("skip", path, e, file=sys.stderr)
        return
    # mark docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            b = node.body
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
                b[0].value._is_doc = True
    PyScan(bag, origin, english).visit(tree)


def walk(base, exts, skip=()):
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in skip and not d.startswith(".")]
        for f in sorted(fn):
            if f.endswith(exts):
                yield os.path.join(dp, f)


def rel(p):
    return os.path.relpath(p, DOCKER)


def app_seban():
    bag = Bag()
    base = os.path.join(DOCKER, "seban-panel")
    for p in walk(os.path.join(base, "templates"), (".html",)):
        scan_markup(open(p, encoding="utf-8").read(), bag, rel(p))
    for p in walk(os.path.join(base, "static"), (".js",)):
        scan_js(open(p, encoding="utf-8", errors="replace").read(), bag, rel(p))
    for p in walk(base, (".py",), skip=("m2clientpack", "templates", "static", "i18n", "integration", "updater")):
        if os.path.basename(p).startswith("test_"):
            continue
        scan_py(p, bag, rel(p))
    for p in ("gm_commands.txt",):
        pass
    return bag


def app_panel():
    bag = Bag()
    base = os.path.join(DOCKER, "panel", "app")
    scan_py(os.path.join(base, "admin_panel.py"), bag, "panel/app/admin_panel.py", english=True)
    for p in walk(base, (".py",)):
        if os.path.basename(p) != "admin_panel.py":
            scan_py(p, bag, rel(p), english=True)
    return bag


def app_itemshop():
    bag = Bag()
    base = os.path.join(DOCKER, "itemshop", "app")
    # the old web shop (app/itemshop, app/user) is removed by the Dockerfile on this line: shop3 only
    for p in walk(base, (".php",), skip=("languages", "classes", "itemshop", "user")):
        src = open(p, encoding="utf-8", errors="replace").read()
        scan_markup(src, bag, rel(p), kind="php")
    for p in walk(os.path.join(base, "shop3", "include", "classes"), (".php",)):
        if os.path.basename(p) == "Medoo.php":
            continue
        scan_php_code(open(p, encoding="utf-8", errors="replace").read(), bag, rel(p))
    for p in walk(base, (".js",), skip=("itemshop", "user")):
        if re.search(r"jquery|min\.js|bootstrap|javascript_?\.js|/[0-9a-f]{30}\.js$|m2i18n", p, re.I):
            continue
        scan_js(open(p, encoding="utf-8", errors="replace").read(), bag, rel(p))
    # ItemShop V3's own language file: every value is a text (its {0}: sprintf's %s/%d)
    for key, val in php_lang_array(os.path.join(base, "shop3", "include", "languages", "pl.php")).items():
        if re.search(r"%[sd]", val):
            bag.add(renumber(re.sub(r"%[sd]", "{9}", val)), "shop3/languages/pl.php:" + key, placeholders=True)
        bag.add(val, "shop3/languages/pl.php:" + key)
    # the catalogue's Polish rows (itemshop3_schema.sql: categories, lines, chests, their drops, bonus and skill
    # names, the slider) - the shop prints them as they are
    sql = open(os.path.join(DOCKER, "mariadb", "playerbot", "itemshop3_schema.sql"), encoding="utf-8").read()
    sql = re.sub(r"^--[^\n]*$", "", sql, flags=re.M)
    for m in re.finditer(r"'((?:[^'\\]|\\.|'')*)'", sql):
        val = m.group(1).replace("''", "'").replace("\\'", "'")
        if not polish(val) or re.search(r"\b(SELECT|FROM|WHERE|CONCAT|COALESCE)\b", val):
            continue
        if re.search(r"%[-+0-9.]*[sd]", val):
            bag.add(renumber(re.sub(r"%[-+0-9.]*[sd]", "{9}", val).replace("%%", "%")), "itemshop3_schema.sql", placeholders=True)
            continue
        bag.add(val.replace("%%", "%"), "itemshop3_schema.sql")
    return bag


PHP_PAIR = re.compile(r"""^\s*(['"])([\w\-]+)\1\s*=>\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)')\s*,?\s*(?://.*)?$""", re.M)


def php_lang_array(path):
    out = {}
    try:
        src = open(path, encoding="utf-8").read()
    except OSError:
        return out
    for m in PHP_PAIR.finditer(src):
        val = m.group(3) if m.group(3) is not None else m.group(4)
        out[m.group(2)] = val.replace("\\'", "'").replace('\\"', '"')
    return out


APPS = {"seban": app_seban, "panel": app_panel, "itemshop": app_itemshop}


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    for name in (argv or list(APPS)):
        bag = APPS[name]()
        data = {"exact": dict(sorted(bag.exact.items())), "patterns": dict(sorted(bag.patterns.items()))}
        with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=0, sort_keys=True)
            f.write("\n")
        print(name, "exact", len(bag.exact), "patterns", len(bag.patterns))


if __name__ == "__main__":
    main(sys.argv[1:])
