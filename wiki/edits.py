"""MT2009 PLUS corrections to the MT2009 wiki's pages.

The copied pages describe the public MT2009.pl server. Where our files
(Tieru's Metin2 SinglePlayer 2.x + MT2009 PLUS) work differently, build.py
applies the edits below to the page before it is published:

    ("note", html)            a framed "MT2009 PLUS" box under the page title
    ("section", h2_id, html)  replaces an <h2> section's body (up to the next <h2>)
    ("drop", h2_id)           removes an <h2> section, heading and body
    ("re", pattern, new)      replaces a regular expression's first match (DOTALL)
    ("sub", old, new)         replaces text; any run of whitespace in `old`
                              matches any whitespace in the page

An edit that no longer finds its place stops the build, so a changed copy
of the MT2009 wiki is noticed instead of silently left uncorrected.

REMOVED lists pages of systems, maps and NPCs our files do not have: they
are not published, leave the search, and every link to them goes (sidebar
entries and categories, list items, category cards; a link in running
text keeps its words).
"""
import html
import re

BOX = ('<div class="mt2009plus-note" style="border:1px solid rgba(245,228,176,.45);'
       'border-left:4px solid #e0b64a;background:rgba(224,182,74,.08);border-radius:6px;'
       'padding:10px 14px;margin:12px 0 18px"><strong><i class="fas fa-star"></i> '
       'MT2009 PLUS</strong><div style="margin-top:6px">%s</div></div>')

DIFFICULTY = ('<a href="/mt2009plus/poziom-trudnosci/">poziomu trudności świata</a>')

REMOVED = [
    "ReworkGildii",
    "Mapy/grotawygnancowv1", "Mapy/krainagigantow", "Mapy/wezowepole",
    "Mapy/gluchaprzlecz", "Mapy/glucheaprzeleczy",
    "Systemy/emblematy", "Systemy/bossygrupowe",
    "faqironman",
    # Search-only lists of the NPCs of removed maps.
    "NPC/wezowepole", "NPC/krainagigantow", "NPC/gluchaprzlecz",
    # NPCs found only on the maps above.
    "NPC/chi-woo", "NPC/min-sun", "NPC/archeologsenn", "NPC/haneul", "NPC/jijin",
    "NPC/meijin", "NPC/starszyjezdziec", "NPC/staruszkalao", "NPC/veshtar",
    "NPC/wampirycznyhandlarz",
]

