# i18n handoff – CLIENT area (MT2009_PLUS_LANG_V1)

Branch `claude/y-tr-client` (worktree `/opt/metin2/git/wt-y-tr-client`). This file tells the next agents how to finish
the client translations **mechanically**. Haiku agents ONLY translate staging chunks; one Opus agent imports, verifies
and commits.

## 1. How the system works (short)

- Polish (`pl`, CP1250) is the source. Every other language is **generated at build time** from the final Polish client
  data by `client-patches/client-2.0.30/tools/lang/build_lang_packs.py` into a new pack `lang` (`locale/<code>/…`).
- Translations live in `client-patches/lang/<code>/` (UTF-8 TSV):
  - `language.cfg` – NAME / NATIVE / CODEPAGE / ORDER;
  - `keyed_orig.tsv`, `tm_orig.tsv` – imported originals (Owsap / upstream). **Generated, never edit.**
  - `tm.tsv` – OUR translations: `Polish text <TAB> translation` (any domain). **This is what the import writes.**
  - `keyed.tsv` – OUR per-key translations (only whole description files: `file <TAB> name <TAB> Polish <TAB> text`).
- Lookup per text: language tables → English → Polish with diacritics folded. A text missing in a language therefore
  shows English, never broken Polish.
- Texts that differ only in numbers are translated once ("numeric templates").
- Escapes inside TSV cells: `\t`, `\n`, `\\`.

## 2. Status at handoff (5 Nov 2026, catalog of the 3.0.15 client build, own-translation coverage)

| lang | codepage | own coverage (entries) | left to translate (export) | works on the current exe-src20 |
|---|---|---|---|---|
| en | 1252 | ~99.9 % | 8 texts | yes |
| de | 1252 | 59 % | 4 636 texts / 204 k chars (16 chunks) – Yohara/3.0.15 content | yes |
| tr | 1254 | 52 % | 6 489 / 255 k (22 chunks) | needs exe-src21 |
| ro | 1250 | 47 % | 7 495 / 283 k (25) | yes |
| es | 1252 | 47 % | 7 461 / 282 k (25) | needs exe-src21 |
| it, fr, pt | 1252 | 43 % (Owsap originals only) | ≈8 250 / 323 k (28 each) | needs exe-src21 |
| cz, hu | 1250 | 43 % | ≈8 220 / 323 k (28 each) | yes |
| gr | 1253 | 43 % | 8 214 / 323 k (28) | needs exe-src21 |
| ae | 1256 | 43 % | 8 189 / 322 k (28) | needs exe-src21 |

Untranslated texts show the English text (en is complete), so every language is usable already.
Exact numbers: the export prints them per language (`N texts to translate, M chunks, C chars`). `ae` (Arabic) is
lowest priority (the UI has no right-to-left layout).

## 3. Staging (already exported once)

Directory: `/opt/metin2/cache/i18n-staging/client/<lang>/`
- `<lang>_NNN.tsv` – chunks of 300 rows: `id <TAB> Polish source <TAB> English reference <TAB> (empty target)`
- `_manifest.tsv` – id → domain/key/Polish (**do not edit**; the import needs it)
- `_glossary.tsv` – official game terms Polish → language (Owsap originals). Read-only help.

Re-export (after new client content, or after an import to see what is left):
```
S=/opt/metin2/cache/i18n-staging/client
R=/opt/metin2/git/wt-y-tr-client   # or the checkout you work in
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $R/client-patches/client-2.0.30/tools/lang/staging.py \
  export <BASE pack dir> <OUT pack dir> $S [--lang de,tr] [--chunk 300]
```
BASE/OUT = a full client pack set (e.g. BASE=`/opt/metin2/cache/cY/pack` and OUT=an empty scratch dir with a copy of
`locale.index/.data` and `Index`; or clientY's `$C/azbase` + `$C/out/pack`). The export REWRITES the language's
staging dir (filled chunks there are lost → import first!).

## 4. Translator rules (give this section + one chunk to each Haiku agent)

Task: fill column 4 of every row of ONE chunk file, in the target language. Keep columns 1–3 unchanged. Write the
file back (UTF-8, tab-separated, one row per line, `\n` inside a cell stays the two characters backslash-n).

1. Placeholders and tags must stay EXACTLY (same ones, same count, positional ones in the same order):
   `%d %s %i %u %x %.0f %0.f %.1f %3d %(name)s %(n)d %%`, `{0} {1} {} {:02d}`, `[ENTER]`, `[DELAY value;0]`, `[WAIT]`,
   colour tags `|cFFxxxxxx` … `|r`, `|h`, `|H…`, `|E…|e`, one-letter key tags like `[K]`. Keep leading/trailing spaces
   and a trailing `:` / `: ` exactly (code appends a value after it).
2. Numbers: every number of the source, same digits, same order (write "Level 3", not "3rd level").
3. Never write: Metin2 (any form), Gameforge, Webzen, Ameria, metin2alerts, or "official/officially" in any
   language (offiziell, oficial, ufficiale, officiel, oficiální, hivatalos, resmi, επίσημ…, رسمي). Rephrase neutrally
   ("sealed document", "standard game music"). URLs like `metin2sp.pl`, `github.com/…` and `MT2009 PLUS` stay as they are.
4. Slash commands and their arguments stay unchanged (`/go trent2`, `/level 99`); only the description after them is
   translated. Strings that are identifiers, file names, garbled/Korean text (`şó ĹĄşę`, `Ář»ç…`) → copy the Polish.
5. Use official game terms: look the Polish term up in `_glossary.tsv` of the language (e.g. `grep -i "Kamień Duszy"`),
   and keep names consistent with what is already in `client-patches/lang/<lang>/tm.tsv`.
   Common: PŻ = HP (de TP), PE = SP/MP, PD = EXP, SM = the premium currency (en "DC"/"Dragon Coins",
   de "Drachenmünzen", tr "Ejderha Parası"), Yang stays Yang.
6. UI texts (short rows, labels, buttons, tabs): keep them about as short as the Polish/English one – the UI has fixed
   widths. Item / monster names: Title Case where the language uses it; expand Polish abbreviations (Czerw. = red,
   Plem. = tribal, (m)/(k) = male/female, MŚ = World Cup).
7. Use the language's own letters (de ä ö ü ß, tr ç ğ ı İ ş, ro ă â î ș ț, es ñ ¿ ¡, fr é è ê à ç œ, pt ã õ ç, cz č ř š ž ů,
   hu ő ű, Greek / Arabic script). Do NOT use emoji, curly “ ” quotes are fine only where the codepage has them (safer:
   straight quotes).
