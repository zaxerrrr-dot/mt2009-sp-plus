# Druga ścieżka umiejętności („skill hack”)

Postać może rozwijać i używać umiejętności **drugiej ścieżki swojej klasy** obok ścieżki głównej – np. wojownik
(body) ma Aurę Miecza i Duchowe Uderzenie, szaman (smok) Leczenie. Znacznik: `MT2009_PLUS_SKILL_HACK_V1 (…)`,
w kodzie i logach prefiks `SKILL2` („SKILL_HACK:” w hack logu to nadal wykrywanie oszustw z `input_main.cpp`).
Plan: `/opt/metin2/cache/yohara/PLAN-SKILL-HACK.md`.

## Decyzje właściciela (4.11.2026)

| | Decyzja |
|---|---|
| P1 | bez osobnej nazwy: gracz wybiera ścieżkę główną jak dotąd (poz. 5), druga jest dodatkowa – w oknie umiejętności druga zakładka z jej zwykłą nazwą |
| P2 | wspólna pula punktów, dokładnie jak dziś (bez dodatkowych punktów) |
| P3 | bez limitów PvP (moc 100 %, stopień do P, wszystkie mapy) |
| P4 | 9. umiejętność drugiej ścieżki – tak (Ninja 177/178, Sura 179/180, Szaman 181/182; Trzęsienie 176 wojownika jest wspólne) |
| P5 | wyłączenie = uśpienie: poziomy zostają, umiejętności nie da się używać, uczyć ani zapominać, klient je ukrywa |
| P6 | Dopalacz (236–243) – tylko ścieżka główna (bez zmian) |
| P7 | Seon-Hae, wymiana ksiąg – tylko księgi ścieżki głównej (bez zmian) |
| P8 | po wyłączeniu wpisy obcych umiejętności znikają z paska szybkiego dostępu |
| P9 | Kamienie Duchowe (G1 → P) działają dla drugiej ścieżki jak dla własnej |
| P10 | od poziomu 5 (gdy ścieżka jest wybrana) |
| P11 | przełącznik na żywo: flaga zdarzenia `m2_skill_hack` |

## Przełącznik

- `.env`: `M2_SKILL_HACK=0` (domyślnie wyłączony; `1/on/yes/true` = włączony) → `docker-compose.yml` →
  `mariadb/playerbot/apply.sh` zapisuje flagę zdarzenia `m2_skill_hack` przy starcie, tylko gdy `.env` zmienił się
  od poprzedniego startu (`m2_skill_hack_env` = wartość + 1) – jak `M2_SHOP_BIG`.
- Na żywo: `/e m2_skill_hack 1|0` (GM) albo strona `.env` panelu (klucz w `LIVE_KEYS`: flaga + wiersz `SKILL2`
  w `web_admin_queue`, który `web_admin.quest` ustawia w działających rdzeniach). `CQuestManager::SetEventFlag`
  woła `Skill2FlagChanged` – każdy gracz online dostaje `SKILL2 1|0` (klient pokazuje/chowa zakładkę), przy
  włączeniu jeszcze raz pakiet poziomów umiejętności, przy wyłączeniu czyszczone są jego wpisy pasków 61–67.
- Rdzeń czyta tylko flagę (`skill2::Enabled`), log: `SKILL2: on|off (event flag m2_skill_hack = N)`.

## Haki (`edits.json`, generator `gen_edits.py`, po `skill9`, `riposty`, `buffi`)

| Plik | Miejsce | Co |
|---|---|---|
| `char_skill.cpp` | `IsLearnableSkill` (przed hakami Buffi/ripost/9.) | obca umiejętność: tylko gracz + włączony przełącznik; przy wyłączonym **false** (uszczelnia dawną lukę: księga drugiej ścieżki przechodziła regułę „tylko klasa”); obca 9. umiejętność – poziom < 40 |
| `char_skill.cpp` | `CanUseSkill` (przed `Skill9CanUse`) | obca umiejętność dozwolona przy włączonym przełączniku (użycie, `/skillup`, pakiet ataku) |
| `char_skill.cpp` | `IsUsableSkillMotion` | ruch obcej 9. umiejętności (9/24 +25 na stopień) i grupa `(job+1)*10 + (3-ścieżka)` w pętli – tylko gdy umiejętność jest nauczona; bez tego pierwsze użycie = `SKILL_HACK:` i rozłączenie |
| `input_login.cpp` | po `BuffiOnLogin` | `Skill2OnLogin`: `SKILL2 1|0` do klienta (+ pakiet poziomów albo czyszczenie pasków) |
| `questmanager.cpp` | `SetEventFlag` | `m2_skill_hack` → `Skill2FlagChanged` |

Funkcje: `linux-port/overlays/playerbot/src/game/src/playerbot_skillhack.{h,cpp}`. Boty, towarzysze i Buffi nigdy
(`Applies`: PC z własnym połączeniem, `!desc->IsBot()`, ścieżka 1/2, klasy 0–3) – dla nich obca umiejętność jest
nieuczalna i nieużywalna jak dotąd.

Bez zmian (decyzje): punkty (wspólne `POINT_SKILL`, blokada 17–19 i reset jak dla każdej), `GetSkillPower`,
obrażenia PvP, dopalacz, riposty, Seon-Hae, tożsamość postaci (łucznik, czarna magia, boty oceniające graczy –
patrzą na ścieżkę główną). Reset umiejętności (`ClearSkill`) zeruje też drugą ścieżkę i oddaje jej punkty. Baza
danych – bez zmian (wszystkie 265 poziomów i tak są w `player.skill_level`).

## Questy

- `linux-port/docker/game/quest/training_grandmaster_skill.quest` – kopia questu paczki (Kamień Duchowy 50513);
  przy fladze `m2_skill_hack` lista dostaje też umiejętności drugiej ścieżki na G1–G10. Nauka i tak przechodzi przez
  `LearnGrandMasterSkill` → `IsLearnableSkill`. Dopisany do listy questów w `Dockerfile` (zastępuje obiekty paczki).
- `mikstura_talentu.quest` – Mikstura Talentu (9. umiejętność G1 → P): przy fladze także obca 9. umiejętność
  (wybór, gdy obie są na G).

## Klient (root, bez zmian exe)

`skillhack.py` (stan z `SKILL2`, sloty 61–66 + 67), `playersettingmodule.py` (`RegisterSkill` → obce sloty),
`uicharacter.py` + `uiscript/characterwindow.py` (trzeci przycisk: `[główna] [druga] [Koń]`), `game.py`
(komenda `SKILL2`). Exe sprawdzone: animacje obu ścieżek ładowane dla każdej rasy, `CanUseSkill` bez ścieżki,
sloty do 265, quickslot `pos < SKILL_MAX_NUM`.
