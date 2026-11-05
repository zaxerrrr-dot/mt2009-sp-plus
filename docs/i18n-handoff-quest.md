# i18n handoff – server quests and server texts (branch claude/y-tr-quest)

State at handoff (5 Nov 2026). The server core (`server-patches/language`, `mt2009_language.{h,cpp}`,
`quest/mt2009_language.lua`, `language.sql`) is finished. Only hand translations of **our own** texts are left.

## What exists per language

All dictionaries are in `linux-port/docker/game/lang/<code>/` – UTF-8, one `Polish<TAB>translation` per line,
`\t \n \\` escapes, `#` comments. The server converts them to the client code page (`language.cfg`).

| file | what | made by |
|---|---|---|
| `10_quest_stock.tsv` | stock quests (official texts) | `tools/i18n/build_server_lang.py` – never edit |
| `20_server_locale.tsv` | engine LC_TEXT (official texts) | generator – never edit |
| `item_names.tsv`, `mob_names.tsv` | official names (vnum<TAB>name) | generator |
| `22_server_locale_more.tsv` | LC_TEXT lines the official sources lack | hand (L ids) |
| `30_quest_custom.tsv` | our quests' texts | hand (Q ids) |
| `32_quest_templates.tsv` | our quests' glued lines as formats (`Za %s sekund ...`) | hand (T ids) |
| `35_quest_fragments.tsv` | pieces of glued lines | hand (F ids) |
| `40_server_custom.tsv` | our C++ chat lines | hand (S ids) |

Hand files are **complete** for: en, de, tr, ro, es, it. (`extract_server_texts.py --check <lang>` still reports ~300
"missing" for those – these are GM/debug/technical lines and names that stay Polish on purpose.)

**Remaining: fr, pt, cz, hu, gr, ae – 3 968 texts each** (Q 2 412, T 331, F 373, S 410-ish, L 298 – counted by
`export_staging.py`). At handoff, four Opus agents were still translating into the scratchpad:
`/tmp/claude-0/-root/9f475014-d1bc-4cf4-a3e1-da3c380fc52c/scratchpad/tw/w2_{A,B,CTL}.fr` and `w2_A.pt`. If those
files exist and pass the check, merge them first (step 0) – then export again.

## Step 0 (integrator, optional) – merge the scratchpad results that finished

```sh
cd /opt/metin2/git/wt-yohara/tools/i18n/handoff
T=/tmp/claude-0/-root/9f475014-d1bc-4cf4-a3e1-da3c380fc52c/scratchpad/tw
for g in A B CTL; do for x in fr:cp1252 pt:cp1252; do l=${x%%:*}; c=${x#*:}
  [ -s $T/w2_$g.$l ] && python3 check_tr2.py w2_$g $T/w2_$g.$l $c && python3 merge.py $l $T/w2_$g.$l
done; done
```
(`check_tr2.py` must print `problems 0` before `merge.py`; `merge.py` writes the hand files by id prefix.)

## Step 1 – export (already run once; re-run after any merge)

```sh
python3 /opt/metin2/git/wt-yohara/tools/i18n/handoff/export_staging.py            # fr pt cz hu gr ae
python3 /opt/metin2/git/wt-yohara/tools/i18n/handoff/export_staging.py fr         # one language
```
Writes `/opt/metin2/cache/i18n-staging/quest/<lang>/001.tsv …` (~300 lines each):
`id<TAB>Polish source<TAB>English reference<TAB>` (4th column empty = the target). Re-running deletes and rewrites the
language's staging folder with what is still untranslated.

## Step 2 – translators (Haiku): fill column 4, nothing else

Give each translator ONE staging file, `tools/i18n/handoff/RULES_<lang>.md` (complete rules – read it) and the
glossary `tools/i18n/handoff/glossary_<lang>.tsv` (Polish<TAB>English<TAB>target<TAB>kind – official item/monster
names; grep it). The official phrasing of the stock game: `linux-port/docker/game/lang/<lang>/10_quest_stock.tsv`.
Short version of the rules:

1. Write the translation into column 4 only; keep columns 1-3 and the line order unchanged; one line per id.
2. Same printf placeholders in the same order (`%d %s %u %ld %lld %.1f %02d %%` …). `T` ids: every `%s` is a value
   glued in at runtime – keep each one.
3. Same `[ENTER]`, `[COLOR …]`, `[DELAY …]`, `[INSERT_IMAGE …]` tags; same leading/trailing spaces (`F` ids are pieces
   glued to numbers/names: `" Yang."` keeps its leading space).
4. Keep length close to the Polish; do not merge lines; quest window lines are cut mid-sentence on purpose.
5. Official names from the glossary (PB / SZC markers as the glossary writes them, e.g. fr/pt/cz… – grep `(PB)`).
   Proper names (Yohara, Seon-Hae, Chaegirab, Jaharr, Enasir, Balathor, Sung Mahi, Erebu, Nemere, Razador as the
   glossary has it) stay.
6. Never write Metin2, Gameforge, "official server", Ameria, metin2alerts.
7. Only characters of the code page: fr/pt cp1252, cz/hu cp1250, gr cp1253, ae cp1256. Straight quotes, "-".
8. Technical lines (GM command syntax like `/goblin gm …`, debug lines full of `%u`, already-English lines from the
   engine): copy the Polish into column 4 unchanged (the importer then skips them).
9. Tone: friendly MMORPG, informal "you" as the stock file of the language does; group messages plural.

Quick self-check a translator can run on its file (prints nothing bad when OK):
`python3 tools/i18n/handoff/import_staging.py <lang> <file> --dry-run`

## Step 3 – import (integrator, Opus)

```sh
cd /opt/metin2/git/wt-yohara
python3 tools/i18n/handoff/import_staging.py fr --dry-run      # report only
python3 tools/i18n/handoff/import_staging.py fr                # validate + merge all staging/fr/*.tsv
python3 tools/i18n/extract_server_texts.py --check fr          # what is still missing
git add linux-port/docker/game/lang/fr && git commit -m "Languages: French …"
```
The importer rejects (and lists `REJECTED file:line id - reason`) a line with an empty target, other placeholders /
tags / edge spaces than the Polish, a character the code page lacks, or a forbidden name; exit code 1 when anything
was rejected – fix those lines in the staging file and run again (merging is idempotent; a later run overwrites the
same Polish keys). Then re-run `export_staging.py <lang>` to see what is left.

## Pitfalls

* The Write tool of an agent drops trailing spaces – the importer rejects those lines ("edge spaces"); restore them.
* A Polish `%` before a letter (`10% do`) is not a placeholder for the checker (space flag excluded) – translations
  may write `10% of`. A real `%d` must survive.
* `T` lines are matched at runtime as formats: a wrong `%s` order swaps values; never add a `%`.
* Never edit `10_` / `20_` / `item_names` / `mob_names` by hand (regenerated by `build_server_lang.py`).
* `merge.py` / `export_staging.py` / `import_staging.py` need `all_pl.tsv`, `w2_A`, `w2_B`, `w2_CTL` from this folder
  (the id → Polish master list). If our quests change, re-run `tools/i18n/extract_server_texts.py` – new texts get no
  id here; translate them by appending `Polish<TAB>translation` to the hand files directly (same checks).
* Test locally: `tools/i18n/lua50/build.sh` builds the engine's Lua 5.0 (`lua50 syn.lua <file>` style checks).