EDITS = {
    "NPC/rybak": [
        ("sub", "Łowienie dostępne jest od 50 poziomu", "Łowienie dostępne jest od 30 poziomu"),
        ("note", "<ul><li>Łowienie i wszystkie wędki są od <strong>30 poziomu</strong>, nie od 50.</li>"
                 "<li><strong>Karta Wędkarska</strong>: opcja „Karta Wedkarska” u Rybaka, "
                 "25 000 Yang + 5× Materiały Rzemieślnicze, od 30 poziomu, raz na 22 godziny. "
                 "Do łowienia trzeba ukończyć misję wprowadzającą Rybaka.</li>"
                 "<li>Ulepszanie wędki u Rybaka: +0 → +1 zawsze się udaje, dalej 88%, 77%, 66%, 55%; "
                 "nieudane ulepszenie zabiera stopień wędki.</li></ul>"),
    ],
    "Systemy/lowienie": [
        ("section", "misja-rybaka",
         "<p>Łowienie zaczyna się od misji wprowadzającej u <a href=\"/NPC/rybak\">Rybaka</a>. "
         "Na MT2009 PLUS nie ma misji z Amuletem Oczyszczającym Wody – wody nie trzeba oczyszczać, "
         "łowić można od razu po misji u Rybaka, od <strong>30 poziomu</strong>.</p> "),
        ("drop", "skladniki-amuletu"),
        ("drop", "aktywacja-amuletu"),
        ("re", r"<p>\s*Istnieje kilka sposobów na zdobycie Karty Wędkarskiej:.*?</ul>",
         "<p>Karty Wędkarskiej nie dostaje się za darmo ani za misje – <strong>kupuje się ją u "
         "<a href=\"/NPC/rybak\">Rybaka</a></strong> (opcja „Karta Wedkarska”): 25 000 Yang "
         "+ 5× Materiały Rzemieślnicze, od 30 poziomu, raz na 22 godziny.</p>"),
        ("note", "<ul><li>Łowienie jest od <strong>30 poziomu</strong> (wędka, łowienie i Karta Wędkarska).</li>"
                 "<li>Kartę Wędkarską kupuje się u Rybaka (opcja „Karta Wedkarska”): 25 000 Yang "
                 "+ 5× Materiały Rzemieślnicze, raz na 22 godziny.</li>"
                 "<li>Ulepszanie wędki: +0 → +1 to 100%, dalej 88%, 77%, 66%, 55%; porażka zabiera stopień.</li>"
                 "<li>Ognisko: Wysuszone Drzewo od Rybaka; stań tyłem do wody, bo ognisko nie zapłonie na wodzie. "
                 "Pieczone ryby dają bonusy, np. karp +20 prędkości ruchu na 600 sekund.</li></ul>"),
    ],
    "Systemy/sklepyoffline": [
        ("sub", "należy posiadać <strong>15 poziom</strong> i <strong>800 zabitych potworów</strong>.",
                "wystarczy <strong>15 poziom</strong> (bez wymogu 800 zabitych potworów)."),
        ("note", "Sklep otworzysz od <strong>15 poziomu</strong>, bez 800 zabitych potworów. "
                 "Wyszukiwarka sklepów umie szukać jednego, klikniętego przedmiotu, a ceny wielu "
                 "przedmiotów zmienisz naraz (Ctrl + prawy przycisk myszy)."),
    ],
    "Mapy/swiatyniahwang": [
        ("section", "klatwa-swiatyni-hwang",
         "<p><strong>Na MT2009 PLUS nie ma Klątwy Świątyni Hwang.</strong> Ciosy trafiają normalnie, "
         "bez Maski Sabaha. Maski Sabaha nie ma w grze: nie wypada z potworów ani ze skrzyni, "
         "nie ma jej w nagrodach ani w sklepie.</p>"),
        ("note", "Świątynia Hwang jest <strong>bez klątwy</strong> – Maska Sabaha nie jest potrzebna "
                 "i nie występuje w grze."),
    ],
    "Mapy/lochymalp": [
        ("sub", "<p>\nNa naszym serwerze została wprowadzona klątwa lochu małp, która ogranicza "
                "drop w lochu do ograniczonego czasu. Aczkolwiek istnieje możliwość "
                "uodpornienia się na klątwe poprzez uprzednie zaopatrzenie się w Zioło z "
                "danego lochu małp, który możemy otrzymać w nagrodę za zabicie BOSS'a\n</p>",
                "<p>Na MT2009 PLUS <strong>nie ma klątwy lochu małp</strong> – w lochu możesz być "
                "dowolnie długo. Zioła z małp nadal wypadają (są potrzebne do misji na 55–57 poziom), "
                "ale ich użycie nic już nie daje.</p>"),
        ("sub", "<p>Klątwa lochu małp jest aktywna\n</p>", "<p>Bez klątwy lochu małp.</p>"),
        ("sub", "<p>Klątwa lochu małp jest aktywna\n</p>", "<p>Bez klątwy lochu małp.</p>"),
        ("note", "<ul><li><strong>Klątwa lochu małp jest usunięta</strong> – nikt nie zamienia się w małpę "
                 "i nie jest wyrzucany z lochu.</li>"
                 "<li>Każde królestwo ma własny łatwy Loch Małp (wejście w drugiej wiosce).</li></ul>"),
    ],
    "Mapy/wiezademonow": [
        ("note", "<ul><li>Wieża jest od <strong>40 poziomu</strong>.</li>"
                 "<li>Na 6. piętrze kowal ulepsza bez materiałów, tylko za Yang; szansa jak u zwykłego "
                 "kowala, a nieudane ulepszenie niszczy przedmiot.</li>"
                 "<li>Na 7. piętrze demony pojawiają się raz; Metin Morderstwa wraca 9 sekund po "
                 "zniszczeniu, dopóki skrzynia nie da mapy.</li>"
                 "<li>Informacje o wejściówkach i Zbrojach z Czarnej Stali dotyczą serwera MT2009.pl "
                 "i mogą nie odpowiadać plikom MT2009 PLUS.</li></ul>"),
    ],
    "NPC/stajenny": [
        ("note", "Kucyk, Księgi Konia i treningi medalami są domyślnie <strong>bez czekania</strong>. "
                 "Czas zależy od " + DIFFICULTY + ": łatwy 0, średni 4 h (treningi 6 h / 7 h), "
                 "trudny 12 h (treningi 18 h / 21 h). Medale prowadzą konia do 20 poziomu; "
                 "21 poziom daje próba w Wieży Demonów (50 demonów, bez limitu czasu)."),
    ],
    "NPC/biolog": [
        ("note", "Kolejne oddanie jest domyślnie możliwe <strong>od razu</strong>, bez doby czekania "
                 "(Eliksir Poszukiwacza nie jest zużywany). Czas zależy od " + DIFFICULTY +
                 ": łatwy 0, średni 8 h, trudny 24 h. Misja „Zbadaj przeklęte zwierzęta” (19 poziom): "
                 "skórę dają wszystkie cztery przeklęte niedźwiedzie."),
    ],
    "Systemy/gornictwo": [
        ("note", "Żyły rud stoją w Dolinie Orków, na Pustyni Yongbi i na Górze Sohan; znikają po "
                 "7–15 minutach i pojawiają się nowe. Kilof kosztuje 80 000 Yang, kopać można od 30 poziomu."),
    ],
    "NPC/egzekutorbitewny": [
        ("re", r"\s*Pełny opis typów wojen, Ligi Bohaterów oraz Punktów Chwały znajdziesz w kategorii <a [^>]*>Rework Gildii</a>\.", ""),
    ],
    "Systemy/zielarstwo": [
        ("re", r'<tr[^>]*>\s*<td class="location-name"[^>]*>Wężowe Pole</td>.*?</tr>', ""),
    ],
    "NPC/alchemik": [
        ("note", "<ul><li><strong>Alchemia bez misji na 30 poziom</strong> – plecak alchemii działa od razu, "
                 "otwierasz go komendą <code>/dragon_soul</code> albo przyciskiem.</li>"
                 "<li>Misja u Alchemika dalej wymienia 10 Odłamków Smoczego Kamienia na Cor Draconis.</li>"
                 "<li>Cor Draconis (50255) wypada z Metinów i bossów. Bonusy kamieni smoka mają nowy balans – "
                 "zobacz <a href=\"/mt2009plus/alchemia/\">Alchemia MT2009 PLUS</a>.</li></ul>"),
    ],
}


