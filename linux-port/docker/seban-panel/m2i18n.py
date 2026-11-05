"""The web pages in other languages (MT2009_PLUS_WEB_I18N_V1).

The panels print their texts where they stand - in templates, in app.py, in
the scripts - and a page is translated when it is finished, not in the code:
one after_request hook turns the HTML a visitor gets into their language, and
static/m2i18n-watch.js does the same in the browser for what a page's script
draws later (the same tables, fetched once from /i18n/<code>.json). Nothing
changes for the page's own language: it is sent byte for byte as rendered.

A language is a file. i18n/<code>.json (and any i18n/<code>/*.json beside it,
merged in name order) holds

    "_meta":    {"name": "Deutsch", "english": "German", "order": 30}
    "exact":    {"a whole text": "its translation"}
    "patterns": {"Zabito {0} potworów": "{0} Monster getötet"}
    "regex":    [["^Lv (\\d+)$", "Lv $1"]]       (rare: a free-form rule)
    "names":    {"Miecz+0": "Schwert+0"}         (item/monster names, server side)

and dropping such a file in is all a new language takes; the switch lists every
file it finds. A text is looked up whole, then by pattern ({0}, {1} stand for
whatever the page put there - which is itself looked up, so a monster's name
inside a sentence comes out translated too), then piece by piece around " · ",
": " and the like. A text the language does not know falls back to the
fallback language's (English) and only then stays as it is.

This file is the same in seban-panel/ and panel/app/ (tools/i18n/sync.py
copies it); the ItemShop has its PHP twin, m2i18n.php.
"""
import html
import json
import os
import re
import threading

PREFERRED_ORDER = ["pl", "en", "de", "tr", "ro", "es", "it", "fr", "pt", "cz", "hu", "gr", "ae", "uk"]
COOKIE = "m2lang"
# the game's language codes are not all the web's: <html lang> gets the web's
HTML_LANG = {"cz": "cs", "gr": "el", "ae": "ar", "dk": "da"}
RTL = {"ae"}
_PH = re.compile(r"\{(\d+)\}")
_WS = re.compile(r"\s+")
_LEADING = re.compile(r"^([^\w(„\"'«]+)(?=\w|[(„\"'«])", re.U)
_TRAILING = re.compile(r"(\s*(?:[:：…*!?.]|\.\.\.|\s[→↗›»]|\s\(\?\))+\s*)$", re.U)
_SPLIT = re.compile(r"((?<=[.!?…])\s+|\s+[·|—–/•]\s+|:\s+|,\s+|\s+\(|\)\s+|\s*[\[\]]\s*)")
_SKIP_BLOCKS = re.compile(r"(<(script|style|textarea|pre|code)\b[^>]*>.*?</\2\s*>)", re.I | re.S)
_NO_TRANSLATE = re.compile(r"(<([a-zA-Z][\w-]*)\b[^>]*\btranslate=[\"']no[\"'][^>]*>.*?</\2\s*>)", re.I | re.S)
_STASHED = re.compile(r"<!--\x00M2(\d+)\x00-->")
_TAG = re.compile(r"""(<(?:[^>"']|"[^"]*"|'[^']*')*>)""")
_ATTRS = re.compile(r"""\b(title|alt|placeholder|aria-label|data-confirm|data-title|data-tip|label)=(["'])(.*?)\2""", re.S)
_VALUE = re.compile(r"""\bvalue=(["'])(.*?)\1""", re.S)
_BUTTON = re.compile(r"""\btype=["']?(submit|button|reset)\b""", re.I)
_HTML_LANG = re.compile(r"(<html\b[^>]*\blang=)([\"'])[\w-]*\2", re.I)
_BODY_END = re.compile(r"</body\s*>", re.I)


def _norm(text):
    return _WS.sub(" ", text).strip()


