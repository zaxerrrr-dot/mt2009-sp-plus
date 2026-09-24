#!/usr/bin/env python3
"""MT2009 PLUS Wiki - builds the static site for metin2sp.pl/wiki.

The base is the MT2009 wiki (wiki.mt2009.pl, copied with its owners'
permission) as crawled into MIRROR (crawl.py, /opt/metin2/wiki-src/mirror):
its built pages, styles, scripts, images and search index. This script
re-roots every absolute link under PREFIX, puts the MT2009 PLUS name, links
and credit in the header and footer, and adds our own pages from
wiki/pages/*.md (front matter: title, category, order) in the same layout,
in the navigation and in the search index (rebuilt by lunr-build.js).

    python3 build.py MIRROR OUT      # OUT/wiki/... ready for the hosting
"""
import html, json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edits

PREFIX = "/wiki"
SITE = "MT2009 PLUS Wiki"
# Our pages' two sections (front matter "group:"): playing vs. running the server.
GROUPS = [("gra", "Gra na MT2009 PLUS", "fa-gamepad"),
          ("serwer", "Serwer i administracja", "fa-server")]
HERE = os.path.dirname(os.path.abspath(__file__))

try:
    import markdown
except ImportError:
    sys.exit("pip install markdown")


def rewrite_html(t):
    # Every root-absolute attribute under the prefix ("//cdn" untouched).
    t = re.sub(r'((?:href|src|content|action|poster|data-[a-z-]+)=")/(?!/)', r'\1%s/' % PREFIX, t)
    t = re.sub(r"(url\(['\"]?)/(?!/)", r"\1%s/" % PREFIX, t)
    t = re.sub(r'(["\'])/(images|data|_astro|lib)/', r'\1%s/\2/' % PREFIX, t)
    return t


def rebrand(t, sidebar=""):
    # MT2009's Cloudflare Web Analytics beacon (their token): our visits are
    # not theirs to count.
    t = re.sub(r'<script[^>]*cloudflareinsights[^>]*>\s*</script>', '', t)
    t = t.replace('<meta name="robots" content="noindex, nofollow">', '<meta name="robots" content="index, follow">')
    t = re.sub(r"<title>Mt2009 Wiki</title>", "<title>%s</title>" % SITE, t)
    t = re.sub(r"<title>([^<]*?)\s*[|-]\s*Mt2009 Wiki</title>", r"<title>\1 | %s</title>" % SITE, t)
    t = t.replace("MT2009 Wiki Logo", SITE)
    t = t.replace("Kompendium wiedzy o świecie MT2009", "Kompendium wiedzy o świecie MT2009 PLUS")
    # Header: the MT2009 PLUS pages beside "Wszystkie strony".
    t = re.sub(r'(<a href="%s/all-pages" class="btn btn-secondary"[^>]*>.*?</a>)' % PREFIX,
               r'\1 <a href="%s/mt2009plus/" class="btn btn-secondary">MT2009 PLUS</a>' % PREFIX, t, count=1, flags=re.S)
    # Footer: our site, the credit to the MT2009 wiki.
    t = t.replace("Oficjalne kompedium wiedzy serwisu MT2009.pl",
                  "Kompendium wiedzy MT2009 PLUS &middot; na podstawie wiki.mt2009.pl, za zgodą MT2009.pl")
    t = t.replace('<a href="https://mt2009.pl" target="_blank" rel="noopener">Oficjalna strona serwisu</a>',
                  '<a href="https://metin2sp.pl/" target="_blank" rel="noopener">metin2sp.pl</a> '
                  '<a href="https://metin2sp.pl/discord" target="_blank" rel="noopener">Discord MT2009 PLUS</a> '
                  '<a href="https://wiki.mt2009.pl/" target="_blank" rel="noopener">Wiki MT2009</a>')
    t = t.replace("&copy; 2026 MT2009.pl Wiki", "&copy; 2026 MT2009 PLUS &middot; treści MT2009 &copy; MT2009.pl")
    t = re.sub(r">\s*MT2009 Wiki\s*<", ">MT2009 PLUS Wiki<", t)
    t = t.replace("Witaj w MT2009 Wiki", "Witaj w MT2009 PLUS Wiki")
    t = t.replace("Kompleksowa baza wiedzy o świecie MT2009.", "Kompleksowa baza wiedzy o świecie MT2009 i MT2009 PLUS.")
    # The sidebar: our pages before "Inne strony".
    if sidebar:
        t = t.replace("<!-- Inne strony -->", sidebar + "<!-- Inne strony -->", 1)
    return t


