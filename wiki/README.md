# MT2009 PLUS Wiki (metin2sp.pl/wiki)

Statyczna strona (HTML, CSS, JS – bez PHP i bazy danych), więc działa na
każdym zwykłym hostingu współdzielonym. Podstawą jest wiki MT2009
([wiki.mt2009.pl](https://wiki.mt2009.pl/), treści skopiowane za zgodą
MT2009.pl – wspomniane w stopce każdej strony), do której dokładamy strony
MT2009 PLUS.

## Jak dodać lub zmienić stronę MT2009 PLUS

1. Utwórz albo edytuj plik `wiki/pages/<adres>.md`, np. `boty.md` – strona
   będzie pod `metin2sp.pl/wiki/mt2009plus/boty/`.
2. Na górze pliku nagłówek:

   ```
   ---
   title: Boty w MT2009 PLUS
   group: gra
   category: Gra na MT2009 PLUS
   order: 20
   keywords: boty, playerboty, sklepy
   ---
   ```

   `group` to `gra` (rozgrywka) albo `serwer` (administracja) – decyduje o
   sekcji w menu; `order` ustala kolejność w menu (mniejsza liczba = wyżej),
   `keywords` pomagają wyszukiwarce.
3. Treść pisz w Markdown: `## Nagłówek`, `**pogrubienie**`, listy `- `,
   tabele `| a | b |`, linki `[tekst](adres)`, kod w `` `…` ``.
   `{{LISTA_STRON}}` (tylko na stronie `index.md`) wstawia listę wszystkich
   naszych stron.
4. Zbuduj i wgraj (niżej). Strona sama trafia do menu bocznego „MT2009
   PLUS”, do listy na stronie MT2009 PLUS i do wyszukiwarki.

## Budowanie (na VPS, potrzebny tylko Docker)

```sh
sh wiki/build.sh
```

Wynik: `/opt/metin2/dist/wiki/wiki/` (folder strony) i
`/opt/metin2/dist/wiki/mt2009plus-wiki.zip`.

Skrypt bierze kopię wiki MT2009 z `/opt/metin2/wiki-src/mirror` (nie ma jej
w Git – to ok. 67 MB obrazków gry). Nowszą kopię ich wiki pobiera
`python3 /opt/metin2/wiki-src/crawl.py /opt/metin2/wiki-src/mirror`.

## Wgrywanie na hosting

Rozpakuj `mt2009plus-wiki.zip` i wgraj folder **`wiki`** przez FTP do
katalogu strony (`public_html`, `www` albo `domains/metin2sp.pl/public_html`)
tak, żeby powstało `public_html/wiki/index.html`. Plik `.htaccess` w tym
folderze ustawia stronę startową i cache obrazków (Apache/LiteSpeed; na
nginx wystarczy zwykłe serwowanie plików).

## Co robi `build.py`

- przepina wszystkie adresy z `/` na `/wiki/` (strony, obrazki, skrypty,
  style, dane, wyszukiwarka),
- zamienia nazwę na MT2009 PLUS Wiki, linki w stopce na metin2sp.pl i nasz
  Discord oraz dopisuje źródło treści,
- usuwa skrypt statystyk Cloudflare z ich stron (ich token),
- składa nasze strony z `pages/*.md` w tym samym wyglądzie,
- przebudowuje indeks wyszukiwarki (`lunr-build.js`) razem z naszymi stronami.

## Podgląd na VPS

Przed wgraniem na hosting wiki jest pod `http://179.61.251.72/wiki/`:
kontener `mt2009plus-wiki` (nginx, `--restart unless-stopped`) serwuje
`/opt/metin2/dist/wiki` z konfiguracją `/opt/metin2/wiki-preview/nginx.conf`
(z nagłówkiem `X-Robots-Tag: noindex`, żeby Google nie zapamiętał adresu
z IP). Po `sh wiki/build.sh` zmiany widać od razu, bez restartu.