def _compile_pattern(source, target):
    """A {0}-style pattern as an anchored regex and its target."""
    parts = _PH.split(source)
    rx, groups, literal = "^", [], ""
    for i, part in enumerate(parts):
        if i % 2 == 0:
            rx += re.escape(part)
            if len(part) > len(literal):
                literal = part
        else:
            groups.append(int(part))
            rx += "(.+?)"
    rx += "$"
    return re.compile(rx, re.S), groups, target, literal


class Catalog:
    """Every language of one app: i18n/<code>.json files in directory."""

    def __init__(self, directory, source="pl", fallback="en", builtin=None):
        self.directory = directory
        self.source = source          # the language the pages are written in
        self.fallback = fallback      # what a missing text falls back to
        self.builtin = dict(builtin or {})   # languages the app renders itself
        self._lock = threading.Lock()
        self._tables = {}
        self._payload = {}
        self._cache = {}
        self._langs = None

    # ------------------------------------------------------------ files
    def _files(self, code):
        out = []
        main = os.path.join(self.directory, code + ".json")
        if os.path.isfile(main):
            out.append(main)
        sub = os.path.join(self.directory, code)
        if os.path.isdir(sub):
            out += [os.path.join(sub, f) for f in sorted(os.listdir(sub)) if f.endswith(".json")]
        return out

    def _read(self, code):
        data = {"_meta": {}, "exact": {}, "patterns": {}, "regex": [], "names": {}}
        for path in self._files(code):
            try:
                with open(path, encoding="utf-8") as fh:
                    part = json.load(fh)
            except (OSError, ValueError):
                continue
            for key in ("_meta", "exact", "patterns", "names"):
                if isinstance(part.get(key), dict):
                    data[key].update({k: v for k, v in part[key].items() if isinstance(v, (str, int, float))})
            if isinstance(part.get("regex"), list):
                data["regex"] += [r for r in part["regex"] if isinstance(r, (list, tuple)) and len(r) == 2]
        # an empty translation means "not translated yet"
        for key in ("exact", "patterns", "names"):
            data[key] = {_norm(k): v for k, v in data[key].items() if isinstance(v, str) and v.strip()}
        return data

    def languages(self):
        """[(code, name)] of every language there is, in the switch's order."""
        if self._langs is None:
            found = dict(self.builtin)
            found.setdefault(self.source, self.source)
            try:
                entries = os.listdir(self.directory)
            except OSError:
                entries = []
            for entry in entries:
                # a language is its main file; i18n/<code>/ alone (names) is not one yet
                if not entry.endswith(".json"):
                    continue
                code = entry[:-5]
                if not re.fullmatch(r"[a-z]{2}(-[a-z]{2})?", code):
                    continue
                meta = self._read_meta(code)
                if meta is not None:
                    found[code] = meta.get("name") or found.get(code) or code
            def order(item):
                code = item[0]
                return (PREFERRED_ORDER.index(code) if code in PREFERRED_ORDER else len(PREFERRED_ORDER), code)
            self._langs = sorted(found.items(), key=order)
        return self._langs

    def _read_meta(self, code):
        for path in self._files(code):
            try:
                with open(path, encoding="utf-8") as fh:
                    return (json.load(fh).get("_meta") or {})
            except (OSError, ValueError):
                continue
        return None

    def codes(self):
        return [c for c, _ in self.languages()]

    def name(self, code):
        return dict(self.languages()).get(code, code)

    # ------------------------------------------------------------ tables
    def tables(self, code):
        with self._lock:
            if code in self._tables:
                return self._tables[code]
            own = self._read(code)
            chain = [own]
            if self.fallback and code not in (self.fallback, self.source):
                chain.append(self._read(self.fallback))
            exact, patterns, names, regex = {}, {}, {}, []
            for data in reversed(chain):
                exact.update(data["exact"])
                patterns.update(data["patterns"])
                names.update(data["names"])
            for data in chain:
                regex += data["regex"]
            compiled = []
            for src, dst in patterns.items():
                if _PH.search(src):
                    compiled.append(_compile_pattern(src, dst))
            # longer literal first: the more specific pattern wins
            compiled.sort(key=lambda p: -len(p[3]))
            rx = []
            for src, dst in regex:
                try:
                    rx.append((re.compile(src), re.sub(r"\$(\d+)", r"\\g<\1>", dst)))
                except re.error:
                    continue
            table = {"exact": exact, "patterns": compiled, "raw_patterns": patterns, "regex": rx,
                     "raw_regex": regex, "names": names, "meta": own["_meta"]}
            self._tables[code] = table
            return table

    def reload(self):
        with self._lock:
            self._tables.clear()
            self._payload.clear()
            self._cache.clear()
            self._langs = None

    # ------------------------------------------------------------ texts
    def _lookup(self, core, t, depth=0):
        hit = t["exact"].get(core)
        if hit is not None:
            return hit
        hit = t["names"].get(core)
        if hit is not None:
            return hit
        for rx, groups, target, literal in t["patterns"]:
            if literal and literal not in core:
                continue
            m = rx.match(core)
            if not m:
                continue
            values = {}
            for idx, number in enumerate(groups):
                value = m.group(idx + 1)
                if depth < 2:
                    inner = self._lookup(value.strip(), t, depth + 1) if value.strip() else None
                    if inner is not None:
                        value = value.replace(value.strip(), inner)
                values[number] = value
            return _PH.sub(lambda g: values.get(int(g.group(1)), g.group(0)), target)
        return None

    def text(self, text, code):
        """One text (not HTML) in the language; unchanged when unknown."""
        if not text or code == self.source or code not in self.codes():
            return text
        core = _norm(text)
        if not core or not re.search(r"[^\W\d_]", core):
            return text
        key = (code, core)
        cached = self._cache.get(key)
        if cached is None:
            cached = self._translate(core, self.tables(code))
            if len(self._cache) > 200000:
                self._cache.clear()
            self._cache[key] = cached
        if cached == core:
            return text
        lead = text[:len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        return lead + cached + trail

    def _translate(self, core, t, depth=0):
        hit = self._lookup(core, t)
        if hit is not None:
            return hit
        # an icon in front, a colon behind: "💾 Zapisz:" is "Zapisz"
        m = _LEADING.match(core)
        if m and depth < 3:
            rest = core[m.end():]
            out = self._translate(rest, t, depth + 1)
            if out != rest:
                return m.group(1) + out
        m = _TRAILING.search(core)
        if m and m.start() > 0 and depth < 3:
            head = core[:m.start()]
            out = self._translate(head, t, depth + 1)
            if out != head:
                return out + m.group(1)
        # pieces around " · ", ": ", ", " ...
        if depth < 2 and _SPLIT.search(core):
            pieces = _SPLIT.split(core)
            changed = False
            for i in range(0, len(pieces), 2):
                piece = pieces[i]
                if piece.strip() and re.search(r"[^\W\d_]", piece):
                    out = self._translate(piece.strip(), t, depth + 1)
                    if out != piece.strip():
                        pieces[i] = piece.replace(piece.strip(), out)
                        changed = True
            if changed:
                return "".join(pieces)
        result = core
        for rx, repl in t["regex"]:
            result = rx.sub(repl, result)
        return result

    # ------------------------------------------------------------ HTML
    def html(self, body, code, script_url=None):
        """A whole page (or a fragment) in the language. With script_url the
        page also gets the browser half (m2i18n-watch.js) before </body>."""
        if not body or code == self.source or code not in self.codes():
            return body
        stash = []

        def keep(m):
            stash.append(m.group(1))
            return "<!--\x00M2%d\x00-->" % (len(stash) - 1)
        work = _SKIP_BLOCKS.sub(keep, body)
        work = _NO_TRANSLATE.sub(keep, work)
        out = []
        for part in _TAG.split(work):
            if not part:
                continue
            if part[0] == "<":
                out.append(self._tag(part, code))
            elif part.strip():
                out.append(html.escape(self.text(html.unescape(part), code), quote=False)
                           if re.search(r"[^\W\d_]", part) else part)
            else:
                out.append(part)
        work = "".join(out)
        previous = None
        while previous != work:
            previous = work
            work = _STASHED.sub(lambda m: stash[int(m.group(1))], work)
        work = _HTML_LANG.sub(lambda m: m.group(1) + m.group(2) + HTML_LANG.get(code, code) + m.group(2)
                              + (' dir="rtl"' if code in RTL else ""), work, count=1)
        if script_url:
            tag = '<script src="%s" data-m2i18n="%s" defer></script>' % (html.escape(script_url), html.escape(code))
            if _BODY_END.search(work):
                work = _BODY_END.sub(lambda m: tag + m.group(0), work, count=1)
        return work

    def _tag(self, tag, code):
        if tag.startswith(("</", "<!")):
            return tag

        def attr(m):
            value = m.group(3)
            if not value or "{{" in value:
                return m.group(0)
            out = html.escape(self.text(html.unescape(value), code), quote=True)
            return "%s=%s%s%s" % (m.group(1), m.group(2), out, m.group(2))
        tag = _ATTRS.sub(attr, tag)
        if tag[:6].lower() == "<input" and _BUTTON.search(tag):
            tag = _VALUE.sub(lambda m: "value=%s%s%s" % (m.group(1), html.escape(
                self.text(html.unescape(m.group(2)), code), quote=True), m.group(1)), tag, count=1)
        return tag

    def json_value(self, value, code, keys=None):
        """A JSON answer's texts (every string, or only under keys)."""
        if code == self.source:
            return value
        if isinstance(value, dict):
            return {k: (self.json_value(v, code, keys) if (keys is None or k in keys or not isinstance(v, str)) else v)
                    for k, v in value.items()}
        if isinstance(value, list):
            return [self.json_value(v, code, keys) for v in value]
        if isinstance(value, str):
            if "<" in value and ">" in value:
                return self.html(value, code)
            return self.text(value, code)
        return value

    # ------------------------------------------------------------ browser
    def payload(self, code):
        """The tables the browser half uses, as JSON text (names stay here:
        thousands of them are too many for every page)."""
        if code in self._payload:
            return self._payload[code]
        t = self.tables(code)
        data = {"lang": code, "exact": t["exact"], "patterns": t["raw_patterns"], "regex": t["raw_regex"]}
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        self._payload[code] = text
        return text

    def version(self, code):
        """Changes whenever the language's files do (for ?v= in its URL)."""
        stamp = 0
        for path in self._files(code) + (self._files(self.fallback) if self.fallback else []):
            try:
                stamp = max(stamp, int(os.stat(path).st_mtime))
            except OSError:
                pass
        return str(stamp)

    # ------------------------------------------------------------ choice
    def pick(self, asked=None, cookie=None, accept=None, default=None, browser=True):
        """The visitor's language: what they asked for now (?lang=), what
        they chose before (the m2lang cookie, shared by every page of the
        server), then the browser's - only when it does not list Polish at
        all, so a Polish player on an English Windows still gets Polish -
        and then the app's own default."""
        codes = self.codes()
        for value in (asked, cookie):
            value = (value or "").strip().lower()
            if value in codes:
                return value
        if browser and accept:
            wanted = []
            for part in accept.split(","):
                bits = part.strip().split(";")
                tag = bits[0].strip().lower()
                q = 1.0
                for b in bits[1:]:
                    b = b.strip()
                    if b.startswith("q="):
                        try:
                            q = float(b[2:])
                        except ValueError:
                            q = 0.0
                if tag:
                    wanted.append((q, tag))
            wanted.sort(key=lambda x: -x[0])
            tags = [tag.split("-")[0] for _, tag in wanted]
            alias = {"cs": "cz", "el": "gr", "ar": "ae", "uk": "uk"}
            tags = [alias.get(x, x) for x in tags]
            if self.source not in tags and "pl" not in tags:
                for tag in tags:
                    if tag in codes:
                        return tag
        default = (default or self.source)
        return default if default in codes else self.source
