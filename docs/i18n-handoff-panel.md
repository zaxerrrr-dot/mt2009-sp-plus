# Web pages i18n – handoff (area: panel + all web pages)

Branch `claude/y-tr-panel`, worktree `/opt/metin2/git/wt-y-tr-panel`. Marker: `MT2009_PLUS_WEB_I18N_V1`.

## 1. What exists

| Part | Code | Language files |
|---|---|---|
| Seban panel (admin, Flask) | `linux-port/docker/seban-panel/m2i18n.py`, hooks in `app.py` (`ui_lang`, `translate_response`, `/i18n/<code>.json`, `/lang/<code>`), switcher in `templates/base.html` + `login.html` | `linux-port/docker/seban-panel/i18n/<code>.json` + `i18n/<code>/{names,game}.json` |
| Classic panel (landing, register, download, account, admin; Flask) | `linux-port/docker/panel/app/m2i18n.py` (copy), `admin_panel.py`: `I18N`, `lang()`, `_i18n_fill`/`i18n_fill_tables`, `i18n_translate_page`, `/i18n/<code>.json`, `/m2i18n-watch.js`, header `<select>` | `linux-port/docker/panel/app/i18n/...` (same layout). Sources are the **English** texts of its own tables plus Polish left in templates |
| ItemShop V3 (PHP, `/shop3/`) | `itemshop/app/shop3/include/functions/m2i18n.php`, `language.php` (translates `$lang_shop`, starts `ob_start('m2i18n_output')`), `header.php` (player's `player.player.language`), `i18n.php` (browser tables), switcher in `index.php`, `pages/shop/login.php` | `linux-port/docker/itemshop/app/i18n/...` (+ `<code>/itemdesc.json`) |
| Browser half (all apps) | `seban-panel/static/m2i18n-watch.js` (copied to `panel/app/` and `itemshop/app/` by `catalog.py sync`) | – |

How it works: the page is rendered in Polish and translated as a finished page (whole text → `{0}`-pattern → pieces around ` · `, `: `, `, `, sentences → names), fallback chain `<lang>` → `en` → unchanged. Language choice: `?lang=` → cookie `m2lang` (shared by all three apps) → (shop: player's game language) → `Accept-Language` only when it lists no Polish → Polish. A language appears in every switcher as soon as `i18n/<code>.json` exists (drop-in).

## 2. State (5 Nov 2026, end of my run)

`python3 tools/i18n/catalog.py stats` (share of the source text):

| | en | de | tr | ro | es | it | fr | pt | cz | hu | gr | ae |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Seban panel (7331) | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 97.4 | 69.2 | 0 | 0 |
| Classic panel (2207, en 327) | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 97.7 | 97.7 | 97.7 | 0 |
| ItemShop (709) | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 96.4 | 96.4 | 0 | 0 |
| Item names (28473 vnums) | 99.9 | 99.8 | 99.9 | 99.8 | 99.8 | 99.8 | 99.8 | 99.8 | 99.8 | 99.8 | 23.7 | 23.7 |

Still running when I stopped (Opus translators; their output lands in `tools/i18n/work/<part>/<lang>/done_*.json` and is picked up by step 4 below): Seban hu (chunks 0–11), Seban gr (0–11), round 2 cz (seban/panel/itemshop `done_100`), ItemShop + names gr, classic panel ae. **Run `staging.py import` once before re-exporting** so their results are merged and not translated twice.

Remaining work = exactly what `staging.py export` writes (`/opt/metin2/cache/i18n-staging/panel/<lang>/`, already exported once): cz 836 rows, hu 3079, gr 9192, ae 11216 (tr 1, it 1 = the Polish suffix "ów", may stay empty).

## 3. Files a translator touches

Only the staging TSVs: `/opt/metin2/cache/i18n-staging/panel/<lang>/<part>_NNN.tsv` (≈300 rows each), UTF-8, LF, header `id<TAB>source<TAB>english<TAB>target`. `<part>`: `seban`, `panel` (source is ENGLISH), `itemshop`, `names` (Polish item/monster name → game name). **Fill only column 4. Never edit id/source/english, never add or remove tabs or lines.**

## 4. Integrator (Opus) – mechanical steps

```
cd /opt/metin2/git/wt-yohara        # branch claude/yohara-3 (wt-y-tr-panel is the old, merged branch)
export UPSTREAM_NAMES=<dir with item_names_en/tr.json + mob_names_en/tr.json>   # see pitfall below
python3 tools/i18n/staging.py import                 # merges filled TSVs + any done_*.json; writes REJECTED.tsv per language
python3 tools/i18n/staging.py export                 # fresh TSVs with only what is still missing (overwrites old ones!)
#   ... translators fill the TSVs ...
python3 tools/i18n/staging.py import [lang ...]      # validate + merge; read <lang>/REJECTED.tsv, fix the rows, import again
python3 tools/i18n/check.py                          # forbidden words / placeholders / still-Polish
python3 tools/i18n/catalog.py stats
git add -A && git commit -m "Web i18n: <lang> ... - MT2009_PLUS_WEB_I18N_V1"
```
Import rejects: placeholder/tag mismatch (`{0}`, `{name}`, `%d`, `%s`, `%.1f`, `%%`, `<b>`…), id/source edited, not UTF-8, U+FFFD, control chars, mojibake, forbidden names. Accepted rows go to `tools/i18n/work/<part>/<lang>/done_2NN.json` → `catalog.py merge` → `i18n/<lang>.json` of the app; names go to `tools/i18n/names_extra/<lang>.tsv` → `build_names.py` regenerates `i18n/<lang>/names.json` in all three apps. Do not export again before importing (export deletes the old TSVs of that language).

Other commands:
- `python3 tools/i18n/extract.py` – re-scan sources after code changes (then export again).
- `python3 tools/i18n/catalog.py sync` – after editing `seban-panel/m2i18n.py` or `static/m2i18n-watch.js` (copies to panel/itemshop).
- `python3 tools/i18n/build_glossary.py`, `build_game_texts.py` – regenerate reference glossary / game texts from Owsap (already done).
- Syntax checks: `python3 -c "import ast;ast.parse(open('linux-port/docker/panel/app/admin_panel.py').read())"`; PHP: `docker run --rm -v $PWD/linux-port/docker/itemshop/app:/app php:8-cli php -l /app/shop3/include/functions/m2i18n.php`.

## 5. Rules for the translator (give these to the Haiku agents verbatim)

1. Fill column 4 only. Keep the row; never touch columns 1–3. Keep the file UTF-8, LF, one row per line, no tabs inside the text.
2. Translate column 2 (Polish; English in `panel_*.tsv`). Column 3 is an English reference – use it for meaning.
3. Keep every placeholder exactly: `{0}` `{1}` … (order may change), `{name}`, `%d`, `%s`, `%.1f`, `%%`, HTML tags `<b>…</b>`, emoji, arrows, `·`. Keep leading/trailing punctuation, a leading comma or lowercase start of a fragment.
4. Length: about the source length; buttons and labels short.
5. Tone: plain UI language, informal "you" (de du, cz ty, hu te, gr εσύ, tr sen, ro tu, es tú, it tu, pt você, fr vous, ae neutral MSA).
6. Game words: use the game's own term. Look it up (grep) in `tools/i18n/glossary/<lang>.tsv` (Polish → official term) and `linux-port/docker/seban-panel/i18n/<lang>/names.json` (item/monster names). Keep proper names: MT2009 PLUS, Seban, Discord, Playerbots, Yang, Shinsoo/Chunjo/Jinno, Docker, VPS, map/village names (Joan, Bokjung…), Metin (stone).
7. Currencies (keep consistent with the existing `<lang>.json`): Smocze Monety (SM) = Dragon Coins, Smocze Znaki (SZ) = Dragon Marks. Already used: cz Dračí mince (DM) / Dračí známky (DZ); hu Sárkányérme (SÉ) / Sárkányjel (SJ); gr Δρακονομίσματα / Δρακοσήματα; HP/SP/EXP as in the glossary (cz ZB/MB/BZK, hu TP/MP).
8. NEVER write: the game's brand name (Metin2), its publisher (Gameforge), the word "official" in any language, Ameria, metin2alerts. Rephrase ("the game", "the original game", drop the name). Exceptions only inside a file name/URL/path that must work: `Metin2Distribute.exe`, `metin2sp.pl`, `/opt/metin2`.
9. If the row is code (CSS, JS fragment, regex, shell command, identifier, `class="…"`), or already correct in the target language, copy column 2 into column 4 unchanged.
10. `names_*.tsv`: follow the existing patterns in names.json (e.g. "+N" levels kept, (m)/(k) gender markers as the game writes them in that language, dragon stones "Diament (Zwykly, Najnizszy)" → the language's stone (grade, clarity) words used for cz/hu/de).

## 6. Pitfalls

- `staging.py` runs `build_names.py`; without `UPSTREAM_NAMES` (dir holding the upstream `item_names_en/tr.json`, `mob_names_en/tr.json`, e.g. unzipped from `linux-port/docker/seban-panel/static/` of `/opt/metin2/cache/tieru-releases/metin2-server-protected-update-2.2.129.zip`) en/tr `names.json` lose ~450 entries. Re-run `build_names.py --upstream <dir>` if that happened.

- Polish suffix fragments (`ów`, `{0} połącze{1}`) come from templates that glue Polish endings; translate as well as possible or leave empty – a template change is the real fix.
- `state=oczekuje … message=…` rows: keep the `state=` value, translate only the message.
- `names.json` maps "Rybie Wnętrzności" to "Fishing Book" (that is the original game's mapping); several agents used "fish entrails" in UI texts – harmless.
- Romanian: `catalog.py` normalises ş/ţ to ș/ț in the UI files; names keep the game's letters.
- Pre-existing texts in `admin_panel.py` T (pl/en/de/tr, landing page "About") name the game's brand and "official"; they are the owner's and are shown natively for pl/en/de/tr (my catalogs cannot override built-in languages). Other languages use neutral wording. Owner/coordinator decision.
- `check.py` false positives: "officer" words in item names (es/pt/it/fr), Turkish "resmi" = picture, Romanian "Bijutierul"/"tierurile".
- `tools/i18n/work/` is not in git; catalogs (`i18n/*.json`) are the source of truth. Never run `catalog.py merge` on a language whose done files you deleted and expect them back – merging only adds.
- Server hook not deployed: the ItemShop reads `player.player.language` (quest branch column) and silently ignores it while the column is missing.