def _fuzzy(s):
    return r"\s+".join(re.escape(w) for w in s.split())


def apply(rel, t):
    """The page `rel` (e.g. "NPC/rybak") with its MT2009 PLUS edits; the texts added, for search."""
    added = []
    for op in EDITS.get(rel, []):
        if op[0] == "sub":
            t, n = re.subn(_fuzzy(op[1]), lambda m: op[2], t, count=1)
            what = op[1]
        elif op[0] == "re":
            t, n = re.subn(op[1], lambda m: op[2], t, count=1, flags=re.S)
            what, added = op[1], added + [op[2]]
        elif op[0] == "drop":
            t, n = re.subn(r'<h2 id="%s"[^>]*>.*?</h2>.*?(?=<h2 )' % re.escape(op[1]), "", t, count=1, flags=re.S)
            what = op[1]
        elif op[0] == "section":
            t, n = re.subn(r'(<h2 id="%s"[^>]*>.*?</h2>).*?(?=<h2 )' % re.escape(op[1]),
                           lambda m: m.group(1) + op[2], t, count=1, flags=re.S)
            what, added = op[1], added + [op[2]]
        elif op[0] == "note":
            t, n = re.subn(r'(<h1 id="(?!mt2009-wiki")[^"]*"[^>]*>.*?</h1>)',
                           lambda m: m.group(1) + BOX % op[1], t, count=1, flags=re.S)
            what, added = "title", added + [op[1]]
        if n != 1:
            raise SystemExit("wiki/edits.py: %s: %s %r not found" % (rel, op[0], what[:60]))
    return t, html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", " ".join(added)))).strip()


def _removed_re():
    return "|".join(re.escape(r) for r in REMOVED)


def is_removed(rel):
    """True for a page of REMOVED (any case: the MT2009 wiki has "systemy/..." twins)."""
    rel = rel.strip("/").lower()
    return any(rel == r.lower() or rel.startswith(r.lower() + "/") for r in REMOVED)


def strip_links(t):
    """The page without its links to REMOVED pages."""
    target = r'href="/(?i:%s)(?:/[^"]*)?/?"' % _removed_re()
    # A sidebar category of a removed section, whole.
    t = re.sub(r'<div class="nav-category[^"]*">\s*<div class="category-header"(?:(?!<div class="nav-category).)*?'
               r'<a %s class="category-link.*?</ul>\s*</div>' % target, "", t, flags=re.S)
    # A category or featured-article card on the front page.
    t = re.sub(r'(?:<!--[^>]*-->\s*)?<a %s class="(?:category|featured)-card.*?</a>' % target, "", t, flags=re.S)
    # List items (no nested list inside).
    t = re.sub(r'<li\b[^>]*>(?:(?!</?li\b).)*?<a %s.*?</li>' % target, "", t, flags=re.S)
    # Anything else: the link's words stay.
    t = re.sub(r'<a %s[^>]*>(.*?)</a>' % target, r"\1", t, flags=re.S)
    # The sidebar's page counts.
    def count(m):
        return m.group(1) + "(%d)" % len(re.findall(r"<li\b", m.group(3))) + m.group(2) + m.group(3)
    t = re.sub(r'(<span class="page-count">)\(\d+\)(</span>\s*</div>\s*)(<ul class="category-pages.*?</ul>)',
               count, t, flags=re.S)
    return t