8. If the Polish source lacks diacritics ("Zlamanie odpornosci"), read it as Polish. The English column is a help, not
   the source; if they disagree, follow the Polish.

## 5. Import (Opus integrator)

```
R=/opt/metin2/git/wt-y-tr-client
python3 $R/client-patches/client-2.0.30/tools/lang/staging.py import /opt/metin2/cache/i18n-staging/client --dry-run
python3 $R/client-patches/client-2.0.30/tools/lang/staging.py import /opt/metin2/cache/i18n-staging/client [--lang de]
```
- Writes `client-patches/lang/<lang>/tm.tsv` (and `keyed.tsv` for description files).
- Refused rows (placeholders, numbers, forbidden name, character outside the language's codepage, tab/newline, unknown
  id) → `/opt/metin2/cache/i18n-staging/client/<lang>/_import_report.tsv`. Fix them (or give them back to a translator)
  and import again; importing twice is harmless (same Polish key = overwritten).
- Then verify on a full pack set (scratch OUT dir!):
```
B=<full pack dir, e.g. /opt/metin2/cache/cY/pack>; O=<scratch dir with copies of $B/locale.index $B/locale.data $B/Index>
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $R/client-patches/client-2.0.30/tools/lang/build_lang_packs.py \
  $B $O --lang-dir $R/client-patches/lang --report $O/lang_report.json      # coverage per language/domain in the json
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $R/client-patches/client-2.0.30/tools/lang/verify_lang.py $O $B
```
  `verify_lang.py` must end with `verify_lang: N languages ok` (missing keys, placeholder mismatch, forbidden names,
  missing vnums, encoding).
- Commit `client-patches/lang/` with a clear message. Never edit `*_orig.tsv`.

## 6. Pitfalls

- Do not run the export while filled chunks are not imported – it deletes the language's staging files.
- Never put a real TAB or newline into a cell; use `\t` / `\n`.
- A translation is keyed by its Polish text: if the Polish text later changes, the old translation is not used (it
  shows English) – just re-export and translate the new rows.
- Romanian: write ș/ț freely, the build maps them to the CP1250 ş/ţ.
- Codepages: pl/cz/hu/ro 1250, en/de/es/fr/it/pt 1252, gr 1253, tr 1254, ae 1256. A character the codepage lacks is
  refused by the import (e.g. Polish ł in a German text).
- The server (quest agent) must send its texts to a player in that player's codepage, same table.
- Owsap "originals" for some languages still have the English text in places (Owsap left them untranslated) – the
  import tool skipped those, the export lists them for translation.
- No new languages in this round (owner).

## 7. What still has to be built / merged (coordinator)

- Merge `claude/y-tr-client`. Files: root (`mt2009lang.py`, `uilanguage.py`, `ui.py`, `localeinfo.py`,
  `uiscriptlocale.py`, `intrologin.py`, `game.py`, `uioptionstabs.py`, `uisystem.py`, `playerbot_lang.py`,
  `playerbot_status_tail.py`, `uiminigame*.py`), tools/lang, client-patches/lang, client-patches/exe (4 files).
- `clientY.sh`: last pack step + verify (see the header of `build_lang_packs.py`):
  `S_lang_packs() { docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/lang/build_lang_packs.py $C/azbase $C/out/pack --lang-dir /opt/metin2/git/wt-yohara/client-patches/lang --report $C/lang_report.json; }; step lang_packs $C/lang.json S_lang_packs`
  and `lang/verify_lang.py` in the verify loop with `A="$C/azbase"`. New pack `lang` (~5.5 MB) + rewritten `locale`
  (old `locale/en/*` removed) go into the patch.
- exe: `cache/yohara/exe-src21` (= exe-src20 + the 4 overlay files, hard-linked copy) – NOT built. Build with
  `build.sh msvc --smoke` when the round's exe is made; without it the client offers only pl/en/de/ro/cz/hu.