def rewrite_js(t):
    for a, b in [('"/data/', '"%s/data/' % PREFIX), ('"/images/', '"%s/images/' % PREFIX),
                 ("`/search-index.json", "`%s/search-index.json" % PREFIX),
                 ('"/search?q=', '"%s/search?q=' % PREFIX), ("`/search?q=", "`%s/search?q=" % PREFIX),
                 ('"/search"', '"%s/search"' % PREFIX), ('"/search/"', '"%s/search/"' % PREFIX)]:
        t = t.replace(a, b)
    # Vite's preload map names chunks from the site root ("/" + "_astro/..").
    t = t.replace('"_astro/', '"%s/_astro/' % PREFIX.strip("/"))
    # A search hit's link: "/" + its url.
    t = re.sub(r'\.startsWith\("/"\)\|\|\((\w)="/"\+\1\)', r'.startsWith("/")||(\1="%s/"+\1)' % PREFIX, t)
    return t


def read_page(path):
    raw = open(path, encoding="utf-8").read()
    meta = {}
    m = re.match(r"---\n(.*?)\n---\n", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        raw = raw[m.end():]
    return meta, raw


def main():
    mirror, out = sys.argv[1], sys.argv[2]
    site = os.path.join(out, PREFIX.strip("/"))
    shutil.rmtree(site, ignore_errors=True)
    shutil.copytree(os.path.join(mirror, "assets"), site)
    for root, _, files in os.walk(site):
        for f in files:
            p = os.path.join(root, f)
            # Read first, then write: open(p, "w") empties the file.
            if f.endswith(".js"):
                t = rewrite_js(open(p, encoding="utf-8").read())
            elif f.endswith(".css"):
                t = re.sub(r"(url\(['\"]?)/(?!/)", r"\1%s/" % PREFIX, open(p, encoding="utf-8").read())
            elif f.endswith(".json") and f != "search-index.json":
                t = open(p, encoding="utf-8").read().replace('"/images/', '"%s/images/' % PREFIX)
            else:
                continue
            open(p, "w", encoding="utf-8").write(t)
    # Our pages, in the FAQ page's layout.
    ours = []
    for f in sorted(os.listdir(os.path.join(HERE, "pages"))):
        if not f.endswith(".md"):
            continue
        meta, body = read_page(os.path.join(HERE, "pages", f))
        slug = f[:-3]
        ours.append((int(meta.get("order", "100")), slug, meta, body))
    ours.sort()
    entries = []
    for _, slug, meta, body in ours:
        title = meta.get("title", slug)
        # Links in our pages are written from the site root, like MT2009's.
        content = rewrite_html(markdown.markdown(body, extensions=["tables", "fenced_code", "toc", "sane_lists"]))
        url = "mt2009plus/" if slug == "index" else "mt2009plus/%s/" % slug
        entries.append((url, title, meta, content))
    def in_group(g):
        return [(u, tt) for u, tt, m, _ in entries if u != "mt2009plus/" and m.get("group") == g]
    sidebar = "".join(
        '<div class="nav-section"> <h3 id="mt2009plus-%s"> <i class="fas %s"></i> %s </h3> <ul>' % (g, icon, name) +
        "".join('<li> <a href="%s/%s" data-astro-prefetch="false"> <i class="fas fa-file-lines page-icon"></i> %s </a> </li>'
                % (PREFIX, u, html.escape(tt)) for u, tt in in_group(g)) + '</ul> </div> '
        for g, name, icon in GROUPS)
    shell = None
    corrected = {}
    pages_dir = os.path.join(mirror, "pages")
    published = 0
    for root, _, files in os.walk(pages_dir):
        for f in files:
            if f != "index.html":
                continue
            src = os.path.join(root, f)
            rel = os.path.relpath(root, pages_dir)
            if rel != "." and edits.is_removed(rel.replace(os.sep, "/")):
                continue
            t, extra = edits.apply(rel.replace(os.sep, "/"), open(src, encoding="utf-8").read())
            if extra:
                corrected[rel.replace(os.sep, "/") + "/"] = extra
            t = rebrand(rewrite_html(edits.strip_links(t)), sidebar)
            dst = os.path.join(site, "" if rel == "." else rel)
            os.makedirs(dst, exist_ok=True)
            open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(t)
            published += 1
            if rel == "faq":
                shell = t
    # The search index's "index" entry is the front page.
    os.makedirs(os.path.join(site, "index"), exist_ok=True)
    shutil.copyfile(os.path.join(site, "index.html"), os.path.join(site, "index", "index.html"))

    def listing(g):
        return "<ul>%s</ul>" % "".join('<li><a href="%s/%s">%s</a></li>' % (PREFIX, u, html.escape(tt)) for u, tt in in_group(g))
    lists = {"{{LISTA_%s}}" % g.upper(): listing(g) for g, _, _ in GROUPS}
    lists["{{LISTA_STRON}}"] = "".join("<h3>%s</h3>%s" % (name, listing(g)) for g, name, _ in GROUPS)

    for url, title, meta, content in entries:
        for k, v in lists.items():
            content = content.replace("<p>%s</p>" % k, v).replace(k, v)
        t = re.sub(r"<main([^>]*)>.*</main>",
                   lambda m: '<main%s><article class="wiki-content mt2009plus-page"><h1>%s</h1>%s</article></main>'
                   % (m.group(1), html.escape(title), content), shell, count=1, flags=re.S)
        t = re.sub(r"<title>[^<]*</title>", "<title>%s | %s</title>" % (html.escape(title), SITE), t, count=1)
        t = re.sub(r'<nav class="toc-nav" id="toc-nav">.*?</nav>', '<nav class="toc-nav" id="toc-nav"></nav>', t, flags=re.S)
        dst = os.path.join(site, url)
        os.makedirs(dst, exist_ok=True)
        open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(t)

    # Search: the MT2009 entries and ours, for lunr-build.js.
    idx = json.load(open(os.path.join(mirror, "assets", "search-index.json"), encoding="utf-8"))
    docs = [d for d in idx["pages"] if not edits.is_removed(d["url"])]
    for d in docs:
        d["title"] = d["title"].replace("Mt2009 Wiki", SITE)
        if d["url"] in corrected:
            d["content"] = "MT2009 PLUS: " + corrected[d["url"]] + " " + d["content"]
    for url, title, meta, content in entries:
        text = html.unescape(re.sub(r"<[^>]+>", " ", content))
        docs.append({"url": url, "title": title, "category": meta.get("category", "MT2009 PLUS"),
                     "content": re.sub(r"\s+", " ", text).strip(),
                     "headings": " ".join(re.findall(r"<h[23][^>]*>(.*?)</h[23]>", content)),
                     "keywords": meta.get("keywords", "")})
    json.dump({"version": idx["version"] + "-plus", "pages": docs},
              open(os.path.join(out, "search-docs.json"), "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(site, ".htaccess"), "w").write(
        "DirectoryIndex index.html\nOptions -Indexes\n"
        "ErrorDocument 404 %s/index.html\n"
        "<IfModule mod_expires.c>\nExpiresActive On\nExpiresByType image/png \"access plus 30 days\"\n"
        "ExpiresByType text/css \"access plus 7 days\"\nExpiresByType application/javascript \"access plus 7 days\"\n</IfModule>\n" % PREFIX)
    print("pages from MT2009: %d, ours: %d, search docs: %d" % (
        published, len(entries), len(docs)))


if __name__ == "__main__":
    main()
